# Claude Context: Lutron Caseta MCP Server

This file helps Claude understand the project context for troubleshooting.

## What Was Done

On 2026-02-23, we:

1. **Scanned the network** and found a Lutron Caseta SmartBridge
2. **Built an MCP server** to control Lutron lights from Claude
3. **Paired with the bridge** using the LEAP protocol (port 8083)
4. **Configured Claude Code** to use the MCP server
5. **Pushed to GitHub**

## Bridge Details

- **IP Address:** 192.168.150.177
- **Hostname:** Lutron-031f764e.local
- **MAC Address:** 90:70:65:d4:58:22
- **Device Type:** SmartBridge (Caseta) - regular, not Pro
- **Protocol:** LEAP on ports 8083/8081
- **Firmware:** 08.25.17f000

## Project Files

```
/Users/yarnin.israel/Projects/lutron-caseta-mcp/
├── server.py           # MCP server (main entry point)
├── pair_bridge.py      # One-time pairing utility
├── requirements.txt    # Python deps: pylutron-caseta, mcp
├── setup.sh            # Automated setup script
├── README.md           # User documentation
├── .gitignore          # Excludes venv/ and lutron_certs/
├── venv/               # Python 3.12 virtual environment
└── lutron_certs/       # Pairing certificates (generated)
    ├── caseta.crt
    ├── caseta.key
    ├── caseta-bridge.crt
    └── bridge_ip.txt
```

## Configuration

### Claude Code Settings
**File:** `~/.claude/settings.json`

```json
{
  "mcpServers": {
    "lutron": {
      "command": "/Users/yarnin.israel/Projects/lutron-caseta-mcp/venv/bin/python",
      "args": [
        "/Users/yarnin.israel/Projects/lutron-caseta-mcp/server.py"
      ],
      "env": {
        "LUTRON_BRIDGE_IP": "192.168.150.177"
      }
    }
  }
}
```

### Claude Desktop Settings (if configured)
**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Same configuration as above.

## GitHub Repository

**URL:** https://github.com/yarninisrael/lutron-caseta-mcp

## Troubleshooting

### MCP server not showing tools
1. Check if venv exists: `ls /Users/yarnin.israel/Projects/lutron-caseta-mcp/venv/`
2. Check if certs exist: `ls /Users/yarnin.israel/Projects/lutron-caseta-mcp/lutron_certs/`
3. Test server manually:
   ```bash
   source /Users/yarnin.israel/Projects/lutron-caseta-mcp/venv/bin/activate
   python /Users/yarnin.israel/Projects/lutron-caseta-mcp/server.py
   ```
4. Run `/mcp` in Claude Code to reload servers

### Connection errors
1. Verify bridge is online: `ping 192.168.150.177`
2. Check LEAP port: `nc -zv 192.168.150.177 8083`
3. Bridge IP may have changed - rediscover:
   ```bash
   dns-sd -B _lutron._tcp local.
   dns-sd -G v4 Lutron-031f764e.local.
   ```

### Re-pairing needed
If certificates are invalid or lost:
```bash
cd /Users/yarnin.israel/Projects/lutron-caseta-mcp
source venv/bin/activate
python pair_bridge.py 192.168.150.177
```
Press the small button on the SmartBridge when prompted.

### Update bridge IP in config
If bridge IP changes, update in:
1. `~/.claude/settings.json` → `mcpServers.lutron.env.LUTRON_BRIDGE_IP`
2. `lutron_certs/bridge_ip.txt`

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `list_devices` | List all Lutron devices with current states |
| `turn_on` | Turn on a light/switch by name or ID |
| `turn_off` | Turn off a light/switch by name or ID |
| `set_brightness` | Set dimmer level (0-100) |
| `get_device_state` | Get current state of a device |
| `list_scenes` | List all Lutron scenes |
| `activate_scene` | Activate a scene by name or ID |

## Notes

- Python 3.12 required (system Python 3.9 is too old for `mcp` package)
- Pairing does NOT affect the Lutron mobile app - multiple clients supported
- All communication is local (no cloud required)
- Certificates in `lutron_certs/` are sensitive - don't commit to git
