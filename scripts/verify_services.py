#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["requests", "pyyaml", "urllib3"]
# ///
"""
Home Server Service Verification Script

Checks that all configured services are responding properly:
1. HTTPS endpoints respond with valid certificates
2. HTTP ports respond correctly

Based on Ansible playbook configuration.
"""

import ipaddress
import re
import socket
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import requests
import yaml
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings when checking without verification
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

STATUS_COLORS = {"ok": GREEN, "WARN": YELLOW, "FAIL": RED}


def colorize(text: str, color: str) -> str:
    """Wrap text in an ANSI color code."""
    return f"{color}{text}{RESET}"


def colorize_status(status: str) -> str:
    """Wrap a status string in the appropriate ANSI color."""
    color = STATUS_COLORS.get(status)
    if color:
        return colorize(status, color)
    return status


def pad_colored(status: str, width: int) -> str:
    """Colorize a status string and pad it to the given visible width.

    ANSI escape codes are invisible but affect string length,
    so we pad based on the raw status length, not the colored length.
    """
    colored = colorize_status(status)
    padding = width - len(status)
    if padding > 0:
        return colored + " " * padding
    return colored


def load_yaml_file(path: str) -> Optional[Dict]:
    """Load a YAML file, automatically decrypting ansible-vault files.
    Returns None if the file is missing or cannot be decrypted."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    if content.startswith("$ANSIBLE_VAULT"):
        result = subprocess.run(
            ["ansible-vault", "view", path],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return None
        content = result.stdout

    return yaml.safe_load(content)


def find_parent_domain(hosts_content: str) -> Optional[str]:
    """Find parent_domain from hosts file (legacy) or group_vars YAML files."""
    # Check hosts file first (legacy format)
    domain_match = re.search(r"parent_domain\s*=\s*([^\s\n]+)", hosts_content)
    if domain_match:
        return domain_match.group(1).strip()

    # Check group_vars YAML files
    for vars_file in ["group_vars/home/vars.yml", "group_vars/home/vault.yml"]:
        data = load_yaml_file(vars_file)
        if data and "parent_domain" in data:
            return data["parent_domain"]

    return None


def parse_hosts_file(filename: str = "hosts") -> Tuple[str, str]:
    """Parse Ansible hosts file and group_vars to get server hostname and parent domain"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract server hostname from [home] or [servers] section
        lines = content.split("\n")
        server_hostname = None
        in_target_section = False

        for line in lines:
            line = line.strip()
            if line in ["[home]", "[servers]"]:
                in_target_section = True
                continue
            if line.startswith("[") and in_target_section:
                break
            if in_target_section and line and not line.startswith("#"):
                server_hostname = line
                break

        if not server_hostname:
            raise ValueError(
                "Could not find server hostname in hosts file"
                " (looked for [home] or [servers] section)"
            )

        parent_domain = find_parent_domain(content)
        if not parent_domain:
            raise ValueError("Could not find parent_domain in hosts or group_vars")

        return server_hostname, parent_domain

    except FileNotFoundError:
        print(
            "FAIL: hosts file not found. Please create it following the README.md format."
        )
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"FAIL: Error parsing hosts file: {e}")
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
    "ntopng": {"tag": "ntopng", "https_hostname": None, "port": 3000},
    "uptime_kuma": {"tag": "uptime_kuma", "https_hostname": None, "port": 3001},
}


def is_private_ip(addr: str) -> bool:
    """Check if an IP address is in a private range (RFC 1918 or IPv6 link-local)."""
    try:
        return ipaddress.ip_address(addr).is_private
    except ValueError:
        return False


def resolve_server_ip(server: str) -> Optional[str]:
    """Resolve a server hostname to an IP address, or return None on failure."""
    try:
        return socket.gethostbyname(server)
    except socket.gaierror:
        return None


