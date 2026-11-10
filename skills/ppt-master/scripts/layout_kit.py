#!/usr/bin/env python3
"""
PPT Master - Content layout kit.

A content layout is a complete page SVG whose text lives in {{SLOT}}
placeholders, each with a known capacity in full-width characters.

Layouts are split into three parts so one structure serves every template:

  templates/content_library/library.py   structure only: geometry, slots, and
                                         color *roles* (ink, primary, levels...)
  <template>/content_src/theme.json      the template's color for each role,
                                         title capacity, and the body box
  <template>/content_src/shell.svg       the template's own page furniture:
                                         background, logo, title, page number

layout_build.py combines them into <template>/content/. This module is the
shared engine; layout_fill.py and layout_stress.py use it too.
"""
import html
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WIDE_CODEPOINT = 0x2E7F
NARROW_WIDTH = 0.55
SLOT_RE = re.compile(r'\{\{(\w+)\}\}')

# The region the library's layouts are drawn in; body_box in theme.json maps
# it onto a template whose header or footer takes more room.
CANONICAL_BODY = (0, 130, 1280, 705)

# The relation vocabulary. A page's content has one of these relations; a
# layout declares the relations it can show (META "relations") and a claim
# its visual makes. The Strategist picks the relation first, then a layout
# that shows it. Keys are what design_spec.md and layouts.json use.
RELATIONS = {
    'statement':        ('论断', '核心是…；一句引语；号召'),
    'metric':           ('数字', '具体数值、比例、规模、时间点'),
    'contrast':         ('对照', '而不是…；误区与事实；之前与之后；两个极端'),
    'problem_solution': ('问题-对策', '风险是…，应对是…'),
    'parallel':         ('并列', '同时；分别；三个方面'),
    'sequence':         ('顺序', '然后；依次；第一步'),
    'escalation':       ('递进', '逐步升级；越来越；成熟度'),
    'layering':         ('分层', '基于；支撑；由外到内'),
    'convergence':      ('收敛', '筛选；层层过滤；最终'),
    'cycle':            ('循环', '闭环；反馈；持续迭代'),
    'hub':              ('中心辐射', '围绕；连接；以…为核心'),
    'classification':   ('分档', '分为几档；属于哪一类'),
    'chain_core':       ('链路+核心', '整条链路；贯穿；支撑与约束'),
    'evidence':         ('论点+证据', '如图所示；案例截图；实测结果'),
    'timeline':         ('时间线', '年份；日期；里程碑'),
    'matrix':           ('二维矩阵', '两个维度；高低×快慢；象限'),
}

# Layout weight by the number of text slots it holds when fully filled.
WEIGHTS = ((12, 'light'), (30, 'medium'), (10 ** 9, 'heavy'))

# Content text runs per body page, by genre: (average, single-page maximum).
# The page title, the page number and a layout's fixed labels (its
# "labelSlots": series tags, section captions, axis names) do not count.
# The average may be a (target, ceiling) range; a hint fires above the ceiling.
DENSITY = {'narrative': ((20, 25), 25), 'report': (25, 40), 'solution': (35, 50)}


def weight_of(runs: int) -> str:
    return next(w for limit, w in WEIGHTS if runs <= limit)


def text_units(s: str) -> float:
    """Approximate rendered width of s, in full-width characters."""
    return sum(1 if ord(c) > WIDE_CODEPOINT else NARROW_WIDTH for c in s)


def slot_pattern(name: str) -> str:
    """COL2_CARD3_L1 -> COL{n}_CARD{n}_L{n}: the key used in layouts.json."""
    return re.sub(r'\d+', '{n}', name)


def grad(id: str, a: str, b: str) -> str:
    return (f'    <linearGradient id="{id}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" stop-color="{a}"/><stop offset="100%" stop-color="{b}"/></linearGradient>')


# --------------------------------------------------------------------------
# Color
# --------------------------------------------------------------------------

def _rgb(h: str) -> Tuple[float, float, float]:
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hex(rgb) -> str:
    return '#' + ''.join(f'{round(max(0, min(1, c)) * 255):02X}' for c in rgb)


def mix(a: str, b: str, t: float) -> str:
    """Blend a toward b by t (0 = a, 1 = b)."""
    return _hex(tuple(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))


