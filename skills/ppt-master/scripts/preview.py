#!/usr/bin/env python3
"""PPT Master - Pre-generation preview.

Generates a single self-contained HTML file that lets the user preview a
project before (or during) SVG generation, at whatever stage it is
currently in. Up to three tabs are shown depending on what exists:

    - design_spec.md only       -> "设计大纲" outline cards (page/title/layout/points)
    - svg_output/ or svg_final  -> "实际排布" real SVG thumbnail gallery
                                    + "实际文字" plain-text transcript of every
                                    <text> run in each SVG, grouped by page —
                                    useful for spotting how much the Executor
                                    added/rewrote beyond the outline, without
                                    visual layout noise
    - multiple present          -> tabbed view, switch between them

Usage:
    python3 scripts/preview.py <project_path> [--open]
"""

from __future__ import annotations

import argparse
import re
import sys
import webbrowser
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SlideOutline:
    number: str
    title: str
    layout: str = ""
    content: List[str] = field(default_factory=list)
    chart: str = ""
    extra: List[tuple] = field(default_factory=list)  # (label, value) for uncommon fields
    part: str = ""


@dataclass
class SvgPage:
    number: str
    filename: str
    rel_path: str


@dataclass
class SvgTextPage:
    number: str
    filename: str
    lines: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# design_spec.md parsing
# ---------------------------------------------------------------------------

# Matches the two known heading conventions for the outline section:
#   English:  ## IX. Content Outline
#   Chinese:  ## 三、内容大纲（17页）  /  ## 九、内容大纲
OUTLINE_SECTION_RE = re.compile(
    r'^#{2}\s*(?:IX\.?\s*Content Outline|[一二三四五六七八九十]+、?\s*内容大纲)',
    re.IGNORECASE,
)

# Some older specs split the outline into two top-level sections: a summary
# table ("内容大纲") followed by per-page detail ("页面详细规划" /
# "Detailed Page Planning"). When the first section turns out to be just a
# table (no slide headings), keep reading into a section matching this.
DETAIL_SECTION_RE = re.compile(
    r'^#{2}\s*(?:[一二三四五六七八九十]+、?\s*)?(?:页面详细规划|详细规划|Detailed Page Planning)',
    re.IGNORECASE,
)

# A heading that starts the *next* top-level section (ends the outline).
NEXT_SECTION_RE = re.compile(r'^#{2}\s*(?:[IVX]+\.|[一二三四五六七八九十]+、)')

# Chapter/part sub-heading: "### Part 1: xxx" or "### 第一部分 xxx"
PART_RE = re.compile(r'^#{3}\s*(?:Part\s*\d+\s*[:：]?\s*(.*)|第[一二三四五六七八九十\d]+部?分[:：]?\s*(.*))', re.IGNORECASE)

# English style page heading: "#### Slide 01 - Title" (#### level)
SLIDE_HEADING_EN_RE = re.compile(r'^#{3,4}\s*Slide\s*(\d+)\s*[-–—:：]\s*(.+)$', re.IGNORECASE)

# Chinese style page heading: "### 第1页：标题 (file.svg)" (### level)
SLIDE_HEADING_CN_RE = re.compile(
    r'^#{3,4}\s*第\s*(\d+)\s*页\s*[:：]\s*([^(（]+?)\s*[\(（]?([\w./_-]*\.svg)?[\)）]?\s*$'
)

# Field lines inside a slide block, e.g. "- **Layout**: xxx" or "**布局**: xxx"
FIELD_RE = re.compile(r'^[-*]?\s*\*\*([^*]+)\*\*\s*[:：]\s*(.*)$')

FIELD_LABEL_MAP = {
    'layout': 'layout', '布局': 'layout',
    'title': 'title', '标题': 'title', '主标题': 'title',
    'content': 'content', '内容': 'content',
    'chart': 'chart', '图表': 'chart',
    'design notes': 'design_notes', '设计要点': 'design_notes',
}

# Display label shown in the detail panel for "extra" (uncommon) fields.
FIELD_DISPLAY_NAME = {
    'design_notes': '设计要点',
    'subtitle': '副标题',
    'info': '信息',
}


def _normalize_label(label: str) -> str:
    key = label.strip().lower()
    return FIELD_LABEL_MAP.get(key, FIELD_LABEL_MAP.get(label.strip(), key))


