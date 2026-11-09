#!/bin/bash
# one render worker: claims jobs from render_jobs.txt atomically (mkdir), moves old frames aside, renders
cd "$(dirname "$0")"
W=$1
while read -r job; do
  [ -z "$job" ] && continue
  key=${job//:/_}
  mkdir "renders/_claims/$key" 2>/dev/null || continue
  if [[ "$job" == half:* ]]; then sid=${job#half:}; else sid="$(echo ${job:0:1} | tr a-z A-Z)${job:1}"; fi
  if [ -d "renders/$sid" ]; then rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"; fi
  echo "=== $(date +%H:%M:%S) [w$W] claim $job ($sid)" >> renders/_queue.log
  ./render_queue.sh "$job"
done < render_jobs.txt
echo "=== $(date +%H:%M:%S) [w$W] worker done" >> renders/_queue.log
