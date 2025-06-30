#!/bin/bash

# Hotgigs.com - Google Cloud Platform Deployment Script
# This script deploys the complete application to GCP using Cloud Run, Cloud SQL, and Cloud Storage

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-""}
REGION=${REGION:-"us-central1"}
PROJECT_NAME="hotgigs"
ENVIRONMENT=${ENVIRONMENT:-"production"}
DOMAIN_NAME=${DOMAIN_NAME:-""}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check gcloud CLI
    if ! command_exists gcloud; then
        log_error "Google Cloud CLI not found. Please install it first:"
        echo "curl https://sdk.cloud.google.com | bash"
        echo "exec -l \$SHELL"
        echo "gcloud init"
        exit 1
    fi
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with Google Cloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check project ID
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [[ -z "$PROJECT_ID" ]]; then
            log_error "PROJECT_ID not set. Please set it as environment variable or run 'gcloud config set project YOUR_PROJECT_ID'"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed!"
    log_info "Using project: $PROJECT_ID"
    log_info "Using region: $REGION"
}

# Function to enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."
    
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        sql-component.googleapis.com \
        sqladmin.googleapis.com \
        storage.googleapis.com \
        cloudresourcemanager.googleapis.com \
        container.googleapis.com \
        artifactregistry.googleapis.com \
        secretmanager.googleapis.com \
        --project=$PROJECT_ID
    
    log_success "APIs enabled successfully!"
}

# Function to create Artifact Registry repository
create_artifact_registry() {
    log_info "Creating Artifact Registry repository..."
    
    # Check if repository already exists
    if gcloud artifacts repositories describe $PROJECT_NAME-repo --location=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
        log_info "Artifact Registry repository already exists"
    else
        gcloud artifacts repositories create $PROJECT_NAME-repo \
            --repository-format=docker \
            --location=$REGION \
            --description="Hotgigs.com container images" \
            --project=$PROJECT_ID
        
        log_success "Artifact Registry repository created!"
    fi
    
    # Configure Docker authentication
    gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
}

# Function to create Cloud SQL instance
create_cloud_sql() {
    log_info "Creating Cloud SQL PostgreSQL instance..."
    
    # Generate database password
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Check if instance already exists
    if gcloud sql instances describe $PROJECT_NAME-db --project=$PROJECT_ID >/dev/null 2>&1; then
        log_info "Cloud SQL instance already exists"
    else
        gcloud sql instances create $PROJECT_NAME-db \
            --database-version=POSTGRES_15 \
            --tier=db-f1-micro \
            --region=$REGION \
            --storage-type=SSD \
            --storage-size=20GB \
            --storage-auto-increase \
            --backup-start-time=03:00 \
            --maintenance-window-day=SUN \
            --maintenance-window-hour=04 \
            --project=$PROJECT_ID
        
        log_success "Cloud SQL instance created!"
    fi
    
    # Create database
    gcloud sql databases create hotgigs --instance=$PROJECT_NAME-db --project=$PROJECT_ID 2>/dev/null || log_info "Database already exists"
    
    # Create user
    gcloud sql users create hotgigs_user \
        --instance=$PROJECT_NAME-db \
        --password=$DB_PASSWORD \
        --project=$PROJECT_ID 2>/dev/null || log_info "User already exists"
    
    # Store database password in Secret Manager
    echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=- --project=$PROJECT_ID 2>/dev/null || \
    echo -n "$DB_PASSWORD" | gcloud secrets versions add db-password --data-file=- --project=$PROJECT_ID
    
    log_success "Cloud SQL setup completed!"
}

# Function to create Cloud Storage bucket
create_storage_bucket() {
    log_info "Creating Cloud Storage bucket..."
    
    BUCKET_NAME="$PROJECT_NAME-assets-$PROJECT_ID"
    
    # Check if bucket already exists
    if gsutil ls -b gs://$BUCKET_NAME >/dev/null 2>&1; then
        log_info "Storage bucket already exists"
    else
        gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
        
        # Make bucket publicly readable
        gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
        
        log_success "Storage bucket created: gs://$BUCKET_NAME"
    fi
}

# Function to build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    REGISTRY_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$PROJECT_NAME-repo"
    
    # Build and push backend image
    log_info "Building backend image..."
    docker build -t $REGISTRY_URL/backend:latest ./backend
    docker push $REGISTRY_URL/backend:latest
    
    # Build and push frontend image
    log_info "Building frontend image..."
    docker build -t $REGISTRY_URL/frontend:latest ./frontend \
        --build-arg VITE_API_BASE_URL=https://$PROJECT_NAME-backend-$(echo $PROJECT_ID | tr ':' '-')-uc.a.run.app
    docker push $REGISTRY_URL/frontend:latest
    
    log_success "Docker images built and pushed!"
}

