# Quick Deployment Script for Windows PowerShell

# Variables
$PROJECT_ROOT = "d:\projects\datos"
$SSH_KEY = "$env:USERPROFILE\.ssh\propsafe_key"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PropSafe AI - Quick Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Generate SSH key if not exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "`n[1/7] Generating SSH key..." -ForegroundColor Yellow
    ssh-keygen -t ed25519 -C "propsafe-aws" -f $SSH_KEY -N '""'
    Write-Host "✓ SSH key generated" -ForegroundColor Green
} else {
    Write-Host "`n[1/7] SSH key already exists" -ForegroundColor Green
}

# Step 2: Initialize Terraform
Write-Host "`n[2/7] Initializing Terraform..." -ForegroundColor Yellow
Push-Location "$PROJECT_ROOT\infra\terraform"
terraform init
Write-Host "✓ Terraform initialized" -ForegroundColor Green

# Step 3: Apply Terraform (create infrastructure)
Write-Host "`n[3/7] Creating AWS infrastructure..." -ForegroundColor Yellow
Write-Host "This will create a t3.small EC2 instance (~$20/month)" -ForegroundColor Yellow
$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled" -ForegroundColor Red
    Pop-Location
    exit
}

terraform apply -auto-approve
Write-Host "✓ Infrastructure created" -ForegroundColor Green

# Get public IP
$PUBLIC_IP = terraform output -raw public_ip
Write-Host "`nPublic IP: $PUBLIC_IP" -ForegroundColor Cyan

Pop-Location

# Step 4: Wait for instance to be ready
Write-Host "`n[4/7] Waiting for instance to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 60
Write-Host "✓ Instance should be ready" -ForegroundColor Green

# Step 5: Upload files
Write-Host "`n[5/7] Uploading application files..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Yellow

Push-Location $PROJECT_ROOT

# Upload application code
scp -i $SSH_KEY -r `
    backend, frontend, ml, scripts, etl, services, `
    docker-compose.prod.yml, .env.example, requirements.txt `
    "ubuntu@${PUBLIC_IP}:/opt/propsafe/"

Write-Host "✓ Application files uploaded" -ForegroundColor Green

# Upload data (this will take longer)
Write-Host "`nUploading processed data (5.7M records)..." -ForegroundColor Yellow
scp -i $SSH_KEY -r data\clean\*.parquet "ubuntu@${PUBLIC_IP}:/opt/propsafe/data/clean/"
Write-Host "✓ Data uploaded" -ForegroundColor Green

Pop-Location

# Step 6: Deploy application on server
Write-Host "`n[6/7] Deploying application on server..." -ForegroundColor Yellow
ssh -i $SSH_KEY "ubuntu@$PUBLIC_IP" @"
cd /opt/propsafe
cp .env.example .env
sed -i 's/your-secret-key-change-in-production/$(openssl rand -base64 32)/' .env
sed -i 's/localhost/$PUBLIC_IP/' .env
chmod +x infra/scripts/deploy.sh
./infra/scripts/deploy.sh
"@
Write-Host "✓ Application deployed" -ForegroundColor Green

# Step 7: Load data
Write-Host "`n[7/7] Loading data into database..." -ForegroundColor Yellow
Write-Host "This will take 30-45 minutes for 5.7M records..." -ForegroundColor Yellow
ssh -i $SSH_KEY "ubuntu@$PUBLIC_IP" `
    "docker exec -it propsafe-backend python /app/scripts/load_data.py --file /app/data/completo.parquet"
Write-Host "✓ Data loaded" -ForegroundColor Green

# Done
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nPublic IP: $PUBLIC_IP" -ForegroundColor Cyan
Write-Host "Application URL: http://$PUBLIC_IP" -ForegroundColor Cyan
Write-Host "API URL: http://${PUBLIC_IP}:8000" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Point DNS for propsafeai.ibacrea.com to $PUBLIC_IP"
Write-Host "2. Train ML models: ssh into server and run training"
Write-Host "3. Enable HTTPS with Let's Encrypt (optional)"
Write-Host "`nSSH Command: ssh -i $SSH_KEY ubuntu@$PUBLIC_IP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green

# Open browser
$openBrowser = Read-Host "`nOpen application in browser? (yes/no)"
if ($openBrowser -eq "yes") {
    Start-Process "http://$PUBLIC_IP"
}
