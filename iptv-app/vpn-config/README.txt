VPN Configuration Guide
=======================

This folder is for custom OpenVPN configuration files.

OPTION 1: Use PIA (Default)
---------------------------
Just edit the .env file:
  VPN_SERVICE_PROVIDER=private internet access
  VPN_REGION=Poland

Available PIA regions:
  - Poland, UK London, UK Manchester, US East, US West
  - Germany, France, Netherlands, Sweden, Switzerland
  - Canada, Australia, Japan, and more...

To change regions:
  1. Edit .env and change VPN_REGION
  2. Run: docker-compose down vpn && docker-compose up -d vpn
  3. Wait 30 seconds for VPN to reconnect


OPTION 2: Use Custom .ovpn File
-------------------------------
To use any VPN provider's .ovpn file:

1. Edit .env and set:
   VPN_SERVICE_PROVIDER=custom

2. Place your OpenVPN config in this folder as: vpn.ovpn

3. If your .ovpn requires username/password, add to vpn.ovpn:
   auth-user-pass /gluetun/custom/auth.txt

4. Create auth.txt with credentials (2 lines):
   username
   password

5. Restart: docker-compose down vpn && docker-compose up -d vpn


QUICK SWITCH SCRIPT
-------------------
To quickly swap VPN configs, rename your .ovpn files:
  - vpn-poland.ovpn
  - vpn-usa.ovpn
  - vpn-uk.ovpn

Then copy the one you want to vpn.ovpn and restart:
  copy vpn-poland.ovpn vpn.ovpn
  docker-compose down vpn && docker-compose up -d vpn
