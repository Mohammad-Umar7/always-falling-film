#!/bin/bash
cd "$(dirname "$0")"
until grep -q "HQ QUEUE COMPLETE" renders/_queue.log; do sleep 20; done
for n in i2b; do
  sid=I2b
  if [ -d "renders/$sid" ]; then rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"; fi
  ./render_queue.sh "$n"
done
echo "=== TAIL QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
