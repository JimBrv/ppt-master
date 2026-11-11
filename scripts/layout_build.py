#!/usr/bin/env python3
"""
PPT Master - Build a template's content layouts from the shared library.

Combines templates/content_library/library.py (structure) with the
template's content_src/theme.json (colors, title capacity, body box) and
content_src/shell.svg (its own background, logo, title, page number), and
writes <template>/content/: one SVG per layout plus layouts.json.

Usage:
    python3 scripts/layout_build.py <template_dir>            # build content/
    python3 scripts/layout_build.py <template_dir> --check    # build to a temp dir and compare; writes nothing
    python3 scripts/layout_build.py --all [--check]           # every template that has content_src/
    python3 scripts/layout_build.py <template_dir> --init     # draft theme.json and shell.svg from 03_content.svg

After building, it reports layouts that overlap the theme's reserved areas
(logo, header, footer) and color roles with weak contrast. --init only
drafts: review both files, especially reserved areas and body_box, before
building.
"""
import argparse
import filecmp
import json
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent
LAYOUTS_ROOT = SKILL / 'templates' / 'layouts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SKILL / 'templates' / 'content_library'))
from layout_kit import Layout, Theme, conflicts, luminance, write_library  # noqa: E402

TOKENS = ('%%BODY%%', '%%DEFS%%', '%%LAYOUT_ID%%', '{{PAGE_TITLE}}', '{{PAGE_NUM}}')


def load_sources(tpl: Path):
    src = tpl / 'content_src'
    theme_path, shell_path = src / 'theme.json', src / 'shell.svg'
    if not theme_path.exists() or not shell_path.exists():
        raise FileNotFoundError(f'{src} needs theme.json and shell.svg (draft them with --init)')
    theme = Theme(json.loads(theme_path.read_text(encoding='utf-8')))
    shell = shell_path.read_text(encoding='utf-8')
    missing = [t for t in TOKENS if t not in shell]
    if missing:
        raise ValueError(f'{shell_path} is missing {missing}')
    return theme, shell


def build(tpl: Path, out: Path):
    import library
    theme, shell = load_sources(tpl)
    layouts = []
    for builder in library.BUILDERS:
        lay = Layout(builder.__name__, theme)
        builder(lay)
        layouts.append(lay)
    write_library(out, layouts, library.META, library.USAGE, shell)
    problems = [f'{lay.id}: {c}' for lay in layouts for c in conflicts(lay)]
    return problems, theme.contrast_warnings()


def report(tpl: Path, problems, warnings):
    for p in problems:
        print(f'  [CONFLICT] {p}')
    for w in warnings:
        print(f'  [CONTRAST] {w}')


def check(tpl: Path) -> bool:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'content'
        problems, warnings = build(tpl, out)
        current = tpl / 'content'
        built = {p.name for p in out.iterdir()}
        have = {p.name for p in current.iterdir()} if current.exists() else set()
        stale = sorted(n for n in built & have if not filecmp.cmp(out / n, current / n, shallow=False))
        missing, extra = sorted(built - have), sorted(have - built)
    ok = not (stale or missing or extra)
    print(f'[{"OK" if ok else "STALE"}] {tpl.name}: content/ {"matches" if ok else "differs from"} a fresh build')
    for label, names in (('changed', stale), ('missing', missing), ('not produced by the build', extra)):
        if names:
            print(f'  {label}: {", ".join(names)}')
    report(tpl, problems, warnings)
    return ok and not problems


# --------------------------------------------------------------------------
# --init: drafts from the template's own content page
# --------------------------------------------------------------------------

def _attr(tag, name, default=None):
    m = re.search(rf'\s{name}="([^"]*)"', tag)
    return m.group(1) if m else default


def _boxes(svg):
    """Rough (y0, y1) extents of rects, lines and texts, for the body box."""
    out = []
    for m in re.finditer(r'<(rect|line|text|image)\b[^>]*>', svg):
        tag, kind = m.group(0), m.group(1)
        try:
            if kind in ('rect', 'image'):
                w, h = float(_attr(tag, 'width', 0)), float(_attr(tag, 'height', 0))
                if w >= 1270 and h >= 700:
                    continue
                y = float(_attr(tag, 'y', 0))
                out.append((y, y + h))
            elif kind == 'line':
                out.append(tuple(sorted((float(_attr(tag, 'y1', 0)), float(_attr(tag, 'y2', 0))))))
            else:
                y, s = float(_attr(tag, 'y', 0)), float(_attr(tag, 'font-size', 16))
                out.append((y - s, y + s * 0.3))
        except ValueError:
            continue
    return out