# Function to create Cloud Run services
create_cloud_run_services() {
    log_info "Creating Cloud Run services..."
    
    REGISTRY_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$PROJECT_NAME-repo"
    
    # Get Cloud SQL connection name
    SQL_CONNECTION_NAME=$(gcloud sql instances describe $PROJECT_NAME-db --format="value(connectionName)" --project=$PROJECT_ID)
    
    # Deploy backend service
    log_info "Deploying backend service..."
    gcloud run deploy $PROJECT_NAME-backend \
        --image=$REGISTRY_URL/backend:latest \
        --platform=managed \
        --region=$REGION \
        --allow-unauthenticated \
        --set-env-vars="FLASK_ENV=production,FLASK_DEBUG=False" \
        --set-secrets="DATABASE_PASSWORD=db-password:latest" \
        --set-env-vars="DATABASE_URL=postgresql://hotgigs_user:\$(DATABASE_PASSWORD)@/hotgigs?host=/cloudsql/$SQL_CONNECTION_NAME" \
        --add-cloudsql-instances=$SQL_CONNECTION_NAME \
        --memory=1Gi \
        --cpu=1 \
        --concurrency=100 \
        --max-instances=10 \
        --project=$PROJECT_ID
    
    # Deploy frontend service
    log_info "Deploying frontend service..."
    BACKEND_URL=$(gcloud run services describe $PROJECT_NAME-backend --platform=managed --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
    
    gcloud run deploy $PROJECT_NAME-frontend \
        --image=$REGISTRY_URL/frontend:latest \
        --platform=managed \
        --region=$REGION \
        --allow-unauthenticated \
        --set-env-vars="VITE_API_BASE_URL=$BACKEND_URL" \
        --memory=512Mi \
        --cpu=1 \
        --concurrency=100 \
        --max-instances=10 \
        --project=$PROJECT_ID
    
    log_success "Cloud Run services deployed!"
}

# Function to setup load balancer
setup_load_balancer() {
    log_info "Setting up load balancer..."
    
    # Get Cloud Run service URLs
    BACKEND_URL=$(gcloud run services describe $PROJECT_NAME-backend --platform=managed --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
    FRONTEND_URL=$(gcloud run services describe $PROJECT_NAME-frontend --platform=managed --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
    
    # Create backend NEG
    gcloud compute network-endpoint-groups create $PROJECT_NAME-backend-neg \
        --region=$REGION \
        --network-endpoint-type=serverless \
        --cloud-run-service=$PROJECT_NAME-backend \
        --project=$PROJECT_ID 2>/dev/null || log_info "Backend NEG already exists"
    
    # Create frontend NEG
    gcloud compute network-endpoint-groups create $PROJECT_NAME-frontend-neg \
        --region=$REGION \
        --network-endpoint-type=serverless \
        --cloud-run-service=$PROJECT_NAME-frontend \
        --project=$PROJECT_ID 2>/dev/null || log_info "Frontend NEG already exists"
    
    # Create backend service for backend
    gcloud compute backend-services create $PROJECT_NAME-backend-service \
        --global \
        --project=$PROJECT_ID 2>/dev/null || log_info "Backend service already exists"
    
    gcloud compute backend-services add-backend $PROJECT_NAME-backend-service \
        --global \
        --network-endpoint-group=$PROJECT_NAME-backend-neg \
        --network-endpoint-group-region=$REGION \
        --project=$PROJECT_ID 2>/dev/null || true
    
    # Create backend service for frontend
    gcloud compute backend-services create $PROJECT_NAME-frontend-service \
        --global \
        --project=$PROJECT_ID 2>/dev/null || log_info "Frontend service already exists"
    
    gcloud compute backend-services add-backend $PROJECT_NAME-frontend-service \
        --global \
        --network-endpoint-group=$PROJECT_NAME-frontend-neg \
        --network-endpoint-group-region=$REGION \
        --project=$PROJECT_ID 2>/dev/null || true
    
    # Create URL map
    gcloud compute url-maps create $PROJECT_NAME-url-map \
        --default-service=$PROJECT_NAME-frontend-service \
        --project=$PROJECT_ID 2>/dev/null || log_info "URL map already exists"
    
    # Add path matcher for API
    gcloud compute url-maps add-path-matcher $PROJECT_NAME-url-map \
        --path-matcher-name=api-matcher \
        --default-service=$PROJECT_NAME-frontend-service \
        --path-rules="/api/*=$PROJECT_NAME-backend-service" \
        --project=$PROJECT_ID 2>/dev/null || true
    
    # Create HTTP(S) target proxy
    gcloud compute target-http-proxies create $PROJECT_NAME-http-proxy \
        --url-map=$PROJECT_NAME-url-map \
        --project=$PROJECT_ID 2>/dev/null || log_info "HTTP proxy already exists"
    
    # Create global forwarding rule
    gcloud compute forwarding-rules create $PROJECT_NAME-http-rule \
        --global \
        --target-http-proxy=$PROJECT_NAME-http-proxy \
        --ports=80 \
        --project=$PROJECT_ID 2>/dev/null || log_info "Forwarding rule already exists"
    
    log_success "Load balancer setup completed!"
}

# Function to setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring and logging..."
    
    # Create log-based metrics
    gcloud logging metrics create backend_errors \
        --description="Backend error count" \
        --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="'$PROJECT_NAME'-backend" AND severity>=ERROR' \
        --project=$PROJECT_ID 2>/dev/null || log_info "Backend error metric already exists"
    
    gcloud logging metrics create frontend_errors \
        --description="Frontend error count" \
        --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="'$PROJECT_NAME'-frontend" AND severity>=ERROR' \
        --project=$PROJECT_ID 2>/dev/null || log_info "Frontend error metric already exists"
    
    log_success "Monitoring setup completed!"
}

# Function to create deployment script
create_deployment_script() {
    log_info "Creating deployment update script..."
    
    cat > update-gcp-deployment.sh << 'EOF'
#!/bin/bash

# Hotgigs.com - GCP Update Deployment Script

set -e

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-"us-central1"}
PROJECT_NAME="hotgigs"

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_info "Updating Hotgigs.com deployment on GCP..."

REGISTRY_URL="$REGION-docker.pkg.dev/$PROJECT_ID/$PROJECT_NAME-repo"

# Build and push new images
log_info "Building and pushing updated images..."
docker build -t $REGISTRY_URL/backend:latest ./backend
docker push $REGISTRY_URL/backend:latest

docker build -t $REGISTRY_URL/frontend:latest ./frontend
docker push $REGISTRY_URL/frontend:latest

# Update Cloud Run services
log_info "Updating Cloud Run services..."
gcloud run deploy $PROJECT_NAME-backend \
    --image=$REGISTRY_URL/backend:latest \
    --platform=managed \
    --region=$REGION \
    --project=$PROJECT_ID

gcloud run deploy $PROJECT_NAME-frontend \
    --image=$REGISTRY_URL/frontend:latest \
    --platform=managed \
    --region=$REGION \
    --project=$PROJECT_ID

log_success "Deployment updated successfully!"
EOF

    chmod +x update-gcp-deployment.sh
    
    log_success "Update script created: update-gcp-deployment.sh"
}

# Function to display deployment information
display_deployment_info() {
    FRONTEND_URL=$(gcloud run services describe $PROJECT_NAME-frontend --platform=managed --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
    BACKEND_URL=$(gcloud run services describe $PROJECT_NAME-backend --platform=managed --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
    LB_IP=$(gcloud compute forwarding-rules describe $PROJECT_NAME-http-rule --global --format="value(IPAddress)" --project=$PROJECT_ID 2>/dev/null || echo "Not configured")
    
    echo ""
    echo "🎉 GCP Deployment Complete!"
    echo "=========================="
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: $FRONTEND_URL"
    echo "   Backend: $BACKEND_URL"
    if [[ "$LB_IP" != "Not configured" ]]; then
        echo "   Load Balancer: http://$LB_IP"
    fi
    echo ""
    echo "📊 GCP Resources:"
    echo "   Project: $PROJECT_ID"
    echo "   Region: $REGION"
    echo "   Cloud SQL: $PROJECT_NAME-db"
    echo "   Storage: gs://$PROJECT_NAME-assets-$PROJECT_ID"
    echo ""
    echo "🔧 Management:"
    echo "   Cloud Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
    echo "   Cloud SQL: https://console.cloud.google.com/sql/instances?project=$PROJECT_ID"
    echo "   Logs: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Configure custom domain (if needed)"
    echo "   2. Set up SSL certificate"
    echo "   3. Configure monitoring alerts"
    echo "   4. Set up CI/CD pipeline"
    echo ""
    echo "🔄 To update deployment:"
    echo "   ./update-gcp-deployment.sh"
    echo ""
}

# Main execution
main() {
    log_info "Starting GCP deployment for Hotgigs.com..."
    
    # Check prerequisites
    check_prerequisites
    
    # Enable required APIs
    enable_apis
    
    # Create Artifact Registry
    create_artifact_registry
    
    # Create Cloud SQL instance
    create_cloud_sql
    
    # Create Storage bucket
    create_storage_bucket
    
    # Build and push images
    build_and_push_images
    
    # Create Cloud Run services
    create_cloud_run_services
    
    # Setup load balancer
    setup_load_balancer
    
    # Setup monitoring
    setup_monitoring
    
    # Create deployment script
    create_deployment_script
    
    # Display deployment information
    display_deployment_info
    
    log_success "GCP deployment completed successfully!"
}

# Run main function
main "$@"

