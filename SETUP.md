# SafeNet RADIUS Manager - Setup Guide

This guide provides detailed step-by-step instructions for setting up SafeNet RADIUS Manager.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Initial Configuration](#initial-configuration)
4. [Network Device Configuration](#network-device-configuration)
5. [Testing](#testing)
6. [Production Deployment](#production-deployment)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+) or macOS
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **RAM**: Minimum 2GB, recommended 4GB
- **Disk Space**: 10GB minimum
- **Network**: Static IP address recommended

### Install Docker

**Ubuntu/Debian:**

```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL:**

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

## Installation

### Step 1: Clone Repository

```bash
cd /opt
sudo git clone <repository-url> safenet
cd safenet
sudo chown -R $USER:$USER .
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required changes in `.env`:**

```env
# Generate a strong secret key (use: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-here

# Database passwords
DB_PASSWORD=your-strong-database-password
DB_ROOT_PASSWORD=your-strong-root-password

# RADIUS secret (use: openssl rand -hex 16)
RADIUS_SECRET=your-radius-shared-secret

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourStrongPassword123!
ADMIN_EMAIL=admin@yourdomain.com
```

### Step 3: Build Containers

```bash
# Build all containers
docker-compose build

# This may take 5-10 minutes on first run
```

### Step 4: Start Services

```bash
# Start all services
docker-compose up -d

# Verify all containers are running
docker-compose ps

# Expected output:
# NAME                STATUS              PORTS
# safenet-db          Up (healthy)        3306/tcp
# safenet-web         Up                  0.0.0.0:5000->5000/tcp
# safenet-radius      Up (healthy)        0.0.0.0:1812-1813->1812-1813/udp
```

### Step 5: Initialize Database

The database is automatically initialized on first startup. To verify:

```bash
# Check web logs
docker-compose logs web | grep "Database initialized"

# Manually initialize if needed
docker-compose exec web flask init-db
```

## Initial Configuration

### Step 1: Access Web Interface

1. Open browser: `http://your-server-ip:5000`
2. Login with credentials from `.env`
3. **Change password immediately**

### Step 2: Create Your First Plan

1. Navigate to **Plans** → **Add Plan**
2. Fill in:
   - **Name**: `basic`
   - **Description**: `Basic Internet Access`
   - **Vendor**: `standard`
3. Click **Save Plan**
4. Add attributes:
   - **Attribute**: `Session-Timeout`
   - **Operator**: `:=`
   - **Value**: `3600` (1 hour)
   - **Vendor**: Leave as Standard

### Step 3: Add Your First User

1. Navigate to **Users** → **Add User**
2. Fill in:
   - **Username**: `testuser`
   - **Password**: `testpass123`
   - **Plan**: `basic`
   - **Active**: ✓ Checked
3. Click **Save User**

### Step 4: Configure NAS Device

1. Navigate to **NAS Devices** → **Add NAS**
2. Fill in:
   - **IP Address**: Your router/switch IP
   - **Short Name**: `router1`
   - **Secret**: Same as `RADIUS_SECRET` in `.env`
   - **Vendor**: Select your device vendor
   - **Type**: `other` or specific type
3. Click **Save NAS**

## Network Device Configuration

### Cisco Router/Switch

```cisco
! Enable AAA
aaa new-model

! Configure RADIUS server
radius server SAFENET
 address ipv4 <safenet-server-ip> auth-port 1812 acct-port 1813
 key <your-radius-secret>

! Configure authentication
aaa authentication login default group radius local
aaa authentication enable default group radius enable

! Configure authorization
aaa authorization exec default group radius local
aaa authorization network default group radius

! Configure accounting
aaa accounting network default start-stop group radius
aaa accounting exec default start-stop group radius

! Apply to VTY lines
line vty 0 4
 login authentication default
 authorization exec default
```

### MikroTik RouterOS

```mikrotik
# Add RADIUS server
/radius add address=<safenet-server-ip> secret=<your-radius-secret> service=login,wireless

# Enable RADIUS for PPP
/ppp aaa set use-radius=yes

# Enable RADIUS for Wireless
/interface wireless security-profiles
set [ find default=yes ] authentication-types=wpa2-eap mode=dynamic-keys supplicant-identity=MikroTik eap-methods=eap-tls,eap-ttls-mschapv2 tls-mode=no-certificates

# Enable RADIUS for HotSpot
/ip hotspot profile
set [ find default=yes ] use-radius=yes
```

### UniFi Controller

1. **Settings** → **Profiles** → **RADIUS**
2. Click **Create New RADIUS Profile**
3. Fill in:
   - **Profile Name**: `SafeNet`
   - **Auth Server**: `<safenet-server-ip>`
   - **Port**: `1812`
   - **Password**: `<your-radius-secret>`
   - **Accounting**: ✓ Enabled
   - **Acct Server**: `<safenet-server-ip>`
   - **Port**: `1813`
4. Apply to WiFi network:
   - **Settings** → **WiFi** → Select network
   - **Security**: `WPA Enterprise`
   - **RADIUS Profile**: `SafeNet`

### TP-Link

1. Access web interface
2. **System Tools** → **RADIUS Settings**
3. Configure:
   - **Primary RADIUS Server**: `<safenet-server-ip>`
   - **Port**: `1812`
   - **Shared Key**: `<your-radius-secret>`
   - **Accounting Port**: `1813`

## Testing

### Test 1: RADIUS Authentication

```bash
# From SafeNet server
docker exec -it safenet-radius radtest testuser testpass123 localhost 0 testing123

# Expected output:
# Sent Access-Request Id 123 from 0.0.0.0:12345 to 127.0.0.1:1812 length 77
# Received Access-Accept Id 123 from 127.0.0.1:1812 to 0.0.0.0:12345 length 20
```

### Test 2: From Network Device

```bash
# Test from your router (example: Cisco)
test aaa group radius username testuser password testpass123 new-code

# Or from MikroTik
/radius incoming print
```

### Test 3: Web Interface

1. Login to web interface
2. Navigate to **Accounting**
3. Attempt authentication from device
4. Verify session appears in accounting

### Test 4: Debug Mode

```bash
# Run FreeRADIUS in debug mode
docker exec -it safenet-radius freeradius -X

# In another terminal, test authentication
docker exec -it safenet-radius radtest testuser testpass123 localhost 0 testing123

# Watch debug output for errors
```

## Production Deployment

### 1. Firewall Configuration

```bash
# Allow web interface (restrict to admin IPs)
sudo ufw allow from <admin-ip> to any port 5000

# Allow RADIUS from NAS devices only
sudo ufw allow from <nas-ip-1> to any port 1812 proto udp
sudo ufw allow from <nas-ip-1> to any port 1813 proto udp
sudo ufw allow from <nas-ip-2> to any port 1812 proto udp
sudo ufw allow from <nas-ip-2> to any port 1813 proto udp

# Enable firewall
sudo ufw enable
```

### 2. HTTPS with Nginx Reverse Proxy

Create `/etc/nginx/sites-available/safenet`:

```nginx
server {
    listen 80;
    server_name radius.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name radius.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/radius.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/radius.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/safenet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Automatic Startup

```bash
# Enable Docker service
sudo systemctl enable docker

# Containers will auto-start with restart: unless-stopped in docker-compose.yml
```

### 4. Monitoring

Create monitoring script `/opt/safenet/monitor.sh`:

```bash
#!/bin/bash

# Check if containers are running
if ! docker-compose -f /opt/safenet/docker-compose.yml ps | grep -q "Up"; then
    echo "SafeNet containers are down!" | mail -s "SafeNet Alert" admin@yourdomain.com
    docker-compose -f /opt/safenet/docker-compose.yml up -d
fi
```

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add monitoring (every 5 minutes)
*/5 * * * * /opt/safenet/monitor.sh
```

### 5. Backup Automation

Create backup script `/opt/safenet/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backup/safenet"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker exec safenet-db mysqldump -u radius -p$DB_PASSWORD radius > $BACKUP_DIR/radius_$DATE.sql

# Compress
gzip $BACKUP_DIR/radius_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "radius_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/safenet/backup.sh
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database connection errors

```bash
# Wait longer for DB to initialize
docker-compose restart web

# Check database is accessible
docker exec -it safenet-db mysql -u radius -p
```

### RADIUS not responding

```bash
# Check FreeRADIUS is running
docker-compose ps freeradius

# Check debug output
docker exec -it safenet-radius freeradius -X

# Verify ports are open
sudo netstat -ulnp | grep 1812
```

## Next Steps

1. Configure all your network devices
2. Create additional plans for different user types
3. Set up automated backups
4. Configure monitoring and alerts
5. Review security settings
6. Test failover scenarios

For more information, see the main [README.md](README.md).


