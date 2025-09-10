#!/usr/bin/env python3
"""
Home Server Service Verification Script

Checks that all configured services are responding properly:
1. HTTPS endpoints respond with valid certificates
2. HTTP ports respond correctly

Based on Ansible playbook configuration.
"""

import requests
import socket
import sys
import configparser
import re
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, List, Optional, Tuple

# Suppress SSL warnings when checking without verification
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def parse_hosts_file(filename: str = "hosts") -> Tuple[str, str]:
    """Parse Ansible hosts file to get server hostname and parent domain"""
    try:
        with open(filename, "r") as f:
            content = f.read()

        # Extract server hostname from [home] or [servers] section
        # Look for section then find the next non-empty, non-comment line
        lines = content.split("\n")
        server_hostname = None
        in_target_section = False

        for line in lines:
            line = line.strip()
            if line in ["[home]", "[servers]"]:
                in_target_section = True
                continue
            elif line.startswith("[") and in_target_section:
                # Hit another section, stop looking
                break
            elif in_target_section and line and not line.startswith("#"):
                server_hostname = line
                break

        if not server_hostname:
            raise ValueError(
                "Could not find server hostname in hosts file (looked for [home] or [servers] section)"
            )

        # Extract parent_domain from vars
        domain_match = re.search(r"parent_domain\s*=\s*([^\s\n]+)", content)
        if not domain_match:
            raise ValueError("Could not find parent_domain in hosts file")
        parent_domain = domain_match.group(1).strip()

        return server_hostname, parent_domain

    except FileNotFoundError:
        print(
            "❌ hosts file not found. Please create it following the README.md format."
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing hosts file: {e}")
        sys.exit(1)


# Parse configuration from hosts file
SERVER_HOSTNAME, PARENT_DOMAIN = parse_hosts_file()

SERVICES = {
    "home_assistant": {
        "tag": "home_assistant",
        "https_hostname": f"assistant.{PARENT_DOMAIN}",
        "port": 8123,
    },
    "jellyfin": {
        "tag": "jellyfin",
        "https_hostname": f"jellyfin.{PARENT_DOMAIN}",
        "port": 8096,
    },
    "jellyseerr": {
        "tag": "jellyseerr",
        "https_hostname": f"jellyseerr.{PARENT_DOMAIN}",
        "port": 5055,
    },
    "just_bangs": {
        "tag": "just_bangs",
        "https_hostname": f"bangs.{PARENT_DOMAIN}",
        "port": 8484,
    },
    "kiwix": {"tag": "kiwix", "https_hostname": f"kiwix.{PARENT_DOMAIN}", "port": 8181},
    "miniflux": {
        "tag": "miniflux",
        "https_hostname": f"miniflux.{PARENT_DOMAIN}",
        "port": 8050,
    },
    "nextcloud": {
        "tag": "nextcloud",
        "https_hostname": f"nextcloud.{PARENT_DOMAIN}",
        "port": 9787,
    },
    "onlyoffice": {
        "tag": "onlyoffice",
        "https_hostname": f"onlyoffice.{PARENT_DOMAIN}",
        "port": 9786,
    },
    "searxng": {
        "tag": "searxng",
        "https_hostname": f"searxng.{PARENT_DOMAIN}",
        "port": 8788,
    },
    "transmission": {"tag": "transmission", "https_hostname": None, "port": 9091},
    "tubesync": {
        "tag": "tubesync",
        "https_hostname": f"tubesync.{PARENT_DOMAIN}",
        "port": 4848,
        "valid_status_codes": [200, 401],
    },
    "wallabag": {
        "tag": "wallabag",
        "https_hostname": f"articles.{PARENT_DOMAIN}",
        "port": None,
    },
    # Services with ports but no HTTPS hostnames
    "prowlarr": {"tag": "prowlarr", "https_hostname": None, "port": 9696},
    "radarr": {"tag": "radarr", "https_hostname": None, "port": 7878},
    "readarr": {"tag": "readarr", "https_hostname": None, "port": 8787},
}


def check_https_endpoint(
    hostname: str, valid_status_codes: List[int] = None, timeout: int = 10
) -> Tuple[str, int, str]:
    """Check if HTTPS endpoint responds properly
    Returns: (status_icon, status_code, details)
    """
    if valid_status_codes is None:
        valid_status_codes = [200]

    try:
        url = f"https://{hostname}"
        response = requests.get(url, timeout=timeout, verify=True)
        if response.status_code in valid_status_codes:
            return "✅", response.status_code, ""
        else:
            return "⚠️", response.status_code, f"HTTP {response.status_code}"
    except requests.exceptions.SSLError as e:
        return "❌", 0, f"SSL Error: {str(e)}"
    except requests.exceptions.Timeout:
        return "❌", 0, "Timeout"
    except requests.exceptions.ConnectionError:
        return "❌", 0, "Connection refused"
    except Exception as e:
        return "❌", 0, f"Error: {str(e)}"


def check_http_port(
    hostname: str, port: int, valid_status_codes: List[int] = None, timeout: int = 10
) -> Tuple[str, int, str]:
    """Check if HTTP port responds
    Returns: (status_icon, status_code, details)
    """
    if valid_status_codes is None:
        valid_status_codes = [200]
    try:
        # First check if port is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, port))
        sock.close()

        if result != 0:
            return "❌", 0, "Port closed"

        # Try HTTP request
        try:
            url = f"http://{hostname}:{port}"
            response = requests.get(url, timeout=timeout)
            if response.status_code in valid_status_codes:
                return "✅", response.status_code, ""
            else:
                return "⚠️", response.status_code, f"HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            return "❌", 0, "HTTP timeout"
        except requests.exceptions.ConnectionError:
            return "❌", 0, "HTTP connection refused"
        except Exception as e:
            return "⚠️", 0, f"Port open (HTTP error: {str(e)[:50]})"

    except Exception as e:
        return "❌", 0, f"Error: {str(e)}"


def main():
    """Main verification function"""
    print("# Home Server Service Verification")
    print()
    print(f"**Server:** {SERVER_HOSTNAME}  ")
    print(f"**Domain:** {PARENT_DOMAIN}")
    print()

    all_results = []

    print("## 🌐 Service Status Check")
    print()
    print("| Service | HTTPS Hostname | Port | HTTPS | Port | Details |")
    print("|---------|----------------|------|--------|------|---------|")

    for service_name, config in SERVICES.items():
        tag = config["tag"]
        hostname = config["https_hostname"] or "-"
        port_display = f"{SERVER_HOSTNAME}:{config['port']}" if config["port"] else "-"

        # Check HTTPS if available
        https_status = "-"
        https_details = ""
        if config["https_hostname"]:
            valid_codes = config.get("valid_status_codes", [200])
            https_icon, https_code, https_msg = check_https_endpoint(
                config["https_hostname"], valid_codes
            )
            https_status = https_icon
            if https_msg:  # Only show details if not success
                https_details = https_msg

        # Check port if available
        port_status = "-"
        port_details = ""
        if config["port"]:
            valid_codes = config.get("valid_status_codes", [200])
            port_icon, port_code, port_msg = check_http_port(
                SERVER_HOSTNAME, config["port"], valid_codes
            )
            port_status = port_icon
            if port_msg:  # Only show details if not success
                port_details = port_msg

        # Combine details only if there are issues
        details_parts = []
        if https_details:
            details_parts.append(f"HTTPS: {https_details}")
        if port_details:
            details_parts.append(f"Port: {port_details}")
        details = ", ".join(details_parts) if details_parts else ""

        print(
            f"| {tag} | {hostname} | {port_display} | {https_status} | {port_status} | {details} |"
        )
        all_results.append(
            (tag, hostname, port_display, https_status, port_status, details)
        )

    print()
    print("## 📊 Summary")
    print()

    # Count status icons
    https_up = sum(
        1 for _, _, _, https_status, _, _ in all_results if https_status == "✅"
    )
    https_warn = sum(
        1 for _, _, _, https_status, _, _ in all_results if https_status == "⚠️"
    )
    https_down = sum(
        1 for _, _, _, https_status, _, _ in all_results if https_status == "❌"
    )
    https_total = https_up + https_warn + https_down

    port_up = sum(
        1 for _, _, _, _, port_status, _ in all_results if port_status == "✅"
    )
    port_warn = sum(
        1 for _, _, _, _, port_status, _ in all_results if port_status == "⚠️"
    )
    port_down = sum(
        1 for _, _, _, _, port_status, _ in all_results if port_status == "❌"
    )
    port_total = port_up + port_warn + port_down

    print(
        f"**HTTPS:** {https_up} ✅, {https_warn} ⚠️, {https_down} ❌ ({https_total} total)  "
    )
    print(
        f"**Ports:** {port_up} ✅, {port_warn} ⚠️, {port_down} ❌ ({port_total} total)"
    )
    print()

    # Exit with error code if any services are down
    total_issues = https_warn + https_down + port_warn + port_down
    if total_issues > 0:
        print(f"⚠️  **{total_issues} issue(s) detected!**")
        sys.exit(1)
    else:
        print(f"🎉 **All services are healthy!**")
        sys.exit(0)


if __name__ == "__main__":
    main()
