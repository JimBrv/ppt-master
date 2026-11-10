# PPT Master — AI generates natively editable PPTX from any document

[![Version](https://img.shields.io/badge/version-v2.3.x-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Based on](https://img.shields.io/badge/based%20on-hugohe3%2Fppt--master-orange.svg)](https://github.com/hugohe3/ppt-master)

**English** | [中文](./README_CN.md)

---

## 📢 About This Fork

> **This repository is a fork of [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) with the following improvements and extensions.**

### 🔧 Key Improvements in this Fork

| Category | Description |
|----------|-------------|
| **🐛 PTY Terminal I/O Fix** | Resolved terminal hang caused by the 4096-char PTY buffer limit when AI writes large files (SVG / design_spec.md). Replaced the Base64 workaround with a stable pipeline of **local `tmp/` staging + plain-text chunked writes**, and hardened `file_write.py` and related spec docs. |
| **🖼️ PDF Image Black Background Fix** | When `pdf_to_md.py` extracts images from PDFs, PNG files with alpha transparency saved directly as JPEG produce black backgrounds. Fixed by **using Pillow to composite alpha onto a white background** before saving, and unified output to JPEG (quality=92) to eliminate extension mismatches. |
| **📊 Excel → Markdown Tool** | Added `excel_to_md.py`: supports `.xlsx / .xlsm / .xltx / .xltm`, multi-sheet sectioned output, merged-cell annotations, hyperlink conversion, cell comment extraction, embedded image export (with black-bg fix), named range summary, and automatic date formatting. |
| **📌 Temp File Convention** | All intermediate files generated during processing are written to a per-project `tmp/` subdirectory and cleaned up automatically on completion. Enforced as a mandatory rule in `SKILL.md`. |
| **📦 uv Environment** | This project uses [uv](https://github.com/astral-sh/uv) as the Python package and virtual-environment manager instead of plain `pip`. All scripts are run via `uv run python3 <script>`, dependencies are installed with `uv pip install`, and project config lives in `pyproject.toml`. |
| **📋 AGENTS.md Update** | Updated the quick-reference command table, added the `excel_to_md.py` entry, and documented the PTY I/O bypass rule. |
| **🛡️ QAX (奇安信) Default Template** | Brand template with the real background art and logo extracted from QAX decks. Recommended by default when no template is named (the user still confirms). |
| **📐 Content Layouts** | 22 ready-made body-page layouts (statement, key metrics, problem → response, contrast, pillars, stages, funnel, pyramid, timeline, 2×2, ...), each declaring the content relation it shows and a claim to test it against. Each is a complete page with `{{SLOT}}` text and per-slot capacity; `layout_fill.py` fills one and rejects overflow. Shipped for `奇安信`, `mckinsey` and `pixel_retro`. |
| **🧭 Relation-driven Layout Choice** | The Strategist picks each body page's layout from the content's relation (16-word vocabulary), checks the layout's visual claim, keeps parallel sections on one layout, and sizes text to the genre (narrative / report / solution). `layout_plan_check.py` checks the plan. |
| **🧩 Shared Layout Library** | Layouts are written once against color roles (`templates/content_library/`); a template adds only `theme.json` + `shell.svg`, and `layout_build.py` produces its `content/`. `pptx_inspect.py` and `layout_stress.py` absorb new layouts from reference decks and stress-test them. |
| **🎨 Your .pptx as the Template** | `pptx_to_template.py` turns a user-supplied `.pptx` into a template with its real backgrounds and logos at exact positions. |
| **👀 Live Preview** | `preview.py --serve` shows outline / rendered layout / text tabs and reloads page by page as SVGs land; `executor_output.md` keeps the Executor transcript. |
| **📦 One-step Export** | `build_pptx.py --verify` runs notes split → finalize → export fail-fast and verifies no text was lost or wrapped; exports one editable deck by default. Single pages can be re-finalized with `--page`. |
| **🤖 Multi-agent Entry** | `AGENTS.md` is the shared entry; `GEMINI.md` imports it, so Gemini / Codex can run the same skill. `uv.lock` is tracked for reproducible environments. |

> **Credit**: Thanks to the original author [@hugohe3](https://github.com/hugohe3) for the excellent design. All extensions in this fork remain under the same MIT license.

---

## Introduction

Drop in a PDF, DOCX, Excel, URL, or Markdown file — AI generates **natively editable PowerPoint presentations with real shapes**, not images. Every text box, chart, and graphic is a real PowerPoint object you can click and edit. Supports PPT 16:9, social media cards, marketing posters, and 10+ other formats.

> 🔥 **Native Editable PPTX** — Generated presentations contain **real PowerPoint shapes** (DrawingML) by default — text, charts, and graphics are directly editable in PowerPoint without any extra steps.
>
> 🎨 **Design Philosophy**: The generated PPTX is a **design draft**, not a finished product. The AI handles visual design, layout, and content structure — delivering a high-quality starting point. For polished results, expect to do your own finishing work in PowerPoint.

---

## 🏗️ System Architecture

```
User Input (PDF / DOCX / XLSX / URL / Markdown)
    ↓
[Source Content Conversion]
    ├── pdf_to_md.py       ← PDF → Markdown (auto image extraction, black-bg fix)
    ├── doc_to_md.py       ← DOCX/EPUB/HTML/LaTeX → Markdown (requires pandoc)
    ├── excel_to_md.py     ← Excel → Markdown (NEW: multi-sheet / merged cells / images)
    └── web_to_md.py       ← URL → Markdown
    ↓
[Create Project] → project_manager.py init <project_name> --format ppt169
    ↓
[Template] — default 奇安信; core pages + optional content layouts (content/)
    ↓
[Strategist] — Eight Confirmations & Design Specifications; picks a content layout per body page
    ↓
[Image_Generator] (when AI image generation is selected)
    ↓
[Executor] — Two-Phase Generation
    ├── Visual Construction Phase: SVG pages → svg_output/
    └── Logic Construction Phase: Speaker notes → notes/total.md
    ↓
[Post-processing Pipeline — SERIAL EXECUTION REQUIRED]
    ├── total_md_split.py  ← Split notes into per-page files
    ├── finalize_svg.py    ← Embed images, fix geometry
    └── svg_to_pptx.py     ← Compile SVG → Native DrawingML PPTX
    (build_pptx.py --verify runs all three fail-fast and checks the text)
    ↓
Output:
    └── <project_name>.pptx      ← Native shapes (DrawingML) — directly editable
```

### 📚 Documentation

| Document | Description |
|----------|-------------|
| 🧭 [AGENTS.md](./AGENTS.md) | Repository-level entry for general AI agents, quick-reference commands |
| 📖 [SKILL.md](./skills/ppt-master/SKILL.md) | Complete workflow rules and role definitions |
| 📐 [Canvas Formats](./skills/ppt-master/references/canvas-formats.md) | PPT / Xiaohongshu / WeChat Moments / poster and 10+ formats |
| 🛠️ [Scripts README](./skills/ppt-master/scripts/README.md) | Script index and high-frequency commands |
| 📊 [Chart Templates](./skills/ppt-master/templates/charts/) | Standardized chart template library |
| 🗂️ [Layout Templates](./skills/ppt-master/templates/layouts/README.md) | Page templates (21) and which ones ship content layouts |
| 📐 [Content Layouts](./skills/ppt-master/scripts/docs/layouts.md) | Fill, build, absorb and stress-test body-page layouts |
| 💼 [Examples](./examples/README.md) | 15 example projects, 229 SVG pages |

---

## 🚀 Quick Start

### 1. Prerequisites

#### Python + uv (Required)

Python 3.8+, managed with **[uv](https://github.com/astral-sh/uv)** — 10–100× faster than `pip` and automatically manages virtual environments.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS / Linux
# or
brew install uv  # macOS with Homebrew

# Verify
uv --version
python3 --version  # >= 3.14
```

#### Install Dependencies

```bash
git clone <this-repo-url>
cd ppt-master

# Install project dependencies (auto-creates .venv)
uv sync
```

> 💡 All scripts are run via **`uv run python3`** to ensure dependency isolation:
> ```bash
> uv run python3 skills/ppt-master/scripts/pdf_to_md.py input.pdf
> ```

#### Pandoc (Optional)

Required for converting DOCX / EPUB / LaTeX and other document formats:

```bash
brew install pandoc   # macOS
sudo apt install pandoc  # Ubuntu
```

#### Node.js (Optional)

Required for `web_to_md.cjs` (WeChat and other high-security sites):

```bash
brew install node  # macOS, requires node >= 18
```

### 2. Choose an AI Editor

| Tool | Rating | Notes |
|------|:------:|-------|
| **Antigravity** | ⭐⭐⭐⭐ | Highly recommended — gemini-3.x-pro |
| **Claude Code** | ⭐⭐⭐ | Highly recommended — native Opus support, largest context window |
| **Cursor** | ⭐⭐ | Popular AI editor, great UX |
| VS Code + Copilot | ⭐⭐ | Microsoft official, cost-effective |
| Codebuddy IDE | ⭐⭐ | Good support for Kimi / MiniMax models |

**Open ppt-master folder in your AI IDE**
**Just chat with IDE and say: I want to create a PPT from a PDF file.**


### 3. Start Creating

Describe your content in the AI chat panel:

```
User: I have a Q3 quarterly report (report.pdf). I need to turn it into a PPT.

AI: Sure. I'll read the file first, then run Strategist eight confirmations:
   [Strategist] 1. Canvas format: PPT 16:9 (recommended)
   [Strategist] 2. Page count: 8–10 pages (recommended)
   ...
```

> 💡 **AI lost context?** Ask it to read `skills/ppt-master/SKILL.md` first; use `AGENTS.md` as the repository-level entry.

---

## 🛠️ Common Commands

```bash
# ── Project Setup ──────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
uv run python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <files...>

# ── Source Conversion ───────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/pdf_to_md.py <PDF_file>
uv run python3 skills/ppt-master/scripts/doc_to_md.py <DOCX_or_other>   # requires pandoc
uv run python3 skills/ppt-master/scripts/excel_to_md.py <XLSX_or_XLSM>  # requires openpyxl pillow
uv run python3 skills/ppt-master/scripts/web_to_md.py <URL>
node skills/ppt-master/scripts/web_to_md.cjs <URL>

# ── Image Tools ─────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 -o <project>/images
uv run python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images

# ── Templates & Content Layouts ─────────────────────────────────
uv run python3 skills/ppt-master/scripts/pptx_to_template.py <template.pptx> <project_path>
uv run python3 skills/ppt-master/scripts/layout_fill.py <project_path> --slots <layout_id>
uv run python3 skills/ppt-master/scripts/layout_fill.py <project_path> <layout_id> <values.json> -o <project_path>/svg_output/<page>.svg
uv run python3 skills/ppt-master/scripts/layout_build.py skills/ppt-master/templates/layouts/<template> [--check|--init]
uv run python3 skills/ppt-master/scripts/layout_plan_check.py <project_path> [--output]
uv run python3 skills/ppt-master/scripts/layout_stress.py skills/ppt-master/templates/layouts/<template>
uv run python3 skills/ppt-master/scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render

# ── Post-processing & Export (recommended: one fail-fast run) ───
uv run python3 skills/ppt-master/scripts/build_pptx.py <project_path> --verify
# Manual form — run one at a time, confirm each before the next:
#   total_md_split.py <project_path> → finalize_svg.py <project_path> → svg_to_pptx.py <project_path> -s final
# Re-process one edited page:
uv run python3 skills/ppt-master/scripts/finalize_svg.py <project_path> --page <page_name>

# ── Live Preview ────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/preview.py <project_path> --serve

# ── SVG Quality Check ───────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
```

---

## 📁 Project Structure

```text
ppt-master/
├── skills/
│   └── ppt-master/                 # Main skill source
│       ├── SKILL.md                #   Workflow entry point
│       ├── workflows/              #   Workflow files
│       ├── references/             #   Role definitions & specs
│       ├── scripts/                #   Tool scripts
│       │   ├── pdf_to_md.py        #     PDF → Markdown (black-bg fix)
│       │   ├── doc_to_md.py        #     DOCX/EPUB → Markdown
│       │   ├── excel_to_md.py      #     Excel → Markdown (NEW)
│       │   ├── web_to_md.py        #     URL → Markdown
│       │   ├── file_write.py       #     Safe I/O writer (PTY hang fix)
│       │   ├── project_manager.py  #     Project management
│       │   ├── finalize_svg.py     #     SVG post-processing
│       │   ├── svg_to_pptx.py      #     SVG → PPTX export
│       │   ├── build_pptx.py       #     One-step export + text verification
│       │   ├── preview.py          #     Live preview
│       │   ├── pptx_to_template.py #     User .pptx → template
│       │   ├── layout_*.py         #     Content layouts: build / fill / stress
│       │   └── image_gen.py        #     AI image generation
│       └── templates/
│           ├── layouts/            #     21 page templates (奇安信 default); content/ = body layouts
│           ├── content_library/    #     Shared library of the 22 body layouts
│           ├── charts/             #     Chart templates
│           └── icons/              #     Vector icons
├── examples/                       # Example projects (15 projects, 229 pages)
├── projects/                       # User project workspace
├── AGENTS.md                       # General AI agent entry
├── CLAUDE.md                       # Claude Code dedicated entry
└── GEMINI.md                       # Gemini entry (imports AGENTS.md)
```

---

## ⚙️ SVG Technical Constraints

The following SVG features are **banned** (not supported by DrawingML):

**Banned**: `clipPath` | `mask` | `<style>` | `class` | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<symbol>+<use>`

**Alternatives**:

| Banned | Use instead |
|--------|-------------|
| `rgba()` | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` | Set opacity on each child element individually |
| `marker-end` arrows | `<polygon>` triangles |

**Canvas Formats**:

| Format | viewBox |
|--------|---------|
| PPT 16:9 | `0 0 1280 720` |
| PPT 4:3 | `0 0 1024 768` |
| Xiaohongshu (RED) | `0 0 1242 1660` |
| WeChat Moments | `0 0 1080 1080` |

---

## ❓ FAQ

<details>
<summary><b>Q: Can I edit the generated presentations?</b></summary>

Yes! The default exported `.pptx` contains **native PowerPoint shapes** — all text, graphics, and colors are directly editable in PowerPoint without any conversion. The accompanying SVG reference version (`_svg.pptx`) can be unlocked via **"Convert to Shape"**. Requires **Office 2016** or later.

</details>

<details>
<summary><b>Q: Why do images in SVG files have a black background?</b></summary>

This is a known issue when PDFs embed PNG images with an alpha (transparency) channel — JPEG does not support alpha, so transparent pixels map to black when written directly. **This fork fixes the problem**: `pdf_to_md.py` and `excel_to_md.py` now use Pillow to composite the alpha channel onto a white background before saving as JPEG.

</details>

<details>
<summary><b>Q: The terminal hangs (freezes) when AI writes SVG files — what do I do?</b></summary>

This is caused by the 4096-character PTY pseudo-terminal buffer limit. **This fork fixes the problem**: all SVG and large-file writes now go through a safe pipeline of local `tmp/` staging → chunked writes → `file_write.py` atomic flush, completely avoiding buffer overflow. See the "I/O Lock Bypass" section in `SKILL.md`.

</details>

<details>
<summary><b>Q: Can I edit the data behind charts?</b></summary>

Charts are rendered as custom SVG graphics converted to native PowerPoint shapes — not Excel-driven chart objects. Visual quality is typically superior to default PowerPoint charts, but the underlying data cannot be edited via the chart editor. If you need live, data-driven charts, replace them manually with native PowerPoint charts after export.

</details>

<details>
<summary><b>Q: How do I use the Excel → Markdown tool?</b></summary>

```bash
# Install dependencies
uv pip install openpyxl pillow

# Basic usage
uv run python3 skills/ppt-master/scripts/excel_to_md.py data.xlsx
uv run python3 skills/ppt-master/scripts/excel_to_md.py report.xlsm -o output.md
```

Features: multi-sheet sections, merged-cell annotations, hyperlinks, comment extraction, embedded images (white background), named ranges, date formatting.

</details>

> 📖 For more questions, see [SKILL.md](./skills/ppt-master/SKILL.md) and [AGENTS.md](./AGENTS.md)

---

## 🔧 Technical Design

**Pipeline: AI generates SVG → post-processing converts to DrawingML (PPTX)**

**Why SVG?**

SVG and DrawingML share the same world view — both are absolute-coordinate 2D vector graphics formats with directly corresponding concepts:

| SVG | DrawingML |
|-----|-----------|
| `<path d="...">` | `<a:custGeom>` |
| `<rect rx="...">` | `<a:prstGeom prst="roundRect">` |
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse">` |
| `transform="translate/scale/rotate"` | `<a:xfrm>` |
| `linearGradient` / `radialGradient` | `<a:gradFill>` |
| `fill-opacity` / `stroke-opacity` | `<a:alpha>` |

The conversion is a translation between two dialects of the same idea — not a format mismatch. SVG simultaneously satisfies every role in the pipeline: **AI can reliably generate it, humans can preview and debug it in any browser, and scripts can precisely convert it** — all before a single line of DrawingML is written.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository
2. Create your branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Contribution areas**: 🎨 Design templates · 📊 Chart components · 📝 Documentation · 🐛 Bug reports · 💡 Feature suggestions

---

## 📄 License

This project is licensed under the [MIT License](LICENSE), consistent with the original repository [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master).

---

## 🙏 Acknowledgments

- **[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)** — Original project, the foundation of this fork
- [SVG Repo](https://www.svgrepo.com/) — Open source icon library
- [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) — CRAP design principles
- McKinsey, Boston Consulting, Bain — Design style inspiration