def init(tpl: Path) -> int:
    page = tpl / '03_content.svg'
    if not page.exists():
        print(f'[ERROR] {page} not found', file=sys.stderr)
        return 1
    src = tpl / 'content_src'
    if (src / 'theme.json').exists() or (src / 'shell.svg').exists():
        print(f'[ERROR] {src} already has a theme.json or shell.svg; move them aside to redraft', file=sys.stderr)
        return 1
    svg = page.read_text(encoding='utf-8')
    svg = re.sub(r'<\?xml[^>]*\?>\s*', '', svg)
    svg = re.sub(r'<!--\s*CONTENT_AREA_START\s*-->.*?<!--\s*CONTENT_AREA_END\s*-->', '', svg, flags=re.S)
    removed = []

    def keep_or_drop(m):
        slots = re.findall(r'\{\{(\w+)\}\}', m.group(0))
        if 'PAGE_TITLE' in slots:
            return re.sub(r'>\s*\{\{PAGE_TITLE\}\}\s*</text>', '>{{PAGE_TITLE}}</text>', m.group(0))
        if 'PAGE_NUM' in slots:
            return re.sub(r'>[^<]*</text>', '>{{PAGE_NUM}}</text>', m.group(0))
        removed.extend(slots)
        return ''
    svg = re.sub(r'<text\b[^>]*>[^<]*\{\{\w+\}\}[^<]*</text>', keep_or_drop, svg, flags=re.S)
    svg = re.sub(r'\n\s*\n+', '\n', svg)
    if 'xmlns:xlink' not in svg:
        svg = svg.replace('<svg xmlns="http://www.w3.org/2000/svg"',
                          '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"', 1)
    open_tag = re.search(r'<svg\b[^>]*>\n?', svg)
    svg = (svg[:open_tag.end()].rstrip('\n') + '\n'
           f'  <!-- {tpl.name} content layout: %%LAYOUT_ID%%. Fill every slot; see layouts.json for capacity. -->\n'
           '%%DEFS%%' + svg[open_tag.end():].lstrip('\n'))
    num = re.search(r'[ \t]*<text\b[^>]*>\{\{PAGE_NUM\}\}</text>', svg)
    if num:
        svg = svg[:num.start()] + '%%BODY%%\n' + svg[num.start():]
    else:
        svg = svg.replace('</svg>', '%%BODY%%\n  <text x="1240" y="712" font-size="14" text-anchor="end" '
                                    'fill="#999999">{{PAGE_NUM}}</text>\n</svg>')
    if '{{PAGE_TITLE}}' not in svg:
        svg = svg.replace('%%BODY%%', '  <text x="60" y="80" font-size="32" font-weight="bold" fill="#222222">'
                                      '{{PAGE_TITLE}}</text>\n%%BODY%%')

    title = re.search(r'<text\b[^>]*>\{\{PAGE_TITLE\}\}</text>', svg).group(0)
    tx, tsize = float(_attr(title, 'x', 60)), float(_attr(title, 'font-size', 32))
    bg = re.search(r'<rect\b(?=[^>]*width="1280")(?=[^>]*height="720")[^>]*fill="(#[0-9A-Fa-f]{6})"', svg)
    page_bg = bg.group(1).upper() if bg else '#FFFFFF'
    fills = Counter(c.upper() for c in re.findall(r'(?:fill|stop-color)[=:]"?\s*(#[0-9A-Fa-f]{6})', svg))
    chroma = [c for c, _ in fills.most_common()
              if max(int(c[i:i + 2], 16) for i in (1, 3, 5)) - min(int(c[i:i + 2], 16) for i in (1, 3, 5)) > 60]
    primary = chroma[0] if chroma else '#2C7FEF'
    dark = luminance(page_bg) < 0.2
    ys = _boxes(svg.replace(title, ''))
    head = max([y1 for y0, y1 in ys if y1 <= 260] + [float(_attr(title, 'y', 80)) + tsize * 0.3])
    foot = min([y0 for y0, y1 in ys if y0 >= 600] + [705])
    theme = {
        'name': tpl.name,
        'font': _attr(title, 'font-family', 'Microsoft YaHei, SimHei, sans-serif'),
        'title_capacity': int((1220 - tx) / tsize),
        'body_box': [0, round(head + 12), 1280, round(foot - 8)],
        'reserved': [],
        'colors': {
            'primary': primary,
            'ink': _attr(title, 'fill', '#E6EDF3' if dark else '#1F2937'),
            'surface': '#161B22' if dark else '#FFFFFF',
            'page_bg': page_bg,
            'on_accent': '#0D1117' if dark else '#FFFFFF',
        },
    }
    src.mkdir(exist_ok=True)
    (src / 'shell.svg').write_text(svg, encoding='utf-8')
    (src / 'theme.json').write_text(json.dumps(theme, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'[DRAFT] {src / "shell.svg"}')
    print(f'[DRAFT] {src / "theme.json"}')
    if removed:
        print(f'  dropped placeholders the library does not fill: {", ".join(sorted(set(removed)))}')
    print('  Review before building:')
    print('  - shell.svg: delete static decorations that belong to the old content area (insight bars, guides)')
    print('  - theme.json: check primary, ink and surface; add series colors; set body_box and reserved areas')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('template_dir', type=Path, nargs='?')
    ap.add_argument('--all', action='store_true', help='Every template under templates/layouts with content_src/')
    ap.add_argument('--check', action='store_true', help='Compare a fresh build with content/ instead of writing')
    ap.add_argument('--init', action='store_true', help='Draft content_src/theme.json and shell.svg')
    args = ap.parse_args()

    if args.init:
        if not args.template_dir:
            ap.error('--init needs a template_dir')
        return init(args.template_dir)
    if args.all:
        targets = sorted(p.parent.parent for p in LAYOUTS_ROOT.glob('*/content_src/theme.json'))
    elif args.template_dir:
        targets = [args.template_dir]
    else:
        ap.error('give a template_dir or --all')

    ok = True
    for tpl in targets:
        if args.check:
            ok &= check(tpl)
            continue
        problems, warnings = build(tpl, tpl / 'content')
        print(f'[OK] {tpl.name}: built content/')
        report(tpl, problems, warnings)
        ok &= not problems
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
