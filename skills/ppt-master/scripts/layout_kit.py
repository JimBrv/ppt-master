#!/usr/bin/env python3
"""
PPT Master - Content layout kit.

A content layout is a complete page SVG whose text lives in {{SLOT}}
placeholders, each with a known capacity in full-width characters. This
module builds layouts (used by templates/layouts/<template>/content_src/)
and fills them (used by layout_fill.py and layout_stress.py).

Not a command-line tool; import it.
"""
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Code points above this count as one full-width character; below, 0.55.
WIDE_CODEPOINT = 0x2E7F
NARROW_WIDTH = 0.55

SLOT_RE = re.compile(r'\{\{(\w+)\}\}')


def text_units(s: str) -> float:
    """Approximate rendered width of s, in full-width characters."""
    return sum(1 if ord(c) > WIDE_CODEPOINT else NARROW_WIDTH for c in s)


def slot_pattern(name: str) -> str:
    """COL2_CARD3_L1 -> COL{n}_CARD{n}_L{n}: the key used in layouts.json."""
    return re.sub(r'\d+', '{n}', name)


def grad(id: str, a: str, b: str) -> str:
    """A horizontal two-stop linear gradient for a layout's <defs>."""
    return (f'    <linearGradient id="{id}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" stop-color="{a}"/><stop offset="100%" stop-color="{b}"/></linearGradient>')


@dataclass
class Shell:
    """What every content layout of one template shares."""
    name: str                                   # shown in each layout's header comment
    font: str
    images: List[Tuple[str, str, str, str, str]]  # (href, x, y, width, height), back to front
    title: Tuple[int, int, int, str, int]        # (x, y, font size, color, capacity)
    page_num: Tuple[int, int, int, str]          # (x, y, font size, color)
    image_slot_fill: str = '#F4F7FB'
    ink: str = '#0F1423'


class Layout:
    """Builder for one content layout. Text slots record their capacity."""

    def __init__(self, id: str, shell: Shell):
        self.id, self.shell = id, shell
        self.p: List[str] = []
        self.caps: Dict[str, int] = {}
        self.icons = set()
        self.imgs: List[dict] = []
        self.defs = ''

    def t(self, x, y, slot, size, maxw, fill=None, bold=False, anchor=None, italic=False):
        """One single-line text slot; capacity = box width / font size."""
        self.caps[slot] = int(maxw / size)
        a = f' text-anchor="{anchor}"' if anchor else ''
        b = ' font-weight="bold"' if bold else ''
        i = ' font-style="italic"' if italic else ''
        fill = fill or self.shell.ink
        self.p.append(f'  <text x="{x}" y="{y}" font-family="{self.shell.font}" font-size="{size}"{b}{i}{a} '
                      f'fill="{fill}">{{{{{slot}}}}}</text>')

    def rr(self, x, y, w, h, r=0, fill='none', op=None, stroke=None, sw=1, box=None):
        """Rect; box=SLOT marks it as that slot's container, removed with the slot."""
        bx = f' data-slot-box="{box}"' if box else ''
        rx = f' rx="{r}"' if r else ''
        o = f' fill-opacity="{op}"' if op is not None else ''
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.p.append(f'  <rect{bx} x="{x}" y="{y}" width="{w}" height="{h}"{rx} fill="{fill}"{o}{st}/>')

    def c(self, cx, cy, r, fill, op=None):
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{o}/>')

    def ring(self, cx, cy, r, stroke, sw, op=None):
        o = f' stroke-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{stroke}" stroke-width="{sw}"{o}/>')

    def poly(self, pts, fill, op=None):
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <polygon points="{pts}" fill="{fill}"{o}/>')

    def path(self, d, fill='none', stroke=None, sw=None, op=None):
        st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"' if stroke else ''
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <path d="{d}" fill="{fill}"{st}{o}/>')

    def raw(self, line):
        """An element the helpers do not cover, e.g. a dashed path or ellipse."""
        self.p.append(f'  {line}')

    def icon(self, x, y, size, slot, fill):
        self.icons.add(slot)
        self.p.append(f'  <use data-icon="{{{{{slot}}}}}" x="{x}" y="{y}" width="{size}" height="{size}" fill="{fill}"/>')

    def img(self, x, y, w, h, name):
        """Image placeholder; layout_fill.py swaps it for an <image> of the same box."""
        self.imgs.append(dict(name=name, x=x, y=y, w=w, h=h))
        self.p.append(f'  <rect data-image-slot="{name}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
                      f'fill="{self.shell.image_slot_fill}" stroke="#9CAEC3" stroke-width="1" stroke-dasharray="6,4"/>')

    def note(self, text):
        self.p.append(f'  <!-- {text} -->')

    def svg(self) -> str:
        s = self.shell
        d = f'  <defs>\n{self.defs}\n  </defs>\n' if self.defs else ''
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1280 720">\n'
                f'  <!-- {s.name} content layout: {self.id}. Fill every slot; see layouts.json for capacity. -->\n{d}')
        head += ''.join(f'  <image href="{h}" x="{x}" y="{y}" width="{w}" height="{hh}" preserveAspectRatio="none"/>\n'
                        for h, x, y, w, hh in s.images)
        tx, ty, tsize, tcolor, tcap = s.title
        px, py, psize, pcolor = s.page_num
        self.caps['PAGE_TITLE'] = tcap
        self.caps['PAGE_NUM'] = 3
        title = (f'  <text x="{tx}" y="{ty}" font-family="{s.font}" font-size="{tsize}" font-weight="bold" '
                 f'fill="{tcolor}">{{{{PAGE_TITLE}}}}</text>\n')
        num = (f'\n  <text x="{px}" y="{py}" font-family="{s.font}" font-size="{psize}" text-anchor="end" '
               f'fill="{pcolor}">{{{{PAGE_NUM}}}}</text>\n</svg>\n')
        return head + title + '\n'.join(self.p) + num


