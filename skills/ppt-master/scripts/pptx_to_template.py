#!/usr/bin/env python3
"""
PPT Master - Convert a user-supplied .pptx into a ppt-master layout template.

When the user says "use this deck as the template", the deck's *slide layouts*
carry the design: full-bleed background art, logos, and the exact geometry the
brand expects. This script lifts those out and writes the four standard
template SVGs plus the brand assets, so the Executor's normal
"template as base layer" rule reproduces the look instead of approximating it.

What it does:
  1. Unpacks the .pptx and reads theme colours + fonts.
  2. Picks the best-matching layout for each standard page type
     (cover / chapter / content / ending) by name, then by artwork.
  3. Extracts every <p:pic> on that layout with its EMU geometry, converts to
     the 1280x720 canvas, and writes a template SVG referencing ../images/.
  4. Copies the referenced media into the project's images/ (downsampled to
     2x canvas by default -- template art is routinely 3-4x oversized).
  5. Writes templates/design_spec.md documenting the extracted palette.

Usage:
    python3 scripts/pptx_to_template.py <template.pptx> <project_path>
    python3 scripts/pptx_to_template.py <template.pptx> <project_path> --no-downsample
"""
import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

EMU_PER_IN = 914400
CANVAS_W, CANVAS_H = 1280, 720

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

# Layout name hints -> standard page type. Chinese first: these decks are
# overwhelmingly authored in PowerPoint/WPS zh-CN.
TYPE_HINTS = {
    'cover':   ['标题幻灯片', '封面', 'title slide', 'cover'],
    'chapter': ['节标题', '章节', 'section', 'divider'],
    'content': ['标题和内容', '内容', 'content', 'title and content'],
    'ending':  ['末尾幻灯片', '结束', '尾页', 'ending', 'closing', 'thank'],
}

STANDARD_FILES = {
    'cover': '01_cover.svg',
    'chapter': '02_chapter.svg',
    'content': '03_content.svg',
    'ending': '04_ending.svg',
}


def emu_to_px(v, axis='x'):
    scale = CANVAS_W / (13.3333333) if axis == 'x' else CANVAS_H / 7.5
    return round(int(v) / EMU_PER_IN * scale)


def parse_rels(z, layout_name):
    """rId -> media filename for one slide layout."""
    rels_path = f'ppt/slideLayouts/_rels/{layout_name}.rels'
    out = {}
    try:
        xml = z.read(rels_path)
    except KeyError:
        return out
    for rel in ET.fromstring(xml):
        tgt = rel.get('Target', '')
        if '/media/' in tgt or tgt.startswith('../media/'):
            out[rel.get('Id')] = tgt.rsplit('/', 1)[-1]
    return out


def layout_pictures(z, layout_file):
    """Every picture on a layout, as (media_filename, x, y, w, h) in canvas px."""
    rmap = parse_rels(z, layout_file)
    root = ET.fromstring(z.read(f'ppt/slideLayouts/{layout_file}'))
    pics = []
    for pic in root.iter(f'{{{NS["p"]}}}pic'):
        blip = pic.find(f'.//{{{NS["a"]}}}blip')
        # Read geometry from the shape's own <a:xfrm>, not any nested one --
        # nested <a:ext> elements (effects, crops) lack cx/cy.
        xfrm = pic.find(f'{{{NS["p"]}}}spPr/{{{NS["a"]}}}xfrm')
        off = xfrm.find(f'{{{NS["a"]}}}off') if xfrm is not None else None
        ext = xfrm.find(f'{{{NS["a"]}}}ext') if xfrm is not None else None
        if blip is None or off is None or ext is None:
            continue
        if ext.get('cx') is None or off.get('x') is None:
            continue
        rid = blip.get(f'{{{NS["r"]}}}embed')
        media = rmap.get(rid)
        if not media:
            continue
        pics.append({
            'media': media,
            'x': emu_to_px(off.get('x'), 'x'),
            'y': emu_to_px(off.get('y'), 'y'),
            'w': emu_to_px(ext.get('cx'), 'x'),
            'h': emu_to_px(ext.get('cy'), 'y'),
        })
    return pics


