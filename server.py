#!/usr/bin/env python3
"""
Lutron Caseta MCP Server

An MCP server that enables Claude to control Lutron Caseta smart lighting.
Connects to the SmartBridge via the local LEAP protocol.

Environment Variables:
    LUTRON_BRIDGE_IP: IP address of your Lutron SmartBridge
    LUTRON_CERT_DIR: Path to certificates (default: ./lutron_certs)
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from pylutron_caseta.smartbridge import Smartbridge
except ImportError:
    print("Error: pylutron_caseta not installed", file=sys.stderr)
    print("Run: pip install pylutron-caseta", file=sys.stderr)
    sys.exit(1)


# Configuration
CERT_DIR = Path(os.environ.get("LUTRON_CERT_DIR", Path(__file__).parent / "lutron_certs"))
BRIDGE_IP = os.environ.get("LUTRON_BRIDGE_IP", "")

# Global bridge connection
bridge: Smartbridge | None = None
server = Server("lutron-caseta")


async def get_bridge() -> Smartbridge:
    """Get or create the bridge connection."""
    global bridge, BRIDGE_IP

    if bridge is not None and bridge.is_connected():
        return bridge

    # Try to load bridge IP from saved file if not set
    if not BRIDGE_IP:
        ip_file = CERT_DIR / "bridge_ip.txt"
        if ip_file.exists():
            BRIDGE_IP = ip_file.read_text().strip()

    if not BRIDGE_IP:
        raise RuntimeError(
            "Bridge IP not configured. Set LUTRON_BRIDGE_IP environment variable "
            "or run pair_bridge.py first."
        )

    cert_path = CERT_DIR / "caseta.crt"
    key_path = CERT_DIR / "caseta.key"
    ca_path = CERT_DIR / "caseta-bridge.crt"

    if not all(p.exists() for p in [cert_path, key_path, ca_path]):
        raise RuntimeError(
            f"Certificates not found in {CERT_DIR}. Run pair_bridge.py first."
        )

    bridge = Smartbridge.create_tls(
        hostname=BRIDGE_IP,
        keyfile=str(key_path),
        certfile=str(cert_path),
        ca_certs=str(ca_path),
    )

    await bridge.connect()
    return bridge


def format_device_info(device_id: str, device: dict) -> dict:
    """Format device information for output."""
    return {
        "id": device_id,
        "name": device.get("name", "Unknown"),
        "type": device.get("type", "Unknown"),
        "zone": device.get("zone"),
        "current_state": device.get("current_state"),
        "fan_speed": device.get("fan_speed"),
        "model": device.get("model"),
        "serial": device.get("serial"),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Lutron control tools."""
    return [
        Tool(
            name="list_devices",
            description="List all Lutron devices (lights, dimmers, switches, fans) with their current states",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="turn_on",
            description="Turn on a light or switch. Use the device name or ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "description": "Device name or ID to turn on",
                    },
                },
                "required": ["device"],
            },
        ),
        Tool(
            name="turn_off",
            description="Turn off a light or switch. Use the device name or ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "description": "Device name or ID to turn off",
                    },
                },
                "required": ["device"],
            },
        ),
        Tool(
            name="set_brightness",
            description="Set brightness level for a dimmer (0-100). 0 is off, 100 is full brightness.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "description": "Device name or ID",
                    },
                    "brightness": {
                        "type": "integer",
                        "description": "Brightness level (0-100)",
                        "minimum": 0,
                        "maximum": 100,
                    },
                },
                "required": ["device", "brightness"],
            },
        ),
        Tool(
            name="get_device_state",
            description="Get the current state of a specific device",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "description": "Device name or ID",
                    },
                },
                "required": ["device"],
            },
        ),
        Tool(
            name="list_scenes",
            description="List all available Lutron scenes",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="activate_scene",
            description="Activate a Lutron scene by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "scene": {
                        "type": "string",
                        "description": "Scene name or ID to activate",
                    },
                },
                "required": ["scene"],
            },
        ),
    ]


def find_device(devices: dict, search: str) -> tuple[str, dict] | None:
    """Find a device by name or ID."""
    search_lower = search.lower()

    # Try exact ID match first
    if search in devices:
        return search, devices[search]

    # Try name match (case-insensitive)
    for device_id, device in devices.items():
        if device.get("name", "").lower() == search_lower:
            return device_id, device

    # Try partial name match
    for device_id, device in devices.items():
        if search_lower in device.get("name", "").lower():
            return device_id, device

    return None


def find_scene(scenes: dict, search: str) -> tuple[str, dict] | None:
    """Find a scene by name or ID."""
    search_lower = search.lower()

    # Try exact ID match first
    if search in scenes:
        return search, scenes[search]

    # Try name match (case-insensitive)
    for scene_id, scene in scenes.items():
        if scene.get("name", "").lower() == search_lower:
            return scene_id, scene

    # Try partial name match
    for scene_id, scene in scenes.items():
        if search_lower in scene.get("name", "").lower():
            return scene_id, scene

    return None


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        b = await get_bridge()

        if name == "list_devices":
            devices = b.get_devices()
            result = []
            for device_id, device in devices.items():
                # Skip non-controllable devices
                if device.get("type") in ["SmartBridge", "Unknown"]:
                    continue
                result.append(format_device_info(device_id, device))

            if not result:
                return [TextContent(type="text", text="No controllable devices found.")]

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "turn_on":
            devices = b.get_devices()
            found = find_device(devices, arguments["device"])

            if not found:
                return [TextContent(
                    type="text",
                    text=f"Device not found: {arguments['device']}"
                )]

            device_id, device = found
            await b.turn_on(device_id)

            return [TextContent(
                type="text",
                text=f"Turned on: {device.get('name', device_id)}"
            )]

        elif name == "turn_off":
            devices = b.get_devices()
            found = find_device(devices, arguments["device"])

            if not found:
                return [TextContent(
                    type="text",
                    text=f"Device not found: {arguments['device']}"
                )]

            device_id, device = found
            await b.turn_off(device_id)

            return [TextContent(
                type="text",
                text=f"Turned off: {device.get('name', device_id)}"
            )]

        elif name == "set_brightness":
            devices = b.get_devices()
            found = find_device(devices, arguments["device"])

            if not found:
                return [TextContent(
                    type="text",
                    text=f"Device not found: {arguments['device']}"
                )]

            device_id, device = found
            brightness = max(0, min(100, arguments["brightness"]))
            await b.set_value(device_id, brightness)

            return [TextContent(
                type="text",
                text=f"Set {device.get('name', device_id)} to {brightness}%"
            )]

        elif name == "get_device_state":
            devices = b.get_devices()
            found = find_device(devices, arguments["device"])

            if not found:
                return [TextContent(
                    type="text",
                    text=f"Device not found: {arguments['device']}"
                )]

            device_id, device = found
            return [TextContent(
                type="text",
                text=json.dumps(format_device_info(device_id, device), indent=2)
            )]

        elif name == "list_scenes":
            scenes = b.get_scenes()
            result = []
            for scene_id, scene in scenes.items():
                result.append({
                    "id": scene_id,
                    "name": scene.get("name", "Unknown"),
                })

            if not result:
                return [TextContent(type="text", text="No scenes found.")]

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "activate_scene":
            scenes = b.get_scenes()
            found = find_scene(scenes, arguments["scene"])

            if not found:
                return [TextContent(
                    type="text",
                    text=f"Scene not found: {arguments['scene']}"
                )]

            scene_id, scene = found
            await b.activate_scene(scene_id)

            return [TextContent(
                type="text",
                text=f"Activated scene: {scene.get('name', scene_id)}"
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
