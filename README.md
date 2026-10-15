# SafeNet RADIUS Manager

A **multi-vendor FreeRADIUS Management Web Application** built with Flask and Docker. This system provides a modern, intuitive admin interface for managing RADIUS authentication across multiple network equipment vendors.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FreeRADIUS](https://img.shields.io/badge/FreeRADIUS-3.0-green.svg)

## 🌟 Features

### Multi-Vendor Support
- ✅ **Cisco** - Full support for Cisco-AVPair and vendor-specific attributes
- ✅ **MikroTik** - Rate limiting, address lists, and custom attributes
- ✅ **TP-Link** - Standard RADIUS attributes
- ✅ **D-Link** - Standard RADIUS attributes
- ✅ **UniFi / Ubiquiti** - Data limits and VLAN support
- ✅ **Aruba** - User roles and admin roles
- ✅ **Any RADIUS-compliant device** - Standard attributes work universally

### Core Functionality
- 👤 **User Management** - Create, edit, delete users with cleartext password authentication
- 📦 **Plans & Policies** - Define service plans with vendor-specific or standard attributes
- 🖧 **NAS Management** - Configure network devices with vendor-specific settings
- 📊 **Accounting & Monitoring** - Real-time session tracking and historical usage data
- 🔐 **Secure Admin Panel** - Password-protected with bcrypt hashing and CSRF protection
- 🎨 **Modern UI** - Clean, responsive Bootstrap 5 interface

### What This System Does NOT Include
- ❌ No voucher system
- ❌ No billing/payment integration
- ❌ No captive portal

This is a **pure RADIUS management system** focused on authentication, authorization, and accounting.

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Browser   │
└─────┬───────┬───┘
      │       │
      │       │ HTTP (Port 8081)
      │       ▼
      │   ┌─────────────────┐
      │   │   phpMyAdmin    │  ← Database Management
      │   └────────┬────────┘
      │            │
      │ HTTP (Port 5000)
      ▼            │
┌─────────────────┐│
│  Flask Web App  ││  ← Admin Interface
│  (Gunicorn)     ││
└────────┬────────┘│
         │         │
         └─────────┘
              │
              ▼
┌─────────────────┐     ┌──────────────────┐
│   MariaDB       │◄────┤  FreeRADIUS 3.0  │
│   Database      │     │  (Ports 1812/1813)│
└─────────────────┘     └────────┬─────────┘
                                 │ RADIUS
                                 ▼
                        ┌─────────────────┐
                        │  Network Device │
                        │  (NAS)          │
                        └─────────────────┘
```

## 📋 Requirements

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd safenet
```

### 2. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and change the following **IMPORTANT** values:

```env
# Flask Configuration
SECRET_KEY=your-very-long-random-secret-key-here

# Database Configuration
DB_PASSWORD=your-strong-database-password
DB_ROOT_PASSWORD=your-strong-root-password

# RADIUS Configuration
RADIUS_SECRET=your-radius-shared-secret

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
ADMIN_EMAIL=admin@yourdomain.com
```

### 3. Build and Start

```bash
# Build the containers
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access the Web Interface

Open your browser and navigate to:

```
http://localhost:5000
```

**Default credentials:**
- Username: `admin` (or what you set in `.env`)
- Password: `admin123` (or what you set in `.env`)

⚠️ **IMPORTANT:** Change the default password immediately after first login!

### 5. Access phpMyAdmin (Database Management)

phpMyAdmin is available for direct database management:

```
http://localhost:8081
```

**Login credentials:**
- **Server**: `db` (or leave default)
- **Username**: `radius` (or your `DB_USER` from `.env`)
- **Password**: Your `DB_PASSWORD` from `.env`

**For root access:**
- **Username**: `root`
- **Password**: Your `DB_ROOT_PASSWORD` from `.env`

⚠️ **Security Note:** In production, restrict phpMyAdmin access via firewall or remove it entirely if not needed.

## 📖 Usage Guide

### Adding a NAS Device

1. Navigate to **NAS Devices** in the sidebar
2. Click **Add NAS**
3. Fill in the details:
   - **IP Address**: The IP of your router/switch/AP
   - **Short Name**: A friendly identifier
   - **Secret**: RADIUS shared secret (must match device config)
   - **Vendor**: Select your device manufacturer
   - **Type**: Device type (Cisco, other, etc.)
4. Click **Save NAS**

### Creating a Plan

1. Navigate to **Plans** in the sidebar
2. Click **Add Plan**
3. Enter plan details:
   - **Name**: Plan identifier (e.g., "basic", "premium")
   - **Description**: What this plan offers
   - **Vendor**: Default vendor for this plan
4. Click **Save Plan**
5. Add RADIUS attributes:
   - Click **Add Attribute**
   - Choose attribute (e.g., `Session-Timeout`, `Mikrotik-Rate-Limit`)
   - Set operator (usually `:=`)
   - Enter value (e.g., `3600`, `10M/10M`)
   - Select vendor (or leave as Standard)

### Adding Users

1. Navigate to **Users** in the sidebar
2. Click **Add User**
3. Fill in user details:
   - **Username**: User's login name
   - **Password**: Cleartext password
   - **Plan**: Assign a service plan (optional)
   - **Expires At**: Optional expiration date
   - **Active**: Enable/disable user
4. Click **Save User**

### Monitoring Sessions

1. Navigate to **Accounting** in the sidebar
2. View active and historical sessions
3. Filter by:
   - Username
   - NAS IP
   - Status (Active/Closed)
4. Click **View** to see detailed session information

## 🔧 Configuration Examples

### Cisco Router

**On the Cisco device:**

```
aaa new-model
aaa authentication login default group radius local
aaa authorization network default group radius
aaa accounting network default start-stop group radius

radius server SAFENET
 address ipv4 <your-server-ip> auth-port 1812 acct-port 1813
 key <your-radius-secret>
```

**In SafeNet:**
- Add NAS with Cisco vendor
- Create plan with `Cisco-AVPair` attributes

### MikroTik Router

**On MikroTik:**

```
/radius
add address=<your-server-ip> secret=<your-radius-secret> service=login
```

**In SafeNet:**
- Add NAS with MikroTik vendor
- Create plan with `Mikrotik-Rate-Limit` (e.g., `10M/10M`)

### UniFi Controller

**In UniFi Controller:**
1. Settings → Profiles → RADIUS
2. Add RADIUS Profile:
   - IP: `<your-server-ip>`
   - Port: `1812`
   - Secret: `<your-radius-secret>`

**In SafeNet:**
- Add NAS with Ubiquiti vendor
- Create plan with standard or Ubiquiti-specific attributes

## 🐛 Debugging & Testing

### Test RADIUS Authentication

From the FreeRADIUS container:

```bash
# Enter the container
docker exec -it safenet-radius bash

# Test authentication
radtest username password localhost 0 testing123

# Run FreeRADIUS in debug mode
freeradius -X
```

### View Logs

```bash
# Web application logs
docker-compose logs -f web

# FreeRADIUS logs
docker-compose logs -f freeradius

# Database logs
docker-compose logs -f db
```

### Check Database

```bash
# Connect to database
docker exec -it safenet-db mysql -u radius -p radius

# View users
SELECT * FROM radcheck;

# View active sessions
SELECT * FROM radacct WHERE acctstoptime IS NULL;
```

### Common Issues

**Issue: Can't connect to web interface**
- Check if container is running: `docker-compose ps`
- Check logs: `docker-compose logs web`
- Verify port 5000 is not in use: `netstat -an | grep 5000`

**Issue: RADIUS authentication fails**
- Run FreeRADIUS in debug mode: `docker exec -it safenet-radius freeradius -X`
- Check NAS secret matches in both device and SafeNet
- Verify user exists: `docker exec -it safenet-db mysql -u radius -p -e "SELECT * FROM radcheck"`

**Issue: Database connection errors**
- Wait for database to fully start (can take 30-60 seconds)
- Check database credentials in `.env`
- Restart services: `docker-compose restart`

## 🔒 Security Best Practices

1. **Change default passwords** immediately
2. **Use strong RADIUS secrets** (20+ random characters)
3. **Enable firewall rules** to restrict access:
   - Port 5000: Admin access only
   - Ports 1812/1813: NAS devices only
4. **Use HTTPS** in production (add reverse proxy like nginx)
5. **Regular backups** of database
6. **Keep Docker images updated**

## 📁 Project Structure

```
safenet/
├── app.py                  # Main Flask application
├── config.py               # Configuration
├── models.py               # Database models
├── forms.py                # WTForms
├── requirements.txt        # Python dependencies
├── Dockerfile              # Flask app container
├── docker-compose.yml      # Docker orchestration
├── .env.example            # Environment template
├── database/
│   └── schema.sql          # Database schema
├── freeradius/
│   ├── Dockerfile          # FreeRADIUS container
│   ├── radiusd.conf        # Main config
│   ├── clients.conf        # NAS clients
│   └── mods-available/
│       └── sql             # SQL module config
├── templates/              # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── auth/
│   ├── users/
│   ├── plans/
│   ├── nas/
│   ├── accounting/
│   └── errors/
└── static/                 # Static assets
    ├── css/
    ├── js/
    └── img/
```

## 🔄 Backup & Restore

### Backup Database

```bash
# Create backup
docker exec safenet-db mysqldump -u radius -p<password> radius > backup_$(date +%Y%m%d).sql

# Or use docker-compose
docker-compose exec db mysqldump -u radius -p<password> radius > backup.sql
```

### Restore Database

```bash
# Restore from backup
docker exec -i safenet-db mysql -u radius -p<password> radius < backup.sql

# Or use docker-compose
docker-compose exec -T db mysql -u radius -p<password> radius < backup.sql
```

## 🛠️ Maintenance

### Update System

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Clean Up

```bash
# Remove old containers and images
docker-compose down --rmi all --volumes

# Prune unused Docker resources
docker system prune -a
```

## 📊 Performance Tuning

### For High-Load Environments

Edit `docker-compose.yml`:

```yaml
web:
  command: gunicorn --bind 0.0.0.0:5000 --workers 8 --timeout 120 app:app
```

Edit `freeradius/radiusd.conf`:

```
thread pool {
    start_servers = 10
    max_servers = 64
    min_spare_servers = 5
    max_spare_servers = 20
}
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the debugging section above
- Review FreeRADIUS documentation: https://freeradius.org/

## 🙏 Acknowledgments

- FreeRADIUS Project
- Flask Framework
- Bootstrap UI Framework
- Docker Community

---

**Built with ❤️ for network administrators worldwide**

