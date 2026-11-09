#!/bin/bash
# V2 assembly: wait for both pass-3 workers, verify every frame, rebuild the mix, composite with 4 workers (RAM-safe)
cd "$(dirname "$0")"
until grep -q "\[p3w1\] worker done" renders/_queue.log && grep -q "\[p3w2\] worker done" renders/_queue.log; do sleep 20; done
echo "=== $(date +%H:%M:%S) renders done; checking" >> renders/_queue.log
python tests/check_renders.py > renders/_check.txt 2>&1
tail -n 1 renders/_check.txt >> renders/_queue.log
grep -q "BAD SHOTS: 0" renders/_check.txt || { echo "=== V2 ASSEMBLY BLOCKED" >> renders/_queue.log; exit 3; }
python post/audio.py > audio/_mix.log 2>&1
python post/edit.py --audio audio/mix.wav --out final/AlwaysFalling_V2.mp4 --workers 4 --crf 18 >> renders/_queue.log 2>&1
echo "=== $(date +%H:%M:%S) V2 ASSEMBLY DONE" >> renders/_queue.log
