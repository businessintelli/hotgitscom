#!/bin/bash

# Hotgigs.com - Microsoft Azure Deployment Script
# This script deploys the complete application to Azure using Container Instances, PostgreSQL, and Storage

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SUBSCRIPTION_ID=${SUBSCRIPTION_ID:-""}
RESOURCE_GROUP=${RESOURCE_GROUP:-"hotgigs-rg"}
LOCATION=${LOCATION:-"East US"}
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
    
    # Check Azure CLI
    if ! command_exists az; then
        log_error "Azure CLI not found. Please install it first:"
        echo "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        exit 1
    fi
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check if user is authenticated
    if ! az account show >/dev/null 2>&1; then
        log_error "Not authenticated with Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Set subscription if provided
    if [[ -n "$SUBSCRIPTION_ID" ]]; then
        az account set --subscription $SUBSCRIPTION_ID
    fi
    
    # Get current subscription
    CURRENT_SUBSCRIPTION=$(az account show --query id -o tsv)
    
    log_success "Prerequisites check completed!"
    log_info "Using subscription: $CURRENT_SUBSCRIPTION"
    log_info "Using location: $LOCATION"
}

# Function to create resource group
create_resource_group() {
    log_info "Creating resource group..."
    
    if az group show --name $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "Resource group already exists"
    else
        az group create --name $RESOURCE_GROUP --location "$LOCATION"
        log_success "Resource group created: $RESOURCE_GROUP"
    fi
}

# Function to create Azure Container Registry
create_container_registry() {
    log_info "Creating Azure Container Registry..."
    
    ACR_NAME="${PROJECT_NAME}acr$(date +%s | tail -c 6)"
    
    if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "Container registry already exists"
    else
        az acr create \
            --resource-group $RESOURCE_GROUP \
            --name $ACR_NAME \
            --sku Basic \
            --admin-enabled true
        
        log_success "Container registry created: $ACR_NAME"
    fi
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
    
    # Login to ACR
    az acr login --name $ACR_NAME
    
    echo $ACR_NAME > .acr_name
    echo $ACR_LOGIN_SERVER > .acr_login_server
}

# Function to create PostgreSQL database
create_postgresql_database() {
    log_info "Creating Azure Database for PostgreSQL..."
    
    DB_SERVER_NAME="${PROJECT_NAME}-db-$(date +%s | tail -c 6)"
    DB_ADMIN_USER="hotgigs_admin"
    DB_PASSWORD=$(openssl rand -base64 32)
    
    if az postgres server show --name $DB_SERVER_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "PostgreSQL server already exists"
    else
        az postgres server create \
            --resource-group $RESOURCE_GROUP \
            --name $DB_SERVER_NAME \
            --location "$LOCATION" \
            --admin-user $DB_ADMIN_USER \
            --admin-password "$DB_PASSWORD" \
            --sku-name B_Gen5_1 \
            --version 11 \
            --storage-size 20480 \
            --backup-retention 7 \
            --geo-redundant-backup Disabled \
            --ssl-enforcement Enabled
        
        log_success "PostgreSQL server created: $DB_SERVER_NAME"
    fi
    
    # Create database
    az postgres db create \
        --resource-group $RESOURCE_GROUP \
        --server-name $DB_SERVER_NAME \
        --name hotgigs 2>/dev/null || log_info "Database already exists"
    
    # Configure firewall to allow Azure services
    az postgres server firewall-rule create \
        --resource-group $RESOURCE_GROUP \
        --server $DB_SERVER_NAME \
        --name AllowAzureServices \
        --start-ip-address 0.0.0.0 \
        --end-ip-address 0.0.0.0 2>/dev/null || log_info "Firewall rule already exists"
    
    # Store database credentials in Key Vault
    create_key_vault
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "db-password" --value "$DB_PASSWORD" >/dev/null
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "db-server" --value "$DB_SERVER_NAME.postgres.database.azure.com" >/dev/null
    az keyvault secret set --vault-name $KEY_VAULT_NAME --name "db-user" --value "$DB_ADMIN_USER@$DB_SERVER_NAME" >/dev/null
    
    echo $DB_SERVER_NAME > .db_server_name
    echo $DB_ADMIN_USER > .db_admin_user
    
    log_success "PostgreSQL database setup completed!"
}

