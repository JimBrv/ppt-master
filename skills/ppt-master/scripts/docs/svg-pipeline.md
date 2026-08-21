# SVG Pipeline Tools

These tools cover post-processing, SVG validation, speaker notes, and PPTX export.

## Recommended Pipeline

Run these steps in order:

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path> -s final
```

## `finalize_svg.py`

Unified post-processing entry point. This is the preferred way to run SVG cleanup.

It aggregates:
- `embed_icons.py`
- `crop_images.py`
- `fix_image_aspect.py`
- `embed_images.py`
- `flatten_tspan.py`
- `svg_rect_to_path.py`

Typical usage:

```bash
python3 scripts/finalize_svg.py <project_path>
```

Use standalone sub-tools only when you need advanced debugging or one-off fixes.

## `svg_to_pptx.py`

Convert project SVGs into PPTX.

```bash
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> -s final --only native
python3 scripts/svg_to_pptx.py <project_path> -s final --only legacy
python3 scripts/svg_to_pptx.py <project_path> -s final --no-notes
python3 scripts/svg_to_pptx.py <project_path> -t none
python3 scripts/svg_to_pptx.py <project_path> -s final --auto-advance 3
```

Behavior:
- Default output: native editable PPTX + SVG reference PPTX
- Recommended source directory: `svg_final/`
- Speaker notes are embedded automatically unless `--no-notes` is used

Dependency:

```bash
pip install python-pptx
```

## `total_md_split.py`

Split `total.md` into per-slide note files.

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/total_md_split.py <project_path> -o <output_directory>
python3 scripts/total_md_split.py <project_path> -q
```

Requirements:
- Each section begins with `# `
- Heading text matches the SVG filename
- Sections are separated by `---`

## `svg_quality_checker.py`

Validate SVG technical compliance.

```bash
python3 scripts/svg_quality_checker.py examples/project/svg_output/01_cover.svg
python3 scripts/svg_quality_checker.py examples/project/svg_output
python3 scripts/svg_quality_checker.py examples/project
python3 scripts/svg_quality_checker.py examples/project --format ppt169
python3 scripts/svg_quality_checker.py --all examples
python3 scripts/svg_quality_checker.py examples/project --export
```

Checks include:
- `viewBox`
- banned elements
- width/height consistency
- line-break structure

## `preview.py`

Generate a self-contained `preview.html` inside the project directory so the
user can review the deck before (or during) SVG generation. When SVGs exist,
also writes `executor_output.md` — a design_spec.md-shaped Markdown transcript
of every page's actual text, for diffing against the original outline.

```bash
python3 scripts/preview.py <project_path>
python3 scripts/preview.py <project_path> --open
```

Behavior (auto-detects project stage, shows up to three tabs):
- Only `design_spec.md` present -> "设计大纲" outline cards (page / title / layout / content points), parsed from the Content Outline section. Text description only, not a real layout.
- `svg_output/` or `svg_final/` has files -> "实际排布" real SVG thumbnail gallery (click to enlarge), plus "实际文字" — every `<text>` run in each SVG extracted and grouped by page, so you can read exactly what the Executor wrote without the visual layout getting in the way
- Multiple present -> tabbed view to compare intended outline vs. actual rendered pages vs. actual text; the bigger the gap between tabs, the more the Executor added or rewrote beyond the outline

`executor_output.md` mirrors design_spec.md's Content Outline structure
(`#### Slide NN - <filename>` sections, raw unmerged `<text>` list per page),
so the two files can be opened side by side to see exactly what the Executor
added or rewrote beyond the outline on a per-page basis.

Output is a single HTML file that references SVGs by relative path (no
inlining), so it opens with a plain double-click — no HTTP server required.
Non-blocking helper; safe to run at any point in the pipeline.

## `svg_position_calculator.py`

Analyze or pre-calculate chart coordinates.

Common commands:

```bash
python3 scripts/svg_position_calculator.py analyze <svg_file>
python3 scripts/svg_position_calculator.py interactive
python3 scripts/svg_position_calculator.py calc bar --data "East:185,South:142"
python3 scripts/svg_position_calculator.py calc pie --data "A:35,B:25,C:20"
python3 scripts/svg_position_calculator.py from-json config.json
```

Use this when chart geometry needs to be verified before or after AI generation.

## Advanced Standalone Tools

### `flatten_tspan.py`

```bash
python3 scripts/svg_finalize/flatten_tspan.py examples/<project>/svg_output
python3 scripts/svg_finalize/flatten_tspan.py path/to/input.svg path/to/output.svg
```

### `svg_rect_to_path.py`

```bash
python3 scripts/svg_finalize/svg_rect_to_path.py <project_path>
python3 scripts/svg_finalize/svg_rect_to_path.py <project_path> -s final
python3 scripts/svg_finalize/svg_rect_to_path.py path/to/file.svg
```

Use when rounded corners must survive PowerPoint shape conversion.

### `fix_image_aspect.py`

```bash
python3 scripts/svg_finalize/fix_image_aspect.py path/to/slide.svg
python3 scripts/svg_finalize/fix_image_aspect.py 01_cover.svg 02_toc.svg
python3 scripts/svg_finalize/fix_image_aspect.py --dry-run path/to/slide.svg
```

Use when embedded images stretch after PowerPoint shape conversion.

### `embed_icons.py`

```bash
python3 scripts/svg_finalize/embed_icons.py output.svg
python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
```

Use for manual icon embedding checks outside `finalize_svg.py`.

## PPT Compatibility Rules

Use PowerPoint-safe transparency syntax:

| Avoid | Use instead |
|------|-------------|
| `fill=\"rgba(...)\"` | `fill=\"#hex\"` + `fill-opacity` |
| `<g opacity=\"...\">` | Set opacity on each child |
| `<image opacity=\"...\">` | Overlay with a mask layer |

PowerPoint also has trouble with:
- marker-based arrows
- unsupported filters
- direct SVG features not mapped to DrawingML