def layout_display_name(z, layout_file):
    root = ET.fromstring(z.read(f'ppt/slideLayouts/{layout_file}'))
    csld = root.find(f'{{{NS["p"]}}}cSld')
    return (csld.get('name') if csld is not None else '') or ''


def theme_info(z):
    """Extract the theme palette and fonts, best-effort."""
    colors, fonts = {}, {}
    try:
        xml = z.read('ppt/theme/theme1.xml').decode('utf-8', 'ignore')
    except KeyError:
        return colors, fonts
    scheme = re.search(r'<a:clrScheme.*?</a:clrScheme>', xml, re.S)
    if scheme:
        for m in re.finditer(r'<a:(\w+)>\s*<a:(?:srgbClr val="([0-9A-Fa-f]{6})"|'
                             r'sysClr[^>]*lastClr="([0-9A-Fa-f]{6})")', scheme.group(0)):
            role, a, b = m.group(1), m.group(2), m.group(3)
            colors[role] = f'#{(a or b).upper()}'
    fs = re.search(r'<a:fontScheme.*?</a:fontScheme>', xml, re.S)
    if fs:
        major = re.search(r'<a:majorFont>.*?<a:ea typeface="([^"]*)"', fs.group(0), re.S)
        minor = re.search(r'<a:minorFont>.*?<a:ea typeface="([^"]*)"', fs.group(0), re.S)
        latin = re.search(r'<a:minorFont>.*?<a:latin typeface="([^"]*)"', fs.group(0), re.S)
        fonts['major'] = (major.group(1) if major else '') or 'Microsoft YaHei'
        fonts['minor'] = (minor.group(1) if minor else '') or 'Microsoft YaHei'
        fonts['latin'] = (latin.group(1) if latin else '') or 'Arial'
    return colors, fonts


def pick_layouts(z):
    """Map each standard page type to the most suitable layout file."""
    files = sorted((n.rsplit('/', 1)[-1] for n in z.namelist()
                    if re.fullmatch(r'ppt/slideLayouts/slideLayout\d+\.xml', n)),
                   key=lambda s: int(re.search(r'(\d+)', s).group(1)))
    named = [(f, layout_display_name(z, f), layout_pictures(z, f)) for f in files]

    chosen = {}
    for ptype, hints in TYPE_HINTS.items():
        for f, name, pics in named:
            if any(h.lower() in name.lower() for h in hints) and pics:
                chosen[ptype] = (f, name, pics)
                break
    # Fallback: any layout carrying a full-bleed background we haven't used.
    used = {v[0] for v in chosen.values()}
    for ptype in TYPE_HINTS:
        if ptype in chosen:
            continue
        for f, name, pics in named:
            if f in used or not pics:
                continue
            if any(p['w'] >= CANVAS_W * 0.95 for p in pics):
                chosen[ptype] = (f, name, pics)
                used.add(f)
                break
    return chosen


