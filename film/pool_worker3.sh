#!/bin/bash
# render worker (pass 2): full re-render jobs move old frames aside first; repair:<job> only fills missing frames
cd "$(dirname "$0")"
W=$1
while read -r job; do
  [ -z "$job" ] && continue
  key=${job//:/_}
  mkdir "renders/_claims3/$key" 2>/dev/null || continue
  j=${job#repair:}
  if [[ "$j" == half:* ]]; then sid=${j#half:}; else sid="$(echo ${j:0:1} | tr a-z A-Z)${j:1}"; fi
  if [[ "$job" == repair:* ]]; then
    find "renders/$sid" -name "*.png" -size 0 -delete 2>/dev/null
  elif [ -d "renders/$sid" ]; then
    rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"
  fi
  echo "=== $(date +%H:%M:%S) [p3w$W] claim $job ($sid)" >> renders/_queue.log
  ./render_queue.sh "$j"
done < render_jobs3.txt
echo "=== $(date +%H:%M:%S) [p3w$W] worker done" >> renders/_queue.log
