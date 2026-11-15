"""Tour sheets for the visual-QA gate: one PNG per warp scene, English final frame | original, 2x.

    python -X utf8 tools/tour_sheets.py [--en work/qa/tour_en] [--jp work/qa/tour_jp] [--out work/qa/tour]

Reads <dir>/shots/<scene>.png from tools/debug/warp_all.py runs (the English build and the original ROM); a scene
missing from the original run gets the English frame alone. Then:
    python -X utf8 $SKILL/scripts/qa_gate.py init work/qa/manifest.tsv work/qa/tour --glob "*.png" --build build/goushouden_en.gba
"""
import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--en", default=str(ROOT / "work" / "qa" / "tour_en"))
    ap.add_argument("--jp", default=str(ROOT / "work" / "qa" / "tour_jp"))
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "tour"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n = alone = 0
    for en in sorted((Path(a.en) / "shots").glob("*.png")):
        jp = Path(a.jp) / "shots" / en.name
        ims = [Image.open(en).convert("RGB")] + ([Image.open(jp).convert("RGB")] if jp.exists() else [])
        alone += len(ims) == 1
        w, h = ims[0].size
        sheet = Image.new("RGB", (len(ims) * (2 * w + 8) - 8, 2 * h), (255, 0, 255))
        for i, im in enumerate(ims):
            sheet.paste(im.resize((2 * w, 2 * h), Image.NEAREST), (i * (2 * w + 8), 0))
        sheet.save(out / en.name)
        n += 1
    print(f"{n} sheets in {out} ({alone} without an original frame)")


if __name__ == "__main__":
    main()