def luminance(h: str) -> float:
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# Every role the library uses. A theme must give the first group; the rest
# are derived when absent, so a new template needs only a handful of colors.
BASE_ROLES = ('primary', 'ink', 'surface', 'page_bg', 'on_accent')
LIST_ROLES = {   # name: length
    'levels': 4, 'ramp': 6, 'trio_a': 3, 'trio_b': 3, 'steps': 4, 'pills': 3,
    'channels': 3, 'track': 5, 'tier_fill': 3, 'tier_text': 3, 'tier_mark': 3,
}


def derive_roles(t: dict) -> dict:
    p, ink, surf = t['primary'], t['ink'], t['surface']
    dark = luminance(t['page_bg']) < 0.2
    up = '#000000' if not dark else '#FFFFFF'   # toward stronger contrast
    d = {
        'secondary': mix(p, ink, 0.25), 'deep': mix(p, up, 0.12), 'strong': p, 'bright': mix(p, surf, 0.2),
        'bright_end': p, 'emphasis': p, 'node_title': mix(p, up, 0.25), 'label': mix(p, up, 0.3),
        'outline': p, 'outline_soft': mix(p, surf, 0.55), 'head_end': mix(p, surf, 0.45), 'card_tint': p,
        'tint': mix(p, surf, 0.95), 'halo': mix(p, surf, 0.84), 'line': mix(p, surf, 0.82),
        'line_soft': mix(p, surf, 0.8), 'panel': mix(p, surf, 0.88), 'shade': mix(p, surf, 0.7),
        'text': mix(ink, surf, 0.15), 'muted': mix(ink, surf, 0.45), 'ink_strong': ink,
        'placeholder_stroke': mix(ink, surf, 0.6),
    }
    series = t.get('series') or [p, d['secondary'], mix(p, surf, 0.4), d['deep'], mix(p, ink, 0.5), mix(p, surf, 0.6)]
    s = (series * 3)[:6]
    d.update({
        'levels': s[:4], 'ramp': s[:6], 'trio_a': s[:3], 'trio_b': s[3:6], 'steps': [s[5], s[0], s[1], s[2]],
        'pills': s[:3], 'channels': s[:3], 'track': [s[0], s[1], s[2], s[3], s[4]],
        'tier_fill': s[:3], 'tier_text': s[:3], 'tier_mark': s[:3],
    })
    return d


class Theme:
    """Role -> color lookup, e.g. T.primary, T.levels[2]."""

    def __init__(self, data: dict):
        missing = [r for r in BASE_ROLES if r not in data.get('colors', {})]
        if missing:
            raise ValueError(f'theme.json colors missing required roles: {missing}')
        colors = dict(data['colors'])
        merged = {**derive_roles(colors), **colors}
        for name, n in LIST_ROLES.items():
            if len(merged[name]) != n:
                raise ValueError(f'theme.json colors.{name} must have {n} entries')
        self.colors = merged
        self.name = data.get('name', 'Template')
        self.font = data.get('font', 'Microsoft YaHei, SimHei, sans-serif')
        self.id_prefix = data.get('id_prefix', 'ly')
        self.title_capacity = int(data.get('title_capacity', 22))
        self.body_box = tuple(data['body_box']) if data.get('body_box') else None
        self.reserved = [tuple(r) for r in data.get('reserved', [])]

    def __getattr__(self, k):
        try:
            return self.__dict__['colors'][k]
        except KeyError:
            raise AttributeError(f'theme has no color role {k!r}') from None

    def contrast_warnings(self, minimum=3.0) -> List[str]:
        out = []
        c = self.colors
        for role in ('ink', 'text', 'muted', 'ink_strong', 'deep', 'strong', 'secondary', 'emphasis',
                     'node_title', 'label', 'bright'):
            for bg in ('surface', 'page_bg'):
                r = contrast(c[role], c[bg])
                if r < minimum:
                    out.append(f'{role} {c[role]} on {bg} {c[bg]}: {r:.1f}:1')
        for bg in ['primary', 'deep'] + [f'{n}[{i}]' for n in ('levels', 'trio_a', 'trio_b', 'steps', 'tier_fill')
                                          for i in range(LIST_ROLES[n])]:
            col = c[bg] if '[' not in bg else c[bg.split('[')[0]][int(bg[-2])]
            r = contrast(c['on_accent'], col)
            if r < minimum:
                out.append(f'on_accent {c["on_accent"]} on {bg} {col}: {r:.1f}:1')
        for i, (txt, fill) in enumerate(zip(c['tier_text'], ['surface'] * 3)):
            r = contrast(txt, c[fill])
            if r < minimum:
                out.append(f'tier_text[{i}] {txt} on surface {c[fill]}: {r:.1f}:1')
        return out


