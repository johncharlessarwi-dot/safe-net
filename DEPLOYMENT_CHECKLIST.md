# SafeNet RADIUS Manager - Deployment Checklist

Use this checklist to ensure a successful deployment.

## Pre-Deployment

### System Requirements
- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] 2GB RAM available
- [ ] 10GB disk space available
- [ ] Ports 5000, 1812, 1813 available
- [ ] Static IP address assigned (recommended)

### Security Preparation
- [ ] Generate strong SECRET_KEY: `openssl rand -hex 32`
- [ ] Generate strong DB_PASSWORD: `openssl rand -hex 16`
- [ ] Generate strong DB_ROOT_PASSWORD: `openssl rand -hex 16`
- [ ] Generate strong RADIUS_SECRET: `openssl rand -hex 16`
- [ ] Choose strong ADMIN_PASSWORD (12+ characters)
- [ ] Document all passwords securely

## Installation

### Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Update `SECRET_KEY` in `.env`
- [ ] Update `DB_PASSWORD` in `.env`
- [ ] Update `DB_ROOT_PASSWORD` in `.env`
- [ ] Update `RADIUS_SECRET` in `.env`
- [ ] Update `ADMIN_USERNAME` in `.env`
- [ ] Update `ADMIN_PASSWORD` in `.env`
- [ ] Update `ADMIN_EMAIL` in `.env`
- [ ] Set `FLASK_ENV=production` in `.env`

### Build and Start
- [ ] Run `docker-compose build`
- [ ] Run `docker-compose up -d`
- [ ] Wait 30-60 seconds for initialization
- [ ] Run `docker-compose ps` - all services should be "Up"
- [ ] Check logs: `docker-compose logs` for errors

### Initial Access
- [ ] Access web interface: `http://your-server-ip:5000`
- [ ] Login with admin credentials
- [ ] Change admin password immediately
- [ ] Verify dashboard loads correctly

## Configuration

### Create First Plan
- [ ] Navigate to Plans → Add Plan
- [ ] Create a test plan (e.g., "basic")
- [ ] Add at least one attribute (e.g., Session-Timeout)
- [ ] Save and verify plan appears in list

### Create Test User
- [ ] Navigate to Users → Add User
- [ ] Create test user (e.g., "testuser")
- [ ] Assign to test plan
- [ ] Set as Active
- [ ] Save and verify user appears in list

### Configure NAS Device
- [ ] Navigate to NAS Devices → Add NAS
- [ ] Add localhost for testing (127.0.0.1)
- [ ] Add your first network device
- [ ] Verify RADIUS secret matches `.env`
- [ ] Select correct vendor
- [ ] Save and verify NAS appears in list

## Testing

### RADIUS Authentication Test
- [ ] Run: `docker exec -it safenet-radius radtest testuser testpass123 localhost 0 testing123`
- [ ] Verify "Access-Accept" response
- [ ] Check for any error messages

### Debug Mode Test
- [ ] Run: `docker exec -it safenet-radius freeradius -X`
- [ ] In another terminal, run radtest
- [ ] Verify authentication appears in debug output
- [ ] Check for any errors or warnings
- [ ] Stop debug mode (Ctrl+C)

### Database Verification
- [ ] Run: `docker exec -it safenet-db mysql -u radius -p`
- [ ] Query: `SELECT * FROM radcheck;`
- [ ] Verify test user exists
- [ ] Query: `SELECT * FROM nas;`
- [ ] Verify NAS devices exist
- [ ] Exit database shell

### Network Device Test
- [ ] Configure your network device with SafeNet IP and secret
- [ ] Attempt authentication from device
- [ ] Check Accounting page for session
- [ ] Verify session details are correct

## Security Hardening

### Firewall Configuration
- [ ] Enable firewall: `sudo ufw enable`
- [ ] Allow SSH: `sudo ufw allow 22/tcp`
- [ ] Restrict web access: `sudo ufw allow from <admin-ip> to any port 5000`
- [ ] Allow RADIUS from NAS only: `sudo ufw allow from <nas-ip> to any port 1812 proto udp`
- [ ] Allow accounting from NAS only: `sudo ufw allow from <nas-ip> to any port 1813 proto udp`
- [ ] Verify rules: `sudo ufw status`

