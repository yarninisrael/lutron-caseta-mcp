#!/usr/bin/env python3
"""
Lutron Caseta Bridge Pairing Utility

This script pairs with your Lutron SmartBridge and saves the authentication
certificates needed for the MCP server to control your lights.

Usage:
    python pair_bridge.py <BRIDGE_IP>

Example:
    python pair_bridge.py 192.168.150.177
"""

import asyncio
import sys
import os
from pathlib import Path

try:
    from pylutron_caseta.pairing import async_pair
except ImportError:
    print("Error: pylutron_caseta not installed.")
    print("Run: pip install pylutron-caseta")
    sys.exit(1)


CERT_DIR = Path(__file__).parent / "lutron_certs"


async def pair_with_bridge(bridge_ip: str) -> None:
    """Pair with the Lutron bridge and save certificates."""

    # Create certificate directory
    CERT_DIR.mkdir(exist_ok=True)

    cert_path = CERT_DIR / "caseta.crt"
    key_path = CERT_DIR / "caseta.key"
    ca_path = CERT_DIR / "caseta-bridge.crt"

    print(f"\nPairing with Lutron bridge at {bridge_ip}...")
    print("\n" + "=" * 50)
    print("  PRESS THE SMALL BUTTON ON YOUR SMARTBRIDGE NOW")
    print("  (You have 30 seconds)")
    print("=" * 50 + "\n")

    try:
        data = await async_pair(bridge_ip)

        # Save certificates
        with open(cert_path, "w") as f:
            f.write(data["cert"])

        with open(key_path, "w") as f:
            f.write(data["key"])

        with open(ca_path, "w") as f:
            f.write(data["ca"])

        # Save bridge IP for convenience
        with open(CERT_DIR / "bridge_ip.txt", "w") as f:
            f.write(bridge_ip)

        print("\n" + "=" * 50)
        print("  PAIRING SUCCESSFUL!")
        print("=" * 50)
        print(f"\nCertificates saved to: {CERT_DIR}")
        print("\nFiles created:")
        print(f"  - {cert_path}")
        print(f"  - {key_path}")
        print(f"  - {ca_path}")
        print(f"  - {CERT_DIR / 'bridge_ip.txt'}")
        print("\nYou can now configure Claude Desktop to use the MCP server.")
        print("See README.md for configuration instructions.")

    except asyncio.TimeoutError:
        print("\nError: Pairing timed out.")
        print("Make sure you pressed the button on the bridge.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during pairing: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python pair_bridge.py <BRIDGE_IP>")
        print("Example: python pair_bridge.py 192.168.150.177")
        sys.exit(1)

    bridge_ip = sys.argv[1]

    # Validate IP format (basic check)
    parts = bridge_ip.split(".")
    if len(parts) != 4:
        print(f"Error: Invalid IP address: {bridge_ip}")
        sys.exit(1)

    print("Lutron Caseta Bridge Pairing Utility")
    print("-" * 40)

    asyncio.run(pair_with_bridge(bridge_ip))


if __name__ == "__main__":
    main()