# Function to create Key Vault
create_key_vault() {
    KEY_VAULT_NAME="${PROJECT_NAME}-kv-$(date +%s | tail -c 6)"
    
    if az keyvault show --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "Key Vault already exists"
    else
        az keyvault create \
            --name $KEY_VAULT_NAME \
            --resource-group $RESOURCE_GROUP \
            --location "$LOCATION" \
            --sku standard
        
        log_success "Key Vault created: $KEY_VAULT_NAME"
    fi
    
    echo $KEY_VAULT_NAME > .key_vault_name
}

# Function to create storage account
create_storage_account() {
    log_info "Creating Azure Storage Account..."
    
    STORAGE_ACCOUNT_NAME="${PROJECT_NAME}storage$(date +%s | tail -c 6)"
    
    if az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "Storage account already exists"
    else
        az storage account create \
            --name $STORAGE_ACCOUNT_NAME \
            --resource-group $RESOURCE_GROUP \
            --location "$LOCATION" \
            --sku Standard_LRS \
            --kind StorageV2 \
            --access-tier Hot
        
        log_success "Storage account created: $STORAGE_ACCOUNT_NAME"
    fi
    
    # Create blob container for assets
    STORAGE_KEY=$(az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT_NAME --query '[0].value' -o tsv)
    
    az storage container create \
        --name assets \
        --account-name $STORAGE_ACCOUNT_NAME \
        --account-key $STORAGE_KEY \
        --public-access blob 2>/dev/null || log_info "Container already exists"
    
    echo $STORAGE_ACCOUNT_NAME > .storage_account_name
    
    log_success "Storage account setup completed!"
}

# Function to build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    ACR_LOGIN_SERVER=$(cat .acr_login_server)
    
    # Build and push backend image
    log_info "Building backend image..."
    docker build -t $ACR_LOGIN_SERVER/backend:latest ./backend
    docker push $ACR_LOGIN_SERVER/backend:latest
    
    # Build and push frontend image
    log_info "Building frontend image..."
    docker build -t $ACR_LOGIN_SERVER/frontend:latest ./frontend \
        --build-arg VITE_API_BASE_URL=https://$PROJECT_NAME-backend.$(echo "$LOCATION" | tr '[:upper:]' '[:lower:]' | tr ' ' '').azurecontainer.io
    docker push $ACR_LOGIN_SERVER/frontend:latest
    
    log_success "Docker images built and pushed!"
}

# Function to create container instances
create_container_instances() {
    log_info "Creating Azure Container Instances..."
    
    ACR_NAME=$(cat .acr_name)
    ACR_LOGIN_SERVER=$(cat .acr_login_server)
    DB_SERVER_NAME=$(cat .db_server_name)
    DB_ADMIN_USER=$(cat .db_admin_user)
    KEY_VAULT_NAME=$(cat .key_vault_name)
    
    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
    
    # Get database password from Key Vault
    DB_PASSWORD=$(az keyvault secret show --vault-name $KEY_VAULT_NAME --name "db-password" --query value -o tsv)
    
    # Create backend container instance
    log_info "Creating backend container instance..."
    az container create \
        --resource-group $RESOURCE_GROUP \
        --name $PROJECT_NAME-backend \
        --image $ACR_LOGIN_SERVER/backend:latest \
        --registry-login-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --dns-name-label $PROJECT_NAME-backend \
        --ports 5000 \
        --cpu 1 \
        --memory 2 \
        --environment-variables \
            FLASK_ENV=production \
            FLASK_DEBUG=False \
            DATABASE_URL="postgresql://$DB_ADMIN_USER:$DB_PASSWORD@$DB_SERVER_NAME.postgres.database.azure.com:5432/hotgigs?sslmode=require" \
        --location "$LOCATION"
    
    # Create frontend container instance
    log_info "Creating frontend container instance..."
    BACKEND_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-backend --query ipAddress.fqdn -o tsv)
    
    az container create \
        --resource-group $RESOURCE_GROUP \
        --name $PROJECT_NAME-frontend \
        --image $ACR_LOGIN_SERVER/frontend:latest \
        --registry-login-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --dns-name-label $PROJECT_NAME-frontend \
        --ports 80 \
        --cpu 1 \
        --memory 1 \
        --environment-variables \
            VITE_API_BASE_URL="http://$BACKEND_FQDN:5000" \
        --location "$LOCATION"
    
    log_success "Container instances created!"
}

