#!/bin/bash
# second redo pass: B4a/B4b head-turn fix, F2 reframes
cd "$(dirname "$0")"
until grep -q "REDO QUEUE COMPLETE" renders/_queue.log; do sleep 30; done
for n in b4a b4b half:F2L half:F2R; do
  sid=${n#half:}; sid=$(echo "$sid" | sed -E 's/^b4/B4/')
  [ -d "renders/$sid" ] && rm -rf "renders_old/$sid" && mv "renders/$sid" "renders_old/$sid"
  ./render_queue.sh "$n"
done
echo "=== REDO2 QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
