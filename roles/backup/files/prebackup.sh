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

for db_arg in "${sqlite_db_args[@]}"; do
    snapshot_name="${db_arg%%=*}"
    source_db_path="${db_arg#*=}"
    sqlite3 "${source_db_path}" ".backup '${backup_staging_directory}/${snapshot_name}.db'"
done
