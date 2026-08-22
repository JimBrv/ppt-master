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

# SVG quality check
uv run python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>

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
uv run python3 skills/ppt-master/scripts/verify_pptx_text.py <project_path>
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

## Output Sanity Rules

- One project → one deliverable deck. If the project root accumulates several
  `.pptx` files, something re-ran with `--timestamp`; keep the newest, drop the rest.
- `tmp/` is scratch. Delete it before handing the project over.
- Verify with `verify_pptx_text.py`, not by eyeballing rendered screenshots —
  it checks every text run on every page in one pass.
