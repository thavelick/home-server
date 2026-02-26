#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "uptime-kuma-api",
# ]
# ///
"""
One-time setup script to create Uptime Kuma monitors and tags for all home
server services.

Usage:
    uv run setup_uptime_kuma_monitors.py <username> <password> <parent_domain>

Requires Uptime Kuma 2.x running on bernard:3001.
"""

import argparse
import json
from typing import Dict

from uptime_kuma_api import MonitorType, UptimeKumaApi


UPTIME_KUMA_URL = "http://bernard:3001"

TAG_COLORS = {
    "public": "#2563eb",
    "private": "#7c3aed",
    "upstream": "#059669",
    "network": "#d97706",
}

PING_MONITORS = [
    {"name": "Google DNS", "hostname": "8.8.8.8", "tag": "upstream"},
    {"name": "Cloudflare DNS", "hostname": "1.1.1.1", "tag": "upstream"},
    {"name": "Router", "hostname": "192.168.1.1", "tag": "network"},
    {"name": "Optical Network Terminal", "hostname": "192.168.0.1", "tag": "network"},
    {"name": "ISP Gateway", "hostname": "207.225.112.17", "tag": "upstream"},
]

HTTP_MONITORS = [
    {"name": "Home Assistant", "url": "http://bernard:8123", "tag": "public"},
    {"name": "Jellyfin", "url": "http://bernard:8096", "tag": "public"},
    {"name": "Jellyseerr", "url": "http://bernard:5055", "tag": "public"},
    {"name": "Just Bangs", "url": "http://bernard:8484", "tag": "public"},
    {"name": "Kiwix", "url": "http://bernard:8181", "tag": "public"},
    {"name": "Miniflux", "url": "http://bernard:8050", "tag": "public"},
    {"name": "Nextcloud", "url": "http://bernard:9787", "tag": "public"},
    {"name": "Onlyoffice", "url": "http://bernard:9786", "tag": "public"},
    {"name": "SearXNG", "url": "http://bernard:8788", "tag": "public"},
    {"name": "Transmission", "url": "http://bernard:9091", "tag": "private"},
    {"name": "Prowlarr", "url": "http://bernard:9696", "tag": "private"},
    {"name": "Radarr", "url": "http://bernard:7878", "tag": "private"},
    {"name": "Readarr", "url": "http://bernard:8787", "tag": "private"},
]


def ensure_tags(api: UptimeKumaApi) -> Dict[str, int]:
    """Ensure all tags exist, return {tag_name: tag_id} mapping."""
    existing = {t["name"]: t["id"] for t in api.get_tags()}
    tag_ids = {}
    for name, color in TAG_COLORS.items():
        if name in existing:
            tag_ids[name] = existing[name]
            print(f"  SKIP  tag '{name}' (already exists)")
        else:
            result = api.add_tag(name=name, color=color)
            tag_ids[name] = result["id"]
            print(f"  ADD   tag '{name}'")
    return tag_ids


def build_monitors(parent_domain: str) -> list:
    """Build the full list of monitor definitions."""
    monitors = []

    for m in PING_MONITORS:
        monitors.append({
            "type": MonitorType.PING,
            "name": m["name"],
            "hostname": m["hostname"],
            "tag": m["tag"],
        })

    for m in HTTP_MONITORS:
        monitors.append({
            "type": MonitorType.HTTP,
            "name": m["name"],
            "url": m["url"],
            "tag": m["tag"],
        })

    monitors.append({
        "type": MonitorType.HTTP,
        "name": "Wallabag",
        "url": f"https://articles.{parent_domain}",
        "tag": "public",
    })
    monitors.append({
        "type": MonitorType.HTTP,
        "name": "Personal Site",
        "url": f"https://{parent_domain}",
        "tag": "public",
    })

    return monitors


def create_monitor(api: UptimeKumaApi, monitor: dict, tag_id: int, tag_name: str) -> None:
    """Create a new monitor and assign its tag."""
    result = api.add_monitor(**monitor, conditions=json.dumps([]))
    monitor_id = result["monitorID"]
    api.add_monitor_tag(tag_id=tag_id, monitor_id=monitor_id, value="")
    desc = monitor.get("hostname") or monitor.get("url")
    print(f"  ADD   {monitor['name']} ({desc}) [{tag_name}]")


def sync_monitors(api: UptimeKumaApi, parent_domain: str, tag_ids: Dict[str, int]) -> None:
    """Create or tag monitors, skipping those that already exist."""
    existing = {m["name"]: m for m in api.get_monitors()}

    for monitor in build_monitors(parent_domain):
        name = monitor["name"]
        tag_name = monitor.pop("tag")
        tag_id = tag_ids[tag_name]

        if name not in existing:
            create_monitor(api, monitor, tag_id, tag_name)
            continue

        existing_tag_ids = {t["tag_id"] for t in existing[name].get("tags", [])}
        if tag_id in existing_tag_ids:
            print(f"  SKIP  {name} (already exists with tag)")
        else:
            api.add_monitor_tag(tag_id=tag_id, monitor_id=existing[name]["id"], value="")
            print(f"  TAG   {name} <- {tag_name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Uptime Kuma monitors for all home server services."
    )
    parser.add_argument("username", help="Uptime Kuma username")
    parser.add_argument("password", help="Uptime Kuma password")
    parser.add_argument("parent_domain", help="Parent domain (e.g. example.com)")
    args = parser.parse_args()

    api = UptimeKumaApi(UPTIME_KUMA_URL)
    api.login(args.username, args.password)

    tag_ids = ensure_tags(api)
    sync_monitors(api, args.parent_domain, tag_ids)

    api.disconnect()
    print("\nDone.")


if __name__ == "__main__":
    main()