def _display_label(label: str) -> str:
    return FIELD_DISPLAY_NAME.get(label, label)


def _extract_outline_block(text: str) -> Optional[str]:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if OUTLINE_SECTION_RE.match(line.strip()):
            start = i + 1
            break
    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        if NEXT_SECTION_RE.match(lines[i].strip()):
            end = i
            break

    block_lines = lines[start:end]

    # If this section has no recognizable slide headings, it's likely just a
    # summary table; the real per-page detail may live in a following
    # "页面详细规划" section. Stitch that in too.
    has_slide_heading = any(
        SLIDE_HEADING_EN_RE.match(l.strip()) or SLIDE_HEADING_CN_RE.match(l.strip())
        for l in block_lines
    )
    if not has_slide_heading:
        detail_start = None
        for i in range(end, len(lines)):
            if DETAIL_SECTION_RE.match(lines[i].strip()):
                detail_start = i + 1
                break
        if detail_start is not None:
            detail_end = len(lines)
            for i in range(detail_start, len(lines)):
                if NEXT_SECTION_RE.match(lines[i].strip()):
                    detail_end = i
                    break
            block_lines = block_lines + lines[detail_start:detail_end]

    return '\n'.join(block_lines)


def _flush_slide(current: Optional[SlideOutline], slides: List[SlideOutline], pending_field: Optional[str],
                  pending_lines: List[str]) -> None:
    if current is None:
        return
    _flush_field(current, pending_field, pending_lines)
    slides.append(current)


def _flush_field(slide: SlideOutline, field_name: Optional[str], lines: List[str]) -> None:
    if not field_name or not lines:
        return
    # Bullet lines (from any field, not just "content") join with line breaks;
    # plain continuation text joins with spaces.
    if all(l.startswith('- ') or l.startswith('* ') for l in lines):
        value = '\n'.join(re.sub(r'^[-*]\s+', '', l) for l in lines)
    else:
        value = ' '.join(l.strip() for l in lines if l.strip())
    if field_name == 'layout':
        slide.layout = value
    elif field_name == 'chart':
        slide.chart = value
    elif field_name == 'title' and not slide.title:
        slide.title = value
    elif field_name == 'content':
        # content may already have bullet lines collected separately
        pass
    else:
        slide.extra.append((field_name, value))


def parse_design_spec(spec_path: Path) -> List[SlideOutline]:
    """Parse the Content Outline section of a design_spec.md file.

    Handles both the canonical English template format and the legacy
    Chinese format found in older example projects. Best-effort: unknown
    or malformed lines are skipped rather than raising.
    """
    text = spec_path.read_text(encoding='utf-8')
    block = _extract_outline_block(text)
    if block is None:
        return []

    slides: List[SlideOutline] = []
    current: Optional[SlideOutline] = None
    current_part = ""
    current_field: Optional[str] = None
    field_buffer: List[str] = []

    def close_field():
        nonlocal current_field, field_buffer
        if current is not None:
            _flush_field(current, current_field, field_buffer)
        current_field = None
        field_buffer = []

    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if stripped in ('---', '***', '___'):
            close_field()
            continue

        part_match = PART_RE.match(stripped)
        if part_match:
            current_part = (part_match.group(1) or part_match.group(2) or '').strip()
            continue

        slide_match = SLIDE_HEADING_EN_RE.match(stripped) or SLIDE_HEADING_CN_RE.match(stripped)
        if slide_match:
            close_field()
            if current is not None:
                slides.append(current)
            groups = slide_match.groups()
            number = groups[0]
            title = groups[1].strip() if len(groups) > 1 and groups[1] else ''
            current = SlideOutline(number=number.zfill(2), title=title, part=current_part)
            continue

        if current is None:
            continue  # content before any recognized slide heading

        field_match = FIELD_RE.match(stripped)
        if field_match:
            close_field()
            label = _normalize_label(field_match.group(1))
            value = field_match.group(2).strip()
            if label == 'content' and not value:
                current_field = 'content'
                field_buffer = []
            else:
                current_field = label
                field_buffer = [value] if value else []
            continue

        # Bullet line under an open "content" field, or a continuation line
        bullet_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if current_field == 'content' and bullet_match:
            current.content.append(bullet_match.group(1).strip())
            continue

        if current_field:
            field_buffer.append(stripped)
        # else: stray text, ignore

    close_field()
    if current is not None:
        slides.append(current)

    return slides


