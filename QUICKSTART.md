# SafeNet RADIUS Manager - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- 2GB RAM available
- Ports 5000, 8081, 1812, 1813 available

## Installation

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your favorite editor
nano .env
```

**Minimum required changes:**

```env
SECRET_KEY=your-random-secret-key-here
DB_PASSWORD=your-database-password
RADIUS_SECRET=your-radius-secret
ADMIN_PASSWORD=your-admin-password
```

### 2. Start Services

```bash
# Build and start
docker-compose up -d

# Wait 30 seconds for database initialization
sleep 30

# Check status
docker-compose ps
```

All four services should show "Up" status:
- `safenet-db` (database)
- `safenet-web` (web interface)
- `safenet-radius` (RADIUS server)
- `safenet-phpmyadmin` (database management)

### 3. Access Web Interface

Open browser: **http://localhost:5000**

Login with:
- Username: `admin` (or your `ADMIN_USERNAME`)
- Password: `admin123` (or your `ADMIN_PASSWORD`)

### 4. Access phpMyAdmin (Optional)

For direct database management, access phpMyAdmin:

**http://localhost:8081**

Login credentials:
- **Server**: `db` (or leave default)
- **Username**: `radius` (or your `DB_USER` from `.env`)
- **Password**: Your `DB_PASSWORD` from `.env`

## First Steps

### Create a Plan

1. Click **Plans** → **Add Plan**
2. Fill in:
   - Name: `basic`
   - Description: `Basic Internet Access`
   - Vendor: `standard`
3. Click **Save Plan**
4. Add attribute:
   - Attribute: `Session-Timeout`
   - Operator: `:=`
   - Value: `3600`
5. Click **Add Attribute**

### Add a User

1. Click **Users** → **Add User**
2. Fill in:
   - Username: `testuser`
   - Password: `testpass123`
   - Plan: `basic`
   - Active: ✓
3. Click **Save User**

### Configure NAS Device

1. Click **NAS Devices** → **Add NAS**
2. Fill in:
   - IP Address: Your router/switch IP
   - Short Name: `router1`
   - Secret: Same as `RADIUS_SECRET` in `.env`
   - Vendor: Select your device vendor
   - Type: `other`
3. Click **Save NAS**

### Test Authentication

```bash
# Test from server
docker exec -it safenet-radius radtest testuser testpass123 localhost 0 testing123

# Expected output: "Access-Accept"
```

## Configure Your Network Device

### Cisco

```cisco
radius server SAFENET
 address ipv4 <server-ip> auth-port 1812 acct-port 1813
 key <your-radius-secret>

aaa new-model
aaa authentication login default group radius local
```

### MikroTik

```mikrotik
/radius add address=<server-ip> secret=<your-radius-secret> service=login
/ppp aaa set use-radius=yes
```

### UniFi

1. Settings → Profiles → RADIUS
2. Create profile with server IP and secret
3. Apply to WiFi network

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Restart
docker-compose restart
```

### Can't login to web interface

```bash
# Reinitialize database
docker-compose exec web flask init-db
```

### RADIUS not working

```bash
# Debug mode
docker exec -it safenet-radius freeradius -X

# Test authentication in another terminal
docker exec -it safenet-radius radtest testuser testpass123 localhost 0 testing123
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [SETUP.md](SETUP.md) for production deployment
- See [VENDOR_ATTRIBUTES.md](VENDOR_ATTRIBUTES.md) for vendor-specific attributes

## Management Commands

```bash
# Using the helper script
./scripts/manage.sh start     # Start services
./scripts/manage.sh stop      # Stop services
./scripts/manage.sh logs      # View logs
./scripts/manage.sh backup    # Backup database
./scripts/manage.sh test      # Test RADIUS
```

## Support

- Check logs: `docker-compose logs`
- Debug RADIUS: `docker exec -it safenet-radius freeradius -X`
- Database shell: `docker exec -it safenet-db mysql -u radius -p`

---

**You're all set! 🎉**

Your multi-vendor RADIUS server is now running and ready to authenticate users across Cisco, MikroTik, UniFi, and other network devices.

