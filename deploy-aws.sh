#!/bin/bash

# Hotgigs.com - AWS Deployment Script
# This script deploys the complete application to AWS using ECS, RDS, and CloudFront

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-"us-west-2"}
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
    
    # Check AWS CLI
    if ! command_exists aws; then
        log_error "AWS CLI not found. Please install it first:"
        echo "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
        echo "unzip awscliv2.zip"
        echo "sudo ./aws/install"
        exit 1
    fi
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check Terraform
    if ! command_exists terraform; then
        log_warning "Terraform not found. Installing Terraform..."
        install_terraform
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    log_success "Prerequisites check completed!"
}

# Function to install Terraform
install_terraform() {
    log_info "Installing Terraform..."
    
    # Download and install Terraform
    TERRAFORM_VERSION="1.5.0"
    wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    unzip "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    sudo mv terraform /usr/local/bin/
    rm "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    
    log_success "Terraform installed successfully!"
}

# Function to create Terraform configuration
create_terraform_config() {
    log_info "Creating Terraform configuration..."
    
    mkdir -p terraform
    
    # Main Terraform configuration
    cat > terraform/main.tf << 'EOF'
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-igw"
    Environment = var.environment
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-public-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "${var.project_name}-private-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = {
    Name        = "${var.project_name}-nat-eip"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name        = "${var.project_name}-nat"
    Environment = var.environment
  }

  depends_on = [aws_internet_gateway.main]
}

# Private Route Table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-private-rt"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "ecs" {
  name_prefix = "${var.project_name}-ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-ecs-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = {
    Name        = "${var.project_name}-rds-sg"
    Environment = var.environment
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Environment = var.environment
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = var.db_instance_class
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-db-final-snapshot"
  
  tags = {
    Name        = "${var.project_name}-database"
    Environment = var.environment
  }
}

# ECR Repositories
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-backend-ecr"
    Environment = var.environment
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project_name}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-frontend-ecr"
    Environment = var.environment
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-cluster"
    Environment = var.environment
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ecs-task-execution-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-backend"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-backend-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}-frontend"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-frontend-logs"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name        = "${var.project_name}-alb"
    Environment = var.environment
  }
}

# Target Groups
resource "aws_lb_target_group" "backend" {
  name     = "${var.project_name}-backend-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project_name}-backend-tg"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "frontend" {
  name     = "${var.project_name}-frontend-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project_name}-frontend-tg"
    Environment = var.environment
  }
}

# Load Balancer Listeners
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "backend" {
  listener_arn = aws_lb_listener.main.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# S3 Bucket for static assets
resource "aws_s3_bucket" "assets" {
  bucket = "${var.project_name}-assets-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-assets"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "assets" {
  bucket = aws_s3_bucket.assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.assets.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.assets]
}
EOF

    # Variables file
    cat > terraform/variables.tf << 'EOF'
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "hotgigs"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "hotgigs"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "hotgigs_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}
EOF

    # Outputs file
    cat > terraform/outputs.tf << 'EOF'
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "ecr_backend_repository_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name for assets"
  value       = aws_s3_bucket.assets.bucket
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}
EOF

    log_success "Terraform configuration created!"
}

# Function to build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Build and push backend image
    log_info "Building backend image..."
    docker build -t $PROJECT_NAME-backend ./backend
    docker tag $PROJECT_NAME-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-backend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-backend:latest
    
    # Build and push frontend image
    log_info "Building frontend image..."
    docker build -t $PROJECT_NAME-frontend ./frontend --build-arg VITE_API_BASE_URL=http://$(terraform -chdir=terraform output -raw load_balancer_dns)
    docker tag $PROJECT_NAME-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-frontend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-frontend:latest
    
    log_success "Docker images built and pushed!"
}

