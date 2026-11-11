# Pixel Retro Style Template - Design Specification

> Suitable for tech talks, programming tutorials, game-related presentations, geek-style content showcases, and similar scenarios.

---

## I. Template Overview

| Property       | Description                                                |
| -------------- | ---------------------------------------------------------- |
| **Template Name** | pixel_retro (Pixel Retro Template)                      |
| **Use Cases**  | Tech talks, programming tutorials, game introductions, geek-style showcases |
| **Design Tone** | Retro gaming, neon cyberpunk, geek tech, 8-bit style      |
| **Theme Mode** | Dark theme (deep space black background + neon accents)    |

---

## II. Canvas Specification

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Format**     | Standard 16:9                 |
| **Dimensions** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **Page Margins** | Left/Right 60px, Top 50px, Bottom 40px |
| **Safe Area**  | x: 60-1220, y: 50-680         |

---

## III. Color Scheme

### Background Colors

| Role           | Value       | Notes                            |
| -------------- | ----------- | -------------------------------- |
| **Deep Space Black** | `#0D1117` | Main background color          |
| **Starry Night Blue** | `#161B22` | Card/block background         |
| **Dark Border** | `#30363D`  | Borders/dividers                 |

### Accent Colors (Neon Series)

| Role           | Value       | Usage                            |
| -------------- | ----------- | -------------------------------- |
| **Neon Green** | `#39FF14`   | Primary accent, success, save points, Git |
| **Cyber Pink** | `#FF2E97`   | Secondary accent, warnings, contrast, GitHub |
| **Electric Blue** | `#00D4FF` | Tertiary accent, links, info, flows |
| **Gold Yellow** | `#FFD700`  | Quaternary accent, history, timelines, highlights |

### Auxiliary Colors

| Role           | Value       | Usage                            |
| -------------- | ----------- | -------------------------------- |
| **Dark Green** | `#238636`   | Muted version of success state   |
| **Dark Pink**  | `#8B2252`   | Muted pink                       |
| **Dark Blue**  | `#1F6FEB`   | Muted blue                       |

### Text Colors

| Role           | Value       | Usage                  |
| -------------- | ----------- | ---------------------- |
| **Moonlight White** | `#E6EDF3` | Primary text         |
| **Mist Gray**  | `#8B949E`   | Secondary descriptive text |
| **Pure White** | `#FFFFFF`   | Emphasized titles      |

---

## IV. Typography System

### Font Stack

**Title Font**: `"Consolas", "Monaco", "Courier New", monospace` - Pixel/code aesthetic

**Body Font**: `-apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif`

**Code Font**: `"Cascadia Code", "Fira Code", "Consolas", monospace`

### Font Size Hierarchy

| Level | Usage              | Size | Weight  |
| ----- | ------------------ | ---- | ------- |
| H1    | Cover main title   | 52px | Bold    |
| H2    | Page heading       | 36px | Bold    |
| H3    | Section title/Subtitle | 22px | 600  |
| P     | Body content       | 18px | Regular |
| High  | Highlighted data   | 48px | Bold    |
| Sub   | Supplementary text | 14px | Regular |
| Code  | Code text          | 16px | Regular |

---

## V. Page Structure

### General Layout

| Area       | Position/Height | Description                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=4-6px    | Neon green decoration line (dual-line effect) |
| **Title Area** | y=50, h=70px | Page title + English subtitle         |
| **Content Area** | y=130, h=510px | Main content area                  |
| **Footer** | y=680, h=40px   | Page number, decoration line, progress indicator |

### Decorative Elements

- **Top Decoration Line**: Neon green dual lines (main line 4px + auxiliary line 2px)
- **Bottom Decoration Line**: Neon green dual lines (auxiliary line 4px + main line 4px)
- **Pixel Blocks**: Corner decorations with decreasing opacity (100% → 60% → 30%)
- **Scanline Grid**: Optional low-opacity background grid lines

---

## VI. Page Types

### 1. Cover Page (01_cover.svg)

- Deep space black background
- Top/bottom neon decoration lines
- Pixel-style console graphic (optional)
- Main title (neon green glow effect)
- Subtitle (moonlight white)
- Function button group (horizontal layout)
- Bottom prompt text (e.g., "PRESS START")

### 2. Table of Contents (02_toc.svg)

- Deep space black background
- Standard top decoration
- Chapter list (with importance labels)
  - Red: Essential / Must-learn
  - Yellow: Recommended
  - Green: Optional
- Pixel-style list design

### 3. Chapter Page (02_chapter.svg)

- Deep space black background
- Full-screen neon effect
- Large chapter number (glow effect)
- Chapter title + English subtitle
- Pixel-style decorative frame

### 4. Content Page (03_content.svg)

- Deep space black background
- Standard top decoration
- Page title (neon green + glow)
- English subtitle (mist gray)
- **Fully open content area** (y=140 to y=670, width 1160px)
- Bottom page number

> **Design Principle**: The content page template only provides the page frame (title area + footer). The content area is freely designed by the Executor based on actual content. Available layouts include but are not limited to: cards, progress bars, tables, timelines, comparison charts, etc.

### 5. Ending Page (04_ending.svg)

- Deep space black background
- Neon glow main title
- Summary card group
- "GAME SAVED" visual effect
- Progress button group

---

## VII. Layout Modes

| Mode               | Use Cases                      |
| ------------------ | ------------------------------ |
| **Single Column Centered** | Cover, closing, key points |
| **Two Columns (5:5)** | Comparative display (e.g., Git vs GitHub) |
| **Dual-Column Cards** | Feature lists, trait comparisons |
| **Three-Column Cards** | Key takeaways, project lists |
| **Progress Bar Display** | Data statistics, usage rates |
| **Timeline**       | History, processes, workflows  |

