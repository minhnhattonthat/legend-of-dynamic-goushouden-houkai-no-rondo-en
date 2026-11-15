"""Warp to a scene and dump its video memory (phase 8 graphics work).

    python -X utf8 tools/ppuscene.py SCENE [--rom jp|en|PATH] [--frames 900] [--find]

Writes work/qa/ppu/<jp|en>_<SCENE>/ppu_<frames-1>.{vram,pal,oam,io}.bin plus the warp shot. --find runs
vramfind.py on the VRAM dump against work/blocks (tools/dumpblocks.py) and prints the matching packed blocks.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402


def rom_path(tag):
    if tag == "jp":
        return next((ROOT / "rom").glob("*.gba"))
    if tag == "en":
        return ROOT / "build" / "goushouden_en.gba"
    return Path(tag)


def dump(scene, tag="jp", frames=900):
    rom = rom_path(tag)
    out = ROOT / "work" / "qa" / "ppu" / f"{'jp' if tag == 'jp' else 'en'}_{scene}"
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(out),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", f"SCENE='{scene}'",
           "--script", str(Path(SKILL) / "scripts" / "lua" / "probes" / "ppudump.lua"),
           "--script", str(ROOT / "tools" / "lua" / "unpacklog.lua"),  # log.txt: the blocks this scene loads
           "--frames", str(frames)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"emu.py exit {r.returncode}: {r.stdout[-400:]} {r.stderr[-400:]}")
    return out / f"ppu_{frames - 1:06d}"


def find(prefix):
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "vramfind.py"),
           str(prefix.with_suffix(".vram.bin")), str(ROOT / "work" / "blocks"), "--fmt", "gba4"]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene")
    ap.add_argument("--rom", default="jp")
    ap.add_argument("--frames", type=int, default=900)
    ap.add_argument("--find", action="store_true")
    a = ap.parse_args()
    p = dump(a.scene, a.rom, a.frames)
    print(p)
    if a.find:
        print(find(p))


if __name__ == "__main__":
    main()
