#!/usr/bin/env python3
"""
PPT Master - Stress-test a template's content layout library.

Checks that every layout in <template>/content/ is consistent with
layouts.json and, when the template has content_src/, that content/ is a
fresh build with no reserved-area conflicts. It then fills every text slot to its full capacity with full-width
characters, then runs the real pipeline on the result: svg_quality_checker.py
and build_pptx.py --verify. A layout that overflows, breaks a technical
constraint, or loses text on export fails here instead of in a real deck.

Run it after adding or editing any layout. The scratch project lives in a
temporary directory and is deleted afterwards unless --keep is given.

Usage:
    python3 scripts/layout_stress.py skills/ppt-master/templates/layouts/奇安信
    python3 scripts/layout_stress.py <template_dir> --layouts funnel_layers,loop_nodes
    python3 scripts/layout_stress.py <template_dir> --keep        # keep the scratch project to inspect it
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from layout_kit import RELATIONS, SLOT_RE, fill_layout, slot_pattern  # noqa: E402

ICON_DIR = SCRIPTS.parent / 'templates' / 'icons'
SAMPLE_ICONS = ['shield-check', 'eye', 'bell', 'server', 'cog', 'key', 'target', 'users', 'lock-closed', 'chart-bar']


def check_library(content: Path, index: dict, wanted):
    """Problems that make a layout unusable regardless of its content."""
    problems = []
    svgs = {p.stem for p in content.glob('*.svg')}
    for lid in sorted(set(index) - svgs):
        problems.append(f'{lid}: listed in layouts.json but {lid}.svg is missing')
    for lid in sorted(svgs - set(index)):
        problems.append(f'{lid}.svg: not listed in layouts.json')
    for lid in wanted:
        if lid not in index or lid not in svgs:
            continue
        svg = (content / f'{lid}.svg').read_text(encoding='utf-8')
        entry = index[lid]
        icons = set(re.findall(r'data-icon="\{\{(\w+)\}\}"', svg))
        for slot in dict.fromkeys(SLOT_RE.findall(svg)):
            if slot in icons:
                continue
            if slot_pattern(slot) not in entry.get('slots', {}):
                problems.append(f'{lid}: slot {slot} has no capacity in layouts.json')
        for img in entry.get('imageSlots', []):
            if f'data-image-slot="{img["name"]}"' not in svg:
                problems.append(f'{lid}: image slot {img["name"]} missing from the SVG')
        for field in ('label', 'summary', 'bestFor', 'avoidFor', 'items', 'relations', 'claim'):
            if not entry.get(field):
                problems.append(f'{lid}: metadata field "{field}" is empty')
        for rel in entry.get('relations', []):
            if rel not in RELATIONS:
                problems.append(f'{lid}: relation "{rel}" is not in the vocabulary (layout_kit.RELATIONS)')
    return problems


def run(cmd, log):
    r = subprocess.run(cmd, capture_output=True, text=True)
    log.write_text(r.stdout + r.stderr, encoding='utf-8')
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('template_dir', type=Path)
    ap.add_argument('--layouts', help='Comma-separated layout IDs (default: all)')
    ap.add_argument('--keep', action='store_true', help='Keep the scratch project')
    ap.add_argument('--skip-build', action='store_true', help='Only check consistency and fill; skip quality check and export')
    args = ap.parse_args()

    content = args.template_dir / 'content'
    index_path = content / 'layouts.json'
    if not index_path.exists():
        print(f'[ERROR] {index_path} not found', file=sys.stderr)
        return 1
    index = json.loads(index_path.read_text(encoding='utf-8'))['layouts']
    wanted = args.layouts.split(',') if args.layouts else sorted(index)

    problems = check_library(content, index, wanted)
    if (args.template_dir / 'content_src' / 'theme.json').exists():
        import layout_build
        if not layout_build.check(args.template_dir):
            problems.append('content/ is stale or overlaps reserved areas; run layout_build.py on the template')
    icons = [n for n in SAMPLE_ICONS if (ICON_DIR / f'{n}.svg').exists()]

    root = Path(tempfile.mkdtemp(prefix='layout_stress_'))
    proj = root / f'{args.template_dir.name}_stress_ppt169_{date.today():%Y%m%d}'
    for d in ('svg_output', 'notes', 'images', 'templates'):
        (proj / d).mkdir(parents=True)
    for pat in ('*.jpg', '*.jpeg', '*.png'):
        for f in args.template_dir.glob(pat):
            shutil.copy(f, proj / 'images')

    notes = []
    for n, lid in enumerate(wanted, 1):
        if lid not in index or not (content / f'{lid}.svg').exists():
            continue
        svg = (content / f'{lid}.svg').read_text(encoding='utf-8')
        caps = index[lid]['slots']
        icon_slots = set(re.findall(r'data-icon="\{\{(\w+)\}\}"', svg))
        values, k = {}, 0
        for slot in dict.fromkeys(SLOT_RE.findall(svg)):
            if slot in icon_slots:
                values[slot] = icons[k % len(icons)]
                k += 1
            elif slot == 'PAGE_NUM':
                values[slot] = str(n)
            else:
                values[slot] = '测' * caps.get(slot_pattern(slot), 1)
        page, errors, _ = fill_layout(svg, values, caps, ICON_DIR, proj / 'images')
        problems += [f'{lid}: {e}' for e in errors]
        stem = f'{n:02d}_{lid}'
        (proj / 'svg_output' / f'{stem}.svg').write_text(page, encoding='utf-8')
        notes.append(f'# {stem}\n\nStress test page.\n')
    (proj / 'notes' / 'total.md').write_text('\n---\n\n'.join(notes), encoding='utf-8')
    (proj / 'README.md').write_text('Layout stress test.\n', encoding='utf-8')

    print(f'[SCAN] {len(notes)} layout(s) filled to capacity from {content}')
    ok = not problems
    for p in problems:
        print(f'  [FAIL] {p}')

    if not args.skip_build and notes:
        code, out = run([sys.executable, str(SCRIPTS / 'svg_quality_checker.py'), str(proj)], root / 'quality.log')
        m = re.search(r'\[ERROR\] With errors: (\d+)', out)
        errors = int(m.group(1)) if m else (0 if code == 0 else -1)
        print(f'[QUALITY] {"OK" if errors == 0 else f"{errors} page(s) with errors"}')
        ok &= errors == 0
        code, out = run([sys.executable, str(SCRIPTS / 'build_pptx.py'), str(proj), '--verify', '--no-plan-check'],
                        root / 'build.log')
        summary = re.findall(r'\[SUMMARY\].*', out)
        print(f'[BUILD] {"OK" if code == 0 else f"failed (exit {code})"}' + (f'  {summary[-1]}' if summary else ''))
        ok &= code == 0

    if args.keep or not ok:
        print(f'[KEEP] scratch project: {proj}  (logs in {root})')
    else:
        shutil.rmtree(root, ignore_errors=True)
    print('[OK] all layouts passed' if ok else '[FAIL] see problems above')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
