#!/usr/bin/env python3
"""
PPT Master - Inspect the slides of a reference .pptx for layout extraction.

Writes, for the chosen pages:
  shapes.json   every shape flattened out of its groups, in 1280x720 canvas px:
                position, size, rotation/flip, preset or custom geometry (path
                normalized to 0..1), fill / gradient / alpha, line, text, font
                size (pt and px), bold, text color, typeface, placeholder flag
  wire/pNN.svg  a colored wireframe of each page, drawn from shapes.json
  render/pNN.png
                the real rendering, via macOS Quick Look (--render, macOS only).
                Each page is rendered from a temporary copy of the deck that
                lists it first; the input file is never modified.
  index.html    render and wireframe side by side for every page

Quick Look draws neither rotated custom shapes nor some gradients; read their
geometry from shapes.json (rot, flip, path) instead of trusting the render.
It also hangs on some generated decks; each page has a time limit.

Usage:
    python3 scripts/pptx_inspect.py <deck.pptx> -o <out_dir>
    python3 scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
CANVAS_W, CANVAS_H = 1280, 720
SCHEME_ALIASES = {'tx1': 'dk1', 'bg1': 'lt1', 'tx2': 'dk2', 'bg2': 'lt2'}


def q(tag):
    p, t = tag.split(':')
    return f'{{{NS[p]}}}{t}'


def parse_pages(spec, total):
    if not spec:
        return list(range(1, total + 1))
    out = []
    for part in spec.split(','):
        a, _, b = part.partition('-')
        out += range(int(a), int(b or a) + 1)
    return [n for n in out if 1 <= n <= total]


class Deck:
    def __init__(self, path: Path):
        self.z = zipfile.ZipFile(path)
        pres = ET.fromstring(self.z.read('ppt/presentation.xml'))
        sz = pres.find('p:sldSz', NS)
        self.cx, self.cy = int(sz.get('cx')), int(sz.get('cy'))
        rels = ET.fromstring(self.z.read('ppt/_rels/presentation.xml.rels'))
        rid_target = {r.get('Id'): r.get('Target') for r in rels}
        self.slides = ['ppt/' + rid_target[s.get(q('r:id'))].lstrip('/').replace('ppt/', '')
                       for s in pres.find('p:sldIdLst', NS)]
        self.scheme = {}
        try:
            theme = self.z.read('ppt/theme/theme1.xml').decode('utf-8', 'ignore')
            for m in re.finditer(r'<a:(dk1|lt1|dk2|lt2|accent\d|hlink|folHlink)>\s*<a:(?:srgbClr val="(\w{6})"|'
                                 r'sysClr[^>]*lastClr="(\w{6})")', theme):
                self.scheme[m.group(1)] = '#' + (m.group(2) or m.group(3)).upper()
        except KeyError:
            pass

    def color(self, el):
        """(hex, alpha%) for the first srgbClr/schemeClr under el."""
        if el is None:
            return None, None
        for c in el.iter():
            tag = c.tag.split('}')[-1]
            if tag in ('srgbClr', 'schemeClr'):
                val = c.get('val')
                hexv = '#' + val.upper() if tag == 'srgbClr' else self.scheme.get(SCHEME_ALIASES.get(val, val), f'scheme:{val}')
                a = c.find('a:alpha', NS)
                return hexv, (int(a.get('val')) // 1000 if a is not None else None)
        return None, None

    def layout_name(self, slide_part):
        rels = slide_part.replace('slides/', 'slides/_rels/') + '.rels'
        m = re.search(r'slideLayouts/(slideLayout\d+\.xml)', self.z.read(rels).decode('utf-8', 'ignore'))
        if not m:
            return ''
        root = ET.fromstring(self.z.read(f'ppt/slideLayouts/{m.group(1)}'))
        csld = root.find('p:cSld', NS)
        return f'{m.group(1)} "{csld.get("name", "")}"'

    def shapes(self, slide_part):
        root = ET.fromstring(self.z.read(slide_part))
        out = []
        self._walk(root.find('p:cSld/p:spTree', NS), (1.0, 1.0, 0.0, 0.0), out)
        return out

    def _walk(self, node, t, out):
        sx, sy, tx, ty = t
        for ch in node:
            tag = ch.tag.split('}')[-1]
            if tag == 'grpSp':
                x = ch.find('p:grpSpPr/a:xfrm', NS)
                inner = t
                if x is not None:
                    o, e, co, ce = (x.find(f'a:{k}', NS) for k in ('off', 'ext', 'chOff', 'chExt'))
                    if None not in (o, e, co, ce) and int(ce.get('cx')) and int(ce.get('cy')):
                        gx, gy = int(e.get('cx')) / int(ce.get('cx')), int(e.get('cy')) / int(ce.get('cy'))
                        inner = (sx * gx, sy * gy, tx + sx * (int(o.get('x')) - int(co.get('x')) * gx),
                                 ty + sy * (int(o.get('y')) - int(co.get('y')) * gy))
                self._walk(ch, inner, out)
            elif tag in ('sp', 'pic', 'cxnSp', 'graphicFrame'):
                rec = self._shape(ch, tag, t)
                if rec:
                    out.append(rec)

    def _shape(self, ch, tag, t):
        sx, sy, tx, ty = t
        x = ch.find('p:xfrm', NS) if tag == 'graphicFrame' else ch.find('p:spPr/a:xfrm', NS)
        if x is None:
            return None
        o, e = x.find('a:off', NS), x.find('a:ext', NS)
        if o is None or e is None:
            return None
        kx, ky = CANVAS_W / self.cx, CANVAS_H / self.cy
        rec = {'kind': tag,
               'x': round((int(o.get('x')) * sx + tx) * kx), 'y': round((int(o.get('y')) * sy + ty) * ky),
               'w': round(int(e.get('cx')) * sx * kx), 'h': round(int(e.get('cy')) * sy * ky)}
        if x.get('rot'):
            rec['rot'] = round(int(x.get('rot')) / 60000, 1)
        if x.get('flipH') == '1' or x.get('flipV') == '1':
            rec['flip'] = ('H' if x.get('flipH') == '1' else '') + ('V' if x.get('flipV') == '1' else '')
        sp = ch.find('p:spPr', NS)
        if sp is not None:
            g = sp.find('a:prstGeom', NS)
            if g is not None:
                rec['geom'] = g.get('prst')
            cg = sp.find('a:custGeom', NS)
            if cg is not None:
                rec['geom'] = 'custom'
                rec['path'] = self._path(cg)
            sf = sp.find('a:solidFill', NS)
            if sf is not None:
                rec['fill'], alpha = self.color(sf)
                if alpha is not None:
                    rec['alpha'] = alpha
            gf = sp.find('a:gradFill', NS)
            if gf is not None:
                rec['grad'] = [self.color(gs)[0] for gs in gf.findall('a:gsLst/a:gs', NS)][:4]
            ln = sp.find('a:ln', NS)
            if ln is not None and ln.find('a:noFill', NS) is None:
                lc, _ = self.color(ln.find('a:solidFill', NS))
                if lc:
                    rec['line'] = lc
        if ch.find('.//p:ph', NS) is not None:
            rec['placeholder'] = True
        text = ''.join(tt.text or '' for tt in ch.iter(q('a:t'))).strip()
        if text:
            rec['text'] = text[:120]
            for r in ch.iter(q('a:rPr')):
                if r.get('sz') and 'pt' not in rec:
                    rec['pt'] = int(r.get('sz')) / 100
                    rec['px'] = round(rec['pt'] * CANVAS_H / 540, 1)
                if r.get('b') == '1':
                    rec['bold'] = True
                if 'color' not in rec:
                    c, _ = self.color(r.find('a:solidFill', NS))
                    if c:
                        rec['color'] = c
                if 'font' not in rec:
                    for f in ('a:ea', 'a:latin'):
                        tf = r.find(f, NS)
                        if tf is not None and not tf.get('typeface', '').startswith('+'):
                            rec['font'] = tf.get('typeface')
                            break
        return rec

    @staticmethod
    def _path(cg):
        out = []
        for p in cg.findall('.//a:path', NS):
            pw, ph = float(p.get('w') or 1) or 1, float(p.get('h') or 1) or 1
            cmds = []
            for c in p:
                pts = [(float(pt.get('x')) / pw, float(pt.get('y')) / ph) for pt in c.findall('a:pt', NS)]
                cmds.append(c.tag.split('}')[-1][0].upper() + ' '.join(f'{a:.3f},{b:.3f}' for a, b in pts))
            out.append(' '.join(cmds))
        return out


def wireframe(page, shapes):
    b = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><rect width="1280" height="720" fill="#FFFFFF"/>']
    for s in shapes:
        x, y, w, h = s['x'], s['y'], s['w'], s['h']
        fill = s.get('fill') or (s.get('grad') or [None])[0]
        fill = fill if fill and fill.startswith('#') else None
        op = f' fill-opacity="{s["alpha"] / 100:.2f}"' if 'alpha' in s else ''
        rot = f' transform="rotate({s["rot"]} {x + w / 2} {y + h / 2})"' if s.get('rot') else ''
        if s['kind'] == 'pic':
            b.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#DDE3EE" stroke="#8795B0"{rot}/>'
                     f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y + h}" stroke="#8795B0"/>')
        elif s['kind'] == 'cxnSp':
            b.append(f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y + h}" stroke="{s.get("line", "#999999")}"/>')
        elif fill or s.get('line') or s.get('geom') == 'custom':
            dash = ' stroke-dasharray="4,3"' if s.get('geom') == 'custom' else ''
            stroke = s.get('line') or ('#8795B0' if s.get('geom') == 'custom' else 'none')
            shape = 'ellipse' if s.get('geom') in ('ellipse', 'donut') else 'rect'
            if shape == 'ellipse':
                b.append(f'<ellipse cx="{x + w / 2}" cy="{y + h / 2}" rx="{w / 2}" ry="{h / 2}" fill="{fill or "none"}"{op} '
                         f'stroke="{stroke}"{dash}{rot}/>')
            else:
                rx = ' rx="6"' if s.get('geom') == 'roundRect' else ''
                b.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"{rx} fill="{fill or "none"}"{op} '
                         f'stroke="{stroke}"{dash}{rot}/>')
        if s.get('text'):
            fs = min(max(int(s.get('px', 16)), 9), 48)
            weight = 'bold' if s.get('bold') else 'normal'
            b.append(f'<text x="{x + 3}" y="{y + fs + 1}" font-size="{fs}" font-family="PingFang SC, sans-serif" '
                     f'font-weight="{weight}" fill="{s.get("color", "#222222")}">{html.escape(s["text"][:40])}</text>')
    b.append(f'<text x="1240" y="30" font-size="24" text-anchor="end" fill="#E03030">P{page}</text></svg>')
    return '\n'.join(b)


def render_pages(src: Path, deck: Deck, pages, out_dir: Path, timeout: int):
    if sys.platform != 'darwin' or not shutil.which('qlmanage'):
        print('[WARN] --render needs macOS Quick Look (qlmanage); skipped.', file=sys.stderr)
        return set()
    pres = deck.z.read('ppt/presentation.xml').decode('utf-8')
    m = re.search(r'(<p:sldIdLst>)(.*?)(</p:sldIdLst>)', pres, re.S)
    ids = re.findall(r'<p:sldId\b[^>]*/>', m.group(2))
    done = set()
    with tempfile.TemporaryDirectory(prefix='pptx_inspect_') as td:
        for page in pages:
            order = [ids[page - 1]] + [x for i, x in enumerate(ids) if i != page - 1]
            new = pres[:m.start(2)] + ''.join(order) + pres[m.end(2):]
            tmp = Path(td) / f'p{page:02d}.pptx'
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as o:
                for info in deck.z.infolist():
                    data = new.encode('utf-8') if info.filename == 'ppt/presentation.xml' else deck.z.read(info.filename)
                    o.writestr(info.filename, data)
            try:
                subprocess.run(['qlmanage', '-t', '-s', '1600', '-o', td, str(tmp)],
                               capture_output=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                subprocess.run(['pkill', '-f', 'qlmanage'], capture_output=True)
                print(f'[WARN] P{page}: Quick Look timed out', file=sys.stderr)
            png = Path(td) / f'{tmp.name}.png'
            if png.exists():
                shutil.move(str(png), out_dir / f'p{page:02d}.png')
                done.add(page)
            else:
                print(f'[WARN] P{page}: no render produced', file=sys.stderr)
            tmp.unlink(missing_ok=True)
    return done


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pptx', type=Path)
    ap.add_argument('-o', '--out', type=Path, required=True, help='Output directory')
    ap.add_argument('--pages', help='Pages to inspect, e.g. "12-35" or "3,5,9-11" (default: all)')
    ap.add_argument('--render', action='store_true', help='Also render real page images (macOS Quick Look)')
    ap.add_argument('--timeout', type=int, default=90, help='Seconds allowed per page render (default 90)')
    args = ap.parse_args()

    if not args.pptx.exists():
        print(f'[ERROR] not found: {args.pptx}', file=sys.stderr)
        return 1
    deck = Deck(args.pptx)
    pages = parse_pages(args.pages, len(deck.slides))
    (args.out / 'wire').mkdir(parents=True, exist_ok=True)

    data = {'meta': {'source': args.pptx.name, 'slides': len(deck.slides), 'slide_emu': [deck.cx, deck.cy],
                     'canvas': [CANVAS_W, CANVAS_H], 'theme': deck.scheme}, 'pages': {}}
    for page in pages:
        part = deck.slides[page - 1]
        shapes = deck.shapes(part)
        data['pages'][str(page)] = {'layout': deck.layout_name(part), 'shapes': shapes}
        (args.out / 'wire' / f'p{page:02d}.svg').write_text(wireframe(page, shapes), encoding='utf-8')
    (args.out / 'shapes.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')

    rendered = set()
    if args.render:
        (args.out / 'render').mkdir(exist_ok=True)
        rendered = render_pages(args.pptx, deck, pages, args.out / 'render', args.timeout)

    cells = []
    for page in pages:
        img = f'<img src="render/p{page:02d}.png">' if page in rendered else '<div class="none">no render</div>'
        cells.append(f'<section><h3>P{page} · {html.escape(data["pages"][str(page)]["layout"])}</h3>'
                     f'<div class="pair">{img}<img src="wire/p{page:02d}.svg"></div></section>')
    (args.out / 'index.html').write_text(
        '<!doctype html><meta charset="utf-8"><title>pptx_inspect</title><style>'
        'body{font:13px sans-serif;margin:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:6px}'
        'img,.none{width:100%;border:1px solid #bbb;aspect-ratio:16/9;object-fit:contain}'
        '.none{display:flex;align-items:center;justify-content:center;color:#999}</style>'
        + ''.join(cells), encoding='utf-8')

    total = sum(len(v['shapes']) for v in data['pages'].values())
    print(f'[OK] {len(pages)} page(s), {total} shapes -> {args.out / "shapes.json"}')
    if args.render:
        print(f'[OK] {len(rendered)}/{len(pages)} page(s) rendered -> {args.out / "render"}')
    print(f'[OK] contact sheet -> {args.out / "index.html"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
