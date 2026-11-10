# CLAUDE.md

This file provides a project overview for Claude Code. Before executing PPT generation tasks, **you MUST first read `skills/ppt-master/SKILL.md`** for the complete workflow and rules.

## Project Overview

PPT Master is an AI-driven presentation generation system. Through multi-role collaboration (Strategist → Image_Generator → Executor), it converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project → Template Option → Strategist Eight Confirmations → [Image_Generator] → Executor → Post-processing → Export PPTX`

## Common Commands

```bash
# Source content conversion
uv run python3 skills/ppt-master/scripts/pdf_to_md.py <PDF_file>
uv run python3 skills/ppt-master/scripts/doc_to_md.py <DOCX_or_other_file>   # Requires: pandoc (DOCX/EPUB/HTML/LaTeX/RST/etc.)
uv run python3 skills/ppt-master/scripts/web_to_md.py <URL>
node skills/ppt-master/scripts/web_to_md.cjs <URL>

# Project management
uv run python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
uv run python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...> --move
uv run python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Image tools
uv run python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
uv run python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images

# Use a user-supplied .pptx as the template (extracts real backgrounds + logos)
uv run python3 skills/ppt-master/scripts/pptx_to_template.py <template.pptx> <project_path>

# SVG quality check
uv run python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>

# Content layouts: fill one page; stress-test a library; build a library from its theme; inspect a reference deck
uv run python3 skills/ppt-master/scripts/layout_fill.py <project_path> <layout_id> <values.json> -o <project_path>/svg_output/<page>.svg
uv run python3 skills/ppt-master/scripts/layout_stress.py skills/ppt-master/templates/layouts/奇安信
uv run python3 skills/ppt-master/scripts/layout_build.py skills/ppt-master/templates/layouts/<template> [--check|--init]
uv run python3 skills/ppt-master/scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render

# Post-processing & export — RECOMMENDED: one fail-fast invocation
uv run python3 skills/ppt-master/scripts/build_pptx.py <project_path> --verify
# Runs notes-split → finalize → export strictly in order, aborting on first failure,
# then asserts no text run wrapped during export.

# Equivalent manual form (still valid; run one at a time, check each before the next)
uv run python3 skills/ppt-master/scripts/total_md_split.py <project_path>
# ✅ Confirm no errors before running the next command
uv run python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
# ✅ Confirm no errors before running the next command
uv run python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> -s final
# Produces exactly ONE editable native-shapes deck, named after the project
# (re-running overwrites it — no timestamped duplicates).
#   --with-svg-ref  also emit the _svg.pptx reference twin (rarely needed)
#   --timestamp     keep each run as a separate file
#   --only legacy   emit only the SVG-image version

# Verify an exported deck on its own
# (uses LibreOffice when present for full visual-wrap detection; otherwise falls
#  back to a python-pptx text-integrity check instead of failing)
uv run python3 skills/ppt-master/scripts/verify_pptx_text.py <project_path>

# Re-process a SINGLE page after editing it (leaves every other page untouched)
uv run python3 skills/ppt-master/scripts/finalize_svg.py <project_path> --page 07_arch

# Live preview: rebuilds on each request and the open page auto-reloads (~2s)
# as new SVGs land, so generation is visible page-by-page.
uv run python3 skills/ppt-master/scripts/preview.py <project_path> --serve
# Stop it:  kill $(lsof -ti tcp:8890)     (or Ctrl+C in its terminal)
```

## Architecture

- `skills/ppt-master/references/` — AI role definitions and technical specifications
- `skills/ppt-master/scripts/` — Runnable tool scripts
- `skills/ppt-master/scripts/docs/` — Topic-focused script docs
- `skills/ppt-master/templates/` — Layout templates, chart templates, 640+ vector icons
- `examples/` — Example projects
- `projects/` — User project workspace

## SVG Technical Constraints (Non-negotiable)

**Banned features**: `clipPath` | `mask` | `<style>` | `class` | external CSS | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<iframe>` | `<symbol>+<use>` (`id` inside `<defs>` is a legitimate reference and is NOT banned)

**PPT compatibility alternatives**:

| Banned | Alternative |
|--------|-------------|
| `rgba()` | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` | Set opacity on each child element individually |
| `<image opacity>` | Overlay with a mask layer |
| `marker-end` arrows | `<polygon>` triangles |

## Canvas Format Quick Reference

| Format | viewBox |
|--------|---------|
| PPT 16:9 | `0 0 1280 720` |
| PPT 4:3 | `0 0 1024 768` |
| Xiaohongshu (RED) | `0 0 1242 1660` |
| WeChat Moments | `0 0 1080 1080` |
| Story | `0 0 1080 1920` |

## Post-processing Notes

- **NEVER** use `cp` as a substitute for `finalize_svg.py`
- **NEVER** export directly from `svg_output/` — MUST export from `svg_final/` (use `-s final`)
- The export emits **one** editable deck by default. Do not ask for the `_svg.pptx`
  twin unless something actually needs it — it is a near-duplicate that doubles
  build time and disk use.
- Run the three stages **strictly in order, checking each before the next**. Use
  `build_pptx.py` (fail-fast wrapper) or three separate shell invocations — never
  chain them blindly in one line where a mid-pipeline failure would go unnoticed.

## Using a User-Supplied .pptx as the Template

When the user says "参照 XXX 模板" / points at a `.pptx`, that deck IS the template.

1. Run `pptx_to_template.py` — it writes `templates/0*.svg` with the real
   background art and logos at their exact coordinates, plus `images/` assets.
2. Every generated page then copies those `<image>` tags verbatim as its base layer.

**Never** empty `templates/` because a built-in template clashes (that silently
downgrades the run to free design and loses the user's brand), never hand-draw a
gradient or re-place a logo you have the real asset for, and never blend two
templates together. Verify before export:

```bash
grep -o 'href="\.\./images/[^"]*"' <project_path>/svg_output/*.svg | sort | uniq -c
```

## Output Sanity Rules

- One project → one deliverable deck. If the project root accumulates several
  `.pptx` files, something re-ran with `--timestamp`; keep the newest, drop the rest.
- `tmp/` is scratch. Delete it before handing the project over.
- Verify with `verify_pptx_text.py`, not by eyeballing rendered screenshots —
  it checks every text run on every page in one pass.
