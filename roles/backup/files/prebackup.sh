#!/bin/bash
set -e

backup_staging_directory=$1
shift

# Remaining args describe each sqlite database to snapshot, as `name=path`
# pairs (e.g. `wallabag=/var/www/.../wallabag.db`). Each one produces
# <staging>/<name>.db via the sqlite online backup API.
sqlite_db_args=("$@")

# change to the backup staging directory to avoid problems where the postgres
# user can't cd to /root
cd "${backup_staging_directory}"
sudo -u postgres pg_dump miniflux_db > "${backup_staging_directory}/miniflux.sql"

# The online backup copies pages verbatim, so a corrupt source produces a
# corrupt snapshot without any error. Check each snapshot so corruption gets
# noticed while older archives still hold a good copy.
corrupt_dbs=()
for db_arg in "${sqlite_db_args[@]}"; do
    snapshot_name="${db_arg%%=*}"
    source_db_path="${db_arg#*=}"
    snapshot_path="${backup_staging_directory}/${snapshot_name}.db"
    sqlite3 "${source_db_path}" ".backup '${snapshot_path}'"
    if [ "$(sqlite3 "${snapshot_path}" 'PRAGMA quick_check;' 2>&1)" != "ok" ]; then
        corrupt_dbs+=("${snapshot_name}")
    fi
done

# BACKUP_PUSH_URL is an Uptime Kuma push monitor. It also goes down if this
# script stops running or exits early, since then nothing pushes at all.
if [ ${#corrupt_dbs[@]} -eq 0 ]; then
    status=up
    message="all ${#sqlite_db_args[@]} sqlite snapshots ok"
else
    status=down
    message="corrupt sqlite snapshots: ${corrupt_dbs[*]}"
    echo "${message}" >&2
fi
if [ -n "${BACKUP_PUSH_URL}" ]; then
    curl -fsS -m 10 -o /dev/null --get "${BACKUP_PUSH_URL}" \
        --data-urlencode "status=${status}" --data-urlencode "msg=${message}"
fi
[ "${status}" = up ]
