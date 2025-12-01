# PropSafe AI - AWS Deployment Guide

## Overview

This guide will deploy PropSafe AI to AWS EC2 using Terraform and Docker Compose.

**Instance Configuration:**
- **Type:** t3.small (2 vCPU, 2GB RAM)
- **Storage:** 30GB SSD
- **Estimated Cost:** ~$15-20/month
- **Domain:** propsafeai.ibacrea.com

## Prerequisites

1. **AWS Credentials** configured in environment or `~/.aws/credentials`
2. **Terraform** installed (`choco install terraform` on Windows)
3. **SSH key pair** for accessing the instance

## Step 1: Generate SSH Key

```powershell
# Generate SSH key pair
ssh-keygen -t ed25519 -C "propsafe-aws" -f ~/.ssh/propsafe_key -N ""

# Verify key was created
ls ~/.ssh/propsafe_key*
```

## Step 2: Deploy Infrastructure with Terraform

```powershell
# Navigate to terraform directory
cd infra/terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply configuration (create EC2 instance)
terraform apply

# Save the output (public IP)
terraform output public_ip
```

**Expected output:**
```
public_ip = "XX.XX.XX.XX"
ssh_command = "ssh -i ~/.ssh/propsafe_key ubuntu@XX.XX.XX.XX"
application_url = "http://XX.XX.XX.XX"
```

## Step 3: Configure DNS

Point your domain to the EC2 public IP:

```
Type: A
Name: propsafeai.ibacrea.com
Value: XX.XX.XX.XX (from terraform output)
TTL: 3600
```

## Step 4: Upload Application Files

```powershell
# From project root, upload everything except data (too large)
scp -i ~/.ssh/propsafe_key -r `
  backend/ frontend/ ml/ scripts/ etl/ services/ `
  docker-compose.prod.yml `
  .env.example `
  ubuntu@XX.XX.XX.XX:/opt/propsafe/

# Upload processed data (this will take time - 5.7M records)
scp -i ~/.ssh/propsafe_key -r data/clean/*.parquet ubuntu@XX.XX.XX.XX:/opt/propsafe/data/clean/

# Upload trained ML models (after training)
scp -i ~/.ssh/propsafe_key -r ml/models/*.joblib ubuntu@XX.XX.XX.XX:/opt/propsafe/ml/models/
```

## Step 5: SSH into Server and Deploy

```powershell
# Connect to server
ssh -i ~/.ssh/propsafe_key ubuntu@XX.XX.XX.XX
```

On the server:

```bash
# Navigate to application directory
cd /opt/propsafe

# Copy environment template
cp .env.example .env

# Edit environment variables (use nano or vi)
nano .env
# Update: DB_PASSWORD, SERVER_IP (use public IP), DOMAIN

# Make deploy script executable
chmod +x infra/scripts/deploy.sh

# Run deployment
./infra/scripts/deploy.sh
```

## Step 6: Load Data into Database

```bash
# Wait for containers to be healthy
docker-compose -f docker-compose.prod.yml ps

# Load data into PostgreSQL (this will take 30-45 minutes for 5.7M records)
docker exec -it propsafe-backend python /app/scripts/load_data.py --file /app/data/completo.parquet
```

## Step 7: Verify Deployment

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Test API health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:80
```

From your local machine:
```powershell
# Test API
curl http://XX.XX.XX.XX:8000/health

# Open in browser
Start-Process "http://XX.XX.XX.XX"
Start-Process "http://propsafeai.ibacrea.com"
```

## Useful Commands

### Container Management

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Database Management

```bash
# Connect to PostgreSQL
docker exec -it propsafe-db psql -U propsafe_user -d propsafe_db

# Backup database
docker exec propsafe-db pg_dump -U propsafe_user propsafe_db > backup.sql

# Check database size
docker exec -it propsafe-db psql -U propsafe_user -d propsafe_db -c "
SELECT 
    pg_size_pretty(pg_database_size('propsafe_db')) as db_size,
    (SELECT COUNT(*) FROM transactions) as transaction_count;
"
```

### System Monitoring

```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check Docker stats
docker stats

# Check system load
htop
```

### SSL/HTTPS Setup (Optional - Later Phase)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d propsafeai.ibacrea.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Cost Optimization

### Current Configuration (t3.small)
- EC2 t3.small: ~$15/month
- 30GB EBS: ~$3/month
- Data transfer: ~$2/month
- **Total: ~$20/month**

### If you need to reduce costs:

1. **Use t3.micro** (1 vCPU, 1GB RAM - $7.50/month)
   - Edit `infra/terraform/variables.tf`
   - Change `instance_type = "t3.micro"`
   - **Note:** May be too small for ML inference

2. **Stop instance when not in use**
   ```bash
   # From local machine
   aws ec2 stop-instances --instance-ids $(terraform output -raw instance_id)
   
   # Start again
   aws ec2 start-instances --instance-ids $(terraform output -raw instance_id)
   ```

3. **Use spot instances** (Edit terraform configuration)

## Troubleshooting

### Port 8000 not accessible
```bash
# Check backend is running
docker ps | grep backend

# Check backend logs
docker logs propsafe-backend

# Check security group allows port 8000
# (Terraform should have configured this)
```

### Database connection failed
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker logs propsafe-db

# Test connection
docker exec -it propsafe-db psql -U propsafe_user -d propsafe_db -c "SELECT 1"
```

### Out of memory errors
```bash
# Check memory usage
free -h
docker stats

# Consider:
# - Reducing CHUNK_SIZE in .env
# - Reducing worker count in docker-compose.prod.yml
# - Upgrading to t3.medium (4GB RAM, $30/month)
```

### Frontend not loading
```bash
# Check nginx logs
docker logs propsafe-frontend

# Check if API URL is correct in frontend
docker exec -it propsafe-frontend cat /etc/nginx/conf.d/default.conf
```

## Cleanup (Destroy Infrastructure)

**⚠️ WARNING: This will delete everything!**

```powershell
# From local machine in infra/terraform directory
terraform destroy

# Confirm by typing 'yes'
```

This will:
- Terminate the EC2 instance
- Delete the Elastic IP
- Remove security groups
- Delete all data on the instance

## Next Steps

1. ✅ Deploy infrastructure
2. ✅ Upload application and data
3. ✅ Load data into PostgreSQL
4. 🔄 Train ML models (Feature Engineering → Model Training)
5. 🔄 Configure monitoring (CloudWatch)
6. 🔄 Set up backups (automated snapshots)
7. 🔄 Enable HTTPS with Let's Encrypt
8. 🔄 Set up CI/CD (GitHub Actions)

## Support

For issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
2. Verify configuration: `cat .env`
3. Check system resources: `htop`, `df -h`, `free -h`
4. Review Terraform state: `terraform show`
