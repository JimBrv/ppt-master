# QAX Style (奇安信) - Design Specification

> Corporate cybersecurity brand template for Qi An Xin (奇安信). Suitable for business planning, security reports, technical solutions, and corporate presentations.

## I. Template Overview

- **Brand**: 奇安信 Qi An Xin — 新一代网络安全领军者
- **Design Tone**: Authoritative, clean, tech-corporate, precise
- **Key Visual Elements**:
  - Right-side tiger silhouette (网安虎) with binary digits, part of the background image
  - Yellow tiger logo with QAX wordmark
  - White-to-light-blue bottom gradient, part of the background image
  - Left-aligned bold titles

## II. Canvas Specification

- **Aspect Ratio**: 16:9
- **viewBox**: `0 0 1280 720`

## III. Brand Assets

Backgrounds and the logo are real image files, referenced as `../images/<file>`. Copy the template's `<image>` tags verbatim; never redraw them.

| File | Used by |
|------|---------|
| `qax_bg_cover.jpg` | `01_cover.svg` |
| `qax_bg_chapter.jpg` | `02_chapter.svg` |
| `qax_bg_content.jpg` | `03_content.svg`, all `content/*.svg` |
| `qax_bg_ending.jpg` | `04_ending.svg` |
| `qax_logo.png` | Chapter and content pages, at x=992.3 y=0 w=275.2 h=110.4. The cover and ending backgrounds already carry the logo. |

## IV. Color Scheme

| Role | HEX | Usage |
|------|-----|-------|
| **QAX Blue** | `#003893` | Cover, chapter, and ending text; content-layout page titles |
| **Shell Title Blue** | `#1D4F9F` | Page title in `03_content.svg` |
| **Primary Blue** | `#2C7FEF` | Solid panels, stage labels |
| **Deep Blue** | `#1E6BEE` | Emphasis text, icons, bands |
| **Header Gradient** | `#1773ED` → `#6C9CE5` | Column headers |
| **Tint / Halo** | `#F4F7FB` / `#D9E8FC` | Card fills, callouts |
| **Border** | `#D4E5FC` | Card outlines |
| **Series Colors** | `#62CB78` `#30C0B4` `#42AFF0` `#75BD42` `#28A963` | Sequences and levels |
| **Insight Accent** | `#0884E2` on `#E5F2FC` | Insight bar in `03_content.svg` |
| **Body Text** | `#0F1423` / `#333333` | Primary body text |
| **Muted Text** | `#666666` / `#9CAEC3` | Dates, sources, page numbers |

## V. Typography System

Font stack: `Microsoft YaHei, SimHei, sans-serif`. Sizes are SVG px; 1pt ≈ 1.33px on this canvas.

| Element | Size | Weight |
|---------|------|--------|
| Cover title | 54px | Bold |
| Cover subtitle | 28px | Regular |
| Chapter title | 48px | Bold |
| Chapter items | 28px | Regular |
| Ending message | 64px | Bold |
| Page title, content layouts | 40px | Bold |
| Page title, `03_content.svg` | 36px | Bold |
| Card and column titles | 20–26px | Bold |
| Body text | 15–18px | Regular |
| Captions and page numbers | 14px | Regular |

## VI. Page Structure

| Page | Key geometry |
|------|--------------|
| Cover | Title x=103 y=420; subtitle y=510; date y=640 |
| Chapter / TOC | Title x=60 y=90; items x=100 from y=220, 70px apart |
| Content shell (`03_content.svg`) | Title x=50 y=62; summary y=110; insight bar y=140 h=50; content area x=50 y=210 w=1180 h=450; source y=695; page number right-aligned at x=1230 |
| Content layouts (`content/*.svg`) | Title x=58 y=88; body fills y=140–695 |
| Ending | Message x=100 y=330 and y=440; slogan x=108 y=545 |

## VII. Content Layouts

`content/layouts.json` indexes fifteen ready-made content pages. Prefer one of these for every body page; use `03_content.svg` only when none fits.

| ID | Best for |
|----|----------|
| `three_pillars` | Three parallel themes |
| `chevron_stages` | Three sequential stages |
| `stair_steps` | Graded levels, low to high |
| `layered_rows` | Layered architectures |
| `hub_numbered_rows` | One concept, three dimensions |
| `image_stack_pills` | Advantage lists with a hero image |
| `loop_nodes` | Five-step closed loops |
| `stage_matrix_evidence` | Case studies backed by a screenshot |
| `architecture_radial` | End-to-end architecture: inputs, central hub, outputs |
| `probe_tier_channels` | One platform connecting several channels |
| `three_track_checklist` | Three parallel step-by-step checklists |
| `tier_chip_pyramid` | Compatibility or support matrices by tier |
| `chain_core_grid` | A chain, a core engine, and its constraints |
| `funnel_layers` | Layers that progressively filter or converge |
| `arrow_track_columns` | Modes or policies that escalate in stages |

## VIII. SVG Technical Constraints

- `viewBox="0 0 1280 720"`
- Use `fill-opacity` for transparency (NO `rgba()`)
- NO `clipPath`, `mask`, `<foreignObject>`, `<style>`, `class`
- Gradients via `<defs>` + `<linearGradient>`
