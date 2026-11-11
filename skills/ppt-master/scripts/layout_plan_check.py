#!/usr/bin/env python3
"""
PPT Master - Check a design spec's layout plan against the selection rules.

Reads <project>/design_spec.md and, when the template has content layouts,
<project>/templates/content/layouts.json. Every body page must carry:

    - **Message**:  the one sentence the audience should remember
    - **Relation**: one relation from the vocabulary (layout_kit.RELATIONS)
    - **Layout**:   a layout ID, or "free: <description>" for a page designed for its content
    - **Claim check**: which content plays which part: against the layout's claim, or, on a
                    free page, against the claim its own design makes
    - **Evidence**: one or more verbatim quotes from sources/, in "…", “…” or 「…」,
                    each at least 8 characters, that the page's content rests on
    - **Series**:   "<group> n/m" for parallel pages that share one layout;
                    required when titles number pages in a group (风险一/风险二, Case 1/Case 2)

I. Project Information may carry **Layout mode**: `open` (design a page freely
whenever that shows the content's own structure better than a layout does) or
`library` (stay with the layouts; the default when the row is missing).

Errors (exit 1): a missing field, an unknown relation or layout, a layout that
does not show the page's relation, an Evidence quote that is not in sources/,
numbered parallel pages without a Series, a series that uses more than one layout.
Hints (never fail): density against the genre budget, rhythm of heavy and
light pages. Density counts content text runs only: the page title, the page
number and a layout's fixed labels (labelSlots in layouts.json) are left out. Density and rhythm are judgement calls; read the hints, then decide.

Cover, TOC, chapter and ending pages are skipped: give them a Layout of
cover / toc / chapter / ending, or name them so in the slide heading.

Usage:
    python3 scripts/layout_plan_check.py <project_path>            # check the plan (Strategist, before handing the spec over)
    python3 scripts/layout_plan_check.py <project_path> --output   # also check svg_output/ against the plan (after the Executor)

--output adds two checks on svg_output/: every page must be a planned slide and
must have been filled from the layout the plan names (error), and its content
density is compared with the genre budget (hint). build_pptx.py runs this mode
before exporting.
"""
import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_kit import DENSITY, FREE_ID, RELATIONS, slot_pattern  # noqa: E402

SLIDE_RE = re.compile(r'^####\s+Slide\s+(\d+)\s*[-–—:]?\s*(.*)$', re.M)
FIELD_RE = re.compile(r'^\s*-\s+\*\*([^*]+)\*\*\s*[:：]\s*(.*)$', re.M)
GENRE_RE = re.compile(r'\*\*Genre\*\*\s*\|?\s*[:：]?\s*`?(\w+)', re.I)
MODE_RE = re.compile(r'\*\*Layout mode\*\*\s*\|?\s*[:：]?\s*`?(\w+)', re.I)
MODES = ('open', 'library')
STANDARD = ('cover', 'toc', 'chapter', 'ending', 'end', 'agenda')
STANDARD_NAMES = re.compile(r'cover|toc|table of contents|agenda|chapter|section divider|ending|closing|thank|'
                            r'封面|目录|章节|过渡|封底|结束|致谢', re.I)


def parse_slides(spec: str):
    heads = list(SLIDE_RE.finditer(spec))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(spec)
        block = spec[m.end():end]
        cut = re.search(r'^#{1,3}\s', block, re.M)
        if cut:
            block = block[:cut.start()]
        fields = {k.strip().lower(): v.strip() for k, v in FIELD_RE.findall(block)}
        yield int(m.group(1)), m.group(2).strip(), fields


def is_standard(name: str, layout: str) -> bool:
    words = re.findall(r'[\w-]+', layout.lower())
    head = words[0] if words else ''
    if head in STANDARD or re.match(r'0\d_(cover|toc|chapter|ending)', head):
        return True
    return bool(STANDARD_NAMES.search(name)) and not layout.lower().startswith('free')


TEXT_SLOT_RE = re.compile(r'<text\b[^>]*?\bx="([^"]+)"[^>]*?\by="([^"]+)"[^>]*>\s*\{\{(\w+)\}\}\s*</text>')


