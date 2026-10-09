"""Rebuild the .ttf files that reportlab uses for the running header and footer of the PDFs.

Each .ttf is the bundled fontsource latin + latin-ext .woff2 of one family and weight, decoded and merged into one TrueType
font, so the header and footer cover Latin-1 and Latin Extended-A (Ł, Š, ő, ğ, ...) in the same glyphs as the body text.
Only Python's standard library is used; the brotli stream inside each .woff2 is unpacked with Node.js (on PATH, or the copy
that ships with Playwright). Layout tables (GSUB, GPOS, kern) are dropped: reportlab does not use them.

Usage:  python _system/pdf/fonts/make_ttf.py [folder]   (writes the files listed in FONTS below; default: next to this script)
"""
import math, os, shutil, struct, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
FONTS = {'inter-400-normal.ttf': 'inter-{}-400-normal', 'inter-600-normal.ttf': 'inter-{}-600-normal',
         'fraunces-500-normal.ttf': 'fraunces-{}-500-normal', 'josefin-sans-600-normal.ttf': 'josefin-sans-{}-600-normal',
         'limelight-400-normal.ttf': 'limelight-{}-400-normal'}
TAGS = ('cmap head hhea hmtx maxp name OS/2 post cvt  fpgm glyf loca prep CFF  VORG EBDT EBLC gasp hdmx kern LTSH PCLT VDMX '
        'vhea vmtx BASE GDEF GPOS GSUB EBSC JSTF MATH CBDT CBLC COLR CPAL SVG  sbix acnt avar bdat bloc bsln cvar fdsc feat '
        'fmtx fvar gvar hsty just lcar mort morx opbd prop trak Zapf Silf Glat Gloc Feat Sill')
TAGS = [TAGS[i:i + 4] for i in range(0, len(TAGS), 5)]
KEEP = ('OS/2', 'cvt ', 'fpgm', 'gasp', 'head', 'hhea', 'maxp', 'name', 'prep')  # copied from the latin font

def node():
    n = shutil.which('node')
    if n: return n
    import playwright
    n = Path(playwright.__file__).parent / 'driver' / ('node.exe' if os.name == 'nt' else 'node')
    if n.exists(): return str(n)
    sys.exit('Node.js is needed to unpack the brotli stream of a .woff2 (install Node.js or Playwright).')

def unbrotli(data):
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / 'in', Path(d) / 'out'
        src.write_bytes(data)
        subprocess.run([node(), '-e', "const z=require('zlib'),f=require('fs');f.writeFileSync(process.argv[2],z.brotliDecompressSync(f.readFileSync(process.argv[1])))",
                        str(src), str(dst)], check=True)
        return dst.read_bytes()

class R:
    def __init__(s, b): s.b, s.i = b, 0
    def take(s, n):
        s.i += n
        if s.i > len(s.b): raise ValueError('truncated stream')
        return s.b[s.i - n:s.i]
    def u8(s): return s.take(1)[0]
    def u16(s): return struct.unpack('>H', s.take(2))[0]
    def i16(s): return struct.unpack('>h', s.take(2))[0]
    def u32(s): return struct.unpack('>I', s.take(4))[0]
    def b128(s):
        v = 0
        for k in range(5):
            c = s.u8()
            if k == 0 and c == 0x80: raise ValueError('bad UIntBase128')
            v = (v << 7) | (c & 0x7f)
            if not c & 0x80: return v
        raise ValueError('bad UIntBase128')
    def u255(s):
        c = s.u8()
        return s.u16() if c == 253 else 253 + s.u8() if c == 255 else 506 + s.u8() if c == 254 else c

def composite_len(r):
    """Length of composite glyph data starting at r.i; returns (bytes, has_instructions)."""
    start, instr = r.i, False
    while True:
        fl = r.u16(); r.u16()
        r.take(4 if fl & 1 else 2)
        r.take(2 if fl & 8 else 4 if fl & 0x40 else 8 if fl & 0x80 else 0)
        instr |= bool(fl & 0x100)
        if not fl & 0x20: return r.b[start:r.i], instr

def sign(f, v): return v if f & 1 else -v