def write_library(out_dir: Path, layouts: List[Layout], meta: Dict[str, dict], usage: str) -> dict:
    """Write each layout's SVG plus the layouts.json index; return the index."""
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = {}
    for lay in layouts:
        if lay.id not in meta:
            raise KeyError(f'no metadata for layout {lay.id}')
        (out_dir / f'{lay.id}.svg').write_text(lay.svg(), encoding='utf-8')
        pat: Dict[str, int] = {}
        for slot, cap in lay.caps.items():
            k = slot_pattern(slot)
            pat[k] = min(pat.get(k, 999), cap)
        icons = sorted({slot_pattern(i) for i in lay.icons})
        entries[lay.id] = {**meta[lay.id], 'slots': pat, 'iconSlots': icons, 'imageSlots': lay.imgs}
    index = {'meta': {'version': 1, 'canvas': '0 0 1280 720', 'usage': usage}, 'layouts': entries}
    (out_dir / 'layouts.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return index


def fill_layout(svg: str, values: Dict[str, object], caps: Dict[str, int],
                icon_dir: Optional[Path] = None, image_dir: Optional[Path] = None):
    """Fill a layout SVG. Returns (svg, errors, removed_slots).

    values maps slot name -> text (icon slots take an icon name), plus an
    optional "_images": {image_slot: filename in images/}. A text, icon or
    container (data-slot-box) whose slot has no value is removed; unfilled
    image slots stay as placeholders. Any error means the result is unusable.
    """
    errors: List[str] = []
    images = dict(values.get('_images') or {})
    vals = {k: v for k, v in values.items() if not k.startswith('_')}
    known = set(SLOT_RE.findall(svg))
    icon_slots = set(re.findall(r'data-icon="\{\{(\w+)\}\}"', svg))

    for k in sorted(set(vals) - known):
        errors.append(f'unknown slot: {k}')
    for name, val in vals.items():
        if not isinstance(val, str):
            errors.append(f'{name}: value must be a string')
            continue
        if name in icon_slots:
            if icon_dir is not None and not (icon_dir / f'{val}.svg').exists():
                errors.append(f'{name}: icon not in library: {val}')
            continue
        cap = caps.get(slot_pattern(name))
        if cap is not None and text_units(val) > cap:
            errors.append(f'{name}: {text_units(val):.1f} wide, capacity {cap}: {val}')
    for name, file in images.items():
        if f'data-image-slot="{name}"' not in svg:
            errors.append(f'unknown image slot: {name}')
        elif image_dir is not None and not (image_dir / file).exists():
            errors.append(f'{name}: image not found in images/: {file}')

    removed: List[str] = []

    def unless_filled(m):
        if m.group(1) in vals:
            return m.group(0)
        removed.append(m.group(1))
        return ''

    svg = re.sub(r'^[ \t]*<rect data-slot-box="(\w+)"[^>]*/>\n', unless_filled, svg, flags=re.M)
    svg = re.sub(r'^[ \t]*<text[^>]*>\s*\{\{(\w+)\}\}\s*</text>\n', unless_filled, svg, flags=re.M)
    svg = re.sub(r'^[ \t]*<use data-icon="\{\{(\w+)\}\}"[^>]*/>\n', unless_filled, svg, flags=re.M)

    for name, file in images.items():
        m = re.search(rf'<rect data-image-slot="{name}" x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"[^>]*/>', svg)
        if m:
            x, y, w, h = m.groups()
            svg = svg.replace(m.group(0), f'<image href="../images/{file}" x="{x}" y="{y}" width="{w}" height="{h}" '
                                          f'preserveAspectRatio="xMidYMid meet"/>')

    svg = SLOT_RE.sub(lambda m: html.escape(vals[m.group(1)], quote=False) if m.group(1) in vals else m.group(0), svg)
    left = sorted(set(SLOT_RE.findall(svg)))
    if left:
        errors.append(f'unfilled slots: {left}')
    return svg, errors, sorted(set(removed))