# ---------------------------------------------------------------------------
# SVG discovery
# ---------------------------------------------------------------------------

SVG_NUMBER_RE = re.compile(r'(\d+)')


def discover_svg_pages(svg_dir: Path, project_path: Path) -> List[SvgPage]:
    files = sorted(svg_dir.glob('*.svg'))
    pages: List[SvgPage] = []
    for f in files:
        m = SVG_NUMBER_RE.search(f.stem)
        number = m.group(1).zfill(2) if m else '??'
        pages.append(SvgPage(
            number=number,
            filename=f.name,
            rel_path=f.relative_to(project_path).as_posix(),
        ))
    return pages


def extract_svg_text_pages(svg_dir: Path) -> List[SvgTextPage]:
    """Extract every <text> run from each SVG, in document order.

    Same traversal as verify_pptx_text.py (ET iter + itertext), but here the
    goal is a readable per-page transcript rather than a wrap-check diff.
    """
    import xml.etree.ElementTree as ET

    files = sorted(svg_dir.glob('*.svg'))
    pages: List[SvgTextPage] = []
    for f in files:
        m = SVG_NUMBER_RE.search(f.stem)
        number = m.group(1).zfill(2) if m else '??'
        lines: List[str] = []
        try:
            root = ET.parse(f).getroot()
            for node in root.iter():
                if node.tag.split('}')[-1] != 'text':
                    continue
                text = ''.join(node.itertext()).strip()
                if text:
                    lines.append(text)
        except ET.ParseError:
            lines = ['(SVG 解析失败，无法提取文字)']
        pages.append(SvgTextPage(number=number, filename=f.name, lines=lines))
    return pages


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

PAGE_CSS = """
:root {
  --bg: #f4f5f7; --panel: #ffffff; --border: #e2e4e9; --text: #1f2430;
  --muted: #6b7280; --accent: #2563eb; --accent-soft: #eff4ff; --tag-bg: #eef0f4;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  background: var(--bg); color: var(--text);
}
header.top {
  position: sticky; top: 0; z-index: 10; background: var(--panel);
  border-bottom: 1px solid var(--border); padding: 16px 28px;
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
}
header.top h1 { font-size: 17px; margin: 0; font-weight: 600; }
header.top .meta { color: var(--muted); font-size: 13px; margin-top: 2px; }
.tabs { display: flex; gap: 6px; }
.tab-btn {
  border: 1px solid var(--border); background: var(--panel); color: var(--text);
  padding: 7px 16px; border-radius: 7px; font-size: 13.5px; cursor: pointer;
}
.tab-btn.active { background: var(--accent); border-color: var(--accent); color: #fff; }
main { padding: 24px 28px 60px; max-width: 1400px; margin: 0 auto; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
.notice {
  background: var(--accent-soft); border: 1px solid #c7dbff; color: #1e40af;
  padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 20px;
}
.grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;
}
.card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px 18px; cursor: pointer; transition: box-shadow .15s, transform .15s;
}
.card:hover { box-shadow: 0 6px 20px rgba(0,0,0,.08); transform: translateY(-2px); }
.card .num { font-size: 12px; color: var(--muted); font-weight: 600; letter-spacing: .04em; }
.card .part { font-size: 11px; color: var(--accent); margin-top: 2px; }
.card h3 { font-size: 15px; margin: 6px 0 8px; line-height: 1.4; }
.card .layout-tag {
  display: inline-block; background: var(--tag-bg); color: var(--muted);
  font-size: 11.5px; padding: 2px 8px; border-radius: 5px; margin-bottom: 8px;
}
.card ul { margin: 0; padding-left: 18px; font-size: 12.5px; color: #444; }
.card ul li { margin-bottom: 3px; line-height: 1.45; }
.card .more { color: var(--muted); font-size: 11.5px; margin-top: 4px; }
.svg-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 18px;
}
.svg-card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
  overflow: hidden; cursor: pointer; transition: box-shadow .15s, transform .15s;
}
.svg-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,.08); transform: translateY(-2px); }
.svg-card .thumb {
  aspect-ratio: 16/9; background: #fff; display: flex; align-items: center; justify-content: center;
  border-bottom: 1px solid var(--border); overflow: hidden;
}
.svg-card .thumb img { width: 100%; height: 100%; object-fit: contain; }
.svg-card .label { padding: 8px 10px; font-size: 12.5px; color: var(--text); }
.svg-card .label .num { color: var(--muted); font-weight: 600; margin-right: 6px; }
.empty-state {
  text-align: center; padding: 60px 20px; color: var(--muted); font-size: 14px;
}
.text-list {
  display: flex; flex-direction: column; gap: 14px; max-width: 900px; margin: 0 auto;
}
.text-card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px;
}
.text-card-head {
  display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}
.text-card-head .num { font-size: 12px; color: var(--muted); font-weight: 600; }
.text-card-head .fname { font-size: 13.5px; font-weight: 600; }
.text-card-head .count { margin-left: auto; font-size: 11.5px; color: var(--muted); }
.text-card ul { margin: 0; padding-left: 18px; font-size: 13px; color: #333; columns: 1; }
.text-card ul li { margin-bottom: 4px; line-height: 1.5; }
@media (min-width: 700px) {
  .text-card ul { columns: 2; column-gap: 24px; }
  .text-card ul li { break-inside: avoid; }
}
.lightbox {
  position: fixed; inset: 0; background: rgba(15,17,24,.82); display: none;
  align-items: center; justify-content: center; z-index: 100; padding: 40px;
}
.lightbox.active { display: flex; }
.lightbox img { max-width: 100%; max-height: 100%; background: #fff; border-radius: 6px; }
.lightbox-close {
  position: absolute; top: 24px; right: 32px; color: #fff; font-size: 28px;
  cursor: pointer; background: none; border: none;
}
.detail-panel {
  position: fixed; inset: 0; background: rgba(15,17,24,.5); display: none;
  align-items: center; justify-content: center; z-index: 100; padding: 30px;
}
.detail-panel.active { display: flex; }
.detail-box {
  background: #fff; border-radius: 12px; max-width: 640px; width: 100%;
  max-height: 84vh; overflow-y: auto; padding: 28px 30px; position: relative;
}
.detail-box h2 { margin: 4px 0 4px; font-size: 19px; }
.detail-box .part { color: var(--accent); font-size: 12.5px; margin-bottom: 10px; }
.detail-box .layout-tag { margin-bottom: 14px; }
.detail-box ul { padding-left: 20px; font-size: 14px; line-height: 1.7; }
.detail-close {
  position: absolute; top: 18px; right: 20px; border: none; background: none;
  font-size: 22px; cursor: pointer; color: var(--muted);
}
"""

