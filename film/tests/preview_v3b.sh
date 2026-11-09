#!/bin/bash
cd "$(dirname "$0")/.."
B="/c/Program Files/Blender Foundation/Blender 5.1/blender.exe"
for job in "F4L 70,110" "E3R 90" "J2 60,110"; do
  set -- $job
  echo "=== $(date +%H:%M:%S) preview $1 $2" >> renders/_previews/_v3.log
  "$B" -b --factory-startup -P shots/half.py -- preset=$1 preview frames=$2 scale=50 2>&1 | grep -E "Traceback|Error|AF: (acting|detail|finished)" >> renders/_previews/_v3.log
done
echo "=== $(date +%H:%M:%S) PREVIEWS B DONE" >> renders/_previews/_v3.log
