#!/bin/bash
# once the old-cast B1/B2 renders finish, release their claims so the appended b1/b2 lines re-render them
cd "$(dirname "$0")/.."
for j in b1 b2; do
  until awk '/--- POOL/{p=1} p' renders/_queue.log | grep -qE "done ${j}\$"; do sleep 10; done
  rmdir "renders/_claims/$j" && echo "=== $(date +%H:%M:%S) released $j for re-render" >> renders/_queue.log
done