def label_positions(layout_svg: Path, labels) -> set:
    """(x, y) of the title, page number and fixed-label slots in a layout.
    layout_fill keeps every text where the layout put it, so a filled page's
    labels sit at exactly these positions."""
    out = set()
    for x, y, slot in TEXT_SLOT_RE.findall(layout_svg.read_text(encoding='utf-8')):
        if slot in ('PAGE_TITLE', 'PAGE_NUM') or slot_pattern(slot) in labels:
            out.add((x, y))
    return out


QUOTE_RE = re.compile(r'“([^”]+)”|"([^"]+)"|「([^」]+)」|『([^』]+)』')
MIN_QUOTE = 8
# "风险一：…", "风险 2：…", "Case 3: …" — a numbered member of a parallel group.
ORDINAL_RE = re.compile(r'\s*([^\s：:0-9一二三四五六七八九十]{1,8}?)\s*([一二三四五六七八九十]{1,3}|\d{1,2})\s*[：:、.．\-—]')


def norm(text: str) -> str:
    """Fold a text for quote matching: Unicode width, curly quotes, Markdown
    links and emphasis, whitespace and case."""
    t = unicodedata.normalize('NFKC', text)
    t = t.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'[*_`]', '', t)
    return re.sub(r'\s+', ' ', t).strip().lower()


def source_text(project: Path) -> str:
    src = project / 'sources'
    files = [f for f in src.rglob('*') if f.is_file() and f.suffix.lower() in ('.md', '.txt', '.markdown')] \
        if src.exists() else []
    return norm('\n'.join(f.read_text(encoding='utf-8', errors='ignore') for f in files))


def quotes(text: str):
    return [next(g for g in m.groups() if g) for m in QUOTE_RE.finditer(text)]


PAGE_LAYOUT_RE = re.compile(r'content layout: (\w+)')


def planned_layouts(spec: str) -> dict:
    """Slide number -> planned layout: a layout ID, 'free', or 'standard'
    (cover / TOC / chapter / ending)."""
    out = {}
    for num, name, f in parse_slides(spec):
        layout = f.get('layout', '')
        if is_standard(name, layout):
            out[num] = 'standard'
        elif layout.lower().startswith('free'):
            out[num] = 'free'
        else:
            out[num] = layout.strip('`').split()[0] if layout else ''
    return out


def page_layout(svg_text: str):
    """The layout a page was filled from (layout_fill keeps the shell's
    'content layout: <id>' comment), or None for a hand-drawn page."""
    m = PAGE_LAYOUT_RE.search(svg_text)
    return m.group(1) if m else None