PAGE_JS = """
function showTab(name) {
  document.querySelectorAll('.tab-panel').forEach(function(p){ p.classList.toggle('active', p.dataset.tab === name); });
  document.querySelectorAll('.tab-btn').forEach(function(b){ b.classList.toggle('active', b.dataset.tab === name); });
}
function openDetail(id) {
  document.getElementById(id).classList.add('active');
}
function closeDetail(id) {
  document.getElementById(id).classList.remove('active');
}
function openLightbox(src) {
  var lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = src;
  lb.classList.add('active');
}
function closeLightbox() {
  document.getElementById('lightbox').classList.remove('active');
}
document.addEventListener('keydown', function(e){
  if (e.key === 'Escape') {
    closeLightbox();
    document.querySelectorAll('.detail-panel.active').forEach(function(p){ p.classList.remove('active'); });
  }
});
"""

LAYOUT_HINT_PATTERNS = [
    (re.compile(r'左.{0,2}右|left.{0,3}right', re.I), '⬛▯ 左右分栏'),
    (re.compile(r'上.{0,2}下|top.{0,3}bottom', re.I), '▭▭ 上下分栏'),
    (re.compile(r'三栏|three.?column', re.I), '▯▯▯ 三栏'),
    (re.compile(r'四.{0,2}宫格|四栏|four.?column|quadrant', re.I), '▦ 四宫格'),
    (re.compile(r'居中|centered|封面|cover', re.I), '◻ 居中'),
    (re.compile(r'卡片|card', re.I), '▢▢▢ 卡片组'),
    (re.compile(r'表格|table', re.I), '▤ 表格'),
]


def layout_hint(layout_text: str) -> str:
    for pattern, hint in LAYOUT_HINT_PATTERNS:
        if pattern.search(layout_text):
            return hint
    return ''


