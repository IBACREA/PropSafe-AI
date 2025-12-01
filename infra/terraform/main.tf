terraform {
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

# Security Group - Allow HTTP, HTTPS, SSH
resource "aws_security_group" "propsafe_sg" {
  name        = "propsafe-security-group"
  description = "Security group for PropSafe AI application"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Backend API"
    from_port   = 8000
    to_port     = 8000
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
    Name        = "propsafe-sg"
    Project     = "PropSafe-AI"
    Environment = "production"
  }
}

# EC2 Key Pair (you'll need to create this locally first)
resource "aws_key_pair" "propsafe_key" {
  key_name   = "propsafe-key"
  public_key = file(var.ssh_public_key_path)
}

# EC2 Instance - t3.small (2 vCPU, 2GB RAM)
resource "aws_instance" "propsafe_server" {
  ami           = var.ami_id # Ubuntu 22.04 LTS
  instance_type = "t3.small"
  key_name      = aws_key_pair.propsafe_key.key_name

  vpc_security_group_ids = [aws_security_group.propsafe_sg.id]

  root_block_device {
    volume_size = 30 # 30GB SSD
    volume_type = "gp3"
  }

  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name        = "propsafe-server"
    Project     = "PropSafe-AI"
    Environment = "production"
  }
}

# Elastic IP for stable public IP
resource "aws_eip" "propsafe_eip" {
  instance = aws_instance.propsafe_server.id
  domain   = "vpc"

  tags = {
    Name        = "propsafe-eip"
    Project     = "PropSafe-AI"
    Environment = "production"
  }
}

# Outputs
output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.propsafe_eip.public_ip
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.propsafe_server.id
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${var.ssh_private_key_path} ubuntu@${aws_eip.propsafe_eip.public_ip}"
}

output "application_url" {
  description = "URL of the application"
  value       = "http://${aws_eip.propsafe_eip.public_ip}"
}
