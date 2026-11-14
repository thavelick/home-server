#!/bin/bash
set -e

# Reports the SMART health of every drive smartctl can open to an Uptime Kuma
# push monitor at DISK_HEALTH_PUSH_URL. The monitor also goes down if this
# script stops running, since then nothing pushes at all.

failing_drives=()
drive_count=0
while read -r device _ device_type _; do
    # Devices smartctl couldn't open are listed as comments.
    [[ "${device}" == \#* ]] && continue
    drive_count=$((drive_count + 1))
    smart_status=0
    smartctl -H -d "${device_type}" "${device}" > /dev/null || smart_status=$?
    # Exit status bit 3 means the drive reports itself as failing; bit 4
    # means a pre-failure attribute has crossed its threshold.
    if (( smart_status & 24 )); then
        failing_drives+=("${device}")
    fi
done < <(smartctl --scan-open)

if [ ${#failing_drives[@]} -eq 0 ]; then
    status=up
    message="${drive_count} drives healthy"
else
    status=down
    message="failing SMART health: ${failing_drives[*]}"
    echo "${message}" >&2
fi
if [ -n "${DISK_HEALTH_PUSH_URL}" ]; then
    curl -fsS -m 10 -o /dev/null --get "${DISK_HEALTH_PUSH_URL}" \
        --data-urlencode "status=${status}" --data-urlencode "msg=${message}"
fi
[ "${status}" = up ]
