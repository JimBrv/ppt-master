# Content Layout Tools

A content layout is a complete page SVG in `templates/layouts/<template>/content/`
whose text lives in `{{SLOT}}` placeholders. `content/layouts.json` indexes each
layout: when to use it, how many items it takes, and the capacity of every
slot in full-width characters (Latin text counts about 0.55 each).

| Script | Role |
|--------|------|
| `pptx_inspect.py` | Extract geometry and real renders from a reference deck |
| `layout_kit.py` | Library for building and filling layouts; imported, not run |
| `layout_fill.py` | Fill one layout from a values file, with every check applied |
| `layout_stress.py` | Fill a whole library to capacity and run the real export |

Each template's layouts are generated from `templates/layouts/<template>/content_src/build_layouts.py`.
Edit that file, not the SVGs; the SVGs and `layouts.json` are its output.

## Filling a page (Executor, Step 6)

```bash
uv run python3 scripts/layout_fill.py <project_path> --slots funnel_layers
uv run python3 scripts/layout_fill.py <project_path> funnel_layers values.json -o <project_path>/svg_output/06_xxx.svg
```

`values.json` maps slot names to text, icon slots to icon names from
`templates/icons/`, and `"_images"` to files in `<project_path>/images/`:

```json
{"PAGE_TITLE": "上下文检测判断真实影响", "L1_LABEL": "L1  客户端检测", "L1_ICON": "keyboard",
 "_images": {"SCREENSHOT": "console.png"}}
```

The script rejects text over capacity, unknown slots, missing icons and missing
images, and writes nothing if anything fails. Slots left out are removed along
with their containers (rects marked `data-slot-box`), so a seven-chip row with
three values keeps three chips. Unfilled image slots stay as placeholders.

## Absorbing layouts from a reference deck

1. **Look at the pages.** Render them and pick the ones worth keeping:

   ```bash
   uv run python3 scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render
   ```

   Open `<out_dir>/index.html` to see each render beside its wireframe.
   `--render` uses macOS Quick Look; it skips rotated custom shapes and some
   gradients, so read those from `shapes.json`.

2. **Read the geometry.** `shapes.json` lists every shape flattened out of its
   groups in 1280x720 canvas px, with rotation, flip, normalized custom paths,
   fills, alpha, text, and font size in pt and px.

3. **Turn each page into a layout.** Add a builder to the template's
   `content_src/build_layouts.py`:
   - keep the structure, and replace every piece of text with a slot;
   - set each text box's width and font size, from which `layout_kit` derives the capacity;
   - map colors onto the template palette;
   - mark single-slot containers with `box=` so unused items disappear cleanly.

   Then add its metadata, especially `bestFor`, `avoidFor`, `items` and
   `source`, and regenerate:

   ```bash
   uv run python3 skills/ppt-master/templates/layouts/<template>/content_src/build_layouts.py
   ```

   SVG features PowerPoint cannot take are simplified: no clip paths, masks,
   rotated text, or 3D. Vertical text becomes horizontal.

4. **Register it.** Update the content-layout table in the template's
   `design_spec.md` and `contentLayouts` in `templates/layouts/layouts_index.json`.

5. **Verify.**

   ```bash
   uv run python3 scripts/layout_stress.py skills/ppt-master/templates/layouts/<template>
   ```

   This checks the SVGs against `layouts.json`, fills every slot to capacity,
   and runs `svg_quality_checker.py` and `build_pptx.py --verify`. Then fill
   the new layout with the reference page's real text using `layout_fill.py`,
   and compare it with the original in PowerPoint before committing.

Keep a page only if its structure recurs or says something the existing
layouts cannot. A near-duplicate of an existing layout makes the Strategist's
choice harder without adding range.

## Another brand

Use `pptx_to_template.py` for the new brand's backgrounds and logos, create
`templates/layouts/<brand>/content_src/build_layouts.py` with that brand's
`Shell` (background images, title position, palette), and copy over the
builders you want to reuse. The structure carries over; only the colors and
shell change.
