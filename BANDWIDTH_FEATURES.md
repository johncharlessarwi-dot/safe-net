# Bandwidth Management & RADIUS Features Guide

## Overview

SafeNet now includes comprehensive bandwidth limit management and full visibility into FreeRADIUS authentication, authorization, and accounting features.

## New Features

### 1. Bandwidth Limit Management

#### Plan-Level Bandwidth Limits
- Set default upload/download speeds for all users in a plan
- Set monthly data caps (in GB)
- Limits are vendor-agnostic and automatically converted to appropriate RADIUS attributes

#### User-Level Bandwidth Limits
- Override plan limits for specific users
- Set individual upload/download speeds
- Set individual data caps
- User limits take precedence over plan limits

#### Supported Formats
- **Speed**: `10M`, `100M`, `1G` (Megabits/Gigabits per second)
- **MikroTik Format**: `10M/20M` (Upload/Download combined)
- **Data Cap**: Specified in GB, automatically converted to bytes

### 2. Enhanced Accounting View

The accounting detail page now shows:
- **Total Data Usage**: Combined upload/download in MB and GB
- **Average Speed**: Calculated based on session duration
- **Session Duration**: Precise timing with hours/minutes/seconds
- **All RADIUS Attributes**: Complete session information

### 3. Authentication & Authorization Logs

New **Auth Logs** page (`/auth-logs`) provides:
- Real-time authentication attempts
- Success/failure tracking
- Filter by reply type (Access-Accept, Access-Reject, Access-Challenge)
- Search by username
- Statistics dashboard showing:
  - Total authentications
  - Accepted count
  - Rejected count
  - Challenged count

### 4. RADIUS Features Reference

New **RADIUS Features** page (`/radius-features`) displays:
- **Standard RADIUS Attributes**: All RFC-compliant attributes
  - Session Management (timeouts, intervals)
  - Network Configuration (IP addresses, routes)
  - Service Control (service types, protocols)
  - Bandwidth & QoS
  - VLAN Assignment
  - Data Limits
- **Vendor-Specific Attributes**: 
  - Cisco (AVPair, QoS policies)
  - MikroTik (Rate-Limit, Data limits)
  - Ubiquiti/UniFi (Data limits, VLAN)
  - Aruba (User roles, Admin roles)
- **Configuration Examples**: Common use cases and formats

## Usage Guide

### Setting Bandwidth Limits for a Plan

1. Navigate to **Plans** → **Add Plan** or **Edit Plan**
2. Scroll to **Bandwidth Limits** section
3. Enter:
   - **Upload Speed**: e.g., `10M`, `100M`
   - **Download Speed**: e.g., `10M`, `100M`
   - **Data Cap**: Monthly limit in GB (e.g., `100` for 100 GB)
4. Click **Save Plan**

### Setting Bandwidth Limits for a User

1. Navigate to **Users** → **Add User** or **Edit User**
2. Scroll to **Bandwidth Limits** section
3. Enter user-specific limits (overrides plan defaults)
4. Leave fields empty to use plan defaults
5. Click **Save User**

### Viewing Authentication Logs

1. Navigate to **Auth Logs** in the sidebar
2. View all authentication attempts
3. Filter by:
   - Username (search)
   - Reply type (Accept/Reject/Challenge)
4. Review statistics in the dashboard cards

### Viewing Enhanced Accounting Data

1. Navigate to **Accounting** → Click on any session
2. View detailed information:
   - Total data usage (MB/GB)
   - Average connection speed
   - Session duration
   - All RADIUS attributes

### Exploring RADIUS Features

1. Navigate to **RADIUS Features** in the sidebar
2. Browse standard and vendor-specific attributes
3. Copy attribute names and formats for use in plans
4. Review configuration examples

## Database Schema Changes

The following columns were added:

**plans table:**
- `upload_speed` VARCHAR(32)
- `download_speed` VARCHAR(32)
- `data_cap` BIGINT(20)

**radusers table:**
- `upload_speed` VARCHAR(32)
- `download_speed` VARCHAR(32)
- `data_cap` BIGINT(20)

Migration script: `database/migrate_add_bandwidth.sql`

## Technical Notes

### Bandwidth Limit Storage
- Speeds are stored as strings (e.g., "10M", "100M")
- Data caps are stored in bytes (converted from GB on input)
- Display converts bytes back to GB for user-friendly viewing

### RADIUS Attribute Application
- Bandwidth limits are stored in the database
- To apply limits via RADIUS, add appropriate attributes to plans:
  - **MikroTik**: `Mikrotik-Rate-Limit := "10M/10M"`
  - **Cisco**: `Cisco-AVPair := "ip:sub-qos-policy-in=POLICY_10M"`
  - **Ubiquiti**: `Ubiquiti-Data-Limit-Down := 10737418240`
- The UI provides bandwidth limit fields for convenience; actual RADIUS enforcement requires adding attributes to plans

### Authentication Logs
- Logs are stored in `radpostauth` table
- Automatically populated by FreeRADIUS on every authentication attempt
- Includes username, password hash, reply type, and timestamp

## Examples

### Example 1: Basic Plan with 10 Mbps Limit
```
Plan: Basic-10M
Upload Speed: 10M
Download Speed: 10M
Data Cap: (unlimited)
```

### Example 2: Premium Plan with 100 Mbps and 500 GB Cap
```
Plan: Premium-100M
Upload Speed: 100M
Download Speed: 100M
Data Cap: 500
```

### Example 3: MikroTik Plan with Asymmetric Speed
```
Plan: MikroTik-Asymmetric
Upload Speed: 10M/20M (MikroTik format)
Download Speed: (leave empty)
Data Cap: 100
```

## Troubleshooting

### Bandwidth Limits Not Applied
- Ensure RADIUS attributes are added to the plan
- Check vendor-specific attribute formats
- Verify NAS device supports the attributes

### Authentication Logs Not Showing
- Verify FreeRADIUS `mods-enabled/sql` is configured
- Check `radpostauth` table exists
- Ensure FreeRADIUS has write permissions

### Data Cap Display Issues
- Data caps are stored in bytes internally
- Display converts to GB automatically
- Check conversion: 1 GB = 1,073,741,824 bytes

## Future Enhancements

Potential future features:
- Automatic RADIUS attribute generation from bandwidth limits
- Real-time bandwidth monitoring
- Bandwidth usage alerts
- Historical bandwidth reports
- Vendor-specific attribute templates

