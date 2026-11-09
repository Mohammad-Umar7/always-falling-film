#!/bin/bash
# after the final character pass: improved non-character shots (door, wall calendar, room lamp, cel Earth)
cd "$(dirname "$0")"
until grep -q "FINAL QUEUE COMPLETE" renders/_queue.log; do sleep 20; done
for n in half:E2L half:F3L half:G3L c3d d1; do
  sid=${n#half:}; sid=$(echo "$sid" | sed -E 's/^c3d$/C3d/; s/^d1$/D1/')
  if [ -d "renders/$sid" ]; then rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"; fi
  ./render_queue.sh "$n"
done
echo "=== POST QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