def downsample(path: Path, max_px: int):
    """Shrink oversized template art in place (macOS sips; skipped elsewhere)."""
    if not shutil.which('sips'):
        return
    try:
        subprocess.run(['sips', '-Z', str(max_px), str(path), '--out', str(path)],
                       capture_output=True, timeout=120, check=False)
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pptx', type=Path, help='Template .pptx to convert')
    ap.add_argument('project_path', type=Path, help='Target project directory')
    ap.add_argument('--max-px', type=int, default=CANVAS_W * 2,
                    help='Downsample template art to this width (default 2560; 0 = keep original)')
    args = ap.parse_args()

    if not args.pptx.exists():
        print(f'[ERROR] Template not found: {args.pptx}', file=sys.stderr)
        return 1
    proj = args.project_path
    if not proj.is_dir():
        print(f'[ERROR] Project directory not found: {proj}', file=sys.stderr)
        return 1

    tpl_dir = proj / 'templates'
    img_dir = proj / 'images'
    tpl_dir.mkdir(exist_ok=True)
    img_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(args.pptx) as z:
        colors, fonts = theme_info(z)
        chosen = pick_layouts(z)
        if not chosen:
            print('[ERROR] No usable slide layouts with artwork found in this .pptx.',
                  file=sys.stderr)
            print('        Its design may live on the slides themselves rather than '
                  'the layouts; extract manually in that case.', file=sys.stderr)
            return 1

        exported = {}
        for ptype, (lfile, lname, pics) in sorted(chosen.items()):
            svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                   f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                   f'width="{CANVAS_W}" height="{CANVAS_H}" '
                   f'viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
                   f'  <!-- Extracted from {args.pptx.name} :: {lname} ({lfile}) -->',
                   '  <!-- Base layer: copy these <image> tags verbatim into every page -->']
            for p in pics:
                src = f'tpl_{ptype}_{Path(p["media"]).stem}{Path(p["media"]).suffix}'
                dst = img_dir / src
                if not dst.exists():
                    dst.write_bytes(z.read(f'ppt/media/{p["media"]}'))
                    if args.max_px:
                        downsample(dst, args.max_px)
                    exported[src] = dst.stat().st_size
                fit = 'none' if p['w'] >= CANVAS_W * 0.95 else 'xMidYMid meet'
                svg.append(f'  <image href="../images/{src}" x="{p["x"]}" y="{p["y"]}" '
                           f'width="{p["w"]}" height="{p["h"]}" preserveAspectRatio="{fit}"/>')
            svg.append('</svg>')
            out = tpl_dir / STANDARD_FILES[ptype]
            out.write_text('\n'.join(svg) + '\n', encoding='utf-8')
            print(f'[OK] {out.name:<16} <- {lname} ({len(pics)} image(s))')

    accent = colors.get('accent1', '#1268E3')
    spec = [
        f'# Template extracted from {args.pptx.name}',
        '',
        '> Generated by pptx_to_template.py. The SVGs in this directory are the',
        '> mandatory base layer for every generated page -- copy their <image>',
        '> tags verbatim; do not redraw backgrounds or re-place logos.',
        '',
        '## Canvas', '',
        f'- viewBox: `0 0 {CANVAS_W} {CANVAS_H}` (16:9)', '',
        '## Theme colors', '',
        '| Role | HEX |', '|------|-----|',
    ]
    for role in ('dk1', 'lt1', 'dk2', 'lt2', 'accent1', 'accent2', 'accent3',
                 'accent4', 'accent5', 'accent6'):
        if role in colors:
            spec.append(f'| {role} | `{colors[role]}` |')
    spec += ['', '## Fonts', '',
             f'- Heading: {fonts.get("major", "Microsoft YaHei")}',
             f'- Body: {fonts.get("minor", "Microsoft YaHei")}',
             f'- Latin: {fonts.get("latin", "Arial")}', '',
             '## Page types', '']
    for ptype, (lfile, lname, pics) in sorted(chosen.items()):
        spec.append(f'- **{ptype}** -> `{STANDARD_FILES[ptype]}` (from "{lname}", {len(pics)} image(s))')
    spec += ['', '## Suggested accent', '', f'Primary accent from theme: `{accent}`', '']
    (tpl_dir / 'design_spec.md').write_text('\n'.join(spec) + '\n', encoding='utf-8')

    print(f'[OK] templates/design_spec.md written ({len(colors)} theme colors)')
    if exported:
        total = sum(exported.values()) / 1024
        print(f'[OK] {len(exported)} brand asset(s) -> images/  ({total:.0f} KB total)')
    print()
    print('Next: run the Executor with these templates as the base layer for every page.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
