# AGENTS.md

The one instruction file for every AI agent working in this repository (Claude Code, Gemini,
Codex, and others; `CLAUDE.md` and `GEMINI.md` only import it). Before executing PPT generation
tasks, **you MUST first read `SKILL.md`** for the complete workflow and rules.

## Repository Layout

The repository root is the skill root: `${SKILL_DIR}` in the docs means this directory.

| Path | Holds |
|------|-------|
| `SKILL.md` | Main entry point and the complete workflow |
| `references/` | Role definitions and technical specifications |
| `workflows/create-template.md` | Standalone template workflow |
| `scripts/` | Tool scripts; topic docs in `scripts/docs/` (`conversion`, `project`, `svg-pipeline`, `image`, `layouts`, `troubleshooting`) |
| `templates/` | Page templates (`layouts/`), the shared content-layout library (`content_library/`), chart templates, 640+ icons |
| `templates/layouts/<template>/content/` | A template's built body layouts (`奇安信`, `mckinsey`, `pixel_retro`); `content_src/` holds its `theme.json` + `shell.svg` |
| `workspace/` | The user's work, never in git: `projects/` (in progress), `archive/` (finished and experiment runs), `inbox/` (raw source documents) |

## How to Run

- **Start from the repository root.** Scripts, the uv environment and `workspace/` all assume it.
- **Run Python through `uv run python3`**, never bare `python3`, so the project's pinned dependencies are used.
- **⛔ BLOCKING steps:** when `SKILL.md` requires a confirmation, ask in plain text and stop until the user replies. Skip a confirmation only if the user has already given that answer.
- **Never move or edit the user's source files.** `import-sources` copies files (from `workspace/inbox/` too); `--move` removes its inputs, so use it only on copies.
- **Do not change the skill or its environment during a run.** Never edit `SKILL.md`, `references/`, `scripts/`, `templates/` or `workflows/`, and never repoint `.venv`. If a tool or the environment fails, stop and report it (`uv sync` repairs the venv); the export warns about local changes.

## Project Overview

PPT Master is an AI-driven presentation generation system. Through multi-role collaboration (Strategist → Image_Generator → Executor), it converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project → Template Option → Strategist Eight Confirmations → [Image_Generator] → Executor → Post-processing → Export PPTX`

- To create a template independently, read `workflows/create-template.md`.
- ⚠️ **Strict serial execution**: every Step in the pipeline MUST be executed sequentially — bundling, batching, or parallelizing Steps is FORBIDDEN.
- 🚨 **File output**: write `design_spec.md` and SVG files through `uv run python3 scripts/file_write.py <target_path>`, passing the content on STDIN terminated by a line containing only `<<EOF>>`. Generate one SVG per cycle and confirm it landed before the next.

## Common Commands

```bash
# Source content conversion
uv run python3 scripts/pdf_to_md.py <PDF_file>
uv run python3 scripts/doc_to_md.py <DOCX_or_other_file>   # Requires: pandoc (DOCX/EPUB/HTML/LaTeX/RST/etc.)
uv run python3 scripts/excel_to_md.py <XLSX_or_XLSM_file>
uv run python3 scripts/web_to_md.py <URL>
node scripts/web_to_md.cjs <URL>

# Project management (new projects go to workspace/projects/)
uv run python3 scripts/project_manager.py init <project_name> --format ppt169
uv run python3 scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...>
uv run python3 scripts/project_manager.py validate <project_path>

# Image tools
uv run python3 scripts/analyze_images.py <project_path>/images
uv run python3 scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images

# Use a user-supplied .pptx as the template (extracts real backgrounds + logos)
uv run python3 scripts/pptx_to_template.py <template.pptx> <project_path>

# SVG quality check
uv run python3 scripts/svg_quality_checker.py <project_path>

# Content layouts: fill one page; stress-test a library; build a library from its theme; inspect a reference deck
uv run python3 scripts/layout_fill.py <project_path> <layout_id> <values.json> -o <project_path>/svg_output/<page>.svg
uv run python3 scripts/layout_stress.py templates/layouts/奇安信
uv run python3 scripts/layout_build.py templates/layouts/<template> [--check|--init]
uv run python3 scripts/layout_plan_check.py <project_path> [--output]        # check the layout plan in design_spec.md
uv run python3 scripts/render_pages.py <project_path> [--page 03] [--sheet]  # render pages to PNG and look at them
uv run python3 scripts/free_page_check.py <project_path>                     # free-design pages: frame kept, no overflow or overlap
uv run python3 scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render

# Post-processing & export — RECOMMENDED: one fail-fast invocation
uv run python3 scripts/build_pptx.py <project_path> --verify
# Preflight first: stops when design_spec.md is missing, svg_output/ does not match the plan,
# or a free page fails its check. Then notes-split → finalize → export strictly in order,
# aborting on first failure, then asserts no text run wrapped during export.

