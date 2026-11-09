#!/bin/bash
# V4 render worker. W=1 renders unconditionally; W=2 only claims a job while the laptop has spare memory.
# Jobs are claimed atomically (mkdir); the V2 frames of a shot move to renders_prev/ as a fallback.
cd "$(dirname "$0")"
W=$1
mkdir -p renders/_claims5
while read -r job; do
  [ -z "$job" ] && continue
  key=${job//:/_}
  [ -d "renders/_claims5/$key" ] && continue
  if [ "$W" != "1" ]; then
    until powershell -NoProfile -ExecutionPolicy Bypass -File memok.ps1 >/dev/null 2>&1; do
      sleep 30
      [ -d "renders/_claims5/$key" ] && continue 2
      grep -q "\[v4w1\] worker done" renders/_queue.log && break 2
    done
  fi
  mkdir "renders/_claims5/$key" 2>/dev/null || continue
  if [[ "$job" == half:* ]]; then sid=${job#half:}; else sid="$(echo ${job:0:1} | tr a-z A-Z)${job:1}"; fi
  [ -n "$sid" ] || continue
  if [ -d "renders/$sid" ]; then rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"; fi
  echo "=== $(date +%H:%M:%S) [v4w$W] claim $job ($sid)" >> renders/_queue.log
  ./render_queue.sh "$job"
done < render_jobs5.txt
echo "=== $(date +%H:%M:%S) [v4w$W] worker done" >> renders/_queue.log
