#!/bin/bash
# high-sample redo of close-ups rendered before the HQ switch
cd "$(dirname "$0")"
until grep -q "POST QUEUE COMPLETE" renders/_queue.log; do sleep 20; done
for n in half:J2 b4a b4b half:F2L half:F2R half:J3; do
  sid=${n#half:}; sid=$(echo "$sid" | sed -E 's/^b4/B4/')
  if [ -d "renders/$sid" ]; then rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"; fi
  ./render_queue.sh "$n"
done
echo "=== HQ QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
