#!/bin/bash
# V3 checks before the full render: acting beats, life pass, set detail. Stills -> renders/_previews/<SID>_<frame>.png
cd "$(dirname "$0")/.."
B="/c/Program Files/Blender Foundation/Blender 5.1/blender.exe"
run() {  # run <script-or-preset> <frames>
  echo "=== $(date +%H:%M:%S) preview $1 $2" >> renders/_previews/_v3.log
  if [[ "$1" == half:* ]]; then
    "$B" -b --factory-startup -P shots/half.py -- preset=${1#half:} preview frames=$2 scale=50 2>&1 | grep -E "Traceback|Error|AF:|line [0-9]+" >> renders/_previews/_v3.log
  else
    "$B" -b --factory-startup -P shots/$1.py -- preview frames=$2 scale=50 2>&1 | grep -E "Traceback|Error|AF:|line [0-9]+" >> renders/_previews/_v3.log
  fi
}
run b1 1,96,140
run half:C1F 30,50,62
run half:K1W 100,150,220
run half:E3R 60,100
run half:F4L 50,110
run half:A2L 54,104,154
run half:E1L 40,120
run half:J2 60
echo "=== $(date +%H:%M:%S) PREVIEWS DONE" >> renders/_previews/_v3.log