# Function to create Application Gateway (Load Balancer)
create_application_gateway() {
    log_info "Creating Application Gateway..."
    
    # Create virtual network
    VNET_NAME="${PROJECT_NAME}-vnet"
    SUBNET_NAME="${PROJECT_NAME}-subnet"
    
    az network vnet create \
        --resource-group $RESOURCE_GROUP \
        --name $VNET_NAME \
        --address-prefix 10.0.0.0/16 \
        --subnet-name $SUBNET_NAME \
        --subnet-prefix 10.0.1.0/24 \
        --location "$LOCATION" 2>/dev/null || log_info "Virtual network already exists"
    
    # Create public IP for Application Gateway
    AG_PUBLIC_IP="${PROJECT_NAME}-ag-pip"
    az network public-ip create \
        --resource-group $RESOURCE_GROUP \
        --name $AG_PUBLIC_IP \
        --allocation-method Static \
        --sku Standard \
        --location "$LOCATION" 2>/dev/null || log_info "Public IP already exists"
    
    # Create Application Gateway
    AG_NAME="${PROJECT_NAME}-appgw"
    
    if az network application-gateway show --name $AG_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "Application Gateway already exists"
    else
        # Get container instance IPs
        BACKEND_IP=$(az container show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-backend --query ipAddress.ip -o tsv)
        FRONTEND_IP=$(az container show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-frontend --query ipAddress.ip -o tsv)
        
        az network application-gateway create \
            --name $AG_NAME \
            --location "$LOCATION" \
            --resource-group $RESOURCE_GROUP \
            --vnet-name $VNET_NAME \
            --subnet $SUBNET_NAME \
            --capacity 2 \
            --sku Standard_v2 \
            --http-settings-cookie-based-affinity Disabled \
            --frontend-port 80 \
            --http-settings-port 80 \
            --http-settings-protocol Http \
            --public-ip-address $AG_PUBLIC_IP \
            --servers $FRONTEND_IP
        
        # Add backend pool for API
        az network application-gateway address-pool create \
            --gateway-name $AG_NAME \
            --resource-group $RESOURCE_GROUP \
            --name backend-pool \
            --servers $BACKEND_IP
        
        # Add path-based routing rule for API
        az network application-gateway url-path-map create \
            --gateway-name $AG_NAME \
            --resource-group $RESOURCE_GROUP \
            --name api-path-map \
            --paths "/api/*" \
            --address-pool backend-pool \
            --default-address-pool appGatewayBackendPool \
            --http-settings appGatewayBackendHttpSettings \
            --default-http-settings appGatewayBackendHttpSettings
        
        log_success "Application Gateway created!"
    fi
}

# Function to setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring and logging..."
    
    # Create Log Analytics workspace
    WORKSPACE_NAME="${PROJECT_NAME}-workspace"
    
    if az monitor log-analytics workspace show --resource-group $RESOURCE_GROUP --workspace-name $WORKSPACE_NAME >/dev/null 2>&1; then
        log_info "Log Analytics workspace already exists"
    else
        az monitor log-analytics workspace create \
            --resource-group $RESOURCE_GROUP \
            --workspace-name $WORKSPACE_NAME \
            --location "$LOCATION"
        
        log_success "Log Analytics workspace created!"
    fi
    
    # Create Application Insights
    APP_INSIGHTS_NAME="${PROJECT_NAME}-insights"
    
    if az monitor app-insights component show --app $APP_INSIGHTS_NAME --resource-group $RESOURCE_GROUP >/dev/null 2>&1; then
        log_info "Application Insights already exists"
    else
        az monitor app-insights component create \
            --app $APP_INSIGHTS_NAME \
            --location "$LOCATION" \
            --resource-group $RESOURCE_GROUP \
            --workspace $WORKSPACE_NAME
        
        log_success "Application Insights created!"
    fi
}

