#!/bin/bash
# V2 re-render: faces/expressions, rebuilt cast, reframed shots. Moves each shot's V1 frames to renders_v1/ first
# (render_anim skips frames that already exist), then renders it. Most important shots first.
cd "$(dirname "$0")"
mkdir -p renders_v1
SHOTS="half:J2 half:J1 half:I3L half:I3R half:J3 half:G1L half:F2L half:F2R b4a b4b half:E3L half:I4W b5 b1 half:C1F
half:F1L half:E1R half:I1L half:I1R half:F5L half:F5R half:C2L half:C2R half:E1L half:E3R half:F1R half:F4L half:F4R
half:G1R half:G2L half:G2R half:G3R half:E2R half:C1R half:K1W half:A2L half:A2R"
echo "--- V2 queue $(date +%H:%M)" >> renders/_queue.log
for n in $SHOTS; do
  sid=${n#half:}
  sid=$(echo "$sid" | sed -E 's/^b([0-9])/B\1/')
  if [ -d "renders/$sid" ] && [ ! -d "renders_v1/$sid" ]; then
    mv "renders/$sid" "renders_v1/$sid"
  fi
  ./render_queue.sh "$n"
done
echo "=== V2 QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