def glyf_decode(t):
    """WOFF2 transformed glyf table -> list of TrueType glyph records (bytes)."""
    h = R(t); h.u16(); opt = h.u16(); n = h.u16(); h.u16()
    sizes = [h.u32() for _ in range(7)]
    st, o = [], h.i
    for z in sizes: st.append(R(t[o:o + z])); o += z
    nc, npt, fl, gs, cs, bb, ins = st
    bmp = bb.take(4 * ((n + 31) // 32))
    ovl = t[o:o + (n + 7) // 8] if opt & 1 else b''
    out = []
    for g in range(n):
        k = nc.i16()
        hasbb = bmp[g >> 3] & (0x80 >> (g & 7))
        if k == 0:
            out.append(b''); continue
        if k < 0:
            comp, hi = composite_len(cs)
            box = bb.take(8)
            rec = struct.pack('>h', -1) + box + comp
            if hi:
                il = gs.u255(); rec += struct.pack('>H', il) + ins.take(il)
            out.append(rec); continue
        ends, tot = [], 0
        for _ in range(k):
            tot += npt.u255(); ends.append(tot - 1)
        pts, x, y = [], 0, 0
        for _ in range(tot):
            f = fl.u8(); on = not f >> 7; f &= 0x7f
            if f < 10: dx, dy = 0, sign(f, ((f & 14) << 7) + gs.u8())
            elif f < 20: dx, dy = sign(f, (((f - 10) & 14) << 7) + gs.u8()), 0
            elif f < 84:
                b0, b1 = f - 20, gs.u8()
                dx, dy = sign(f, 1 + (b0 & 0x30) + (b1 >> 4)), sign(f >> 1, 1 + ((b0 & 0x0c) << 2) + (b1 & 0x0f))
            elif f < 120:
                b0, a, b = f - 84, gs.u8(), gs.u8()
                dx, dy = sign(f, 1 + ((b0 // 12) << 8) + a), sign(f >> 1, 1 + (((b0 % 12) >> 2) << 8) + b)
            elif f < 124:
                a, b, c = gs.u8(), gs.u8(), gs.u8()
                dx, dy = sign(f, (a << 4) + (b >> 4)), sign(f >> 1, ((b & 0x0f) << 8) + c)
            else:
                a, b, c, d = gs.u8(), gs.u8(), gs.u8(), gs.u8()
                dx, dy = sign(f, (a << 8) + b), sign(f >> 1, (c << 8) + d)
            x += dx; y += dy; pts.append((x, y, on, dx, dy))
        il = gs.u255(); code = ins.take(il)
        box = bb.take(8) if hasbb else struct.pack('>4h', min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
        flags, xs, ys = bytearray(), bytearray(), bytearray()
        for i, (_, _, on, dx, dy) in enumerate(pts):
            f = 1 if on else 0
            if i == 0 and ovl and ovl[g >> 3] & (0x80 >> (g & 7)): f |= 0x40
            if dx == 0: f |= 0x10
            elif -255 <= dx <= 255: f |= 0x02 | (0x10 if dx > 0 else 0); xs.append(abs(dx))
            else: xs += struct.pack('>h', dx)
            if dy == 0: f |= 0x20
            elif -255 <= dy <= 255: f |= 0x04 | (0x20 if dy > 0 else 0); ys.append(abs(dy))
            else: ys += struct.pack('>h', dy)
            flags.append(f)
        out.append(struct.pack('>h', k) + box + struct.pack(f'>{k}H', *ends) + struct.pack('>H', il) + code + bytes(flags) + bytes(xs) + bytes(ys))
    return out

def woff2(path):
    """Read a .woff2: {tag: table bytes}, with glyf decoded to a list of glyph records and loca dropped."""
    r = R(path.read_bytes())
    if r.take(4) != b'wOF2': raise ValueError(f'{path.name} is not a WOFF2 file')
    flavor = r.take(4); r.u32(); nt = r.u16(); r.u16(); r.u32(); comp = r.u32(); r.take(24)
    if flavor != b'\0\1\0\0': raise ValueError(f'{path.name}: only TrueType-flavoured WOFF2 is supported')
    dirs = []
    for _ in range(nt):
        f = r.u8(); tag = TAGS[f & 63] if f & 63 != 63 else r.take(4).decode('latin-1')
        ver, ln = f >> 6, r.b128()
        tr = (ver == 0) if tag in ('glyf', 'loca') else ver != 0
        if tr and tag not in ('glyf', 'loca'): raise ValueError(f'{path.name}: transformed {tag} table is not supported')
        dirs.append((tag, r.b128() if tr else ln))
    data, o, t = unbrotli(r.take(comp)), 0, {}
    for tag, ln in dirs:
        t[tag] = data[o:o + ln]; o += ln
    t['glyf'] = glyf_decode(t['glyf']); t.pop('loca', None)
    return t

def hmtx(t):
    n, g = struct.unpack('>H', t['hhea'][34:36])[0], len(t['glyf'])
    m = [struct.unpack('>Hh', t['hmtx'][4 * i:4 * i + 4]) for i in range(n)]
    return m + [(m[-1][0], struct.unpack('>h', t['hmtx'][4 * n + 2 * j:4 * n + 2 * j + 2])[0]) for j in range(g - n)]

def cmap(t):
    b, out = t['cmap'], {}
    for i in range(struct.unpack('>H', b[2:4])[0]):
        pid, eid, off = struct.unpack('>HHI', b[4 + 8 * i:12 + 8 * i])
        fmt = struct.unpack('>H', b[off:off + 2])[0]
        if (pid, eid) not in ((3, 1), (0, 3), (3, 10), (0, 4)): continue
        if fmt == 4:
            n = struct.unpack('>H', b[off + 6:off + 8])[0] // 2
            a = lambda k: struct.unpack(f'>{n}H', b[off + k:off + k + 2 * n])
            end, start, delta, ro = a(14), a(16 + 2 * n), a(16 + 4 * n), a(16 + 6 * n)
            for s in range(n):
                for c in range(start[s], end[s] + 1):
                    if c == 0xFFFF: continue
                    if ro[s] == 0: gid = (c + delta[s]) & 0xFFFF
                    else:
                        p = off + 16 + 6 * n + 2 * s + ro[s] + 2 * (c - start[s])
                        gid = struct.unpack('>H', b[p:p + 2])[0]
                        gid = (gid + delta[s]) & 0xFFFF if gid else 0
                    if gid: out.setdefault(c, gid)
        elif fmt == 12:
            for k in range(struct.unpack('>I', b[off + 12:off + 16])[0]):
                s, e, g = struct.unpack('>III', b[off + 16 + 12 * k:off + 28 + 12 * k])
                for c in range(s, e + 1): out.setdefault(c, g + c - s)
    return out

def cmap4(m):
    segs = []
    for c in sorted(m):
        d = (m[c] - c) & 0xFFFF
        if segs and segs[-1][1] == c - 1 and segs[-1][2] == d: segs[-1][1] = c
        else: segs.append([c, c, d])
    segs.append([0xFFFF, 0xFFFF, 1])
    n = len(segs); p = 2 ** int(math.log2(n))
    sub = struct.pack('>7H', 4, 16 + 8 * n, 0, 2 * n, 2 * p, int(math.log2(n)), 2 * n - 2 * p)
    sub += struct.pack(f'>{n}H', *[s[1] for s in segs]) + b'\0\0' + struct.pack(f'>{n}H', *[s[0] for s in segs])
    sub += struct.pack(f'>{n}H', *[s[2] for s in segs]) + b'\0\0' * n
    return struct.pack('>HHHHIHHI', 0, 2, 0, 3, 20, 3, 1, 20) + sub

def remap(rec, add):
    """Shift the component glyph ids of a composite glyph record by add."""
    if not rec or struct.unpack('>h', rec[:2])[0] >= 0: return rec
    b, i = bytearray(rec), 10
    while True:
        fl, g = struct.unpack('>HH', b[i:i + 4]); b[i + 2:i + 4] = struct.pack('>H', g + add)
        i += 4 + (4 if fl & 1 else 2) + (2 if fl & 8 else 4 if fl & 0x40 else 8 if fl & 0x80 else 0)
        if not fl & 0x20: return bytes(b)

def checksum(b):
    b += b'\0' * (-len(b) % 4)
    return sum(struct.unpack(f'>{len(b) // 4}I', b)) & 0xFFFFFFFF

def merge(a, b):
    """Latin font a plus every glyph of latin-ext font b that a lacks."""
    na, ca, cb = len(a['glyf']), cmap(a), cmap(b)
    hint = all(a.get(k) == b.get(k) for k in ('fpgm', 'prep', 'cvt '))
    glyphs = a['glyf'] + [remap(g, na) for g in b['glyf']]
    if not hint: glyphs = [strip(g) for g in glyphs]
    m = dict(ca); m.update({c: g + na for c, g in cb.items() if c not in ca})
    if max(m) > 0xFFFF: raise ValueError('characters outside the BMP need a format 12 cmap')
    met = hmtx(a) + hmtx(b)
    t = {k: a[k] for k in KEEP if k in a and (hint or k not in ('fpgm', 'prep', 'cvt '))}
    glyf, loca = b'', []
    for g in glyphs:
        loca.append(len(glyf)); glyf += g + b'\0' * (-len(g) % 4)
    loca.append(len(glyf))
    t['glyf'], t['loca'], t['cmap'] = glyf, struct.pack(f'>{len(loca)}I', *loca), cmap4(m)
    t['hmtx'] = b''.join(struct.pack('>Hh', w, l) for w, l in met)
    hh = bytearray(a['hhea']); hh[34:36] = struct.pack('>H', len(met)); hh[10:12] = struct.pack('>H', max(w for w, _ in met))
    for k, f in ((12, min), (14, min), (16, max)):  # minLeftSideBearing, minRightSideBearing, xMaxExtent
        hh[k:k + 2] = struct.pack('>h', f(struct.unpack('>h', a['hhea'][k:k + 2])[0], struct.unpack('>h', b['hhea'][k:k + 2])[0]))
    t['hhea'] = bytes(hh)
    mp = bytearray(a['maxp']); mp[4:6] = struct.pack('>H', len(glyphs))
    for k in range(6, min(len(a['maxp']), len(b['maxp'])), 2):
        mp[k:k + 2] = struct.pack('>H', max(struct.unpack('>H', a['maxp'][k:k + 2])[0], struct.unpack('>H', b['maxp'][k:k + 2])[0]))
    t['maxp'] = bytes(mp)
    hd = bytearray(a['head']); hd[8:12] = b'\0' * 4; hd[50:52] = struct.pack('>h', 1)
    for k, f in ((36, min), (38, min), (40, max), (42, max)):
        hd[k:k + 2] = struct.pack('>h', f(struct.unpack('>h', a['head'][k:k + 2])[0], struct.unpack('>h', b['head'][k:k + 2])[0]))
    t['head'] = bytes(hd)
    os2 = bytearray(a['OS/2'])
    for k in range(42, 58, 4):  # ulUnicodeRange1-4
        os2[k:k + 4] = struct.pack('>I', struct.unpack('>I', a['OS/2'][k:k + 4])[0] | struct.unpack('>I', b['OS/2'][k:k + 4])[0])
    os2[64:68] = struct.pack('>HH', min(m), min(max(m), 0xFFFF))
    t['OS/2'] = bytes(os2)
    t['post'] = struct.pack('>I', 0x30000) + a['post'][4:32]
    return t

def strip(g):
    """Drop the hinting instructions of a glyph record (used only when the two subsets carry different hinting programs)."""
    if not g: return g
    k = struct.unpack('>h', g[:2])[0]
    if k < 0:
        b, i = bytearray(g), 10
        while True:
            fl = struct.unpack('>H', b[i:i + 2])[0]; b[i:i + 2] = struct.pack('>H', fl & ~0x100)
            i += 4 + (4 if fl & 1 else 2) + (2 if fl & 8 else 4 if fl & 0x40 else 8 if fl & 0x80 else 0)
            if not fl & 0x20: return bytes(b[:i])
    o = 10 + 2 * k; il = struct.unpack('>H', g[o:o + 2])[0]
    return g[:o] + b'\0\0' + g[o + 2 + il:]

def sfnt(t):
    tags = sorted(t); n = len(tags); p = 2 ** int(math.log2(n))
    head = struct.pack('>IHHHH', 0x10000, n, 16 * p, int(math.log2(n)), 16 * n - 16 * p)
    off, body, dirs = 12 + 16 * n, b'', b''
    for k in tags:
        d = t[k]; dirs += struct.pack('>4sIII', k.encode('latin-1'), checksum(d), off + len(body), len(d))
        body += d + b'\0' * (-len(d) % 4)
    font = bytearray(head + dirs + body)
    h = struct.unpack('>I', dirs[16 * tags.index('head') + 8:16 * tags.index('head') + 12])[0]
    font[h + 8:h + 12] = struct.pack('>I', (0xB1B0AFBA - checksum(bytes(font))) & 0xFFFFFFFF)
    return bytes(font)

def main():
    for out, stem in FONTS.items():
        t = merge(woff2(HERE / f"{stem.format('latin')}.woff2"), woff2(HERE / f"{stem.format('latin-ext')}.woff2"))
        data = sfnt(t)
        (OUT / out).write_bytes(data)
        print(f'{out}: {len(cmap(t))} characters, {struct.unpack(">H", t["maxp"][4:6])[0]} glyphs, {len(data)} bytes')

if __name__ == '__main__':
    main()
