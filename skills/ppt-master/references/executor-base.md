# Executor Common Guidelines

> Style-specific content is in the corresponding `executor-{style}.md`. Technical constraints are in shared-standards.md.

---

## 1. Template Adherence Rules

> 🚨 **CRITICAL — MANDATORY**: If template SVG files exist in the project's `templates/` directory, **you MUST use them as the actual base layer for every generated SVG page**. This is NOT optional styling guidance — it is a hard structural requirement.

### 1.1 Core Rule: Template as Base Layer

**The correct workflow for EVERY SVG page is:**

1. **READ** the corresponding template file (`templates/01_cover.svg`, `templates/03_content.svg`, etc.)
2. **COPY** the entire `<svg>` opening tag (including `xmlns:xlink` namespace) from the template
3. **COPY ALL `<image>` elements** from the template as the **first children** inside `<svg>` — these carry the actual brand background and logo. They MUST appear before any content elements.
4. **ADD your content elements** (text, shapes, charts) AFTER the template background layers
5. **DO NOT redraw** the background — no custom `<linearGradient>`, no hand-drawn watermark paths, no self-made logo groups

**Required SVG structure when a template exists:**

```xml
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1280 720">
  <!-- ✅ STEP 1: Copy ALL <image> tags verbatim from the template -->
  <image href="../images/qax_bg_content.jpg" x="0" y="0" width="1280" height="720" preserveAspectRatio="none"/>
  <image href="../images/qax_logo.png" x="992.3" y="0" width="275.2" height="110.4" preserveAspectRatio="none"/>

  <!-- ✅ STEP 2: Add your page content BELOW the background images -->
  <text x="60" y="380" font-family="Microsoft YaHei, sans-serif" font-size="54" font-weight="bold" fill="#003892">Your Title</text>
  <!-- ... more content elements ... -->
</svg>
```

### 1.2 Template → Page Type Mapping

| Page Type | Corresponding Template | What to Copy | What to Add |
|-----------|----------------------|--------------|-------------|
| Cover | `templates/01_cover.svg` | ALL `<image>` tags (background + logo) | Title text, subtitle, date — positioned per design_spec |
| Chapter / TOC | `templates/02_chapter.svg` | ALL `<image>` tags | Chapter number, title, TOC items |
| Content (all body pages) | `templates/03_content.svg` | ALL `<image>` tags | Page title text, all content area elements |
| Ending | `templates/04_ending.svg` | ALL `<image>` tags (background + logo) | Thank-you text, slogan, contact info |

> ⚠️ If `02_chapter.svg` doesn't exist but `02_toc.svg` does, use `02_toc.svg` for chapter/TOC pages.

### 1.3 Strict Prohibitions When Template Exists

**FORBIDDEN — do NOT do any of these:**

- ❌ Creating a `<linearGradient>` background to simulate the template
- ❌ Drawing `<path>` elements to approximate a brand watermark or decorative pattern
- ❌ Drawing a `<rect>` with `fill="#FFFFFF"` as a full-canvas background instead of the template image
- ❌ Creating a hand-drawn logo group with `<circle>` + `<text>` instead of using the template's `<image>` logo
- ❌ Generating the SVG from scratch without opening and reading the template file first
- ❌ Omitting `xmlns:xlink` namespace when the template uses `xlink:href`

### 1.4 How to Extract Template Background Elements

Before writing any SVG page, **read the template file** and extract the `<image>` elements:

```bash
# Inspect the template structure (look for <image> tags)
grep -n '<image' templates/03_content.svg
```

The template `<image>` elements typically look like:

```xml
<!-- Full-canvas brand background -->
<image href="../images/qax_bg_content.jpg" x="0" y="0" width="1280" height="720" preserveAspectRatio="none"/>
<!-- HD logo overlay (top-right corner) -->
<image href="../images/qax_logo.png" x="992.3" y="0" width="275.2" height="110.4" preserveAspectRatio="none"/>
```

Copy both tags **verbatim** into your generated SVG. `finalize_svg.py` embeds the files at export. Older project templates may still inline base64; copy those as-is too.

### 1.5 Pre-Generation Checklist (Required)

Before generating each page, you MUST:

