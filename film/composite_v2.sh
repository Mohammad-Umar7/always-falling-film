#!/bin/bash
# after the single-worker pass: verify every render (abort if broken), rebuild the mix, composite V2 (6 workers: RAM-safe)
cd "$(dirname "$0")"
until grep -q "\[p3w1\] worker done" renders/_queue.log; do sleep 20; done
echo "=== $(date +%H:%M:%S) pass 3 done; checking renders" >> renders/_queue.log
python tests/check_renders.py > renders/_check.txt 2>&1
if ! grep -q "BAD SHOTS: 0" renders/_check.txt; then
  echo "=== $(date +%H:%M:%S) V2 COMPOSITE BLOCKED: broken renders (see renders/_check.txt)" >> renders/_queue.log
  exit 1
fi
python post/audio.py > audio/_mix.log 2>&1
python post/edit.py --audio audio/mix.wav --out final/AlwaysFalling_V2.mp4 --workers 6 --crf 18 >> renders/_queue.log 2>&1
echo "=== $(date +%H:%M:%S) V2 COMPOSITE DONE" >> renders/_queue.log
