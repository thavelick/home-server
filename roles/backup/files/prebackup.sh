#!/bin/bash
set -e

backup_staging_directory=$1
wallabag_db_file=$2
nextcloud_db_file=$3
miniflux_dump_file="${backup_staging_directory}/miniflux.sql"


# change to the backup staging directory to avoid problems where the postgres
# user can't cd to /root
cd "${backup_staging_directory}"
sudo -u postgres pg_dump miniflux_db > "${miniflux_dump_file}"

# snapshot sqlite databases using the online backup API for a consistent copy
sqlite3 "${wallabag_db_file}" ".backup '${backup_staging_directory}/wallabag.db'"
sqlite3 "${nextcloud_db_file}" ".backup '${backup_staging_directory}/nextcloud.db'"
