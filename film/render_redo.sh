#!/bin/bash
# After the V2 queue: redo shots affected by the critique fixes (eye glow/tears, launch exposure, cel Earth).
cd "$(dirname "$0")"
until grep -q "V2 QUEUE COMPLETE" renders/_queue.log; do sleep 30; done
mkdir -p renders_old
echo "--- REDO queue $(date +%H:%M)" >> renders/_queue.log
for n in half:J2 half:J1 half:I3L half:I3R half:J3 c3a c3b c3c h1; do
  sid=${n#half:}
  sid=$(echo "$sid" | sed -E 's/^c3/C3/; s/^h1$/H1/')
  if [ -d "renders/$sid" ]; then
    rm -rf "renders_old/$sid"
    mv "renders/$sid" "renders_old/$sid"
  fi
  ./render_queue.sh "$n"
done
echo "=== REDO QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
