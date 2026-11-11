#!/usr/bin/env python3
"""
PPT Master - Render pages to PNG so the model can look at what it drew.

Writing SVG coordinates is working blind: text that overflows, shapes that
collide and a page that feels lopsided only show in the picture. Render a
free-design page, look at the PNG, fix what is wrong, and render again.

Usage:
    python3 scripts/render_pages.py <project_path>                 # every page in svg_output/
    python3 scripts/render_pages.py <project_path> --page 03       # one page (number or name prefix; repeatable)
    python3 scripts/render_pages.py <project_path> --sheet         # also one contact sheet of the whole deck
    python3 scripts/render_pages.py <project_path> --source final  # render svg_final/ (icons embedded)

PNGs go to <project_path>/tmp/render/ (scratch: delete tmp/ before handing the
project over). Icons (<use data-icon>) are embedded only by finalize_svg.py, so
they are blank when rendering svg_output/.

Renderer: Quick Look (macOS), else rsvg-convert, else inkscape. Exit code 2
when none is available: open the live preview instead (preview.py --serve).
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WIDTH = 1280


def canvas(svg: Path):
    m = re.search(r'viewBox="\s*[\d.]+[\s,]+[\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', svg.read_text(encoding='utf-8'))
    return (float(m.group(1)), float(m.group(2))) if m else (1280.0, 720.0)


def crop_to_canvas(png: Path, w: float, h: float) -> None:
    """Quick Look pads a thumbnail to a square; cut it back to the page."""
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(png)
    W, H = im.size
    if w >= h:
        ph = round(W * h / w)
        box = (0, (H - ph) // 2, W, (H - ph) // 2 + ph)
    else:
        pw = round(H * w / h)
        box = ((W - pw) // 2, 0, (W - pw) // 2 + pw, H)
    if box != (0, 0, W, H):
        im.crop(box).save(png)


def render(svg: Path, out: Path) -> bool:
    w, h = canvas(svg)
    if shutil.which('qlmanage'):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(['qlmanage', '-t', '-s', str(WIDTH if w >= h else round(WIDTH * h / w)), '-o', td, str(svg)],
                           capture_output=True, timeout=120)
            made = list(Path(td).glob('*.png'))
            if made:
                shutil.move(str(made[0]), out)
                crop_to_canvas(out, w, h)
                return True
    if shutil.which('rsvg-convert'):
        r = subprocess.run(['rsvg-convert', '-w', str(WIDTH), '-o', str(out), str(svg)], capture_output=True, timeout=120)
        if r.returncode == 0 and out.exists():
            return True
    if shutil.which('inkscape'):
        r = subprocess.run(['inkscape', str(svg), '--export-type=png', f'--export-filename={out}', f'--export-width={WIDTH}'],
                           capture_output=True, timeout=180)
        if r.returncode == 0 and out.exists():
            return True
    return False


def contact_sheet(pngs, out: Path, cols=3, cell=640) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False
    thumbs = []
    for p in pngs:
        im = Image.open(p).convert('RGB')
        thumbs.append(im.resize((cell, round(cell * im.height / im.width))))
    row_h = max(t.height for t in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * row_h), 'white')
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % cols) * cell, (i // cols) * row_h))
    sheet.save(out)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project_path', type=Path)
    ap.add_argument('--page', action='append', default=[], help='Slide number or file-name prefix; repeatable')
    ap.add_argument('--source', default='output', help='SVG dir to render: output (default) or final')
    ap.add_argument('--sheet', action='store_true', help='Also write sheet.png: every rendered page on one image')
    ap.add_argument('-o', '--out', type=Path, default=None, help='Output dir (default: <project>/tmp/render)')
    args = ap.parse_args()

    svg_dir = args.project_path / f'svg_{args.source}'
    pages = sorted(svg_dir.glob('*.svg'))
    if args.page:
        def wanted(p):
            m = re.match(r'\d+', p.stem)
            return any(p.stem.startswith(q) or (m and q.isdigit() and int(q) == int(m.group())) for q in args.page)
        pages = [p for p in pages if wanted(p)]
    if not pages:
        print(f'[ERROR] no matching SVGs in {svg_dir}')
        return 1
    if not any(shutil.which(t) for t in ('qlmanage', 'rsvg-convert', 'inkscape')):
        print('[ERROR] no SVG renderer found (qlmanage on macOS, rsvg-convert, or inkscape).')
        print('        Look at the pages in the live preview instead:  preview.py <project_path> --serve')
        return 2

    out_dir = args.out or args.project_path / 'tmp' / 'render'
    out_dir.mkdir(parents=True, exist_ok=True)
    done = []
    for svg in pages:
        png = out_dir / f'{svg.stem}.png'
        if render(svg, png):
            done.append(png)
            print(f'[OK] {png}')
        else:
            print(f'[FAIL] could not render {svg.name}')
    if args.sheet and done:
        sheet = out_dir / 'sheet.png'
        if contact_sheet(done, sheet):
            print(f'[OK] {sheet}  ({len(done)} page(s))')
        else:
            print('[SKIP] contact sheet needs Pillow')
    return 0 if len(done) == len(pages) else 1


if __name__ == '__main__':
    sys.exit(main())