- [ ] Confirm which template file maps to this page type
- [ ] Read the template file and identify all `<image>` elements
- [ ] Plan the content layout within the safe area (avoiding overlap with logo)
- [ ] Confirm `xmlns:xlink` will be present in the SVG root element

### 1.6 Page-Template Declaration (Required Output)

Before generating each page's SVG code, declare:

```
📝 **Template base**: `templates/03_content.svg` — copying 2 <image> background tags
🎯 **Content layout**: [describe what content goes where in the safe area]
```

- **No template found**: Generate entirely per the Design Specification & Content Outline (free design)

---

### 1.7 Content Layouts

When a page's `Layout` field in the design spec is a layout ID, build that page from `templates/content/<id>.svg` instead of `03_content.svg`:

1. Read the SVG and its entry in `templates/content/layouts.json`. The SVG is the complete page, including the background layer and title.
2. Keep its geometry, colors, and font sizes. Replace every `{{SLOT}}`; each text slot is one line.
3. If text exceeds the slot's capacity, shorten the text. Do not shrink the font or resize the box.
4. Delete the whole `<text>` element for an unused line. Change the number of items only as the entry's `items` rule describes.
5. Fill icon slots with names from the approved icon list.
6. Replace a `<rect data-image-slot="...">` with an `<image>` using the same box, or keep the rect if the image is a placeholder.

Prefer filling the page with `scripts/layout_fill.py`. It applies rules 3–6 and refuses to write a page that breaks them:

```bash
uv run python3 ${SKILL_DIR}/scripts/layout_fill.py <project_path> --slots <layout_id>
uv run python3 ${SKILL_DIR}/scripts/layout_fill.py <project_path> <layout_id> <project_path>/tmp/<page>.json -o <project_path>/svg_output/<page>.svg
```

Write values files under `<project_path>/tmp/`, never in the project root, and delete `tmp/` when the
pages are done. Fill only what the spec's Content holds: an empty slot is removed cleanly, an invented
item is a defect (strategist.md P4). After all pages are written, compare density with the genre budget:

```bash
uv run python3 ${SKILL_DIR}/scripts/layout_plan_check.py <project_path> --output
```

A `free: ...` Layout value means free design inside `03_content.svg`. Before leaving Step 6, `grep -l '{{' svg_output/*.svg` must print nothing.

---

## 2. Design Parameter Confirmation (Mandatory Step)

> Before generating the first SVG page, you **must review the key design parameters from the Design Specification & Content Outline** to ensure all subsequent generation strictly follows the spec.

Must output confirmation including: canvas dimensions, body font size, color scheme (primary/secondary/accent HEX values), font plan.

**Why is this step mandatory?** Prevents the "spec says one thing, execution does another" disconnect.

---

## 3. Execution Guidelines

- **Proximity principle**: Place related elements close together to form visual groups; increase spacing between unrelated groups to reinforce logical structure
- **Absolute spec adherence**: Strictly follow the color, layout, canvas format, and typography parameters in the spec
- **Follow template structure**: If templates exist, inherit the template's visual framework
- **Phased batch generation** (recommended):
  1. **Visual Construction Phase**: Generate all SVG pages continuously, ensuring high consistency in design style and layout coordinates (Visual Consistency)
  2. **Logic Construction Phase**: After all SVGs are finalized, batch-generate speaker notes to ensure narrative coherence (Narrative Continuity)
- **Technical specifications**: See [shared-standards.md](shared-standards.md) for SVG technical constraints and PPT compatibility rules

### SVG File Naming Convention

File naming format: `<number>_<page_name>.svg`

- **Chinese content** → Chinese naming: `01_封面.svg`, `02_目录.svg`, `03_核心优势.svg`
- **English content** → English naming: `01_cover.svg`, `02_agenda.svg`, `03_key_benefits.svg`
- **Number rules**: Two-digit numbers, starting from 01
- **Page name**: Concise and descriptive, matching the page title in the Design Specification & Content Outline

---

## 4. Icon Usage

Four approaches: **A: Emoji** (`<text>🚀</text>`) | **B: AI-generated** (SVG basic shapes) | **C: Built-in library** (`templates/icons/` 640+ icons, recommended) | **D: Custom** (user-specified)

**Built-in icons — Placeholder method (recommended)**:

```xml
<use data-icon="chart-bar" x="100" y="200" width="48" height="48" fill="#005587"/>
```

