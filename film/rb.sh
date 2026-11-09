#!/bin/bash
# usage: ./rb.sh shots/b3.py preview frames=100 scale=50
cd "$(dirname "$0")"
s=$1; shift
t0=$(date +%s)
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P "$s" -- "$@" 2>&1 | grep -E "Traceback|Error|error:|line [0-9]+|AF:" | tail -n 25
echo "elapsed $(( $(date +%s) - t0 ))s  [$s $*]"
