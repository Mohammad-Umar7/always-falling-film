#!/bin/bash
# FINAL character render pass (all fixes + faces + sparkles + soft cel edges).
# B4a/B4b/F2L/F2R/I4W are being re-rendered by the redo2/redo3 passes with the same code, so they are skipped.
cd "$(dirname "$0")"
until grep -q "REDO2 QUEUE COMPLETE" renders/_queue.log; do sleep 20; done
sleep 40
EXTRA=""
if tail -n 3 renders/_queue.log | grep -q "start half:I4W"; then
  until grep -q "REDO3 QUEUE COMPLETE" renders/_queue.log; do sleep 20; done
else
  EXTRA="half:I4W"
fi
mkdir -p renders_prev
echo "--- FINAL queue $(date +%H:%M)" >> renders/_queue.log
SHOTS="half:J2 half:I3L half:I3R half:J3 half:J1 half:G1L half:F1L half:E1R half:E3L
half:F5L half:F5R half:G2L half:I1L half:I1R half:E2R half:F4L half:C2L half:C2R half:E1L half:E3R half:F1R half:F4R
half:G1R half:G2R half:G3R half:C1F half:C1R b1 b2 b3 b5 half:K1W half:A2L half:A2R $EXTRA"
for n in $SHOTS; do
  sid=${n#half:}
  sid=$(echo "$sid" | sed -E 's/^b([0-9])/B\1/')
  if [ -d "renders/$sid" ]; then rm -rf "renders_prev/$sid"; mv "renders/$sid" "renders_prev/$sid"; fi
  ./render_queue.sh "$n"
done
echo "=== FINAL QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
