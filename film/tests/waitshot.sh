#!/bin/bash
# wait until the pool has finished the given shot ids (done line after the POOL marker)
cd "$(dirname "$0")/.."
for sid in "$@"; do
  until awk '/--- POOL/{p=1} p' renders/_queue.log | grep -qE "done (half:)?${sid}\$"; do sleep 10; done
done