# Equivalent manual form (run one at a time, check each before the next)
uv run python3 scripts/total_md_split.py <project_path>
uv run python3 scripts/finalize_svg.py <project_path>
uv run python3 scripts/svg_to_pptx.py <project_path> -s final
# Produces exactly ONE editable native-shapes deck, named after the project (re-running overwrites it).
#   --with-svg-ref  also emit the _svg.pptx reference twin (rarely needed)
#   --timestamp     keep each run as a separate file
#   --only legacy   emit only the SVG-image version

# Verify an exported deck on its own (LibreOffice when present for visual-wrap
# detection; otherwise a python-pptx text-integrity check)
uv run python3 scripts/verify_pptx_text.py <project_path>

# Re-process a SINGLE page after editing it (leaves every other page untouched)
uv run python3 scripts/finalize_svg.py <project_path> --page 07_arch

# Live preview: rebuilds on each request and auto-reloads as new SVGs land.
# It blocks its terminal, so run it in the background. Stop: kill $(lsof -ti tcp:8890)
uv run python3 scripts/preview.py <project_path> --serve
```

## Templates and Content Layouts

- Default template: `templates/layouts/奇安信/`. A template = core pages (`01_cover` … `04_ending`,
  always used for cover / TOC / chapter / ending) + optional `content/` body layouts. Step 3 of
  `SKILL.md` copies the SVGs, `content/` and the image assets into the project.
- **First principle**: when you can read the page content's own structure or metaphor, design the
  page for it yourself instead of fitting it into a preset layout. The layouts are the default,
  not a cage; never merge, drop, regroup or pad what the source says to fit one.
- `奇安信`, `mckinsey`, `pixel_retro` ship 22 body layouts each (`contentLayouts` in
  `layouts_index.json`). A layout's SVG is the complete page: the Executor fills its `{{SLOT}}`
  placeholders with `layout_fill.py` and keeps its geometry, colors and font sizes. Other
  templates design body pages freely on `03_content.svg`.
- `**Layout mode**` in the spec decides how freely pages are designed. `open` (frontier-tier
  models: Claude Opus / Fable, Gemini argon-class): write `Layout: free: <description>` when the
  source has its own count, grouping, links or metaphor; build the page on
  `templates/content/free_frame.svg`, render it and look at it (`render_pages.py`), and pass
  `free_page_check.py`. `library` (small or fast-tier models, or strict uniformity): stay with the
  layouts; `free` only when no layout's claim holds.
- Choose a page's form by the content's **relation** (16-word vocabulary: statement, metric,
  contrast, problem_solution, parallel, sequence, …), never for variety. Each body page in
  `design_spec.md` carries Message / Relation / Layout / Claim check / Evidence (verbatim quotes,
  checked against `sources/`) (/ Series for parallel pages); run `layout_plan_check.py` before
  presenting the spec. Rules: `references/strategist.md` → Content Layout Selection and
  `references/executor-base.md` §1.7.
- Layouts come from one shared library (`templates/content_library/library.py`) plus each
  template's `content_src/theme.json` + `shell.svg`. Never edit `content/` by hand; rebuild it with
  `layout_build.py` and verify with `layout_stress.py`. Adding layouts to another template is done
  on request only; see `scripts/docs/layouts.md`.

## Using a User-Supplied .pptx as the Template

When the user says "参照 XXX 模板" / points at a `.pptx`, that deck IS the template.

1. Run `pptx_to_template.py` — it writes `templates/0*.svg` with the real background art and
   logos at their exact coordinates, plus `images/` assets.
2. Every generated page then copies those `<image>` tags verbatim as its base layer.

**Never** empty `templates/` because a built-in template clashes (that silently downgrades the run
to free design and loses the user's brand), never hand-draw a gradient or re-place a logo you have
the real asset for, and never blend two templates together. Verify before export:

```bash
grep -o 'href="\.\./images/[^"]*"' <project_path>/svg_output/*.svg | sort | uniq -c
```

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

- **NEVER** use `cp` as a substitute for `finalize_svg.py`.
- **NEVER** export directly from `svg_output/` — MUST export from `svg_final/` (use `-s final`).
- The export emits **one** editable deck. Do not ask for the `_svg.pptx` twin unless something
  needs it — it is a near-duplicate that doubles build time and disk use.
- Run the stages **strictly in order, checking each before the next**: `build_pptx.py` (fail-fast)
  or separate invocations — never chained blindly in one line.

## Output Sanity Rules

- Each project is built only from its own `sources/`. Never copy notes, values files, pages or a
  design spec from another project, including an earlier run on the same source. `layout_fill.py`
  and `build_pptx.py` refuse pages that `design_spec.md` does not plan.
- One project → one deliverable deck. If the project root accumulates several `.pptx` files,
  something re-ran with `--timestamp`; keep the newest, drop the rest.
- `tmp/` is scratch. Delete it before handing the project over.
- Verify with `verify_pptx_text.py`, not by eyeballing rendered screenshots — it checks every text
  run on every page in one pass.
- When a deck is done, move its folder from `workspace/projects/` to `workspace/archive/`.
