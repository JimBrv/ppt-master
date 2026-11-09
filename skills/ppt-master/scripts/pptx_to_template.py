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
  2. Picks the layout for each standard page type (cover / toc / chapter /
     content / ending) by name, preferring the one the deck's slides really use.
  3. Extracts the layout's art -- its <p:bg> picture fill (or the master's when
     the layout has none), the master's pictures, and its own <p:pic>s --
     converts to the 1280x720 canvas, and writes SVGs referencing ../images/.
  4. Copies the referenced media into the project's images/ (downsampled to
     2x canvas by default -- template art is routinely 3-4x oversized).
  5. Writes templates/design_spec.md documenting the extracted palette.

Usage:
    python3 scripts/pptx_to_template.py <template.pptx> <project_path>
    python3 scripts/pptx_to_template.py <template.pptx> <project_path> --no-downsample
"""
import argparse
import collections
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
    'toc':     ['目录', 'contents', 'agenda'],
    'chapter': ['节标题', '章节', 'section', 'divider'],
    'content': ['内板', '纯文字', '标题和内容', '内容', 'content', 'title and content'],
    'ending':  ['末尾幻灯片', '结束', '尾页', '感谢', 'ending', 'closing', 'thank'],
}
# Whole-name matches only: "标题" is a substring of "标题幻灯片" and "标题和内容".
EXACT_HINTS = {'chapter': ['标题']}
REQUIRED_TYPES = ('cover', 'chapter', 'content', 'ending')

STANDARD_FILES = {
    'cover': '01_cover.svg',
    'toc': '02_toc.svg',
    'chapter': '02_chapter.svg',
    'content': '03_content.svg',
    'ending': '04_ending.svg',
}

# What finalize_svg.py can embed; EMF/WMF/TIFF art would be left dangling.
SUPPORTED_MEDIA = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


def slide_size(z):
    sz = ET.fromstring(z.read('ppt/presentation.xml')).find('p:sldSz', NS)
    return int(sz.get('cx')), int(sz.get('cy'))


def parse_rels(z, part):
    """(rId -> media filename, master part path) for a layout or master part."""
    directory, name = part.rsplit('/', 1)
    media, master = {}, None
    try:
        xml = z.read(f'{directory}/_rels/{name}.rels')
    except KeyError:
        return media, master
    for rel in ET.fromstring(xml):
        tgt = rel.get('Target', '')
        if '/media/' in tgt:
            media[rel.get('Id')] = tgt.rsplit('/', 1)[-1]
        elif 'slideMasters/' in tgt:
            master = 'ppt/slideMasters/' + tgt.rsplit('/', 1)[-1]
    return media, master


def walk_pictures(node, rmap, size, t=(1.0, 1.0, 0.0, 0.0)):
    """Every <p:pic> below node in canvas px; t maps child EMU to slide EMU."""
    cx, cy = size
    sx, sy, tx, ty = t
    pics = []
    for child in node:
        tag = child.tag.rsplit('}', 1)[-1]
        if tag == 'grpSp':
            xfrm = child.find('p:grpSpPr/a:xfrm', NS)
            inner = t
            if xfrm is not None:
                off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
                ch_off, ch_ext = xfrm.find('a:chOff', NS), xfrm.find('a:chExt', NS)
                if None not in (off, ext, ch_off, ch_ext) and int(ch_ext.get('cx')) and int(ch_ext.get('cy')):
                    gx = int(ext.get('cx')) / int(ch_ext.get('cx'))
                    gy = int(ext.get('cy')) / int(ch_ext.get('cy'))
                    inner = (sx * gx, sy * gy,
                             tx + sx * (int(off.get('x')) - int(ch_off.get('x')) * gx),
                             ty + sy * (int(off.get('y')) - int(ch_off.get('y')) * gy))
            pics += walk_pictures(child, rmap, size, inner)
        elif tag == 'pic':
            blip = child.find('.//a:blip', NS)
            # The shape's own <a:xfrm>: nested <a:ext> (effects, crops) lack cx/cy.
            xfrm = child.find('p:spPr/a:xfrm', NS)
            if blip is None or xfrm is None:
                continue
            off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
            media = rmap.get(blip.get(f'{{{NS["r"]}}}embed'))
            if off is None or ext is None or not media or ext.get('cx') is None:
                continue
            pics.append({
                'media': media,
                'x': round((int(off.get('x')) * sx + tx) / cx * CANVAS_W),
                'y': round((int(off.get('y')) * sy + ty) / cy * CANVAS_H),
                'w': round(int(ext.get('cx')) * sx / cx * CANVAS_W),
                'h': round(int(ext.get('cy')) * sy / cy * CANVAS_H),
            })
    return pics


def background_art(root, rmap):
    """(part declares its own background?, [full-canvas picture fill, if any])."""
    bg = root.find('p:cSld/p:bg', NS)
    if bg is None:
        return False, []
    blip = bg.find('.//a:blip', NS)
    media = rmap.get(blip.get(f'{{{NS["r"]}}}embed')) if blip is not None else None
    if not media:
        return True, []
    crop = bg.find('.//a:srcRect', NS)
    return True, [{'media': media, 'x': 0, 'y': 0, 'w': CANVAS_W, 'h': CANVAS_H,
                   'cropped': crop is not None and any(int(v) for v in crop.attrib.values())}]


def layout_pictures(z, layout_file, size):
    """A layout's art, back to front: background, master pictures, own pictures."""
    part = f'ppt/slideLayouts/{layout_file}'
    root = ET.fromstring(z.read(part))
    rmap, master = parse_rels(z, part)
    has_bg, art = background_art(root, rmap)
    if master:
        master_root = ET.fromstring(z.read(master))
        master_rmap, _ = parse_rels(z, master)
        if not has_bg:
            art = background_art(master_root, master_rmap)[1]
        if root.get('showMasterSp', '1') != '0':
            art += walk_pictures(master_root.find('p:cSld/p:spTree', NS), master_rmap, size)
    return art + walk_pictures(root.find('p:cSld/p:spTree', NS), rmap, size)