> No need to manually run `embed_icons.py`; `finalize_svg.py` post-processing tool will auto-embed icons.

**Common icons**: `chart-bar` `arrow-trend-up` `users` `cog` `circle-checkmark` `target` `clock` `file` `dollar` `lightbulb`

> ⚠️ **Icon validation rule**: If the Design Specification includes an icon inventory list, Executor may **only** use icons from that approved list. Using icon names not in the index is FORBIDDEN — verify against `templates/icons/icons_index.json` if uncertain.

Full index: `templates/icons/README.md`

---

## 5. Chart Reference

When the Design Spec includes a **VII. Chart Reference List**, read the referenced SVG templates from `templates/charts/` to understand common chart patterns.

**Adaptation rules**:
- **Must preserve**: Chart type (bar/line/pie etc.) as specified in the Design Spec
- **Must adapt**: Data values, labels, colors (match the project's color scheme), and dimensions to fit the page layout
- **May adjust**: Axis ranges, grid lines, legend position, spacing — as long as the chart remains accurate and readable
- **Must NOT**: Change chart type without Design Spec justification, or remove data points specified in the outline

> Chart templates: `templates/charts/` (33 types). Index: `templates/charts/charts_index.json`

---

## 6. Image Handling

Handle images based on their status in the Design Specification's "Image Resource List":

| Status | Source | Handling |
|--------|--------|----------|
| **Existing** | User-provided | Reference images directly from `../images/` directory |
| **AI-generated** | Generated by Image_Generator | Images already in `../images/`, reference directly |
| **Placeholder** | Not yet prepared | Use dashed border placeholder |

**Reference**: `<image href="../images/xxx.png" ... preserveAspectRatio="xMidYMid slice"/>`

**Placeholder**: Dashed border `<rect stroke-dasharray="8,4" .../>` + description text

---

## 7. Font Usage

Apply corresponding fonts for different text roles based on the font plan in the Design Specification & Content Outline:

| Role | Chinese Recommended | English Recommended |
|------|--------------------|--------------------|
| Title font | Microsoft YaHei / KaiTi / SimHei | Arial / Georgia |
| Body font | Microsoft YaHei / SimSun | Calibri / Times |
| Emphasis font | SimHei | Arial Black / Consolas |
| Annotation font | Microsoft YaHei / SimSun | Arial / Times |

---

## 8. Speaker Notes Generation Framework

### Task 1. Generate Complete Speaker Notes Document

After **all SVG pages are generated and finalized**, enter the "Logic Construction Phase" and generate the complete speaker notes document in `notes/total.md`.

**Why not generate page-by-page?** Batch-writing notes allows planning transitions like a script, ensuring coherent presentation logic.

**Format**: Each page starts with `# <number>_<page_title>`, separated by `---` between pages. Each page includes: script text (2-5 sentences), `Key points: ① ② ③`, `Duration: X minutes`. Except for the first page, each page's text starts with a `[Transition]` phrase.

**Basic stage direction markers** (common to all styles):

| Marker | Purpose |
|--------|---------|
| `[Pause]` | Whitespace after key content, letting the audience absorb |
| `[Transition]` | Standalone paragraph at the start of each page's text, bridging from the previous page |

> Each style may extend with additional markers (`[Interactive]`/`[Data]`/`[Scan Room]`/`[Benchmark]` etc.), see `executor-{style}.md`.

**Requirements**:

- Notes should be conversational and flow naturally
- Highlight each page's core information and presentation key points
- Users can manually edit and override in the `notes/` directory

### Task 2. Split Into Per-Page Note Files

Automatically split `notes/total.md` into individual speaker note files in the `notes/` directory.

**File naming convention**:

- **Recommended**: Match SVG names (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Compatible**: Also supports `slide01.md` format (backward compatibility)

---

## 9. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase (all SVG pages) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export** (see [shared-standards.md](shared-standards.md)):

```bash
# 1. Split speaker notes
uv run python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (auto-embed icons, images, etc.)
uv run python3 scripts/finalize_svg.py <project_path>

# 3. Export PPTX
uv run python3 scripts/svg_to_pptx.py <project_path> -s final
# Default: generates native shapes (.pptx) + SVG reference (_svg.pptx)
```
