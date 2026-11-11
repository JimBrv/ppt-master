#!/usr/bin/env python3
"""
PPT Master - Check free-design pages by their result.

A page filled from a content layout is safe by construction: its geometry was
measured and its text was checked against each slot's capacity. A free page
(`Layout: free: …` in design_spec.md) has no such guarantee, so this script
checks what came out:

    frame     the template's background, logo, title and page number are all
              there, exactly where the frame puts them
    canvas    no text runs off the page or into a reserved area (logo, header)
    fit       no text is wider than the box or circle it sits in
    overlap   no two lines of text overlap
    leftovers no {{PLACEHOLDER}} remains
    series    free pages of one Series share one design (hint)

Text width is estimated the way the layout library does it: a full-width
character is one font-size wide, a Latin character 0.55. That is close but not
exact, so a small tolerance applies; render the page and look at it as well
(render_pages.py).

The frame is templates/content/free_frame.svg when the template has content
layouts, otherwise templates/03_content.svg. Without design_spec.md, every page
that was not filled from a layout is checked for canvas, fit, overlap and
leftovers only.

Usage:
    python3 scripts/free_page_check.py <project_path>
    python3 scripts/free_page_check.py <project_path> --page 03      # one page
    python3 scripts/free_page_check.py <project_path> --source final # check svg_final/

Exit code 0 = clean, 1 = problems found.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_kit import FRAME_FILE, FREE_ID, text_units  # noqa: E402
from layout_plan_check import page_layout, parse_slides, planned_layouts  # noqa: E402

MIN_FONT = 12          # smaller text is unreadable once projected
SLOT = re.compile(r'\{\{\w+\}\}')


def tag(node) -> str:
    return node.tag.split('}')[-1]


def num(v, default=0.0) -> float:
    try:
        return float(str(v).strip().rstrip('px'))
    except (TypeError, ValueError):
        return default


def parse_transform(value: str):
    """(sx, sy, tx, ty) for translate / scale chains; None for anything else
    (rotate, matrix, skew), which this check cannot follow."""
    sx = sy = 1.0
    tx = ty = 0.0
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', value or ''):
        a = [num(x) for x in re.split(r'[\s,]+', args.strip()) if x]
        if name == 'translate':
            dx, dy = (a + [0.0, 0.0])[:2]
            tx, ty = tx + sx * dx, ty + sy * dy
        elif name == 'scale':
            kx = a[0] if a else 1.0
            ky = a[1] if len(a) > 1 else kx
            sx, sy = sx * kx, sy * ky
        else:
            return None
    return sx, sy, tx, ty


def compose(outer, inner):
    if outer is None or inner is None:
        return None
    osx, osy, otx, oty = outer
    isx, isy, itx, ity = inner
    return osx * isx, osy * isy, otx + osx * itx, oty + osy * ity


class Line:
    """One rendered line of text, in canvas coordinates."""

    def __init__(self, x, y, size, anchor, text, tf):
        sx, sy, tx, ty = tf
        w = text_units(text) * size * sx
        ax = x * sx + tx
        self.x0 = ax if anchor in ('', 'start') else (ax - w / 2 if anchor == 'middle' else ax - w)
        self.x1 = self.x0 + w
        self.y = y * sy + ty
        self.size = size * sy
        self.anchor_x = ax
        self.text = text
        self.w = w

    @property
    def top(self):
        return self.y - self.size * 0.82

    @property
    def bottom(self):
        return self.y + self.size * 0.18

    def label(self):
        t = self.text if len(self.text) <= 24 else self.text[:23] + '…'
        return f'"{t}"'


def lines_of(node, tf, inherited_size):
    """The lines a <text> element renders: one, or one per positioned <tspan>."""
    size = num(node.get('font-size'), inherited_size)
    x, y = num(node.get('x')), num(node.get('y'))
    anchor = node.get('text-anchor', 'start')
    spans = [c for c in node if tag(c) == 'tspan']
    positioned = [c for c in spans if c.get('x') is not None or c.get('y') is not None or c.get('dy') is not None]
    if not positioned:
        s = ''.join(node.itertext()).strip()
        return [Line(x, y, size, anchor, s, tf)] if s else []
    out, cur_y = [], y
    head = (node.text or '').strip()
    if head:
        out.append(Line(x, cur_y, size, anchor, head, tf))
    for c in spans:
        csize = num(c.get('font-size'), size)
        if c.get('y') is not None:
            cur_y = num(c.get('y'))
        dy = c.get('dy')
        if dy:
            cur_y += num(dy[:-2]) * csize if dy.strip().endswith('em') else num(dy)
        s = ''.join(c.itertext()).strip()
        if s:
            out.append(Line(num(c.get('x'), x), cur_y, csize, c.get('text-anchor', anchor), s, tf))
    return out


def scan(svg_path: Path):
    """(lines, rects, circles, images, canvas, unfollowed) of one page."""
    root = ET.parse(svg_path).getroot()
    vb = [num(v) for v in (root.get('viewBox') or '0 0 1280 720').split()]
    canvas = (vb[2], vb[3]) if len(vb) == 4 else (1280.0, 720.0)
    lines, rects, circles, images = [], [], [], []
    unfollowed = 0

    def walk(node, tf, size):
        nonlocal unfollowed
        t = tag(node)
        if t in ('defs', 'title', 'desc', 'metadata'):
            return
        own = parse_transform(node.get('transform')) if node.get('transform') else (1.0, 1.0, 0.0, 0.0)
        tf = compose(tf, own)
        if tf is None:
            unfollowed += 1
            return
        size = num(node.get('font-size'), size)
        sx, sy, tx, ty = tf
        if t == 'text':
            lines.extend(lines_of(node, tf, size))
            return
        if t == 'rect':
            x, y, w, h = (num(node.get(k)) for k in ('x', 'y', 'width', 'height'))
            visible = node.get('fill', '#000') != 'none' or node.get('stroke') not in (None, 'none')
            if visible:
                rects.append((x * sx + tx, y * sy + ty, (x + w) * sx + tx, (y + h) * sy + ty))
        elif t == 'circle':
            cx, cy, r = (num(node.get(k)) for k in ('cx', 'cy', 'r'))
            circles.append((cx * sx + tx, cy * sy + ty, r * min(sx, sy)))
        elif t == 'image':
            href = node.get('href') or node.get('{http://www.w3.org/1999/xlink}href') or ''
            images.append((href, *(round(num(node.get(k)), 1) for k in ('x', 'y', 'width', 'height'))))
        for c in node:
            walk(c, tf, size)

    walk(root, (1.0, 1.0, 0.0, 0.0), 16.0)
    return lines, rects, circles, images, canvas, unfollowed


def frame_parts(frame: Path):
    """What a page must keep from the frame: its images and the positions of
    the title and the page number."""
    root = ET.parse(frame).getroot()
    images, title, page_num = [], None, None
    for node in root.iter():
        t = tag(node)
        if t == 'image':
            href = node.get('href') or node.get('{http://www.w3.org/1999/xlink}href') or ''
            images.append((href, *(round(num(node.get(k)), 1) for k in ('x', 'y', 'width', 'height'))))
        elif t == 'text':
            s = ''.join(node.itertext())
            key = (round(num(node.get('x')), 1), round(num(node.get('y')), 1), round(num(node.get('font-size')), 1))
            if '{{PAGE_TITLE}}' in s:
                title = key
            elif '{{PAGE_NUM}}' in s:
                page_num = key
    return images, title, page_num


def check_page(svg: Path, frame, reserved):
    raw = svg.read_text(encoding='utf-8')
    errors, notes = [], []
    if SLOT.search(raw):
        errors.append(f'placeholder left in the page: {", ".join(sorted(set(SLOT.findall(raw)))[:4])}')
    try:
        lines, rects, circles, images, (W, H), unfollowed = scan(svg)
    except ET.ParseError as e:
        return [f'not well-formed XML: {e}'], notes
    if unfollowed:
        notes.append(f'{unfollowed} element(s) under a rotate/matrix transform were not checked; look at the render')

    frame_keys = set()
    if frame:
        f_images, f_title, f_num = frame
        for img in f_images:
            if img not in images:
                errors.append(f'frame image missing or moved: {img[0]} at ({img[1]:g},{img[2]:g}) {img[3]:g}×{img[4]:g} — '
                              'copy the frame\'s <image> tags unchanged')
        at = {(round(l.anchor_x, 1), round(l.y, 1), round(l.size, 1)) for l in lines}
        for name, key in (('title', f_title), ('page number', f_num)):
            if key and key not in at:
                errors.append(f'{name} is not where the frame puts it (x={key[0]:g}, y={key[1]:g}, font-size {key[2]:g})')
            if key:
                frame_keys.add(key)

    body = [l for l in lines if (round(l.anchor_x, 1), round(l.y, 1), round(l.size, 1)) not in frame_keys]
    page_boxes = [r for r in rects if (r[2] - r[0]) < W * 0.95 or (r[3] - r[1]) < H * 0.9]

    for l in body:
        if l.size < MIN_FONT:
            errors.append(f'{l.label()}: font-size {l.size:g} is below {MIN_FONT}')
        tol = max(2.0, l.w * 0.03)
        if l.x0 < -tol or l.x1 > W + tol or l.top < -2 or l.bottom > H + 2:
            errors.append(f'{l.label()}: runs off the canvas (x {l.x0:.0f}–{l.x1:.0f}, y {l.y:.0f})')
            continue
        for rx0, ry0, rx1, ry1 in reserved:
            if l.x0 < rx1 and rx0 < l.x1 and l.top < ry1 and ry0 < l.bottom:
                errors.append(f'{l.label()}: enters the reserved area ({rx0:g},{ry0:g})–({rx1:g},{ry1:g}) '
                              '(logo / header / page number)')
                break
        # The smallest box or circle the line starts in is its container.
        px, py = min(max(l.anchor_x, l.x0 + 1), l.x1 - 1), l.y - l.size * 0.35
        holders = [(r[2] - r[0]) * (r[3] - r[1]) for r in page_boxes]
        inside = [(a, r) for a, r in zip(holders, page_boxes)
                  if r[0] <= px <= r[2] and r[1] <= py <= r[3] and (r[3] - r[1]) >= l.size * 0.9 and (r[2] - r[0]) >= 8]
        round_inside = [(3.1416 * r * r, (cx - r, cy - r, cx + r, cy + r)) for cx, cy, r in circles
                        if (px - cx) ** 2 + (py - cy) ** 2 <= r * r and 2 * r >= l.size * 0.9]
        if inside or round_inside:
            _, (bx0, by0, bx1, by1) = min(inside + round_inside, key=lambda t: t[0])
            over = max(l.x1 - bx1, bx0 - l.x0)
            if over > tol:
                errors.append(f'{l.label()}: about {over:.0f}px wider than its box (x {bx0:.0f}–{bx1:.0f}); '
                              'shorten the text, split the line or widen the box')

    for i, a in enumerate(body):
        for b in body[i + 1:]:
            dx = min(a.x1, b.x1) - max(a.x0, b.x0)
            dy = min(a.bottom, b.bottom) - max(a.top, b.top)
            small = min(a.size, b.size)
            if dx > small * 0.5 and dy > small * 0.3:
                errors.append(f'{a.label()} and {b.label()} overlap')
    return errors, notes


def signature(svg: Path):
    """The shapes of a page, rounded: pages of one design share most of them."""
    _, rects, circles, _, _, _ = scan(svg)
    return {('r', *(round(v / 4) for v in r)) for r in rects} | {('c', *(round(v / 4) for v in c)) for c in circles}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project_path', type=Path)
    ap.add_argument('--page', action='append', default=[], help='Slide number or file-name prefix; repeatable')
    ap.add_argument('--source', default='output', help='SVG dir to check: output (default) or final')
    args = ap.parse_args()

    proj = args.project_path
    svg_dir = proj / f'svg_{args.source}'
    pages = sorted(svg_dir.glob('*.svg'))
    if not pages:
        print(f'[ERROR] no SVGs in {svg_dir}')
        return 1

    spec_path = proj / 'design_spec.md'
    spec = spec_path.read_text(encoding='utf-8') if spec_path.exists() else ''
    plan = planned_layouts(spec) if spec else {}
    series = {n: (f.get('series') or '').split()[0] for n, _, f in parse_slides(spec) if f.get('series')} if spec else {}

    content = proj / 'templates' / 'content'
    frame_path = content / FRAME_FILE if (content / FRAME_FILE).exists() else proj / 'templates' / '03_content.svg'
    frame = frame_parts(frame_path) if frame_path.exists() else None
    reserved = []
    if (content / 'layouts.json').exists():
        meta = json.loads((content / 'layouts.json').read_text(encoding='utf-8')).get('meta', {})
        reserved = [tuple(r) for r in meta.get('frame', {}).get('reserved', [])]
    # The header band holds the title and the page-number box holds the number: only body text is tested against them.

    checked, failed, by_series = 0, 0, {}
    for svg in pages:
        m = re.match(r'\d+', svg.stem)
        n = int(m.group()) if m else None
        if args.page and not any(svg.stem.startswith(p) or (n is not None and p.isdigit() and int(p) == n) for p in args.page):
            continue
        marker = page_layout(svg.read_text(encoding='utf-8'))
        if plan:
            if plan.get(n) != 'free':
                continue
        elif marker and marker != FREE_ID:
            continue
        checked += 1
        errors, notes = check_page(svg, frame, reserved)
        for e in errors:
            print(f'  [FAIL] {svg.name}: {e}')
        for h in notes:
            print(f'  [NOTE] {svg.name}: {h}')
        failed += bool(errors)
        if n in series:
            by_series.setdefault(series[n], []).append(svg)

    for name, group in by_series.items():
        if len(group) < 2:
            continue
        first = signature(group[0])
        for other in group[1:]:
            sig = signature(other)
            shared = len(first & sig) / max(1, len(first | sig))
            if shared < 0.5:
                print(f'  [HINT] series "{name}": {other.name} shares {shared:.0%} of its shapes with {group[0].name}; '
                      'pages of one series should repeat one design')

    frame_name = frame_path.relative_to(proj) if frame else 'none'
    print(f'[SCAN] {checked} free page(s) in {svg_dir.name}/; frame: {frame_name}')
    if failed:
        print(f'[FAIL] {failed} page(s) with problems')
        return 1
    print('[OK] free pages pass' if checked else '[OK] no free pages to check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
