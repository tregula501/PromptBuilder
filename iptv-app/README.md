# IPTV Streaming Application

A secure IPTV streaming web application with VPN-routed streams.

## Features

- Browse 2,400+ live TV channels
- Search and filter by category
- Favorites system
- Secure authentication (admin-managed users)
- Streams routed through PIA VPN (Poland)
- Hourly health checks
- Chrome/Firefox compatible video player
- Auto-retry on stream failure (3 attempts)

## Quick Start

### 1. Configure Environment

Edit the `.env` file and fill in the required values:

```bash
# Generate a secure JWT secret
openssl rand -hex 32

# Required changes in .env:
JWT_SECRET=<paste generated secret>
ADMIN_PASSWORD=<choose a secure password>
PIA_USERNAME=<your PIA username, e.g., p1234567>
PIA_PASSWORD=<your PIA password>
```

### 2. Build and Start

```bash
cd C:\docker-projects\iptv-app

# Build containers
docker-compose build

# Start all services
docker-compose up -d
```

### 3. Configure SWAG (Unraid Server)

Copy the nginx configuration to your SWAG container:

```bash
# On Unraid, copy the file:
# From: C:\docker-projects\iptv-app\nginx\iptv.subdomain.conf
# To:   /mnt/user/appdata/swag/nginx/proxy-confs/iptv.subdomain.conf

# Then restart SWAG
docker restart swag
```

### 4. Access the Application

- URL: https://iptv.regulaplex.net
- Login with your admin credentials

## Architecture

```
Internet -> SWAG (Unraid:443) -> Windows Docker (192.168.154.158)
                                  |-- Frontend (:3000)
                                  |-- Backend (:4000)
                                  \-- VPN Container -> Poland -> Streams
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React SPA |
| Backend | 4000 | Express API |
| VPN | 8888 | Gluetun HTTP proxy |

## Admin Panel

Access admin features at `/admin`:
- Create/manage users
- View system status (VPN, playlist, streams)
- Trigger manual health checks

## Troubleshooting

### Check if VPN is connected
```bash
docker logs iptv-vpn
docker exec iptv-vpn wget -qO- http://ipinfo.io
```

### Check backend logs
```bash
docker logs iptv-backend
```

### Rebuild after changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database location
SQLite database is stored at: `backend/data/iptv.db`

## Security Notes

- All streams routed through VPN
- JWT tokens with 15-minute expiry
- Passwords hashed with bcrypt (12 rounds)
- Rate limiting on login (5 attempts/15 min)
- HTTPS via SWAG/Let's Encrypt

## Technology Stack

- **Frontend**: React 18, Tailwind CSS, Video.js
- **Backend**: Node.js, Express, SQLite
- **VPN**: Gluetun (PIA Poland)
- **Proxy**: SWAG/nginx