def svg_runs(svg: Path, skip=None) -> int:
    """Content text runs on a page. With skip (positions from label_positions)
    the title, page number and fixed labels are left out; without it (a free
    page) the largest text is taken as the title and a bare number as the page
    number."""
    texts = [n for n in ET.parse(svg).getroot().iter()
             if n.tag.split('}')[-1] == 'text' and ''.join(n.itertext()).strip()]
    if skip is not None:
        return sum(1 for n in texts if (n.get('x'), n.get('y')) not in skip)

    def size(n):
        try:
            return float(n.get('font-size', '0').rstrip('px'))
        except ValueError:
            return 0
    title = max(texts, key=size, default=None)
    return sum(1 for n in texts if n is not title and not re.fullmatch(r'\d{1,3}', ''.join(n.itertext()).strip()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project_path', type=Path)
    ap.add_argument('--output', action='store_true', help='Also count text runs per page in svg_output/')
    args = ap.parse_args()

    spec_path = args.project_path / 'design_spec.md'
    if not spec_path.exists():
        print(f'[ERROR] {spec_path} not found')
        return 1
    spec = spec_path.read_text(encoding='utf-8')
    index_path = args.project_path / 'templates' / 'content' / 'layouts.json'
    layouts = json.loads(index_path.read_text(encoding='utf-8'))['layouts'] if index_path.exists() else {}

    m = GENRE_RE.search(spec)
    genre = m.group(1).lower() if m else None
    m = MODE_RE.search(spec)
    mode = m.group(1).lower() if m else 'library'
    errors, hints, body = [], [], []
    if mode not in MODES:
        errors.append(f'**Layout mode** "{mode}" is not one of: {", ".join(MODES)}')
        mode = 'library'
    source = source_text(args.project_path)
    if not source:
        errors.append('sources/ holds no text (.md / .txt): save the converted full source there (Step 1); '
                      'every page\'s Evidence is checked against it')

    for num, name, f in parse_slides(spec):
        layout = f.get('layout', '')
        if is_standard(name, layout):
            continue
        tag = f'Slide {num:02d}'
        for field in ('message', 'relation', 'layout'):
            if not f.get(field):
                errors.append(f'{tag}: missing **{field.capitalize()}**')
        rel = f.get('relation', '').split()[0].strip('`') if f.get('relation') else ''
        if rel and rel not in RELATIONS:
            errors.append(f'{tag}: relation "{rel}" is not in the vocabulary: {", ".join(RELATIONS)}')
        lid = layout.strip('`').split()[0] if layout else ''
        free = layout.lower().startswith('free')
        weight = None
        if layout and not free:
            if layouts and lid not in layouts:
                errors.append(f'{tag}: layout "{lid}" is not in templates/content/layouts.json')
            elif lid in layouts:
                entry = layouts[lid]
                weight = entry.get('weight')
                if rel in RELATIONS and rel not in entry.get('relations', []):
                    errors.append(f'{tag}: {lid} shows {entry.get("relations")}, not "{rel}" — '
                                  f'pick a layout for "{rel}" or write Layout: free: …')
                if not f.get('claim check'):
                    claim = entry.get('claim')
                    errors.append(f'{tag}: missing **Claim check**'
                                  + (f' — test the content against: {claim}' if claim else ''))
        if free:
            if not f.get('claim check'):
                errors.append(f'{tag}: missing **Claim check** — a free page makes its own claim: say what the '
                              'picture asserts and which content plays which part')
            shows = sorted(k for k, e in layouts.items() if rel in e.get('relations', []))
            if mode == 'library' and shows:
                hints.append(f'{tag}: free page in library mode, though {", ".join(shows)} show "{rel}"; '
                             'keep it only if none of their claims holds, or set **Layout mode** to open')
        ev = f.get('evidence', '')
        found = [q for q in quotes(ev) if len(norm(q)) >= MIN_QUOTE]
        if not ev or not found:
            errors.append(f'{tag}: **Evidence** needs at least one verbatim quote from sources/ '
                          f'(in "…", “…” or 「…」, ≥ {MIN_QUOTE} characters)')
        elif source:
            missing = [q for q in found if norm(q) not in source]
            for q in missing:
                errors.append(f'{tag}: Evidence quote not found in sources/: "{q[:60]}"')
        msg = f.get('message', '')
        if msg and len(msg) > 40:
            hints.append(f'{tag}: Message is {len(msg)} characters; one sentence of ≤ 30 reads better')
        om = ORDINAL_RE.match(f.get('title') or name)
        body.append(dict(num=num, rel=rel, lid=lid if not free else 'free', weight=weight,
                         series=(f.get('series') or '').split()[0] if f.get('series') else '',
                         group=om.group(1) if om else ''))

    # Numbered titles mark a parallel group; its pages must declare it.
    numbered = {}
    for p in body:
        if p['group']:
            numbered.setdefault(p['group'], []).append(p)
    for g, pages in numbered.items():
        if len(pages) < 2:
            continue
        nums = ', '.join(f'{p["num"]:02d}' for p in pages)
        if any(not p['series'] for p in pages):
            errors.append(f'Slides {nums} are numbered "{g}…": a parallel group. Give each the same '
                          f'**Series** (e.g. "{g} 1/{len(pages)}") and one shared layout')
        elif len({p['series'] for p in pages}) > 1:
            errors.append(f'Slides {nums} are numbered "{g}…" but name different Series')

    # Parallel pages share one layout.
    groups = {}
    for p in body:
        if p['series']:
            groups.setdefault(p['series'], set()).add(p['lid'])
    for g, ids in groups.items():
        if len(ids) > 1:
            errors.append(f'series "{g}": pages use {sorted(ids)}; parallel pages should share one layout')

    # Rhythm.
    run = 0
    for p in body:
        run = run + 1 if p['weight'] == 'heavy' else 0
        if run == 3:
            hints.append(f'Slide {p["num"]:02d}: third heavy page in a row; consider a lighter page between them')
    if genre == 'narrative' and body:
        light = sum(1 for p in body if p['weight'] == 'light' or p['rel'] in ('statement', 'metric'))
        need = max(1, len(body) // 5)
        if light < need:
            hints.append(f'narrative genre: {light} light page(s) (statement / metric) for {len(body)} body pages; '
                         f'aim for at least {need}')
    for a, b in zip(body, body[1:]):
        if a['lid'] == b['lid'] and a['lid'] != 'free' and not (a['series'] and a['series'] == b['series']):
            hints.append(f'Slides {a["num"]:02d}–{b["num"]:02d}: same layout {a["lid"]} back to back outside a series')

    # Pages on disk must be the pages that were planned.
    if args.output:
        plan = planned_layouts(spec)
        for svg in sorted((args.project_path / 'svg_output').glob('*.svg')):
            m = re.match(r'\d+', svg.stem)
            if not m:
                errors.append(f'svg_output/{svg.name}: page files must start with the slide number (NN_name.svg)')
                continue
            num = int(m.group())
            if num not in plan:
                errors.append(f'svg_output/{svg.name}: no "#### Slide {num:02d}" in design_spec.md')
                continue
            want, got = plan[num], page_layout(svg.read_text(encoding='utf-8'))
            if want not in ('free', 'standard', '') and got != want:
                errors.append(f'svg_output/{svg.name}: design_spec.md plans {want}, but the page '
                              + (f'was filled from {got}' if got else 'was not filled from a layout (use layout_fill.py)'))
            elif want == 'free' and got and got != FREE_ID:
                errors.append(f'svg_output/{svg.name}: design_spec.md plans a free page, but it was filled from {got}')

    # Density, after the Executor.
    if args.output:
        if genre not in DENSITY:
            hints.append('no **Genre** (narrative / report / solution) in the spec; density not checked')
        else:
            avg_cap, max_cap = DENSITY[genre]
            avg_ceiling = avg_cap[1] if isinstance(avg_cap, tuple) else avg_cap
            avg_label = f'{avg_cap[0]}–{avg_cap[1]}' if isinstance(avg_cap, tuple) else str(avg_cap)
            pages = sorted((args.project_path / 'svg_output').glob('*.svg'))
            by_num = {p['num']: p for p in body}
            content_dir = args.project_path / 'templates' / 'content'
            counts = []
            for svg in pages:
                m = re.match(r'\d+', svg.stem)
                page = by_num.get(int(m.group())) if m else None
                if by_num and not page:
                    continue
                skip = None
                if page and page['lid'] in layouts and (content_dir / f'{page["lid"]}.svg').exists():
                    skip = label_positions(content_dir / f'{page["lid"]}.svg', layouts[page['lid']].get('labelSlots', []))
                counts.append((svg.stem, svg_runs(svg, skip)))
            for s, c in counts:
                if c > max_cap:
                    hints.append(f'{s}: {c} text runs, over the {genre} page maximum of {max_cap}')
            if counts:
                avg = sum(c for _, c in counts) / len(counts)
                print(f'[DENSITY] {genre}: average {avg:.1f} content text runs per body page (budget {avg_label}), '
                      f'max {max(c for _, c in counts)} (budget {max_cap})')
                if avg > avg_ceiling:
                    hints.append(f'average {avg:.1f} content text runs per page is over the {genre} budget of {avg_label}')

    print(f'[SCAN] {len(body)} body page(s); genre: {genre or "not set"}; layout mode: {mode}; '
          f'{"content layouts: " + str(len(layouts)) if layouts else "no content layouts (free design)"}')
    for p in body:
        print(f'  Slide {p["num"]:02d}  {p["rel"] or "?":17} {p["lid"] or "?":22} {p["weight"] or "":7} {p["series"]}')
    for e in errors:
        print(f'  [FAIL] {e}')
    for h in hints:
        print(f'  [HINT] {h}')
    if not genre and not args.output:
        print('  [HINT] add a **Genre** row (narrative / report / solution) to I. Project Information')
    print('[OK] layout plan passes' if not errors else f'[FAIL] {len(errors)} problem(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
