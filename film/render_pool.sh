#!/bin/bash
cd "$(dirname "$0")"
rm -rf renders/_claims; mkdir -p renders/_claims renders_prev
echo "--- POOL $(date +%H:%M) workers=2 jobs=$(grep -c . render_jobs.txt)" >> renders/_queue.log
./pool_worker.sh 1 &
sleep 30
./pool_worker.sh 2 &
wait
echo "=== POOL COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
