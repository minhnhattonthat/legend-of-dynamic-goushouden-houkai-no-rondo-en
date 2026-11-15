"""Decode every packed block in work/packed_blocks.json (tools/scanpacked.py) to work/blocks/<OFFSET>.bin,
so vramfind.py can search them: python -X utf8 $SKILL/scripts/vramfind.py X.vram.bin work/blocks

    python -X utf8 tools/dumpblocks.py [--lo HEX --hi HEX] [--out DIR]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import packed  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", default="0")
    ap.add_argument("--hi", default="FFFFFFFF")
    ap.add_argument("--out", default=str(ROOT / "work" / "blocks"))
    a = ap.parse_args()
    lo, hi = int(a.lo, 16), int(a.hi, 16)
    rom = next((ROOT / "rom").glob("*.gba")).read_bytes()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n = bad = 0
    for off, *_ in json.loads((ROOT / "work" / "packed_blocks.json").read_text()):
        if not lo <= off < hi:
            continue
        try:
            raw = packed.unpack(rom, off)[1]
        except Exception as e:  # a false-positive header: list it, never drop it silently
            print(f"skip {off:06X}: {e}")
            bad += 1
            continue
        (out / f"{off:06X}.bin").write_bytes(raw)
        n += 1
    print(f"{n} blocks written to {out}, {bad} skipped")


if __name__ == "__main__":
    main()
