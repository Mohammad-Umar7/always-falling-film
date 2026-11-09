#!/bin/bash
# V3 assembly: wait for both render workers, decode-check every frame (repair what is broken), rebuild the mix,
# composite with 4 workers (RAM-safe), make the 720p phone copy, copy both to the Downloads folder.
cd "$(dirname "$0")"
L=renders/_queue.log
until grep -q "\[v3w1\] worker done" $L && grep -q "\[v3w2\] worker done" $L; do sleep 30; done
echo "=== $(date +%H:%M:%S) V3 renders done; checking" >> $L
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
grep -q "BAD SHOTS: 0" renders/_check.txt || { echo "=== V3 ASSEMBLY BLOCKED (see renders/_check.txt)" >> $L; exit 3; }
python post/audio.py > audio/_mix_v3.log 2>&1 || { echo "=== V3 MIX FAILED" >> $L; exit 4; }
python post/edit.py --audio audio/mix.wav --out final/AlwaysFalling_V3.mp4 --workers 4 --crf 18 >> $L 2>&1 || { echo "=== V3 COMPOSITE FAILED" >> $L; exit 5; }
cd final
ffmpeg -v error -y -i AlwaysFalling_V3.mp4 -vf scale=1280:720 -c:v libx264 -preset slow -b:v 640k -threads 8 -pass 1 -passlogfile v3p -an -f mp4 NUL
ffmpeg -v error -y -i AlwaysFalling_V3.mp4 -vf scale=1280:720 -c:v libx264 -preset slow -b:v 640k -maxrate 900k -bufsize 1800k -threads 8 -pass 2 -passlogfile v3p -c:a aac -b:a 96k -movflags +faststart AlwaysFalling_V3_phone720p.mp4
rm -f v3p-0.log v3p-0.log.mbtree
cp AlwaysFalling_V3.mp4 AlwaysFalling_V3_phone720p.mp4 "/c/Users/omerj/Downloads/DADC-Always-Falling/"
cd ..
echo "=== $(date +%H:%M:%S) V3 ASSEMBLY DONE" >> $L