# --------------------------------------------------------------------------
# Building
# --------------------------------------------------------------------------

def _num(v):
    return float(v)


class Layout:
    """Builder for one content layout. Text slots record their capacity;
    every element extends the layout's bounding box unless it is marked
    bleed (an intentional full-width band), which the conflict check skips."""

    def __init__(self, id: str, theme: Theme):
        self.id, self.T = id, theme
        self.p: List[str] = []
        self.caps: Dict[str, int] = {}
        self.icons = set()
        self.imgs: List[dict] = []
        self.defs = ''
        self.boxes: List[Tuple[float, float, float, float]] = []

    def _extend(self, x0, y0, x1, y1, bleed=False):
        if not bleed:
            self.boxes.append((x0, y0, x1, y1))

    def t(self, x, y, slot, size, maxw, fill=None, bold=False, anchor=None, italic=False):
        self.caps[slot] = int(maxw / size)
        x0 = x if anchor in (None, 'start') else (x - maxw / 2 if anchor == 'middle' else x - maxw)
        self._extend(x0, y - size, x0 + maxw, y + size * 0.25)
        a = f' text-anchor="{anchor}"' if anchor else ''
        b = ' font-weight="bold"' if bold else ''
        i = ' font-style="italic"' if italic else ''
        fill = fill or self.T.ink
        self.p.append(f'  <text x="{x}" y="{y}" font-family="{self.T.font}" font-size="{size}"{b}{i}{a} '
                      f'fill="{fill}">{{{{{slot}}}}}</text>')

    def rr(self, x, y, w, h, r=0, fill='none', op=None, stroke=None, sw=1, box=None, bleed=False):
        self._extend(x, y, x + w, y + h, bleed)
        bx = f' data-slot-box="{box}"' if box else ''
        rx = f' rx="{r}"' if r else ''
        o = f' fill-opacity="{op}"' if op is not None else ''
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.p.append(f'  <rect{bx} x="{x}" y="{y}" width="{w}" height="{h}"{rx} fill="{fill}"{o}{st}/>')

    def c(self, cx, cy, r, fill, op=None):
        self._extend(cx - r, cy - r, cx + r, cy + r)
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{o}/>')

    def ring(self, cx, cy, r, stroke, sw, op=None):
        self._extend(cx - r, cy - r, cx + r, cy + r)
        o = f' stroke-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{stroke}" stroke-width="{sw}"{o}/>')

    def _extend_points(self, text, bleed):
        nums = [_num(v) for v in re.findall(r'-?\d+(?:\.\d+)?', text)]
        xs, ys = nums[0::2], nums[1::2]
        if xs and ys:
            self._extend(min(xs), min(ys), max(xs), max(ys), bleed)

    def poly(self, pts, fill, op=None, bleed=False):
        self._extend_points(pts, bleed)
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <polygon points="{pts}" fill="{fill}"{o}/>')

    def path(self, d, fill='none', stroke=None, sw=None, op=None, bleed=False):
        self._extend_points(re.sub(r'[A-Za-z]', ' ', d), bleed)
        st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"' if stroke else ''
        o = f' fill-opacity="{op}"' if op is not None else ''
        self.p.append(f'  <path d="{d}" fill="{fill}"{st}{o}/>')

    def raw(self, line, box=None, bleed=False):
        """An element the helpers do not cover; pass its bounding box."""
        if box:
            self._extend(*box, bleed=bleed)
        self.p.append(f'  {line}')

    def icon(self, x, y, size, slot, fill):
        self._extend(x, y, x + size, y + size)
        self.icons.add(slot)
        self.p.append(f'  <use data-icon="{{{{{slot}}}}}" x="{x}" y="{y}" width="{size}" height="{size}" fill="{fill}"/>')

    def img(self, x, y, w, h, name):
        self._extend(x, y, x + w, y + h)
        self.imgs.append(dict(name=name, x=x, y=y, w=w, h=h))
        self.p.append(f'  <rect data-image-slot="{name}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
                      f'fill="{self.T.tint}" stroke="{self.T.placeholder_stroke}" stroke-width="1" stroke-dasharray="6,4"/>')

    def note(self, text):
        self.p.append(f'  <!-- {text} -->')


