"""sweep_quarters.py: cut each work/sweep/pageNNN.png into 4 quarters zoomed 2x (pageNNN_q0..q3.png in
work/sweep/q/), so a reviewer model sees glyph detail instead of a downscaled page.

  python -X utf8 tools/sweep_quarters.py [--zoom 2]
"""
import argparse
import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zoom", type=int, default=2)
    ap.add_argument("--dir", default=os.path.join(ROOT, "work", "sweep"))
    a = ap.parse_args()
    out = os.path.join(a.dir, "q")
    os.makedirs(out, exist_ok=True)
    n = 0
    for p in sorted(glob.glob(os.path.join(a.dir, "page*.png"))):
        im = Image.open(p)
        w, h = im.size
        base = os.path.splitext(os.path.basename(p))[0]
        for k, (x, y) in enumerate(((0, 0), (w // 2, 0), (0, h // 2), (w // 2, h // 2))):
            q = im.crop((x, y, x + w // 2, y + h // 2)).resize((w // 2 * a.zoom, h // 2 * a.zoom), Image.NEAREST)
            q.save(os.path.join(out, "%s_q%d.png" % (base, k)))
            n += 1
    print("%d quarters in %s" % (n, out))


if __name__ == "__main__":
    main()
