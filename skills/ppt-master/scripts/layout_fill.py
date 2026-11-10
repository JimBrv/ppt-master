#!/usr/bin/env python3
"""
PPT Master - Fill one content layout from a values file.

Reads <project>/templates/content/<layout_id>.svg, checks every value against
the slot capacities in layouts.json, removes the lines and containers of
unused slots, swaps image placeholders for real images, and writes the page.
Nothing is written if any check fails.

The page must be planned: <project>/design_spec.md has to exist and the slide
whose number starts the output file name (05_xxx.svg -> "#### Slide 05") must
name this layout. A page that the Strategist did not plan, or planned with a
different layout, is refused. --no-plan-check skips this for tests outside a
real project.

values.json maps slot names to text; icon slots take an icon name from
templates/icons/; "_images" maps image slots to files in <project>/images/:

    {"PAGE_TITLE": "...", "COL1_TITLE": "...", "COL1_CARD1_ICON": "server",
     "_images": {"SCREENSHOT": "console.png"}}

Usage:
    python3 scripts/layout_fill.py <project_path> <layout_id> <values.json> -o <project_path>/svg_output/05_xxx.svg
    python3 scripts/layout_fill.py <project_path> <layout_id> <values.json>          # print to stdout
    python3 scripts/layout_fill.py <project_path> --slots <layout_id>                # list slots and capacities
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_kit import SLOT_RE, fill_layout, slot_pattern  # noqa: E402
from layout_plan_check import planned_layouts  # noqa: E402

ICON_DIR = Path(__file__).resolve().parent.parent / 'templates' / 'icons'


def load(project: Path, layout_id: str):
    content = project / 'templates' / 'content'
    index_path = content / 'layouts.json'
    if not index_path.exists():
        sys.exit(f'[ERROR] {index_path} not found; copy the template content/ directory in Step 3.')
    index = json.loads(index_path.read_text(encoding='utf-8'))['layouts']
    if layout_id not in index:
        sys.exit(f'[ERROR] unknown layout {layout_id!r}; available: {", ".join(sorted(index))}')
    svg_path = content / f'{layout_id}.svg'
    if not svg_path.exists():
        sys.exit(f'[ERROR] {svg_path} not found')
    return svg_path.read_text(encoding='utf-8'), index[layout_id]


def plan_problem(project: Path, layout_id: str, output) -> str:
    """Why this page may not be written, or '' when the plan allows it."""
    spec = project / 'design_spec.md'
    if not spec.exists():
        return (f'{spec} not found. Plan the deck first (Step 4): the Strategist writes design_spec.md '
                'at the project root, then pages are filled from it.')
    plan = planned_layouts(spec.read_text(encoding='utf-8'))
    if output is None:
        if layout_id not in plan.values():
            return f'design_spec.md plans no page with layout {layout_id}'
        return ''
    m = re.match(r'\d+', output.name)
    if not m:
        return f'{output.name}: name pages NN_name.svg, where NN is the slide number in design_spec.md'
    num = int(m.group())
    if num not in plan:
        return f'design_spec.md has no "#### Slide {num:02d}"'
    if plan[num] != layout_id:
        return f'design_spec.md plans Slide {num:02d} as {plan[num] or "(no layout)"}, not {layout_id}'
    return ''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project_path', type=Path)
    ap.add_argument('layout_id', nargs='?')
    ap.add_argument('values', nargs='?', type=Path, help='JSON file of slot values')
    ap.add_argument('-o', '--output', type=Path, help='Write the page here instead of stdout')
    ap.add_argument('--slots', metavar='LAYOUT_ID', help='List the slots of a layout and exit')
    ap.add_argument('--no-plan-check', action='store_true',
                    help='Do not require a matching page in design_spec.md (tests only)')
    args = ap.parse_args()

    if args.slots:
        svg, entry = load(args.project_path, args.slots)
        icons = set(entry.get('iconSlots', []))
        for name in dict.fromkeys(SLOT_RE.findall(svg)):
            pat = slot_pattern(name)
            kind = 'icon' if pat in icons else f'{entry["slots"].get(pat, "?")} chars'
            print(f'{name:<24} {kind}')
        for img in entry.get('imageSlots', []):
            print(f'_images.{img["name"]:<16} image {img["w"]}x{img["h"]}')
        return 0

    if not args.layout_id or not args.values:
        ap.error('layout_id and values are required unless --slots is given')
    svg, entry = load(args.project_path, args.layout_id)
    if not args.no_plan_check:
        why = plan_problem(args.project_path, args.layout_id, args.output)
        if why:
            print(f'[ERROR] {why}', file=sys.stderr)
            print('[FAIL] page not written.', file=sys.stderr)
            return 1
    values = json.loads(args.values.read_text(encoding='utf-8'))
    page, errors, removed = fill_layout(svg, values, entry['slots'], ICON_DIR, args.project_path / 'images')
    if errors:
        for e in errors:
            print(f'[ERROR] {e}', file=sys.stderr)
        print(f'[FAIL] {len(errors)} problem(s); nothing written.', file=sys.stderr)
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page, encoding='utf-8')
        print(f'[OK] {args.output} ({args.layout_id}; {len(removed)} unused slot(s) removed)', file=sys.stderr)
    else:
        sys.stdout.write(page)
        print(f'[OK] {args.layout_id}; {len(removed)} unused slot(s) removed', file=sys.stderr)
    if removed:
        print(f'     removed: {", ".join(removed)}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