def body_transform(theme: Theme) -> Optional[Tuple[float, float, float]]:
    """(tx, ty, scale) mapping CANONICAL_BODY into theme.body_box, or None."""
    if not theme.body_box or tuple(theme.body_box) == CANONICAL_BODY:
        return None
    cx0, cy0, cx1, cy1 = CANONICAL_BODY
    bx0, by0, bx1, by1 = theme.body_box
    s = min((bx1 - bx0) / (cx1 - cx0), (by1 - by0) / (cy1 - cy0))
    tx = bx0 + ((bx1 - bx0) - (cx1 - cx0) * s) / 2 - cx0 * s
    ty = by0 - cy0 * s
    return round(tx, 2), round(ty, 2), round(s, 4)


def render(lay: Layout, shell: str) -> str:
    """Place a built layout into the template shell."""
    defs = f'  <defs>\n{lay.defs}\n  </defs>\n' if lay.defs else ''
    body = '\n'.join(lay.p)
    tr = body_transform(lay.T)
    if tr:
        tx, ty, s = tr
        body = f'  <g transform="translate({tx},{ty}) scale({s})">\n' + body + '\n  </g>'
    lay.caps['PAGE_TITLE'] = lay.T.title_capacity
    lay.caps['PAGE_NUM'] = 3
    return shell.replace('%%LAYOUT_ID%%', lay.id).replace('%%DEFS%%', defs).replace('%%BODY%%', body)


def mapped_boxes(lay: Layout):
    tr = body_transform(lay.T)
    if not tr:
        return list(lay.boxes)
    tx, ty, s = tr
    return [(x0 * s + tx, y0 * s + ty, x1 * s + tx, y1 * s + ty) for x0, y0, x1, y1 in lay.boxes]


def conflicts(lay: Layout) -> List[str]:
    """Elements that overlap a reserved shell area (logo, header, footer)."""
    out = []
    for r in lay.T.reserved:
        rx0, ry0, rx1, ry1 = r
        hits = [b for b in mapped_boxes(lay) if b[0] < rx1 and rx0 < b[2] and b[1] < ry1 and ry0 < b[3]]
        if hits:
            x0, y0, x1, y1 = hits[0]
            out.append(f'{len(hits)} element(s) overlap reserved {list(r)}, '
                       f'e.g. ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})')
    return out


def write_library(out_dir: Path, layouts: List[Layout], meta: Dict[str, dict], usage: str, shell: str) -> dict:
    """Write each layout's SVG plus the layouts.json index; return the index."""
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = {}
    for lay in layouts:
        if lay.id not in meta:
            raise KeyError(f'no metadata for layout {lay.id}')
        (out_dir / f'{lay.id}.svg').write_text(render(lay, shell), encoding='utf-8')
        pat: Dict[str, int] = {}
        for slot, cap in lay.caps.items():
            k = slot_pattern(slot)
            pat[k] = min(pat.get(k, 999), cap)
        icons = sorted({slot_pattern(i) for i in lay.icons})
        m = meta[lay.id]
        bad = [r for r in m.get('relations', []) if r not in RELATIONS]
        if not m.get('relations') or bad or not m.get('claim'):
            raise ValueError(f'{lay.id}: metadata needs "relations" from RELATIONS and a "claim"'
                             + (f'; unknown: {bad}' if bad else ''))
        labels = list(m.get('labels', []))
        unknown = [x for x in labels if x not in pat]
        if unknown:
            raise ValueError(f'{lay.id}: labels {unknown} are not slots of this layout')
        runs = len([k for k in lay.caps
                    if k not in ('PAGE_TITLE', 'PAGE_NUM') and slot_pattern(k) not in labels])
        entries[lay.id] = {**{k: v for k, v in m.items() if k != 'labels'},
                           'maxRuns': runs, 'weight': weight_of(runs), 'labelSlots': labels,
                           'slots': pat, 'iconSlots': icons, 'imageSlots': lay.imgs}
    index = {'meta': {'version': 2, 'canvas': '0 0 1280 720', 'usage': usage,
                      'relations': {k: v[0] for k, v in RELATIONS.items()}},
             'layouts': entries}
    (out_dir / 'layouts.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return index


# --------------------------------------------------------------------------
# Filling
# --------------------------------------------------------------------------

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