def render_outline_cards(slides: List[SlideOutline]) -> str:
    if not slides:
        return '<div class="empty-state">未能从 design_spec.md 解析出内容大纲（IX. Content Outline 章节）。</div>'

    cards = []
    details = []
    for slide in slides:
        hint = layout_hint(slide.layout)
        layout_display = f'{escape(slide.layout)}' + (f'　<span style="opacity:.6">{hint}</span>' if hint else '')
        preview_items = slide.content[:4]
        more_count = len(slide.content) - len(preview_items)
        li_html = ''.join(f'<li>{escape(item)}</li>' for item in preview_items)
        more_html = f'<div class="more">+{more_count} 更多…</div>' if more_count > 0 else ''
        detail_id = f'detail-{slide.number}'

        cards.append(f'''
        <div class="card" onclick="openDetail('{detail_id}')">
          <div class="num">P{escape(slide.number)}{f" · {escape(slide.part)}" if slide.part else ""}</div>
          <h3>{escape(slide.title) or '(未命名页面)'}</h3>
          {f'<div class="layout-tag">{layout_display}</div>' if slide.layout else ''}
          <ul>{li_html}</ul>
          {more_html}
        </div>''')

        full_li = ''.join(f'<li>{escape(item)}</li>' for item in slide.content) or '<li style="color:#999">(无内容要点)</li>'

        def _render_field_value(value: str) -> str:
            if '\n' in value:
                items = ''.join(f'<li>{escape(v)}</li>' for v in value.split('\n') if v.strip())
                return f'<ul style="margin:4px 0">{items}</ul>'
            return escape(value)

        extra_html = ''.join(
            f'<p style="margin:8px 0"><strong>{escape(_display_label(label))}：</strong>{_render_field_value(value)}</p>'
            for label, value in slide.extra
        )
        details.append(f'''
        <div class="detail-panel" id="{detail_id}">
          <div class="detail-box">
            <button class="detail-close" onclick="closeDetail('{detail_id}')">&times;</button>
            <div class="num">P{escape(slide.number)}</div>
            {f'<div class="part">{escape(slide.part)}</div>' if slide.part else ''}
            <h2>{escape(slide.title) or '(未命名页面)'}</h2>
            {f'<div class="layout-tag">{layout_display}</div>' if slide.layout else ''}
            {f'<p><strong>图表：</strong>{escape(slide.chart)}</p>' if slide.chart else ''}
            <ul>{full_li}</ul>
            {extra_html}
          </div>
        </div>''')

    return f'<div class="grid">{"".join(cards)}</div>{"".join(details)}'


def render_svg_gallery(pages: List[SvgPage], source_label: str) -> str:
    if not pages:
        return f'<div class="empty-state">{escape(source_label)} 目录暂无 SVG 文件。</div>'

    cards = []
    for page in pages:
        title = Path(page.filename).stem
        cards.append(f'''
        <div class="svg-card" onclick="openLightbox('{escape(page.rel_path)}')">
          <div class="thumb"><img src="{escape(page.rel_path)}" loading="lazy" alt="{escape(title)}"></div>
          <div class="label"><span class="num">P{escape(page.number)}</span>{escape(title)}</div>
        </div>''')

    return f'<div class="svg-grid">{"".join(cards)}</div>'


def render_text_pages(pages: List[SvgTextPage], source_label: str) -> str:
    if not pages:
        return f'<div class="empty-state">{escape(source_label)} 目录暂无 SVG 文件。</div>'

    cards = []
    for page in pages:
        title = Path(page.filename).stem
        li_html = ''.join(f'<li>{escape(line)}</li>' for line in page.lines) \
            or '<li style="color:#999">(页面无文字内容)</li>'
        cards.append(f'''
        <div class="text-card">
          <div class="text-card-head">
            <span class="num">P{escape(page.number)}</span>
            <span class="fname">{escape(title)}</span>
            <span class="count">{len(page.lines)} 条文字</span>
          </div>
          <ul>{li_html}</ul>
        </div>''')

    return f'<div class="text-list">{"".join(cards)}</div>'


