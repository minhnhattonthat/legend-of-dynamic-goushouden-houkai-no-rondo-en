"""Unpack a player's mGBA / RetroArch-mGBA savestate into dumps that tools/lua/mgba_load.lua injects into Mesen.

    python -X utf8 tools/mgba_state.py PLAYER.state1 work/p1     -> work/p1.{iwram,ewram,vram,oam,pram,io} + work/p1.lua

Accepts RetroArch RZIP (#RZIPv1#), a RetroArch RASTATE wrapper, or a raw mGBA GBASerializedState (0x61000 bytes).
Layout (mGBA src/gba/serialize.h): 0x20 gprs[16], 0x60 cpsr, 0x70 bankedRegisters[6][7] (bank 2 IRQ, 3 SVC:
[0]=SP [1]=LR), 0x400 IO, 0x800 palette, 0xC00 OAM, 0x1000 VRAM, 0x19000 IWRAM, 0x21000 EWRAM.
RetroArch states end at VBlank start (VCOUNT 160), which is where Mesen's endFrame callback fires.
"""
import struct
import sys
import zlib


def unwrap(d):
    if d[:8] == b'#RZIPv\x01#':  # u32 chunk size, u64 total, then (u32 len + zlib) chunks
        p, out = 20, bytearray()
        while p < len(d):
            n = struct.unpack_from('<I', d, p)[0]
            out += zlib.decompress(d[p + 4:p + 4 + n])
            p += 4 + n
        d = bytes(out)
    if d[:8] == b'RASTATE\x01':  # blocks: 4-byte tag, u32 len, data padded to 8
        p = 8
        while p < len(d):
            tag, n = d[p:p + 4], struct.unpack_from('<I', d, p + 4)[0]
            if tag == b'MEM ':
                return d[p + 8:p + 8 + n]
            p += 8 + ((n + 7) & ~7)
        raise SystemExit('RASTATE without a MEM block')
    return d


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    s = unwrap(open(sys.argv[1], 'rb').read())
    if len(s) < 0x61000:
        raise SystemExit(f'not an mGBA state ({len(s):#x} bytes)')
    ver, _, crc = struct.unpack_from('<III', s, 0)
    title = s[0x10:0x1C].rstrip(b'\0').decode('ascii', 'replace')
    gprs = struct.unpack_from('<16I', s, 0x20)
    cpsr = struct.unpack_from('<I', s, 0x60)[0]
    bank = struct.unpack_from('<42I', s, 0x70)
    spsr = struct.unpack_from('<6I', s, 0x118)
    vcount = struct.unpack_from('<H', s, 0x406)[0]
    pre = sys.argv[2]
    for ext, lo, n in (('io', 0x400, 0x400), ('pram', 0x800, 0x400), ('oam', 0xC00, 0x400),
                       ('vram', 0x1000, 0x18000), ('iwram', 0x19000, 0x8000), ('ewram', 0x21000, 0x40000)):
        open(f'{pre}.{ext}', 'wb').write(s[lo:lo + n])
    thumb = bool(cpsr & 0x20)
    pc = gprs[15] - (4 if thumb else 8)  # mGBA r15 = next fetch; Mesen reloads from the next instruction to execute
    regs = {f'cpu.r{i}': gprs[i] for i in range(15)}
    regs.update({'cpu.r15': pc, 'cpu.cpsr.thumb': thumb, 'cpu.cpsr.irqDisable': bool(cpsr & 0x80),
                 'cpu.cpsr.fiqDisable': bool(cpsr & 0x40), 'cpu.cpsr.negative': bool(cpsr >> 31 & 1),
                 'cpu.cpsr.zero': bool(cpsr >> 30 & 1), 'cpu.cpsr.carry': bool(cpsr >> 29 & 1),
                 'cpu.cpsr.overflow': bool(cpsr >> 28 & 1),
                 'cpu.irqRegs0': bank[14], 'cpu.irqRegs1': bank[15],
                 'cpu.supervisorRegs0': bank[21], 'cpu.supervisorRegs1': bank[22],
                 'cpu.pipeline.reloadRequested': True})
    lua = ['MGBA_REGS = {'] + [f'  ["{k}"] = {str(v).lower() if isinstance(v, bool) else v},' for k, v in regs.items()]
    lua += ['}', f'MGBA_INFO = "{title} crc {crc:08X} pc {pc:08X} {"thumb" if thumb else "arm"} cpsr {cpsr:08X} '
            f'vcount {vcount} irq-spsr {spsr[2]:08X}"']
    open(f'{pre}.lua', 'w').write('\n'.join(lua) + '\n')
    print(f'mGBA state v{ver:08X} {title} crc {crc:08X} pc {pc:08X} cpsr {cpsr:08X} vcount {vcount} -> {pre}.*')
    if (cpsr & 0x1F) != 0x1F:
        print(f'warning: CPU mode {cpsr & 0x1F:#x}, not system; the loader keeps the base state\'s mode')


if __name__ == '__main__':
    main()
