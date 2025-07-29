#!/bin/bash

# Add Swap Space to DigitalOcean Droplet
# This provides overflow memory to prevent OOM kills

SERVER="root@170.64.199.151"
SSH_KEY="~/.ssh/id_rsa"

echo "💾 Adding Swap Space to Remote Server..."
echo "======================================="

ssh -i "$SSH_KEY" "$SERVER" '
# Check current swap
echo "Current swap status:"
swapon --show
free -h

# Create 2GB swap file (adjust size as needed)
echo "Creating 2GB swap file..."
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make it persistent
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab

# Optimize swappiness (10 = use swap less aggressively)
sudo sysctl vm.swappiness=10
echo "vm.swappiness = 10" | sudo tee -a /etc/sysctl.conf

echo "✅ Swap configuration complete:"
swapon --show
free -h
'
