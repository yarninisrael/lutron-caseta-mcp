# Lutron Caseta MCP Server

An MCP (Model Context Protocol) server that enables Claude Desktop to control Lutron Caseta smart lighting systems.

## Overview

This server connects to your Lutron Caseta SmartBridge via the local LEAP protocol (port 8083) and exposes tools that Claude can use to:

- List all lights, dimmers, and devices
- Turn lights on/off
- Set dimmer brightness levels
- Activate scenes
- Get current device states

## Requirements

- Lutron Caseta SmartBridge (regular or Pro)
- Python 3.9+
- Claude Desktop

## Installation

### 1. Clone/Copy this folder

Ensure all files are in place.

### 2. Create a virtual environment

```bash
cd lutron-caseta-mcp
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Pair with your Lutron Bridge

This is a one-time setup that generates authentication certificates.

First, find your bridge IP address:
```bash
dns-sd -G v4 $(dns-sd -B _lutron._tcp local. 2>&1 | grep -o 'Lutron-[a-f0-9]*' | head -1).local.
```

Then run the pairing script:
```bash
python pair_bridge.py <BRIDGE_IP>
```

Example:
```bash
python pair_bridge.py 192.168.150.177
```

**Important:** When prompted, press the small button on the back of your SmartBridge within 30 seconds.

This creates a `lutron_certs/` folder with your authentication credentials.

### 5. Configure Claude Desktop

Add this to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lutron": {
      "command": "/path/to/lutron-caseta-mcp/venv/bin/python",
      "args": ["/path/to/lutron-caseta-mcp/server.py"],
      "env": {
        "LUTRON_BRIDGE_IP": "192.168.150.177"
      }
    }
  }
}
```

Replace `/path/to/` with your actual path and update the bridge IP.

### 6. Restart Claude Desktop

Quit and reopen Claude Desktop to load the MCP server.

## Usage

Once configured, you can ask Claude things like:

- "Turn on the living room lights"
- "Dim the bedroom to 50%"
- "What lights are currently on?"
- "Turn off all lights"
- "Set the kitchen lights to 75%"
- "Activate the movie scene"

## Available Tools

| Tool | Description |
|------|-------------|
| `list_devices` | List all Lutron devices with their current states |
| `turn_on` | Turn on a light or switch |
| `turn_off` | Turn off a light or switch |
| `set_brightness` | Set a dimmer to a specific level (0-100) |
| `get_device_state` | Get the current state of a specific device |
| `list_scenes` | List all available scenes |
| `activate_scene` | Activate a scene |

## Troubleshooting

### "Connection refused" error
- Ensure your bridge IP is correct
- Verify the bridge is on the same network as your computer
- Check that ports 8083/8081 are accessible

### "Certificate error" or "Not paired"
- Re-run the pairing script: `python pair_bridge.py <BRIDGE_IP>`
- Make sure to press the bridge button within 30 seconds

### Claude doesn't see the Lutron tools
- Verify the path in `claude_desktop_config.json` is correct
- Check the Python path points to the virtual environment
- Restart Claude Desktop completely

## Files

- `server.py` - Main MCP server
- `pair_bridge.py` - One-time pairing utility
- `requirements.txt` - Python dependencies
- `lutron_certs/` - Generated certificates (after pairing)

## Security Notes

- Certificates in `lutron_certs/` grant control of your lights - keep them private
- The LEAP protocol uses TLS encryption
- All communication is local (no cloud required)

## License

MIT License - Feel free to modify and share.
