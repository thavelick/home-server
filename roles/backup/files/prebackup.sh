#!/bin/bash
set -e

backup_staging_directory=$1
wallabag_db_file=$2
miniflux_dump_file="${backup_staging_directory}/miniflux.sql"

# change to the backup staging directory to avoid problems where the postgres
# user can't cd to /root
cd "${backup_staging_directory}"
sudo -u postgres pg_dump miniflux_db > "${miniflux_dump_file}"

# copy the wallbag db file to the backup staging directory
cp "${wallabag_db_file}" "${backup_staging_directory}"

