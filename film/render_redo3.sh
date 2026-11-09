#!/bin/bash
cd "$(dirname "$0")"
until grep -q "REDO2 QUEUE COMPLETE" renders/_queue.log; do sleep 30; done
for n in half:I4W; do
  sid=${n#half:}
  [ -d "renders/$sid" ] && rm -rf "renders_old/$sid" && mv "renders/$sid" "renders_old/$sid"
  ./render_queue.sh "$n"
done
echo "=== REDO3 QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
