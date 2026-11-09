#!/bin/bash
# usage: ./render_queue.sh b1 b2 half:C2L half:C2R ...   (final renders, sequential, logs to renders/_queue.log)
cd "$(dirname "$0")"
for n in "$@"; do
  echo "=== $(date +%H:%M:%S) start $n" >> renders/_queue.log
  if [[ "$n" == half:* ]]; then
    p=${n#half:}
    "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P "shots/half.py" -- preset=$p final 2>&1 | grep -E "Traceback|Error|AF:" >> renders/_queue.log
  else
    "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P "shots/$n.py" -- final 2>&1 | grep -E "Traceback|Error|AF:" >> renders/_queue.log
  fi
  echo "=== $(date +%H:%M:%S) done $n" >> renders/_queue.log
done
echo "=== QUEUE COMPLETE $(date +%H:%M:%S)" >> renders/_queue.log
