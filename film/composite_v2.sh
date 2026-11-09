#!/bin/bash
# after pass 2: verify every render (abort if anything is broken), rebuild the mix, composite V2
cd "$(dirname "$0")"
for w in 1 2 3 4; do
  until grep -q "\[p2w$w\] worker done" renders/_queue.log; do sleep 15; done
done
echo "=== $(date +%H:%M:%S) pass 2 done; checking renders" >> renders/_queue.log
python tests/check_renders.py > renders/_check.txt 2>&1
if ! grep -q "BAD SHOTS: 0" renders/_check.txt; then
  echo "=== $(date +%H:%M:%S) V2 COMPOSITE BLOCKED: broken renders (see renders/_check.txt)" >> renders/_queue.log
  exit 1
fi
python post/audio.py > audio/_mix.log 2>&1
python post/edit.py --audio audio/mix.wav --out final/AlwaysFalling_V2.mp4 --workers 12 --crf 18 >> renders/_queue.log 2>&1
echo "=== $(date +%H:%M:%S) V2 COMPOSITE DONE" >> renders/_queue.log