def layout_display_name(z, layout_file):
    root = ET.fromstring(z.read(f'ppt/slideLayouts/{layout_file}'))
    csld = root.find('p:cSld', NS)
    return (csld.get('name') if csld is not None else '') or ''


def layout_usage(z):
    """layout filename -> number of slides built on it."""
    used = collections.Counter()
    for n in z.namelist():
        if re.fullmatch(r'ppt/slides/_rels/slide\d+\.xml\.rels', n):
            m = re.search(r'slideLayouts/(slideLayout\d+\.xml)', z.read(n).decode('utf-8', 'ignore'))
            if m:
                used[m.group(1)] += 1
    return used


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


def pick_layouts(z, size, usage):
    """Map page types to layouts: (ptype -> (file, name, pics), guessed ptypes)."""
    files = sorted((n.rsplit('/', 1)[-1] for n in z.namelist()
                    if re.fullmatch(r'ppt/slideLayouts/slideLayout\d+\.xml', n)),
                   key=lambda s: int(re.search(r'(\d+)', s).group(1)))
    named = [(f, layout_display_name(z, f), layout_pictures(z, f, size)) for f in files]

    def matches(ptype, name):
        low = name.strip().lower()
        return low in EXACT_HINTS.get(ptype, []) or any(h in low for h in TYPE_HINTS[ptype])

    chosen, used, guessed = {}, set(), []
    for ptype in TYPE_HINTS:
        cands = [n for n in named if n[2] and n[0] not in used and matches(ptype, n[1])]
        if cands:
            # Decks carry dead layouts; the one slides really use is the design.
            best = max(cands, key=lambda n: usage[n[0]])
            chosen[ptype] = best
            used.add(best[0])
    for ptype in REQUIRED_TYPES:
        if ptype in chosen:
            continue
        cands = [n for n in named if n[0] not in used
                 and any(p['w'] >= CANVAS_W * 0.95 for p in n[2])]
        if cands:
            best = max(cands, key=lambda n: usage[n[0]])
            chosen[ptype] = best
            used.add(best[0])
            guessed.append(ptype)
    return chosen, guessed


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
        size = slide_size(z)
        if abs(size[0] / size[1] - CANVAS_W / CANVAS_H) > 0.01:
            print(f'[WARN] Deck is {size[0]}x{size[1]} EMU, not 16:9; art will be stretched '
                  f'to {CANVAS_W}x{CANVAS_H}.', file=sys.stderr)
        colors, fonts = theme_info(z)
        usage = layout_usage(z)
        chosen, guessed = pick_layouts(z, size, usage)
        if 'content' not in chosen:
            print('[ERROR] No slide layout with background art or pictures can serve as '
                  'the content page.', file=sys.stderr)
            print('        Checked layout/master <p:bg> picture fills and <p:pic>s; any '
                  'vector-only design must be extracted by hand.', file=sys.stderr)
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
                if Path(p['media']).suffix.lower() not in SUPPORTED_MEDIA:
                    print(f'[WARN] {ptype}: skipped {p["media"]} (unsupported image format)',
                          file=sys.stderr)
                    continue
                if p.get('cropped'):
                    print(f'[WARN] {ptype}: background {p["media"]} is cropped in the deck; '
                          'exported uncropped, check it visually.', file=sys.stderr)
                src = f'tpl_{ptype}_{Path(p["media"]).stem}{Path(p["media"]).suffix}'
                dst = img_dir / src
                if src not in exported:
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
            print(f'[OK] {out.name:<16} <- {lname} ({len(pics)} image(s), '
                  f'used by {usage[lfile]} slide(s))')

        for ptype in guessed:
            print(f'[WARN] {ptype}: no layout name matched; guessed "{chosen[ptype][1]}". '
                  'Check it before generating.', file=sys.stderr)
        for ptype in REQUIRED_TYPES:
            if ptype not in chosen:
                print(f'[WARN] {ptype}: no layout found, {STANDARD_FILES[ptype]} not written.',
                      file=sys.stderr)

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
