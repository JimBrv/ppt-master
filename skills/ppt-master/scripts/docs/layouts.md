# Content Layout Tools

A content layout is a complete page SVG in `templates/layouts/<template>/content/`
whose text lives in `{{SLOT}}` placeholders. `content/layouts.json` indexes each
layout: when to use it, how many items it takes, and the capacity of every
slot in full-width characters (Latin text counts about 0.55 each).

| Script | Role |
|--------|------|
| `pptx_inspect.py` | Extract geometry and real renders from a reference deck |
| `layout_kit.py` | Library for building and filling layouts; imported, not run |
| `layout_build.py` | Build a template's `content/` from the shared library and its theme |
| `layout_plan_check.py` | Check a design spec's layout plan: relation ↔ layout, series, density |
| `layout_fill.py` | Fill one layout from a values file, with every check applied |
| `layout_stress.py` | Fill a whole library to capacity and run the real export |

## Relations and claims

Every layout declares the content **relation** it shows and the **claim** its
visual makes. The Strategist classifies a page's content into one relation,
chooses among the layouts that show it, and tests the claim against the
content (rules: `references/strategist.md` → Content Layout Selection).

The vocabulary is `RELATIONS` in `layout_kit.py`: statement, metric, contrast,
problem_solution, parallel, sequence, escalation, layering, convergence, cycle,
hub, classification, chain_core, evidence, timeline, matrix. `layouts.json`
carries, per layout:

| Field | Source | Meaning |
|-------|--------|---------|
| `relations` | `META` in the library | Relations the layout shows; the first is the main one |
| `claim` | `META` in the library | A sentence the content must make true, e.g. funnel: "every layer is narrower than the one above" |
| `labels` → `labelSlots` | `META` in the library | Fixed labels (series tag, section captions, axis names); not counted as content |
| `maxRuns` | computed | Content text slots when fully filled (title, page number and labels excluded) |
| `weight` | computed | `light` ≤ 12, `medium` ≤ 30, `heavy` > 30 |

`layout_build.py` refuses a layout whose relations are missing or not in the
vocabulary, or whose claim is empty. Add a relation to the vocabulary only when
a real page cannot be described by any existing one, and give it a layout.

```bash
uv run python3 scripts/layout_plan_check.py <project_path>            # the plan in design_spec.md
uv run python3 scripts/layout_plan_check.py <project_path> --output   # plus content text runs per page vs the genre budget
```

## How a library is put together

Structure and styling are kept apart, so one layout works in every template:

| Piece | Where | Holds |
|-------|-------|-------|
| Shared library | `templates/content_library/library.py` | One builder per layout: geometry, slots, capacities, metadata. Colors are **roles** (`T.primary`, `T.surface`, `T.trio_a[1]`, ...), never hex values |
| Theme | `templates/layouts/<template>/content_src/theme.json` | The template's colors for each role, title capacity, `body_box`, `reserved` areas, gradient `id_prefix` |
| Shell | `templates/layouts/<template>/content_src/shell.svg` | The template's own page frame: background, logo, title, page number, with the tokens `%%DEFS%%`, `%%BODY%%`, `%%LAYOUT_ID%%`, `{{PAGE_TITLE}}`, `{{PAGE_NUM}}` |

`layout_build.py` combines the three and writes `content/`. Edit the library,
theme or shell, never the generated SVGs or `layouts.json`.

```bash
uv run python3 scripts/layout_build.py templates/layouts/<template>           # build content/
uv run python3 scripts/layout_build.py templates/layouts/<template> --check   # is content/ fresh? writes nothing
uv run python3 scripts/layout_build.py --all --check                          # every template with content_src/
```

**Theme.** Only `primary`, `ink`, `surface`, `page_bg` and `on_accent` are
required; every other role is derived from them (`derive_roles` in
`layout_kit.py`) and can be overridden one by one. Series roles (`levels`,
`ramp`, `trio_a`, `steps`, `tier_fill`, ...) are lists. A dark template sets
`surface`/`page_bg` dark and `on_accent` to its background color.

**Body box.** Builders draw on a canonical body area, `(0, 130)`–`(1280, 705)`.
When a template's header or footer takes a different amount of room, set
`body_box` and the body is scaled uniformly into it. Capacities stay valid
because uniform scaling keeps text and boxes in proportion.

**Checks after every build.** Elements that overlap a `reserved` area (logo,
header, footer) are reported as conflicts; intentional full-width bands are
built with `bleed=True` and skipped. Color pairs with weak contrast are
reported as warnings only, so review those pages by eye.

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
images, and writes nothing if anything fails. It also refuses a page that
`design_spec.md` at the project root does not plan: the output name's leading
number is the slide number, and that slide's Layout must be this layout
(`--no-plan-check` for tests outside a project). `build_pptx.py` checks the same
thing for every page before exporting. Slots left out are removed along
with their containers (rects marked `data-slot-box`), so a seven-chip row with
three values keeps three chips. Unfilled image slots stay as placeholders.

## Giving an existing template the layouts

1. **Draft the theme and shell** from the template's `03_content.svg`:

   ```bash
   uv run python3 scripts/layout_build.py templates/layouts/<template> --init
   ```

   This is a draft. Check the shell keeps the template's real background,
   logo and title; set `reserved` to the logo, header and footer areas and
   `body_box` to the space between them; correct the colors.

2. **Build and look.**

   ```bash
   uv run python3 scripts/layout_build.py templates/layouts/<template>
   uv run python3 scripts/layout_stress.py templates/layouts/<template>
   ```

   Fix every conflict. Then fill a few layouts with real text and look at
   them, in a dark template especially, for text that loses contrast.

3. **Register it.** Add a Content Layouts section to the template's
   `design_spec.md` and set `contentLayouts` in `templates/layouts/layouts_index.json`.

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

3. **Turn each page into a layout.** Add a builder to
   `templates/content_library/library.py`, plus its `META` entry and a place
   in `BUILDERS`:
   - keep the structure, and replace every piece of text with a slot;
   - set each text box's width and font size, from which `layout_kit` derives the capacity;
   - use color roles, not hex values; add a role to `layout_kit.derive_roles`
     only when no existing one fits;
   - keep the body inside the canonical body area;
   - mark single-slot containers with `box=` so unused items disappear cleanly.

   Fill in `relations`, `claim`, `bestFor`, `avoidFor`, `items` and `source` in the metadata.
   A layout drawn without a reference page (to cover a relation the library lacks) records
   `source='原创（补位：…）'`.
   SVG features PowerPoint cannot take are simplified: no clip paths, masks,
   rotated text, or 3D. Vertical text becomes horizontal.

4. **Rebuild every template** that uses the library, and register the new
   count in each `design_spec.md` and `layouts_index.json`:

   ```bash
   uv run python3 scripts/layout_build.py --all
   ```

5. **Verify** each template:

   ```bash
   uv run python3 scripts/layout_stress.py templates/layouts/<template>
   ```

   This checks the SVGs against `layouts.json`, confirms `content/` is a
   fresh build with no reserved-area conflicts, fills every slot to capacity,
   and runs `svg_quality_checker.py` and `build_pptx.py --verify`. Then fill
   the new layout with the reference page's real text using `layout_fill.py`,
   and compare it with the original in PowerPoint before committing.

Keep a page only if its structure recurs or says something the existing
layouts cannot. A near-duplicate of an existing layout makes the Strategist's
choice harder without adding range.

## A new brand

Run `pptx_to_template.py` for the brand's backgrounds and logos, then follow
"Giving an existing template the layouts" above. The structure carries over
unchanged; only the theme and shell are new.