def build_html(project_name: str, spec_slides: List[SlideOutline],
                svg_pages: List[SvgPage], svg_source_label: str,
                text_pages: List[SvgTextPage]) -> str:
    has_outline = bool(spec_slides)
    has_svg = bool(svg_pages)
    has_text = bool(text_pages)  # only meaningful when has_svg is also true

    # Assemble whichever tabs have content. Falls back to a single empty-state
    # panel when neither the outline nor any SVG could be found.
    tabs: List[tuple] = []  # (key, label, panel_html)
    if has_outline:
        tabs.append(('outline', '设计大纲', render_outline_cards(spec_slides)))
    if has_svg:
        tabs.append(('layout', '实际排布', render_svg_gallery(svg_pages, svg_source_label)))
    if has_text:
        tabs.append(('text', '实际文字', render_text_pages(text_pages, svg_source_label)))

    if not tabs:
        tabs.append(('outline', '设计大纲', render_outline_cards([])))

    # Default view: prefer the real layout gallery when available, else outline.
    default_tab = 'layout' if has_svg else tabs[0][0]

    if has_outline and has_svg:
        notice = '<div class="notice">💡 「设计大纲」基于 design_spec.md 的文字描述；「实际排布」「实际文字」取自 svg_output/svg_final 中已生成的真实页面 —— 三者可能存在差异，差异越大说明 Executor 在生成时补充/改写得越多。</div>'
    elif has_outline:
        notice = '<div class="notice">💡 当前仅有设计大纲，尚未生成 SVG 页面。以下卡片按 design_spec.md 的文字描述展示，非最终排布。</div>'
    elif has_svg:
        notice = ''
    else:
        notice = '<div class="notice">未找到 design_spec.md 大纲内容，也未找到任何 SVG 文件。</div>'

    tabs_html = ''
    if len(tabs) > 1:
        buttons = ''.join(
            f'<button class="tab-btn{" active" if key == default_tab else ""}" '
            f'data-tab="{key}" onclick="showTab(\'{key}\')">{escape(label)}</button>'
            for key, label, _ in tabs
        )
        tabs_html = f'<div class="tabs">{buttons}</div>'

    panels_html = ''.join(
        f'<div class="tab-panel{" active" if key == default_tab else ""}" data-tab="{key}">{panel}</div>'
        for key, _, panel in tabs
    )

    page_count = len(spec_slides) if has_outline else len(svg_pages)
    meta_label = ' + '.join(label for _, label, _ in tabs)

    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(project_name)} - 预览</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="top">
  <div>
    <h1>{escape(project_name)}</h1>
    <div class="meta">{page_count} 页 · {escape(meta_label)}</div>
  </div>
  {tabs_html}
</header>
<main>
  {notice}
  {panels_html}
</main>
<div class="lightbox" id="lightbox" onclick="if(event.target===this) closeLightbox()">
  <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
  <img id="lightbox-img" src="">
</div>
<script>{PAGE_JS}</script>
</body>
</html>'''


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description='Generate a pre-export preview of a PPT Master project.')
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('--open', action='store_true', help='Open the generated preview.html in the default browser')
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f'[error] Project directory not found: {project_path}', file=sys.stderr)
        return 1

    spec_path = project_path / 'design_spec.md'
    spec_slides: List[SlideOutline] = []
    if spec_path.exists():
        spec_slides = parse_design_spec(spec_path)

    svg_final = project_path / 'svg_final'
    svg_output = project_path / 'svg_output'
    if svg_final.exists() and any(svg_final.glob('*.svg')):
        svg_dir, svg_label = svg_final, 'svg_final'
    elif svg_output.exists() and any(svg_output.glob('*.svg')):
        svg_dir, svg_label = svg_output, 'svg_output'
    else:
        svg_dir, svg_label = None, ''

    svg_pages = discover_svg_pages(svg_dir, project_path) if svg_dir else []
    text_pages = extract_svg_text_pages(svg_dir) if svg_dir else []

    if not spec_slides and not svg_pages:
        print('[warn] Neither a parsable design_spec.md outline nor SVG pages were found.', file=sys.stderr)
        print('       Nothing meaningful to preview yet.', file=sys.stderr)

    html = build_html(project_path.name, spec_slides, svg_pages, svg_label, text_pages)
    out_path = project_path / 'preview.html'
    out_path.write_text(html, encoding='utf-8')

    print(f'[ok] Preview written to: {out_path}')
    print(f'     Outline pages parsed: {len(spec_slides)}')
    print(f'     SVG pages found ({svg_label or "none"}): {len(svg_pages)}')
    if text_pages:
        total_lines = sum(len(p.lines) for p in text_pages)
        print(f'     Text runs extracted: {total_lines} across {len(text_pages)} page(s)')

    if args.open:
        webbrowser.open(out_path.as_uri())

    return 0


if __name__ == '__main__':
    sys.exit(main())
