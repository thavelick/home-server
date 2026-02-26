# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ansible-based infrastructure-as-code for a single home server ("bernard") running ~20 services behind nginx reverse proxies. Services are a mix of Docker containers and native packages/systemd services.

## Commands

```bash
# Install external Galaxy roles (run once or after updating requirements.yml)
ansible-galaxy install -r requirements.yml

# Run full playbook
ansible-playbook -i hosts playbook.yml

# Run a single role by tag
ansible-playbook -i hosts playbook.yml --tags home_assistant

# Dry run with diff output
ansible-playbook -i hosts playbook.yml --check --diff --tags home_assistant

# Verify deployed services are responding
python3 scripts/verify_services.py
```

## Architecture

**Single playbook** (`playbook.yml`) targets one host with `become: true`. Playbook-level variables define domains, directories, and credentials.

**Variable storage** uses `group_vars/home/`:
- `vars.yml` — non-secret config (paths, generic settings), committed to git
- `vault.yml` — secrets encrypted with `ansible-vault`, committed to git
- The vault password lives in `.vault-password` (gitignored). `ansible.cfg` points to this file so decryption is automatic.

**Reusable utility roles:**
- `nginx_standard` — nginx reverse proxy config, included by most service roles via `include_role` with variable overrides
- `service_standard` — systemd service wrapper from template

**Service roles** follow a consistent pattern:
1. Create directories
2. Deploy config files (templates or static files)
3. Launch service — either via `docker_container` module or as a native package/systemd service
4. Include `nginx_standard` for reverse proxy setup

**Role directory layout:**
```
roles/{name}/
├── tasks/main.yml       # Always present
├── defaults/main.yml    # Default variables (optional)
├── templates/*.j2       # Jinja2 templates (optional)
└── files/*              # Static config files (optional)
```

**Service deployment types:**

*Docker:*
- home_assistant
- jellyseerr
- nextcloud
- onlyoffice
- prowlarr
- radarr
- readarr
- transmission
- tubesync

*Native (package/systemd):*
- dnsmasq
- dynamicdns
- just_auth
- just_bangs
- kiwix
- miniflux
- searxng
- wallabag

**Variable naming:** `{service_name}_{purpose}` (e.g., `nextcloud_base_directory`, `wallabag_domain`). Domains follow `{service}.{{parent_domain}}` pattern.

## Conventions

- New services should use Docker unless there's a good reason not to

- Commit messages: `feat:` / `fix:` prefix style
- Docker containers use `restart_policy: unless-stopped`
- Secrets live in `group_vars/home/vault.yml`, encrypted with `ansible-vault`. The vault password file (`.vault-password`) is gitignored
- External roles from Galaxy are pinned in `requirements.yml`