---

## VIII. Spacing Guidelines

| Element          | Value  |
| ---------------- | ------ |
| Card spacing     | 20-30px |
| Content block spacing | 30px |
| Card padding     | 20-24px |
| Card border radius | 0px (blocky feel) or 4px |
| Border width     | 2-3px  |
| Icon-to-text gap | 12px   |

---

## IX. Visual Effects

### Pixel Style Characteristics

- Blocky icons and decorations
- Use block characters such as: full block, dark shade, light shade, upper half, lower half, small black/white squares for decoration
- Progress bars filled with blocks
- Borders use double lines or dotted patterns
- Card corners with pixel decoration blocks

### Neon Glow Effect

Apply glow filters to key text/elements:

```xml
<defs>
  <filter id="glowGreen" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3-4" result="blur" />
    <feMerge>
      <feMergeNode in="blur" />
      <feMergeNode in="SourceGraphic" />
    </feMerge>
  </filter>
</defs>

<!-- Usage -->
<text filter="url(#glowGreen)" fill="#39FF14">Glowing Text</text>
```

> **Note**: `filter` effects are typically ignored in PPT, but render well in SVG-compatible viewers.

### Emoji Usage

- 🎮 Game/Save
- 💾 Save
- 🔀 Branch/Merge
- 📁 Folder
- 📝 Document
- 🚀 Release
- ⏪ Revert
- 👾 Developer
- 🌐 Network/Cloud
- ✅ Confirm/Success
- 🎯 Target/Key Point
- 🤔 Question/Thinking

---

## X. SVG Technical Constraints

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Use `<rect>` elements for backgrounds
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; `rgba()` is prohibited
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles instead of `<marker>` for arrows

### PPT Compatibility Rules

- No `<g opacity="...">` (group opacity); set opacity on each child element individually
- Use overlay layers instead of image opacity
- Use inline styles only; external CSS and `@font-face` are prohibited
- `filter` effects serve as enhancements (allowed) and do not affect baseline display

---

## XI. Placeholder Specification

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| Placeholder        | Description        |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Main title         |
| `{{SUBTITLE}}`     | Subtitle           |
| `{{AUTHOR}}`       | Author/Organization |
| `{{PAGE_TITLE}}`   | Page title         |
| `{{PAGE_TITLE_EN}}`| Page title (English) |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{PAGE_NUM}}`     | Page number        |
| `{{TOTAL_PAGES}}`  | Total page count   |
| `{{VERSION}}`      | Version number     |

---

## XII. Usage Instructions

1. Copy the template to the project `templates/` directory
2. Select the appropriate page template based on content requirements
3. Mark content to be replaced using placeholders
4. Generate the final SVG through the Executor role
5. Define glow effects using `filter` (within `<defs>`)
6. Maintain consistency of the neon color scheme

---

## XIII. Color Quick Reference

```
Background Layer:
  Main background    #0D1117  Deep Space Black
  Card background    #161B22  Starry Night Blue
  Borders            #30363D  Dark Border

Accent Colors (use in order):
  Primary accent     #39FF14  Neon Green
  Secondary accent   #FF2E97  Cyber Pink
  Tertiary accent    #00D4FF  Electric Blue
  Quaternary accent  #FFD700  Gold Yellow

Text:
  Primary text       #E6EDF3  Moonlight White
  Secondary text     #8B949E  Mist Gray
  Emphasis text      #FFFFFF  Pure White
```

---

## XIV. Content Layouts

`content/layouts.json` indexes twenty-two ready-made content pages built from the shared library (`templates/content_library/`) with this template's `content_src/theme.json` and `shell.svg`. They are the default for body pages. In open layout mode, design a page freely on `content/free_frame.svg` (this template's frame with an empty body; colors in `layouts.json` → `meta.frame.palette`) when the content has its own count, grouping, links or metaphor; in library mode, go free only when no layout's claim holds. Rebuild with `scripts/layout_build.py`; never edit `content/` by hand. Choose by the content's relation, then test the layout's `claim` (see `references/strategist.md` → Content Layout Selection).

| ID | Relation | Best for |
|----|----------|----------|
| `three_pillars` | parallel | Three parallel themes |
| `chevron_stages` | sequence | Three sequential stages |
| `stair_steps` | escalation | Graded levels, low to high |
| `layered_rows` | layering | Layered architectures |
| `hub_numbered_rows` | hub | One concept, three dimensions |
| `image_stack_pills` | evidence, parallel | Advantage lists with a hero image |
| `loop_nodes` | cycle | Five-step closed loops |
| `stage_matrix_evidence` | evidence, sequence | Case studies backed by a screenshot |
| `architecture_radial` | hub | End-to-end architecture: inputs, central hub, outputs |
| `probe_tier_channels` | hub | One platform connecting several channels |
| `three_track_checklist` | parallel | Three parallel step-by-step checklists |
| `tier_chip_pyramid` | classification | Compatibility or support matrices by tier |
| `chain_core_grid` | chain_core | A chain, a core engine, and its constraints |
| `funnel_layers` | convergence | Layers that progressively filter or converge |
| `arrow_track_columns` | escalation, sequence | Modes or policies that escalate in stages |
| `hero_statement` | statement | One thesis, a quotation, or a call to action |
| `key_metrics` | metric | Three key numbers that carry the point |
| `problem_solution` | problem_solution | A problem and its responses; repeats across parallel sections |
| `contrast_split` | contrast | Myth vs fact, before vs after, row-by-row comparison |
| `spectrum_position` | contrast | A position held between two extremes |
| `timeline` | timeline | Dated milestones or a roadmap |
| `matrix_2x2` | matrix | Positioning on two independent dimensions |
