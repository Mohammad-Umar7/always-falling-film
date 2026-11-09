#!/bin/bash
# keep C: from filling up: clear superseded frame caches (renders_prev/*) and old previews when free space is low.
# never touches renders/ (current frames), final/, assets/, audio/, scripts.
cd "$(dirname "$0")"
while true; do
  free=$(df -k /c | awk 'NR==2{print $4}')
  if [ "$free" -lt 12000000 ]; then
    n=$(ls renders_prev 2>/dev/null | wc -l)
    find renders_prev -mindepth 1 -maxdepth 1 -mmin +2 -exec rm -rf {} + 2>/dev/null
    find renders/_previews -name "*.png" -mmin +30 -delete 2>/dev/null
    echo "=== $(date +%H:%M:%S) disk_watch: free $((free/1024/1024)) GB, cleared $n superseded folders -> $(df -h /c | awk 'NR==2{print $4}') free" >> renders/_queue.log
  fi
  sleep 120
done