# Function to create ECS task definitions
create_ecs_tasks() {
    log_info "Creating ECS task definitions..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    DB_ENDPOINT=$(terraform -chdir=terraform output -raw database_endpoint)
    
    # Backend task definition
    cat > backend-task-definition.json << EOF
{
  "family": "$PROJECT_NAME-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$PROJECT_NAME-ecs-task-execution-role",
  "containerDefinitions": [
    {
      "name": "$PROJECT_NAME-backend",
      "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://hotgigs_user:$(openssl rand -base64 32)@$DB_ENDPOINT:5432/hotgigs"
        },
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "FLASK_DEBUG",
          "value": "False"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$PROJECT_NAME-backend",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

    # Frontend task definition
    cat > frontend-task-definition.json << EOF
{
  "family": "$PROJECT_NAME-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/$PROJECT_NAME-ecs-task-execution-role",
  "containerDefinitions": [
    {
      "name": "$PROJECT_NAME-frontend",
      "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$PROJECT_NAME-frontend",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

    # Register task definitions
    aws ecs register-task-definition --cli-input-json file://backend-task-definition.json
    aws ecs register-task-definition --cli-input-json file://frontend-task-definition.json
    
    log_success "ECS task definitions created!"
}

# Function to create ECS services
create_ecs_services() {
    log_info "Creating ECS services..."
    
    CLUSTER_NAME=$(terraform -chdir=terraform output -raw ecs_cluster_name)
    VPC_ID=$(terraform -chdir=terraform output -raw vpc_id)
    
    # Get subnet and security group IDs
    PRIVATE_SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*private*" --query 'Subnets[].SubnetId' --output text | tr '\t' ',')
    ECS_SECURITY_GROUP=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=*ecs*" --query 'SecurityGroups[0].GroupId' --output text)
    
    # Backend service
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $PROJECT_NAME-backend \
        --task-definition $PROJECT_NAME-backend \
        --desired-count 2 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$ECS_SECURITY_GROUP],assignPublicIp=DISABLED}" \
        --load-balancers "targetGroupArn=$(aws elbv2 describe-target-groups --names $PROJECT_NAME-backend-tg --query 'TargetGroups[0].TargetGroupArn' --output text),containerName=$PROJECT_NAME-backend,containerPort=5000"
    
    # Frontend service
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $PROJECT_NAME-frontend \
        --task-definition $PROJECT_NAME-frontend \
        --desired-count 2 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$ECS_SECURITY_GROUP],assignPublicIp=DISABLED}" \
        --load-balancers "targetGroupArn=$(aws elbv2 describe-target-groups --names $PROJECT_NAME-frontend-tg --query 'TargetGroups[0].TargetGroupArn' --output text),containerName=$PROJECT_NAME-frontend,containerPort=80"
    
    log_success "ECS services created!"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Generate database password
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Plan deployment
    terraform plan -var="db_password=$DB_PASSWORD" -var="aws_region=$AWS_REGION" -var="environment=$ENVIRONMENT"
    
    # Apply deployment
    terraform apply -auto-approve -var="db_password=$DB_PASSWORD" -var="aws_region=$AWS_REGION" -var="environment=$ENVIRONMENT"
    
    cd ..
    
    log_success "Infrastructure deployed!"
}

# Function to wait for services
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    CLUSTER_NAME=$(terraform -chdir=terraform output -raw ecs_cluster_name)
    
    # Wait for backend service
    log_info "Waiting for backend service..."
    aws ecs wait services-stable --cluster $CLUSTER_NAME --services $PROJECT_NAME-backend
    
    # Wait for frontend service
    log_info "Waiting for frontend service..."
    aws ecs wait services-stable --cluster $CLUSTER_NAME --services $PROJECT_NAME-frontend
    
    log_success "All services are healthy!"
}

# Function to display deployment information
display_deployment_info() {
    LOAD_BALANCER_DNS=$(terraform -chdir=terraform output -raw load_balancer_dns)
    
    echo ""
    echo "🎉 AWS Deployment Complete!"
    echo "=========================="
    echo ""
    echo "🌐 Application URL: http://$LOAD_BALANCER_DNS"
    echo "🔧 API URL: http://$LOAD_BALANCER_DNS/api/health"
    echo ""
    echo "📊 AWS Resources:"
    echo "   ECS Cluster: $(terraform -chdir=terraform output -raw ecs_cluster_name)"
    echo "   Load Balancer: $LOAD_BALANCER_DNS"
    echo "   Database: $(terraform -chdir=terraform output -raw database_endpoint)"
    echo ""
    echo "🔧 Management:"
    echo "   AWS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION"
    echo "   CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Configure custom domain (if needed)"
    echo "   2. Set up SSL certificate"
    echo "   3. Configure monitoring and alerts"
    echo "   4. Set up CI/CD pipeline"
    echo ""
}

# Main execution
main() {
    log_info "Starting AWS deployment for Hotgigs.com..."
    
    # Check prerequisites
    check_prerequisites
    
    # Create Terraform configuration
    create_terraform_config
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Build and push images
    build_and_push_images
    
    # Create ECS tasks and services
    create_ecs_tasks
    create_ecs_services
    
    # Wait for services to be ready
    wait_for_services
    
    # Display deployment information
    display_deployment_info
    
    log_success "AWS deployment completed successfully!"
}

# Run main function
main "$@"