# Function to create deployment script
create_deployment_script() {
    log_info "Creating deployment update script..."
    
    cat > update-azure-deployment.sh << 'EOF'
#!/bin/bash

# Hotgigs.com - Azure Update Deployment Script

set -e

RESOURCE_GROUP=${RESOURCE_GROUP:-"hotgigs-rg"}
PROJECT_NAME="hotgigs"

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_info "Updating Hotgigs.com deployment on Azure..."

# Read stored values
ACR_NAME=$(cat .acr_name)
ACR_LOGIN_SERVER=$(cat .acr_login_server)

# Login to ACR
az acr login --name $ACR_NAME

# Build and push new images
log_info "Building and pushing updated images..."
docker build -t $ACR_LOGIN_SERVER/backend:latest ./backend
docker push $ACR_LOGIN_SERVER/backend:latest

docker build -t $ACR_LOGIN_SERVER/frontend:latest ./frontend
docker push $ACR_LOGIN_SERVER/frontend:latest

# Restart container instances to pull new images
log_info "Restarting container instances..."
az container restart --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-backend
az container restart --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-frontend

log_success "Deployment updated successfully!"
EOF

    chmod +x update-azure-deployment.sh
    
    log_success "Update script created: update-azure-deployment.sh"
}

# Function to display deployment information
display_deployment_info() {
    FRONTEND_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-frontend --query ipAddress.fqdn -o tsv)
    BACKEND_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-backend --query ipAddress.fqdn -o tsv)
    AG_IP=$(az network public-ip show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-ag-pip --query ipAddress -o tsv 2>/dev/null || echo "Not configured")
    
    echo ""
    echo "🎉 Azure Deployment Complete!"
    echo "============================="
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: http://$FRONTEND_FQDN"
    echo "   Backend: http://$BACKEND_FQDN:5000"
    if [[ "$AG_IP" != "Not configured" ]]; then
        echo "   Load Balancer: http://$AG_IP"
    fi
    echo ""
    echo "📊 Azure Resources:"
    echo "   Resource Group: $RESOURCE_GROUP"
    echo "   Location: $LOCATION"
    echo "   Container Registry: $(cat .acr_name)"
    echo "   Database: $(cat .db_server_name)"
    echo "   Storage: $(cat .storage_account_name)"
    echo ""
    echo "🔧 Management:"
    echo "   Azure Portal: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP"
    echo "   Container Instances: https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.ContainerInstance%2FcontainerGroups"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Configure custom domain (if needed)"
    echo "   2. Set up SSL certificate"
    echo "   3. Configure monitoring alerts"
    echo "   4. Set up CI/CD pipeline"
    echo ""
    echo "🔄 To update deployment:"
    echo "   ./update-azure-deployment.sh"
    echo ""
}

# Main execution
main() {
    log_info "Starting Azure deployment for Hotgigs.com..."
    
    # Check prerequisites
    check_prerequisites
    
    # Create resource group
    create_resource_group
    
    # Create container registry
    create_container_registry
    
    # Create PostgreSQL database
    create_postgresql_database
    
    # Create storage account
    create_storage_account
    
    # Build and push images
    build_and_push_images
    
    # Create container instances
    create_container_instances
    
    # Create application gateway
    create_application_gateway
    
    # Setup monitoring
    setup_monitoring
    
    # Create deployment script
    create_deployment_script
    
    # Display deployment information
    display_deployment_info
    
    log_success "Azure deployment completed successfully!"
}

# Run main function
main "$@"

