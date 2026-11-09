"""Verify every render folder the edit uses: frames exist for the whole used range, no gaps > 2, no 0-byte files."""
import os, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "post"))
import timeline as TL

R = os.path.join(ROOT, "renders")
need = {}            # sid -> max local frame needed


def want(sid, n):
    need[sid] = max(need.get(sid, 0), n)


for sid, a, b, kind, src, ex in TL.SEQ:
    n = b - a + 1
    if kind == "full":
        want(src, n)
    elif kind == "split":
        want(src[0], n)
        want(src[1], n)
    elif kind == "c1":
        want(src[0], n)
        want(src[1], b - ex["split_at"] + 1)
    elif kind == "i4":
        want(src[2], n)
        want(src[0], 168)
        want(src[1], 168)
    elif kind == "k1":
        want(src[2], n)
        want(src[0], ex["split_offset"] + n)
        want(src[1], ex["split_offset"] + n)
bad = 0
for sid in sorted(need):
    fs = sorted(glob.glob(os.path.join(R, sid, "[0-9][0-9][0-9][0-9].png")))
    nums = [int(os.path.basename(f)[:4]) for f in fs]
    zero = [os.path.basename(f) for f in fs if os.path.getsize(f) == 0]
    gaps = [(x, y) for x, y in zip(nums, nums[1:]) if y - x > 3]
    last = nums[-1] if nums else 0
    ok = nums and nums[0] <= 1 and last >= need[sid] - 2 and not zero and not gaps
    if not ok:
        bad += 1
    print(f"{'OK ' if ok else 'BAD'} {sid:5s} frames={len(nums):4d} first={nums[0] if nums else '-'} last={last:4d} need={need[sid]:4d}"
          + (f" ZERO={zero[:3]}" if zero else "") + (f" GAPS={gaps[:3]}" if gaps else ""))
print("BAD SHOTS:", bad)
