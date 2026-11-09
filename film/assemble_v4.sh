#!/bin/bash
# V4 chain: after V3 is fully assembled, switch V4 on, render every shot (worker 2 only when memory allows), decode-check
# and repair, rebuild the mix, composite V4, make the phone copy, copy both to the Downloads folder.
cd "$(dirname "$0")"
L=renders/_queue.log
until grep -qE "V3 ASSEMBLY DONE|V3 ASSEMBLY BLOCKED|V3 MIX FAILED|V3 COMPOSITE FAILED" $L; do sleep 30; done
grep -q "V3 ASSEMBLY DONE" $L || { echo "=== V4 CHAIN STOPPED: V3 did not finish" >> $L; exit 2; }
touch v4.flag
echo "--- V4 render $(date +%H:%M)" >> $L
(./pool_worker5.sh 1 > /dev/null 2>&1 &)
sleep 5
(./pool_worker5.sh 2 > /dev/null 2>&1 &)
until grep -q "\[v4w1\] worker done" $L && grep -q "\[v4w2\] worker done" $L; do sleep 30; done
echo "=== $(date +%H:%M:%S) V4 renders done; checking" >> $L
for pass in 1 2; do
  python tests/verify_pngs.py --delete > renders/_verify.txt 2>&1
  python tests/check_renders.py > renders/_check.txt 2>&1
  tail -n 1 renders/_check.txt >> $L; grep "BAD" renders/_verify.txt >> $L
  bad=$( (grep "^BAD [A-Za-z0-9]*:" renders/_verify.txt; grep -E "^(BAD|MISSING|GAP)" renders/_check.txt) | grep -v "SHOTS" | sed -E 's/^(BAD|MISSING|GAP)[ :]+([A-Za-z0-9]+).*/\2/' | sort -u)
  [ -z "$bad" ] && grep -q "BAD SHOTS: 0" renders/_check.txt && break
  for sid in $bad; do
    case $sid in B1|B2|B3|B4a|B4b|B5|C3a|C3b|C3c|C3d|C4|D1|D2|H1|I2a|I2b|I2c) job=$(echo $sid | tr A-Z a-z);; *) job=half:$sid;; esac
    echo "=== $(date +%H:%M:%S) repair $job" >> $L
    ./render_queue.sh "$job"
  done
done
grep -q "BAD SHOTS: 0" renders/_check.txt || { echo "=== V4 ASSEMBLY BLOCKED (see renders/_check.txt)" >> $L; exit 3; }
python post/audio.py > audio/_mix_v4.log 2>&1 || { echo "=== V4 MIX FAILED" >> $L; exit 4; }
python post/edit.py --audio audio/mix.wav --out final/AlwaysFalling_V4.mp4 --workers 4 --crf 18 >> $L 2>&1 || { echo "=== V4 COMPOSITE FAILED" >> $L; exit 5; }
cd final
ffmpeg -v error -y -i AlwaysFalling_V4.mp4 -vf scale=1280:720 -c:v libx264 -preset slow -b:v 640k -threads 8 -pass 1 -passlogfile v4p -an -f mp4 NUL
ffmpeg -v error -y -i AlwaysFalling_V4.mp4 -vf scale=1280:720 -c:v libx264 -preset slow -b:v 640k -maxrate 900k -bufsize 1800k -threads 8 -pass 2 -passlogfile v4p -c:a aac -b:a 96k -movflags +faststart AlwaysFalling_V4_phone720p.mp4
rm -f v4p-0.log v4p-0.log.mbtree
cp AlwaysFalling_V4.mp4 AlwaysFalling_V4_phone720p.mp4 "/c/Users/omerj/Downloads/DADC-Always-Falling/"
cd ..
echo "=== $(date +%H:%M:%S) V4 ASSEMBLY DONE" >> $L
