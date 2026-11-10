# AGENTS.md

This file is the project entry point for AI agents other than Claude Code (Codex, Gemini CLI, and others). Before executing PPT generation tasks, **you MUST first read `skills/ppt-master/SKILL.md`** for the complete workflow and rules.

## How to Run

- **Start from the repository root.** Scripts, the uv environment, and the `projects/` workspace all assume it.
- **`${SKILL_DIR}` in the docs means `skills/ppt-master`.** Substitute it yourself.
- **Run Python through `uv run python3`**, never bare `python3`, so the project's pinned dependencies are used.
- **⛔ BLOCKING steps:** when `SKILL.md` requires a confirmation, ask in plain text and stop until the user replies. Skip a confirmation only if the user has already given that answer.
- **Do not edit the source files in place.** `import-sources --move` removes its inputs, so run it on a copy of anything the user still needs.

## Project Overview

PPT Master is an AI-driven presentation generation system. Through multi-role collaboration (Strategist → Image_Generator → Executor), it converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project → Template Option → Strategist Eight Confirmations → [Image_Generator] → Executor → Post-processing → Export PPTX`

**Execution Requirements**:

- Before starting a PPT task, read `skills/ppt-master/SKILL.md` first
- To create a template independently, read `skills/ppt-master/workflows/create-template.md`
- Role-specific rules and technical constraints are in `skills/ppt-master/references/`
- ⚠️ **Strict serial execution**: Every Step in the pipeline MUST be executed sequentially — bundling, batching, or parallelizing Steps is FORBIDDEN
- 🚨 **File output**: Write `design_spec.md` and SVG files through `uv run python3 skills/ppt-master/scripts/file_write.py <target_path>`, passing the content on STDIN terminated by a line containing only `<<EOF>>`. Generate one SVG per cycle and confirm it landed before the next.

## Templates and Content Layouts

- The default template is `skills/ppt-master/templates/layouts/奇安信/`. Follow Step 3 of `SKILL.md`; it copies the SVGs, `content/`, and the image assets into the project.
- When `<project>/templates/content/layouts.json` exists, every body page should name a layout ID in its `Layout` field. The layout's SVG is the complete page: fill its `{{SLOT}}` placeholders and keep its geometry, colors, and font sizes. Rules are in `references/strategist.md` and section 1.7 of `references/executor-base.md`.
- Use `Layout: free: <description>` with `03_content.svg` only when no layout fits.
- Templates with content layouts: `奇安信`, `mckinsey`, `pixel_retro` (15 each, `contentLayouts` in `layouts_index.json`). The others have core pages only; their body pages are designed freely, as before.
- All three are built from one shared library, `templates/content_library/library.py`, plus each template's `content_src/theme.json` and `shell.svg`. Never edit `content/` by hand; rebuild it with `layout_build.py`. Adding layouts to another template is done on request only; see `skills/ppt-master/scripts/docs/layouts.md`.

## Common Commands

```bash
# Source content conversion
uv run python3 skills/ppt-master/scripts/pdf_to_md.py <PDF_file>
uv run python3 skills/ppt-master/scripts/doc_to_md.py <DOCX_or_other_file>   # Requires: pandoc (DOCX/EPUB/HTML/LaTeX/RST/etc.)
uv run python3 skills/ppt-master/scripts/excel_to_md.py <XLSX_or_XLSM_file>
uv run python3 skills/ppt-master/scripts/web_to_md.py <URL>
node skills/ppt-master/scripts/web_to_md.cjs <URL>

# Project management
uv run python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
uv run python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...> --move
uv run python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Use a user-supplied .pptx as the template
uv run python3 skills/ppt-master/scripts/pptx_to_template.py <template.pptx> <project_path>

# Image tools
uv run python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
uv run python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images

# SVG quality check
uv run python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>

# Content layouts: fill one page; stress-test a library; build a library from its theme; inspect a reference deck
uv run python3 skills/ppt-master/scripts/layout_fill.py <project_path> <layout_id> <values.json> -o <project_path>/svg_output/<page>.svg
uv run python3 skills/ppt-master/scripts/layout_stress.py skills/ppt-master/templates/layouts/奇安信
uv run python3 skills/ppt-master/scripts/layout_build.py skills/ppt-master/templates/layouts/<template> [--check|--init]
uv run python3 skills/ppt-master/scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render

# Post-processing and export: one fail-fast invocation (recommended)
uv run python3 skills/ppt-master/scripts/build_pptx.py <project_path> --verify

# Re-process a single page after editing it
uv run python3 skills/ppt-master/scripts/finalize_svg.py <project_path> --page <page_name>

# Live preview; blocks its terminal, so run it in the background
uv run python3 skills/ppt-master/scripts/preview.py <project_path> --serve
```

## Core Directories

- `skills/ppt-master/SKILL.md` — Main entry point and complete workflow
- `skills/ppt-master/workflows/create-template.md` — Standalone template workflow
- `skills/ppt-master/references/` — Role definitions and technical specifications
- `skills/ppt-master/scripts/` — Tool scripts
- `skills/ppt-master/scripts/docs/` — Topic-focused script docs (`conversion`, `project`, `svg-pipeline`, `image`, `troubleshooting`)
- `skills/ppt-master/templates/` — Layout templates, chart templates, icon library
- `skills/ppt-master/templates/content_library/` — Shared content-layout library (15 body-page layouts, structure + color roles)
- `skills/ppt-master/templates/layouts/<template>/content/` — A template's built body layouts (`奇安信`, `mckinsey`, `pixel_retro`); `content_src/` holds its `theme.json` + `shell.svg`
- `examples/` — Example projects
- `projects/` — User project workspace

## SVG Technical Constraints

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
- Prefer `build_pptx.py --verify`. If you run the stages by hand, run them one at a time and check each before the next.
- The export emits **one** editable deck. Do not request the `_svg.pptx` twin unless something needs it.
- Verify with `verify_pptx_text.py`; it checks every text run on every page.
