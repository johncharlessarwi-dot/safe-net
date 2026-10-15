# Vendor-Specific RADIUS Attributes Guide

This document provides examples of vendor-specific RADIUS attributes for different network equipment manufacturers.

## Table of Contents

1. [Standard RADIUS Attributes](#standard-radius-attributes)
2. [Cisco](#cisco)
3. [MikroTik](#mikrotik)
4. [Ubiquiti / UniFi](#ubiquiti--unifi)
5. [Aruba](#aruba)
6. [TP-Link](#tp-link)
7. [D-Link](#d-link)

## Standard RADIUS Attributes

These attributes work with **all** RADIUS-compliant devices.

### Session Management

| Attribute | Operator | Value Example | Description |
|-----------|----------|---------------|-------------|
| `Session-Timeout` | `:=` | `3600` | Maximum session time in seconds |
| `Idle-Timeout` | `:=` | `600` | Disconnect after idle time (seconds) |
| `Acct-Interim-Interval` | `:=` | `300` | Accounting update interval (seconds) |

### Network Configuration

| Attribute | Operator | Value Example | Description |
|-----------|----------|---------------|-------------|
| `Framed-IP-Address` | `:=` | `192.168.1.100` | Assign specific IP address |
| `Framed-IP-Netmask` | `:=` | `255.255.255.0` | Subnet mask for framed IP |
| `Framed-Route` | `:=` | `192.168.2.0/24` | Add static route |
| `Filter-Id` | `:=` | `allow-all` | Apply ACL/filter |

### Service Control

| Attribute | Operator | Value Example | Description |
|-----------|----------|---------------|-------------|
| `Service-Type` | `:=` | `Framed-User` | Type of service |
| `Framed-Protocol` | `:=` | `PPP` | Framing protocol |
| `Reply-Message` | `:=` | `Welcome!` | Message to user |

## Cisco

### Cisco-AVPair

The most versatile Cisco attribute. Format: `key=value`

#### QoS / Rate Limiting

```
Attribute: Cisco-AVPair
Operator: :=
Value: ip:sub-qos-policy-in=POLICY_10M
Vendor: cisco
```

```
Attribute: Cisco-AVPair
Operator: :=
Value: ip:sub-qos-policy-out=POLICY_10M
Vendor: cisco
```

#### ACL Assignment

```
Attribute: Cisco-AVPair
Operator: :=
Value: ip:inacl#1=permit ip any any
Vendor: cisco
```

```
Attribute: Cisco-AVPair
Operator: :=
Value: ip:outacl#1=permit ip any any
Vendor: cisco
```

#### VLAN Assignment

```
Attribute: Tunnel-Type
Operator: :=
Value: VLAN
Vendor: standard
```

```
Attribute: Tunnel-Medium-Type
Operator: :=
Value: IEEE-802
Vendor: standard
```

```
Attribute: Tunnel-Private-Group-Id
Operator: :=
Value: 100
Vendor: standard
```

#### Privilege Level

```
Attribute: Cisco-AVPair
Operator: :=
Value: shell:priv-lvl=15
Vendor: cisco
```

### Example Plans

**Basic Internet (10 Mbps)**

```
Session-Timeout := 28800 (8 hours)
Idle-Timeout := 600
Cisco-AVPair := "ip:sub-qos-policy-in=10M"
Cisco-AVPair += "ip:sub-qos-policy-out=10M"
```

**Admin Access**

```
Cisco-AVPair := "shell:priv-lvl=15"
Service-Type := Administrative-User
```

## MikroTik

### Rate Limiting

The most common MikroTik attribute.

#### Basic Rate Limit

```
Attribute: Mikrotik-Rate-Limit
Operator: :=
Value: 10M/10M
Vendor: mikrotik
```

Format: `rx-rate[/tx-rate] [rx-burst-rate[/tx-burst-rate] [rx-burst-threshold[/tx-burst-threshold] [rx-burst-time[/tx-burst-time] [priority] [rx-rate-min[/tx-rate-min]]]]]`

#### Advanced Rate Limit with Burst

```
Attribute: Mikrotik-Rate-Limit
Operator: :=
Value: 10M/10M 20M/20M 5M/5M 10/10 8
Vendor: mikrotik
```

- Download: 10 Mbps (burst to 20 Mbps at 5 Mbps threshold)
- Upload: 10 Mbps (burst to 20 Mbps at 5 Mbps threshold)
- Burst time: 10 seconds
- Priority: 8

### Address Lists

```
Attribute: Mikrotik-Address-List
Operator: :=
Value: premium_users
Vendor: mikrotik
```

### Group Assignment

```
Attribute: Mikrotik-Group
Operator: :=
Value: full
Vendor: mikrotik
```

### Data Limits

```
Attribute: Mikrotik-Recv-Limit
Operator: :=
Value: 10737418240
Vendor: mikrotik
```

```
Attribute: Mikrotik-Xmit-Limit
Operator: :=
Value: 10737418240
Vendor: mikrotik
```

Value in bytes (example: 10 GB = 10737418240 bytes)

### Example Plans

**Basic Plan (5 Mbps)**

```
Mikrotik-Rate-Limit := "5M/5M"
Session-Timeout := 86400 (24 hours)
```

**Premium Plan (20 Mbps with burst)**

```
Mikrotik-Rate-Limit := "20M/20M 30M/30M 10M/10M 15/15 8"
Mikrotik-Address-List := "premium_users"
```

**Limited Data Plan (10 GB)**

```
Mikrotik-Rate-Limit := "10M/10M"
Mikrotik-Recv-Limit := 10737418240
Mikrotik-Xmit-Limit := 10737418240
```

## Ubiquiti / UniFi

### Data Limits

```
Attribute: Ubiquiti-Data-Limit-Down
Operator: :=
Value: 10737418240
Vendor: ubiquiti
```

```
Attribute: Ubiquiti-Data-Limit-Up
Operator: :=
Value: 10737418240
Vendor: ubiquiti
```

Value in bytes.

### VLAN Assignment

```
Attribute: Ubiquiti-VLAN-ID
Operator: :=
Value: 100
Vendor: ubiquiti
```

### Example Plans

**Guest WiFi (1 GB limit)**

```
Session-Timeout := 3600
Ubiquiti-Data-Limit-Down := 1073741824
Ubiquiti-Data-Limit-Up := 1073741824
Ubiquiti-VLAN-ID := 10
```

**Premium WiFi (Unlimited, VLAN 20)**

```
Session-Timeout := 28800
Ubiquiti-VLAN-ID := 20
```

## Aruba

### User Roles

```
Attribute: Aruba-User-Role
Operator: :=
Value: employee
Vendor: aruba
```

### Admin Roles

```
Attribute: Aruba-Admin-Role
Operator: :=
Value: network-admin
Vendor: aruba
```

### Example Plans

**Employee Access**

```
Aruba-User-Role := "employee"
Session-Timeout := 28800
```

**Guest Access**

```
Aruba-User-Role := "guest"
Session-Timeout := 3600
Idle-Timeout := 600
```

**Administrator**

```
Aruba-Admin-Role := "network-admin"
Service-Type := Administrative-User
```

## TP-Link

TP-Link devices primarily use **standard RADIUS attributes**.

### Example Plans

**Basic Internet**

```
Session-Timeout := 3600
Idle-Timeout := 600
Filter-Id := "allow-internet"
```

**VLAN Assignment**

```
Tunnel-Type := VLAN
Tunnel-Medium-Type := IEEE-802
Tunnel-Private-Group-Id := 100
```

## D-Link

D-Link devices primarily use **standard RADIUS attributes**.

### Example Plans

**Standard Access**

```
Session-Timeout := 7200
Service-Type := Framed-User
Framed-Protocol := PPP
```

**VLAN Assignment**

```
Tunnel-Type := VLAN
Tunnel-Medium-Type := IEEE-802
Tunnel-Private-Group-Id := 50
```

## Creating Plans in SafeNet

### Example: MikroTik 10 Mbps Plan

1. **Create Plan**
   - Name: `mikrotik_10m`
   - Vendor: `mikrotik`

2. **Add Attributes**
   - Attribute: `Mikrotik-Rate-Limit`
   - Operator: `:=`
   - Value: `10M/10M`
   - Vendor: `mikrotik`

   - Attribute: `Session-Timeout`
   - Operator: `:=`
   - Value: `86400`
   - Vendor: (leave empty for standard)

### Example: Cisco Admin Access

1. **Create Plan**
   - Name: `cisco_admin`
   - Vendor: `cisco`

2. **Add Attributes**
   - Attribute: `Cisco-AVPair`
   - Operator: `:=`
   - Value: `shell:priv-lvl=15`
   - Vendor: `cisco`

   - Attribute: `Service-Type`
   - Operator: `:=`
   - Value: `Administrative-User`
   - Vendor: (standard)

### Example: Multi-Vendor Guest WiFi

1. **Create Plan**
   - Name: `guest_wifi`
   - Vendor: `standard`

2. **Add Attributes**
   - Attribute: `Session-Timeout`
   - Operator: `:=`
   - Value: `3600`
   - Vendor: (standard)

   - Attribute: `Idle-Timeout`
   - Operator: `:=`
   - Value: `600`
   - Vendor: (standard)

   - Attribute: `Tunnel-Type`
   - Operator: `:=`
   - Value: `VLAN`
   - Vendor: (standard)

   - Attribute: `Tunnel-Medium-Type`
   - Operator: `:=`
   - Value: `IEEE-802`
   - Vendor: (standard)

   - Attribute: `Tunnel-Private-Group-Id`
   - Operator: `:=`
   - Value: `10`
   - Vendor: (standard)

## Operators

| Operator | Meaning | Use Case |
|----------|---------|----------|
| `:=` | Assign | Set attribute value |
| `==` | Equal | Check attribute value |
| `+=` | Add | Add to existing value |
| `!=` | Not Equal | Check not equal |
| `>` | Greater Than | Numeric comparison |
| `<` | Less Than | Numeric comparison |
| `>=` | Greater or Equal | Numeric comparison |
| `<=` | Less or Equal | Numeric comparison |

Most commonly used: `:=` (assign) and `+=` (add multiple values)

## Testing Attributes

After creating a plan and assigning it to a user, test with:

```bash
# From SafeNet server
docker exec -it safenet-radius radtest username password localhost 0 testing123

# Check what attributes are returned
docker exec -it safenet-radius freeradius -X
# Then authenticate from your device
```

## References

- [FreeRADIUS Dictionary Files](https://github.com/FreeRADIUS/freeradius-server/tree/master/share/dictionary)
- [Cisco RADIUS Attributes](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/security/a1/sec-a1-cr-book/sec-cr-r1.html)
- [MikroTik RADIUS](https://wiki.mikrotik.com/wiki/Manual:RADIUS_Client)
- [RFC 2865 - RADIUS](https://tools.ietf.org/html/rfc2865)