### HTTPS Setup (Production)
- [ ] Install nginx: `sudo apt install nginx`
- [ ] Obtain SSL certificate (Let's Encrypt recommended)
- [ ] Configure nginx reverse proxy
- [ ] Test nginx config: `sudo nginx -t`
- [ ] Reload nginx: `sudo systemctl reload nginx`
- [ ] Access via HTTPS: `https://your-domain.com`
- [ ] Update firewall for HTTPS: `sudo ufw allow 443/tcp`

### Docker Security
- [ ] Verify containers run as non-root (web container)
- [ ] Check no unnecessary ports exposed: `docker-compose ps`
- [ ] Verify internal network isolation
- [ ] Review `.env` file permissions: `chmod 600 .env`

## Backup Configuration

### Manual Backup Test
- [ ] Run: `./scripts/manage.sh backup`
- [ ] Verify backup file created in `backups/`
- [ ] Test restore: `./scripts/manage.sh restore <backup-file>`
- [ ] Verify data restored correctly

### Automated Backups
- [ ] Create backup script in `/opt/safenet/backup.sh`
- [ ] Make executable: `chmod +x /opt/safenet/backup.sh`
- [ ] Test backup script
- [ ] Add to crontab: `crontab -e`
- [ ] Add daily backup: `0 2 * * * /opt/safenet/backup.sh`
- [ ] Verify cron job: `crontab -l`

### Backup Storage
- [ ] Configure off-site backup location
- [ ] Test backup restoration from off-site
- [ ] Document backup retention policy
- [ ] Set up backup monitoring/alerts

## Monitoring

### Service Monitoring
- [ ] Create monitoring script
- [ ] Test monitoring script
- [ ] Add to crontab (every 5 minutes)
- [ ] Configure email alerts
- [ ] Test alert system

### Log Monitoring
- [ ] Configure log rotation
- [ ] Set up centralized logging (optional)
- [ ] Define log retention policy
- [ ] Test log access

### Performance Monitoring
- [ ] Monitor CPU usage: `docker stats`
- [ ] Monitor disk usage: `df -h`
- [ ] Monitor memory usage: `free -h`
- [ ] Set up alerts for resource thresholds

## Documentation

### Internal Documentation
- [ ] Document server IP address
- [ ] Document admin credentials (secure location)
- [ ] Document RADIUS secret (secure location)
- [ ] Document NAS device configurations
- [ ] Document backup procedures
- [ ] Document restore procedures
- [ ] Document troubleshooting steps

### Network Device Documentation
- [ ] Document each NAS device configuration
- [ ] Document RADIUS settings on each device
- [ ] Create network diagram
- [ ] Document vendor-specific settings

## Production Readiness

### Performance Tuning
- [ ] Adjust Gunicorn workers if needed (docker-compose.yml)
- [ ] Adjust FreeRADIUS thread pool if needed (radiusd.conf)
- [ ] Configure database connection pool
- [ ] Test under expected load

### High Availability (Optional)
- [ ] Configure database replication
- [ ] Set up multiple RADIUS servers
- [ ] Configure load balancing
- [ ] Test failover scenarios

### Maintenance Plan
- [ ] Schedule regular updates
- [ ] Plan maintenance windows
- [ ] Document update procedures
- [ ] Create rollback plan

## Post-Deployment

### User Training
- [ ] Train administrators on web interface
- [ ] Document common tasks
- [ ] Create user management procedures
- [ ] Document plan creation procedures

### Monitoring Setup
- [ ] Verify all monitoring is active
- [ ] Test alert notifications
- [ ] Review logs daily for first week
- [ ] Establish baseline metrics

### Support Preparation
- [ ] Document support contacts
- [ ] Create incident response plan
- [ ] Set up support ticket system (if needed)
- [ ] Document escalation procedures

## Ongoing Maintenance

### Daily Tasks
- [ ] Check service status
- [ ] Review error logs
- [ ] Monitor active sessions
- [ ] Check disk space

### Weekly Tasks
- [ ] Review accounting data
- [ ] Check backup success
- [ ] Review security logs
- [ ] Update user accounts as needed

### Monthly Tasks
- [ ] Review and clean old accounting data
- [ ] Update documentation
- [ ] Review security settings
- [ ] Plan capacity upgrades if needed
- [ ] Test backup restoration

### Quarterly Tasks
- [ ] Update Docker images
- [ ] Review and update plans
- [ ] Security audit
- [ ] Performance review
- [ ] Disaster recovery test

## Verification

### Final Checks
- [ ] All services running: `docker-compose ps`
- [ ] Web interface accessible
- [ ] RADIUS authentication working
- [ ] Accounting data being recorded
- [ ] Backups configured and tested
- [ ] Monitoring active
- [ ] Documentation complete
- [ ] Security hardened
- [ ] Firewall configured
- [ ] HTTPS enabled (production)

### Sign-Off
- [ ] Deployment completed by: ________________
- [ ] Date: ________________
- [ ] Verified by: ________________
- [ ] Production ready: Yes / No

## Troubleshooting Reference

If issues occur during deployment:

1. **Check logs**: `docker-compose logs`
2. **Verify environment**: `cat .env`
3. **Test database**: `docker exec -it safenet-db mysql -u radius -p`
4. **Debug RADIUS**: `docker exec -it safenet-radius freeradius -X`
5. **Restart services**: `docker-compose restart`
6. **Rebuild if needed**: `docker-compose down && docker-compose build --no-cache && docker-compose up -d`

For detailed troubleshooting, see [SETUP.md](SETUP.md) and [README.md](README.md).

---

**Once all items are checked, your SafeNet RADIUS Manager is production-ready! 🎉**


