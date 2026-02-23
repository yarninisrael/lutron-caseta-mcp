#!/bin/bash
#
# Lutron Caseta MCP Server Setup Script
#
# This script automates the setup process:
# 1. Creates a Python virtual environment
# 2. Installs dependencies
# 3. Guides you through pairing
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Lutron Caseta MCP Server Setup"
echo "========================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencies installed."

# Check if already paired
if [ -f "lutron_certs/caseta.crt" ]; then
    echo ""
    echo "Existing pairing found in lutron_certs/"
    read -p "Do you want to re-pair? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Setup complete! Skipping pairing."
        echo ""
        echo "To configure Claude Desktop, add this to your config:"
        echo "  ~/Library/Application Support/Claude/claude_desktop_config.json"
        echo ""
        exit 0
    fi
fi

# Get bridge IP
echo ""
echo "Searching for Lutron bridge on your network..."
BRIDGE_IP=""

# Try to find bridge via mDNS
if command -v dns-sd &> /dev/null; then
    BRIDGE_HOSTNAME=$(timeout 5 dns-sd -B _lutron._tcp local. 2>&1 | grep -o 'Lutron-[a-f0-9]*' | head -1 || true)
    if [ -n "$BRIDGE_HOSTNAME" ]; then
        BRIDGE_IP=$(timeout 5 dns-sd -G v4 "${BRIDGE_HOSTNAME}.local." 2>&1 | grep -oE '192\.[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
    fi
fi

if [ -n "$BRIDGE_IP" ]; then
    echo "Found bridge at: $BRIDGE_IP"
    read -p "Use this address? (Y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        BRIDGE_IP=""
    fi
fi

if [ -z "$BRIDGE_IP" ]; then
    read -p "Enter your Lutron bridge IP address: " BRIDGE_IP
fi

if [ -z "$BRIDGE_IP" ]; then
    echo "Error: Bridge IP is required."
    exit 1
fi

# Run pairing
echo ""
echo "Starting pairing process..."
python pair_bridge.py "$BRIDGE_IP"

# Generate Claude Desktop config snippet
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
SERVER_PATH="$SCRIPT_DIR/server.py"

echo ""
echo "========================================"
echo "  Claude Desktop Configuration"
echo "========================================"
echo ""
echo "Add this to your Claude Desktop config file:"
echo "  ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "{"
echo "  \"mcpServers\": {"
echo "    \"lutron\": {"
echo "      \"command\": \"$VENV_PYTHON\","
echo "      \"args\": [\"$SERVER_PATH\"],"
echo "      \"env\": {"
echo "        \"LUTRON_BRIDGE_IP\": \"$BRIDGE_IP\""
echo "      }"
echo "    }"
echo "  }"
echo "}"
echo ""
echo "Then restart Claude Desktop to load the Lutron tools."
echo ""