def run_dig(query_name: str, server_ip: Optional[str] = None,
            timeout: int = 5) -> Tuple[bool, str]:
    """Run dig +short and return (success, output_or_error)."""
    cmd = ["dig", "+short", query_name]
    if server_ip:
        cmd.insert(1, f"@{server_ip}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return False, "dig not found (install bind-tools)"
    except subprocess.TimeoutExpired:
        return False, "DNS timeout"

    if result.returncode != 0:
        return False, f"dig failed: {result.stderr.strip()}"

    output = result.stdout.strip()
    if not output:
        return False, "No DNS result"

    return True, output.splitlines()[0]


def check_dns_resolve(
    server: Optional[str], query_name: str,
    expect_private: bool = False, timeout: int = 5,
) -> Tuple[str, str, str]:
    """Check if a DNS query resolves successfully via dig +short.
    When server is given, queries that specific server; otherwise uses system default.
    When expect_private is True, warns if the result is not a private IP.
    Returns: (status, ip_result, details)
    """
    server_ip = None
    if server:
        server_ip = resolve_server_ip(server)
        if not server_ip:
            return "FAIL", "", f"Cannot resolve server {server}"

    success, output = run_dig(query_name, server_ip, timeout)
    if not success:
        return "FAIL", "", output

    if expect_private and not is_private_ip(output):
        return "WARN", output, "Expected private IP"

    return "ok", output, ""


def check_https_endpoint(
    hostname: str, valid_status_codes: Optional[List[int]] = None, timeout: int = 10
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
            return "ok", response.status_code, ""
        return "WARN", response.status_code, f"HTTP {response.status_code}"
    except requests.exceptions.SSLError as e:
        return "FAIL", 0, f"SSL Error: {str(e)}"
    except requests.exceptions.Timeout:
        return "FAIL", 0, "Timeout"
    except requests.exceptions.ConnectionError:
        return "FAIL", 0, "Connection refused"
    except Exception as e:  # pylint: disable=broad-exception-caught
        return "FAIL", 0, f"Error: {str(e)}"


def is_port_open(hostname: str, port: int, timeout: int = 10) -> bool:
    """Check if a TCP port is accepting connections."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((hostname, port)) == 0
    finally:
        sock.close()


def check_http_port(
    hostname: str, port: int,
    valid_status_codes: Optional[List[int]] = None, timeout: int = 10,
) -> Tuple[str, int, str]:
    """Check if HTTP port responds.
    Returns: (status_icon, status_code, details)
    """
    if valid_status_codes is None:
        valid_status_codes = [200]

    if not is_port_open(hostname, port, timeout):
        return "FAIL", 0, "Port closed"

    try:
        url = f"http://{hostname}:{port}"
        response = requests.get(url, timeout=timeout)
        if response.status_code in valid_status_codes:
            return "ok", response.status_code, ""
        return "WARN", response.status_code, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return "FAIL", 0, "HTTP timeout"
    except requests.exceptions.ConnectionError:
        return "FAIL", 0, "HTTP connection refused"
    except Exception as e:  # pylint: disable=broad-exception-caught
        return "WARN", 0, f"Port open (HTTP error: {str(e)[:50]})"


def check_service(config):
    """Check a single service's HTTPS and port status.
    Returns: (tag, https_status, port_status, details)
    """
    tag = config["tag"]
    valid_codes = config.get("valid_status_codes", [200])

    https_status, https_details = "-", ""
    if config["https_hostname"]:
        https_status, _, https_details = check_https_endpoint(
            config["https_hostname"], valid_codes
        )

    port_status, port_details = "-", ""
    if config["port"]:
        port_status, _, port_details = check_http_port(
            SERVER_HOSTNAME, config["port"], valid_codes
        )

    details_parts = []
    if https_details:
        details_parts.append(f"HTTPS: {https_details}")
    if port_details:
        details_parts.append(f"Port: {port_details}")

    return tag, https_status, port_status, ", ".join(details_parts)


def count_status(results, index, status):
    """Count how many results have a given status at the given index."""
    return sum(1 for r in results if r[index] == status)


def format_summary(label, results, index):
    """Format a colored summary line for HTTPS or port results."""
    up = count_status(results, index, "ok")
    warn = count_status(results, index, "WARN")
    down = count_status(results, index, "FAIL")
    total = up + warn + down
    return (
        f"{label}: {colorize(f'{up} ok', GREEN)}, "
        f"{colorize(f'{warn} warn', YELLOW)}, "
        f"{colorize(f'{down} fail', RED)} ({total} total)"
    )


def format_infra_row(name: str, name_width: int, status: str, details: str) -> str:
    """Format a single infrastructure check row for display."""
    details_str = ""
    if details:
        if status == "ok":
            details_str = f"  {details}"
        else:
            color = YELLOW if status == "WARN" else RED
            details_str = f"  {colorize(details, color)}"
    return (
        f"{name:<{name_width}}  "
        f"{pad_colored(status, 6)}"
        f"{details_str}"
    )


def print_infra_checks() -> int:
    """Run and print infrastructure DNS checks.
    Returns the number of failures.
    """
    name_width = max(len("INFRASTRUCTURE"), len("dnsmasq forward"))
    print()
    header = f"{'INFRASTRUCTURE':<{name_width}}  STATUS  DETAILS"
    print(header)
    print("-" * len(header))

    checks = [
        ("dnsmasq local", SERVER_HOSTNAME, f"assistant.{PARENT_DOMAIN}", True),
        ("dnsmasq forward", SERVER_HOSTNAME, "google.com", False),
        ("dynamicdns", None, f"home.{PARENT_DOMAIN}", False),
    ]

    results: List[Tuple[str, str, str]] = []
    for name, server, query, expect_private in checks:
        status, ip_result, details = check_dns_resolve(
            server, query, expect_private=expect_private
        )
        results.append((name, status, details or ip_result))

    for name, status, details in results:
        print(format_infra_row(name, name_width, status, details))

    infra_fail = sum(1 for _, status, _ in results if status != "ok")
    infra_ok = len(results) - infra_fail
    print(
        f"\nInfra: {colorize(f'{infra_ok} ok', GREEN)}, "
        f"{colorize(f'{infra_fail} fail', RED)} ({len(results)} total)"
    )
    return infra_fail


def main():
    """Main verification function"""
    print("Home Server Service Verification")
    print(f"Server: {SERVER_HOSTNAME}")
    print(f"Domain: {PARENT_DOMAIN}")
    print()

    name_width = max(
        len("SERVICE"),
        max(len(c["tag"]) for c in SERVICES.values()),
    )
    header = f"{'SERVICE':<{name_width}}  HTTPS  PORT   DETAILS"
    print(header)
    print("-" * len(header))

    all_results = []
    for config in SERVICES.values():
        tag, https_status, port_status, details = check_service(config)
        details_str = f"  {colorize(details, RED)}" if details else ""
        print(
            f"{tag:<{name_width}}  "
            f"{pad_colored(https_status, 5)}  "
            f"{pad_colored(port_status, 5)}"
            f"{details_str}"
        )
        all_results.append((https_status, port_status))

    infra_fail = print_infra_checks()

    print()
    print(format_summary("HTTPS", all_results, 0))
    print(format_summary("Ports", all_results, 1))

    total_issues = (
        count_status(all_results, 0, "WARN")
        + count_status(all_results, 0, "FAIL")
        + count_status(all_results, 1, "WARN")
        + count_status(all_results, 1, "FAIL")
        + infra_fail
    )
    if total_issues > 0:
        print(f"\n{colorize(f'{total_issues} issue(s) detected!', RED)}")
        sys.exit(1)
    else:
        print(f"\n{colorize('All services are healthy!', GREEN)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
