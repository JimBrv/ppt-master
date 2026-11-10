---
name: ppt-master
description: >
  AI-driven multi-format SVG content generation system. Converts source documents
  (PDF/DOCX/URL/Markdown) into high-quality SVG pages and exports to PPTX through
  multi-role collaboration. Use when user asks to "create PPT", "make presentation",
  "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master".
---

# PPT Master Skill

> AI-driven multi-format SVG content generation system. Converts source documents into high-quality SVG pages through multi-role collaboration and exports to PPTX.

**Core Pipeline**: `Source Document → Create Project → Template Option → Strategist → [Image_Generator] → Executor → Post-processing → Export`

> [!CAUTION]
> ## 🚨 Global Execution Discipline (MANDATORY)
>
> **This workflow is a strict serial pipeline. The following rules have the highest priority — violating any one of them constitutes execution failure:**
>
> 1. **SERIAL EXECUTION** — Steps MUST be executed in order; the output of each step is the input for the next. Non-BLOCKING adjacent steps may proceed continuously once prerequisites are met, without waiting for the user to say "continue"
> 2. **BLOCKING = HARD STOP** — Steps marked ⛔ BLOCKING require a full stop; the AI MUST wait for an explicit user response before proceeding and MUST NOT make any decisions on behalf of the user
> 3. **NO CROSS-PHASE BUNDLING** — Cross-phase bundling is FORBIDDEN. (Note: the Eight Confirmations in Step 4 are ⛔ BLOCKING — the AI MUST present recommendations and wait for explicit user confirmation before proceeding. Once the user confirms, all subsequent non-BLOCKING steps — design spec output, SVG generation, speaker notes, and post-processing — may proceed automatically without further user confirmation)
> 4. **GATE BEFORE ENTRY** — Each Step has prerequisites (🚧 GATE) listed at the top; these MUST be verified before starting that Step
> 5. **NO SPECULATIVE EXECUTION** — "Pre-preparing" content for subsequent Steps is FORBIDDEN (e.g., writing SVG code during the Strategist phase)

> [!IMPORTANT]
> ## 🌐 Language & Communication Rule
>
> - **Response language**: Always match the language of the user's input and provided source materials. For example, if the user asks in Chinese, respond in Chinese; if the source material is in English, respond in English.
> - **Explicit override**: If the user explicitly requests a specific language (e.g., "请用英文回答" or "Reply in Chinese"), use that language instead.
> - **Template format**: The `design_spec.md` file MUST always follow its original English template structure (section headings, field names), regardless of the conversation language. Content values within the template may be in the user's language.

## Main Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `${SKILL_DIR}/scripts/pdf_to_md.py` | PDF to Markdown |
| `${SKILL_DIR}/scripts/doc_to_md.py` | Documents to Markdown via Pandoc (DOCX, EPUB, HTML, LaTeX, RST, etc.) |
| `${SKILL_DIR}/scripts/web_to_md.py` | Web page to Markdown |
| `${SKILL_DIR}/scripts/web_to_md.cjs` | WeChat / high-security sites to Markdown |
| `${SKILL_DIR}/scripts/project_manager.py` | Project init / validate / manage |
| `${SKILL_DIR}/scripts/pptx_to_template.py` | Turn a user-supplied `.pptx` into a layout template (real backgrounds + logos) |
| `${SKILL_DIR}/scripts/layout_fill.py` | Fill one content layout from a values file, checking every slot's capacity |
| `${SKILL_DIR}/scripts/layout_build.py` | Build a template's content layouts from the shared library and its theme |
| `${SKILL_DIR}/scripts/layout_plan_check.py` | Check the design spec's layout plan (relation ↔ layout, series, density) |
| `${SKILL_DIR}/scripts/layout_stress.py` | Stress-test a template's content layout library |
| `${SKILL_DIR}/scripts/pptx_inspect.py` | Extract geometry and renders from a reference deck to build new layouts |
| `${SKILL_DIR}/scripts/analyze_images.py` | Image analysis |
| `${SKILL_DIR}/scripts/image_gen.py` | AI image generation (multi-provider) |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG quality check |
| `${SKILL_DIR}/scripts/total_md_split.py` | Speaker notes splitting |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG post-processing (unified entry) |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | Export to PPTX |
| `${SKILL_DIR}/scripts/verify_pptx_text.py` | Verify no text wrapped in the exported deck |
| `${SKILL_DIR}/scripts/build_pptx.py` | Run all of Step 7 as one fail-fast command |
| `${SKILL_DIR}/scripts/preview.py` | Pre-export preview: outline cards, SVG thumbnail gallery, and/or plain-text transcript |

For complete tool documentation, see `${SKILL_DIR}/scripts/README.md`.

## Template Index

| Index | Path | Purpose |
|-------|------|---------|
| Layout templates | `${SKILL_DIR}/templates/layouts/layouts_index.json` | Query available page layout templates (`contentLayouts` = number of ready-made body layouts) |
| Content layouts | `<project_path>/templates/content/layouts.json` | Body-page layouts of the chosen template, if it has any (see Step 3) |
| Chart templates | `${SKILL_DIR}/templates/charts/charts_index.json` | Query available chart SVG templates |
| Icon library | `${SKILL_DIR}/templates/icons/icons_index.json` | Query available icon names and categories |

## Standalone Workflows

| Workflow | Path | Purpose |
|----------|------|---------|
| `create-template` | `workflows/create-template.md` | Standalone template creation workflow |

---

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: User has provided source material (PDF / DOCX / EPUB / URL / Markdown file / text description / conversation content — any form is acceptable).

When the user provides non-Markdown content, convert immediately:

| User Provides | Command |
|---------------|---------|
| PDF file | `uv run python3 ${SKILL_DIR}/scripts/pdf_to_md.py <file>` |
| DOCX / Word / Office document | `uv run python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| EPUB / HTML / LaTeX / RST / other | `uv run python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| Web link | `uv run python3 ${SKILL_DIR}/scripts/web_to_md.py <URL>` |
| WeChat / high-security site | `node ${SKILL_DIR}/scripts/web_to_md.cjs <URL>` |
| Markdown | Read directly |

**✅ Checkpoint — Confirm source content is ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown file, user-provided text, or requirements described in conversation are all valid).

```bash
uv run python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

Format options: `ppt169` (default), `ppt43`, `xhs`, `story`, etc. For the full format list, see `references/canvas-formats.md`.

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF/MD/etc.) | `uv run python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...> --move` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps can reference it directly |

> ⚠️ **MUST use `--move`**: All source files (original PDF / MD / images) MUST be **moved** (not copied) into `sources/` for archiving.
> - Markdown files generated in Step 1, original PDFs, original MDs — **all** must be moved into the project via `import-sources --move`
> - Intermediate artifacts (e.g., `_files/` directories) are handled automatically by `import-sources`
> - After execution, source files no longer exist at their original location

**✅ Checkpoint — Confirm project structure created successfully, `sources/` contains all source files, converted materials are ready. Proceed to Step 3.**

---

### Step 3: Template Selection

🚧 **GATE**: Step 2 complete; project directory structure is ready.

⛔ **BLOCKING**: If the user has not yet clearly expressed whether to use a template, you MUST present options and **wait for an explicit user response** before proceeding. If the user has previously stated "no template" or specified a particular template, skip this prompt and proceed directly.

**⚡ Early-exit**: If the user has already stated "no template" / "不使用模板" / "自由设计" (or equivalent) at any prior point in the conversation, **do NOT query `layouts_index.json`** — skip directly to Step 4. This avoids unnecessary token consumption.

> [!CAUTION]
> ## 🎯 Case C — the user supplies their own `.pptx` as the template
>
> **This takes priority over the built-in library.** When the user points at a `.pptx`
> ("参照 XXX 模板输出", "用这个模板"), that file — not a `layouts/` entry — is the
> template, and its look must be reproduced, not approximated.
>
> ```bash
> uv run python3 ${SKILL_DIR}/scripts/pptx_to_template.py <template.pptx> <project_path>
> ```
> This unpacks the deck, extracts each layout's real background images and logos at
> their **exact** positions, and writes `templates/01_cover.svg` … `04_ending.svg`
> plus the brand assets into `images/`. Step 6 then inherits them automatically via
> the normal "template as base layer" rule.
>
> **Three failure modes to avoid — all observed in practice:**
> 1. ❌ **Never delete `templates/` because the built-in template clashes.** Emptying
>    that directory silently downgrades the run to free design, and the user's brand
>    disappears. Replace its contents instead.
> 2. ❌ **Never hand-draw a stand-in** for a background or logo you have the real
>    asset for (no `<linearGradient>` mimicking the backdrop, no re-placed logo at a
>    position you chose). Copy the real `<image>` at the real coordinates.
> 3. ❌ **Never mix two templates.** A built-in layout's colours plus the user's
>    background is not "fusion", it is a broken deck. One template wins.
>
> **Self-check before leaving Step 6** — every page must reference the template's own
> assets, and no page may carry a hand-made substitute:
> ```bash
> grep -o 'href="\.\./images/[^"]*"' <project_path>/svg_output/*.svg | sort | uniq -c
> ```

**Template recommendation flow** (only when the user has NOT yet decided):
Query `${SKILL_DIR}/templates/layouts/layouts_index.json` to list available templates and their style descriptions.
**When presenting options, you MUST provide a professional recommendation based on the current PPT topic and content** (recommend a specific template or free design, with reasoning), then ask the user:

> **Default recommendation**: Unless the content is clearly a poor fit for it (e.g. a
> non-corporate, non-technical, or non-security topic — academic defense, wedding invite,
> children's book, etc.), recommend the **QAX (奇安信)** template — `templates/layouts/奇安信/` —
> as the default choice. Still present it as a recommendation, not an automatic pick: the user
> confirms or overrides in their reply.

> 💡 **AI Recommendation**: Based on your content topic (brief summary), I recommend **[QAX (奇安信),
> unless clearly unsuitable] / [specific template / free design]** because...
>
> Which approach would you prefer?
> **A) Use an existing template** (please specify template name or style preference)
> **B) No template** — free design

After the user confirms option A, copy template files to the project directory:
```bash
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.svg <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/design_spec.md <project_path>/templates/
cp -R ${SKILL_DIR}/templates/layouts/<template_name>/content <project_path>/templates/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.png <project_path>/images/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.jpg <project_path>/images/ 2>/dev/null || true
```

> 📐 **Content layouts (body pages)**: a template has two layers. Its core pages
> (`01_cover` / `02_chapter` / `02_toc` / `03_content` / `04_ending`) are always used for
> cover, TOC, chapter and ending pages. A template whose entry in `layouts_index.json` has
> `contentLayouts` also ships `content/`: ready-made body pages with `{{SLOT}}` text and
> capacities (currently `奇安信`, `mckinsey`, `pixel_retro`, 22 layouts each). The `cp -R`
> above copies it; the Strategist then picks a layout ID per body page and the Executor fills
> it with `layout_fill.py`. Templates without `content/` design body pages freely on
> `03_content.svg`, as before. All templates share one layout library
> (`templates/content_library/`); give another template the layouts with `layout_build.py`
> — see `scripts/docs/layouts.md`. Do this only when the user asks; it is not part of a normal run.

After the user confirms option B, proceed directly to Step 4.

> To create a new template, Read `references/template-designer.md`

**✅ Checkpoint — User has responded with template selection, template files copied (if option A). Proceed to Step 4.**

---

### Step 4: Strategist Phase (MANDATORY — cannot be skipped)

🚧 **GATE**: Step 3 complete; user has confirmed template selection.

First, read the role definitions:
```
Read references/strategist.md
Read references/shared-standards.md
```

**Must complete the Eight Confirmations** (refer to `templates/design_spec_reference.md` for the template structure):

⛔ **BLOCKING**: The Eight Confirmations MUST be presented to the user as a bundled set of recommendations, and you MUST **wait for the user to confirm or modify** before outputting the Design Specification & Content Outline. This is one of only two core confirmation points in the workflow (the other is template selection). Once confirmed, all subsequent script execution and slide generation should proceed fully automatically.

1. Canvas format
2. Page count range
3. Target audience
4. Style objective (including **genre and density**: narrative / report / solution — see strategist.md §d)
5. Color scheme
6. Icon usage approach
7. Typography plan
8. Image usage approach

If the user has provided images, run the analysis script **before outputting the design spec** (do NOT directly read/open image files — use the script output only):
```bash
uv run python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> ⚠️ **Image handling rule**: The AI must NEVER directly read, open, or view image files (`.jpg`, `.png`, etc.). All image information must come from the `analyze_images.py` script output or the Design Specification's Image Resource List.

**Output**: `<project_path>/design_spec.md`
> 🚨 **CRITICAL I/O RULE**: To prevent IDE/Watcher deadlocks in this workspace, **NEVER** use standard AI file writing tools (like `write_to_file`) to output `design_spec.md`. You MUST use `uv run python3 ${SKILL_DIR}/scripts/file_write.py <target_path>` and pass the content via STDIN (e.g., using `send_command_input`) terminated by `<<EOF>>`.

The spec lives at the project root (`<project_path>/design_spec.md`, not under `templates/`):
the preview, the checker and the Executor all read it from there.

**Layout plan (every body page)**: choose layouts by the content's relation, not for variety — follow
`references/strategist.md` → *Content Layout Selection* (principles P1–P7, relation vocabulary,
five fields per page: Message / Relation / Layout / Claim check / Series). Then check the plan and fix
every `[FAIL]` before the checkpoint; `[HINT]` lines (density, rhythm) are for judgement:
```bash
uv run python3 ${SKILL_DIR}/scripts/layout_plan_check.py <project_path>
```

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:
```markdown
## ✅ Strategist Phase Complete
- [x] Eight Confirmations completed (user confirmed)
- [x] Design Specification & Content Outline generated
- [x] `layout_plan_check.py` passes
- [ ] **Next**: Auto-proceed to [Image_Generator / Executor] phase
```

**Auto-preview (non-blocking, FIRST appearance)**: Immediately run
```bash
uv run python3 ${SKILL_DIR}/scripts/preview.py <project_path> --serve
```
`--serve` writes `preview.html` as usual, then starts a local HTTP server rooted at the project
directory and opens it in the user's browser at `http://127.0.0.1:8890/preview.html` (falls back to
a random free port if 8890 is taken). **This is the recommended way to open it — not a plain
double-click** — because the "实际排布" SVG gallery and its lightbox reference pages by relative
path (`svg_output/xxx.svg`); serving over real HTTP guarantees those resolve regardless of how the
browser or environment handles local files, whereas a bare `file://` open depends on the viewer
keeping the HTML next to its sibling folder (usually fine, but not guaranteed everywhere). It also
means the "实际排布" gallery always reflects whatever is on disk **right now** with zero extra
effort — no rebuild needed just to see a newly-added SVG, since the browser fetches it live.

Tell the user the server is running and give them the URL from the command's own output, e.g.
"💡 Live preview: http://127.0.0.1:8890/preview.html — 页面会随生成自动刷新，无需手动重载".
`--serve` blocks the terminal it runs in — run it as a background/detached process so it doesn't
block the rest of the pipeline.

**Live refresh (automatic)**: the served page polls a small state endpoint and reloads itself
within ~2s whenever a new SVG lands in `svg_output/`, and `preview.html` is regenerated on every
request. So generation is visible **page by page** as it happens — the user does not need to
refresh, and you do not need to re-run `preview.py` just to make new pages appear.

**Stopping the preview server**:
```bash
kill $(lsof -ti tcp:8890)     # or press Ctrl+C in the terminal running it
```
Always stop it when the project is finished or you start a different project on the same port. Re-running
`preview.py` **without** `--serve` from elsewhere still works to refresh the "设计大纲"/"实际文字"
tabs (their content is baked into the HTML at write time, unlike the live SVG gallery) — the
running server will pick up the rewritten `preview.html` on the browser's next reload.

At this point only `design_spec.md` exists, so the preview shows the "设计大纲" outline-cards tab
(no SVGs yet) — this is expected and is the whole point: the user gets something to look at from
the earliest possible moment, before any SVG generation starts. This does not require user
confirmation and must not block or delay proceeding to the next step.

> 🔁 **This same server and file keep evolving in place** — see the refresh call inside Step 6
> below. The user just reloads the browser tab to see progress; no new link or server is needed.

---

### Step 5: Image_Generator Phase (Conditional)

🚧 **GATE**: Step 4 complete; Design Specification & Content Outline generated and user confirmed.

> **Trigger condition**: Image approach includes "AI generation". If not triggered, skip directly to Step 6 (Step 6 GATE must still be satisfied).

Read `references/image-generator.md`

1. Extract all images with status "pending generation" from the design spec
2. Generate prompt document → `<project_path>/images/image_prompts.md`
3. Generate images (CLI tool recommended):
   ```bash
   uv run python3 ${SKILL_DIR}/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
   ```

**✅ Checkpoint — Confirm all images are ready, proceed to Step 6**:
```markdown
## ✅ Image_Generator Phase Complete
- [x] Prompt document created
- [x] All images saved to images/
```

---

### Step 6: Executor Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete; all prerequisite deliverables are ready.

Read the role definition based on the selected style:
```
Read references/executor-base.md          # REQUIRED: common guidelines
Read references/executor-general.md       # General flexible style
Read references/executor-consultant.md    # Consulting style
Read references/executor-consultant-top.md # Top consulting style (MBB level)
```

> Only need to read executor-base + one style file.

> 📐 When a page's `Layout` field is a layout ID, fill `templates/content/<id>.svg` with
> `scripts/layout_fill.py` (executor-base.md §1.7) instead of drawing the page from scratch.

**Design Parameter Confirmation (Mandatory)**: Before generating the first SVG, the Executor MUST review and output key design parameters from the Design Specification (canvas dimensions, color scheme, font plan, body font size) to ensure spec adherence. See executor-base.md Section 2 for details.

**Visual Construction Phase**:
- Generate SVG pages one by one → `<project_path>/svg_output/`
> 🚨 **CRITICAL I/O RULE**: Do NOT use standard AI file writing tools directly to workspace files to create SVGs (to prevent IDE Watcher lock). Additionally, because terminal PTY pseudoterminals have single-command length limits (e.g., 4096 bytes) which cause bash HEREDOCs to hang and drop characters, you MUST use the Python Chunking bypass:
> 1. Create a `tmp/` directory inside the current project (`<project_path>/tmp/`).
> 2. Use `uv run python3 -c 'with open("<project_path>/tmp/page.svg.tmp", "a", encoding="utf-8") as f: f.write("""[CHUNK]""")'` to append small chunks (e.g., < 1000 characters) sequentially into a `.tmp` file.
> 3. Run `uv run python3 ${SKILL_DIR}/scripts/file_write.py <target_path> < <project_path>/tmp/page.svg.tmp` via `run_command` to safely write it into the workspace.
> 4. After the file is successfully written, delete the temporary file/directory (`rm -rf <project_path>/tmp/`).
> ⚠️ **SINGLE PAGE GENERATION RULE (MANDATORY)**: You MUST only generate **ONE SVG page per cycle**. Wait for the command to finish and verify that the SVG file was successfully generated before proceeding to the next page. **NEVER** batch-generate multiple SVGs.

**Auto-preview refresh (non-blocking, after EVERY page)**: Immediately after each SVG page is
successfully written to `svg_output/`, re-run
```bash
uv run python3 ${SKILL_DIR}/scripts/preview.py <project_path>
```
(without `--serve` here — the server from Step 4 is already running in the background; this call
just rewrites `preview.html` on disk). This is cheap (no LLM call, just re-parses `svg_output/`)
and updates the "实际文字" tab's baked-in transcript to include the page just generated. Note the
"实际排布" gallery itself needs no refresh call at all when `--serve` is running — it fetches SVGs
live from disk on every browser reload, so a newly-written page shows up the moment the user
reloads, even before this preview.py call runs. Do not skip the preview.py re-run anyway — it's
what keeps "实际文字" and the outline-vs-actual diff notice in sync. Do not re-surface the link
each time (it was already shared after Step 4 and is the same server); only mention progress in
your own status update if useful, e.g. "page 3/8 done, reload the preview to see it."

**Logic Construction Phase**:
- Generate speaker notes → `<project_path>/notes/total.md`

**✅ Checkpoint — Confirm all SVGs and notes are fully generated. Proceed directly to Step 7 post-processing**:
```markdown
## ✅ Executor Phase Complete
- [x] All SVGs generated to svg_output/
- [x] Speaker notes generated at notes/total.md
```

---

### Step 7: Post-processing & Export

🚧 **GATE**: Step 6 complete; all SVGs generated to `svg_output/`; speaker notes `notes/total.md` generated.

> ⚠️ The following three sub-steps MUST be **executed individually one at a time**. Each command must complete and be confirmed successful before running the next.
> ❌ **NEVER** put all three commands in a single code block or single shell invocation.

**Step 7.1** — Split speaker notes:
```bash
uv run python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Step 7.2** — SVG post-processing (icon embedding / image crop & embed / text flattening / rounded rect to path):
```bash
uv run python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Step 7.3** — Export PPTX (embeds speaker notes by default):
```bash
uv run python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
# Produces exactly ONE editable native-shapes deck named after the project.
# Re-running overwrites it in place — no timestamped duplicates accumulate.
#   --with-svg-ref  also emit the _svg.pptx reference twin (rarely needed)
#   --timestamp     keep each run as a separate file
```

**Step 7.4 (recommended)** — Verify the export:
```bash
uv run python3 ${SKILL_DIR}/scripts/verify_pptx_text.py <project_path>
```
Renders the deck and asserts every text run survived intact. Use this instead of
rendering page screenshots — it checks all pages at once and names the offender.

> ❌ **NEVER** use `cp` as a substitute for `finalize_svg.py` — it performs multiple critical processing steps
> ❌ **NEVER** export directly from `svg_output/` — MUST use `-s final` to export from `svg_final/`
> ❌ **NEVER** request the `_svg.pptx` twin by default — one deck is the deliverable

**Shortcut** — all of Step 7 as a single fail-fast command:
```bash
uv run python3 ${SKILL_DIR}/scripts/build_pptx.py <project_path> --verify
```
Stages stay serial and abort on first failure; this only removes the round-trips.

**Auto-preview (non-blocking)**: After export (Step 7.3 or the `build_pptx.py` shortcut)
completes, immediately run
```bash
uv run python3 ${SKILL_DIR}/scripts/preview.py <project_path>
```
(no `--serve` — the server started back at Step 4 is still running; this just rewrites
`preview.html` so the "实际文字" tab and outline-vs-actual diff notice reflect the final
`svg_final/` pages). If the user still has the preview open, tell them to reload for the final
state — no new link needed, same server. If no server is running for this project (e.g. resuming
in a fresh session), start one now with `--serve` and share the URL. It also writes
`<project_path>/executor_output.md`, a design_spec.md-shaped Markdown transcript of the same
per-page text, for diffing against the original outline. This runs once, does not require user
confirmation, and must not block or delay reporting the pipeline as complete.

---

## Editing a Single Page in an Existing Project

> Scope: content changes to one already-generated page. Structural changes
> (add/remove/reorder slides) are NOT covered here — do those directly in
> PowerPoint after export; it's native there and a script would only add a
> layer of indirection.

Two edit paths, depending on what changed:

| Change type | Path |
|-------------|------|
| Wording / numbers only (typo, updated figure, phrasing) — layout and structure untouched | Edit the `<text>` content directly in `svg_final/<page>.svg` (and `svg_output/<page>.svg` to keep them in sync) |
| Content or layout redesign (wrong emphasis, wants a different layout, needs a new chart) | Edit the matching `#### Slide NN` entry in `design_spec.md` first, then re-invoke the Executor role for that page only, overwriting both `svg_output/<page>.svg` and `svg_final/<page>.svg` |

**Locate the target page first**: use `<project_path>/executor_output.md` or the "实际文字" tab in
`preview.html` to find the page number and filename by its actual rendered content.

**Then re-process.** Prefer the incremental path — it re-runs post-processing for just that page
and leaves every other page in `svg_final/` untouched:
```bash
uv run python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path> --page <page_name>
uv run python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
```
Use the full rebuild when several pages changed or you are unsure:
```bash
uv run python3 ${SKILL_DIR}/scripts/build_pptx.py <project_path> --verify
```
Either way, never hand-patch the exported `.pptx`. The live preview refreshes on its own.
Check the changed page in the refreshed `preview.html` (layout tab) and `executor_output.md`
(text tab) before calling the edit done.

---

## Role Switching Protocol

Before switching roles, you **MUST first read** the corresponding reference file — skipping is FORBIDDEN. Output marker:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

---

## Reference Resources

| Resource | Path |
|----------|------|
| Shared technical constraints | `references/shared-standards.md` |
| Canvas format specification | `references/canvas-formats.md` |
| Image layout specification | `references/image-layout-spec.md` |
| SVG image embedding | `references/svg-image-embedding.md` |

---

## Notes

- Do NOT add extra flags like `--only` to the post-processing commands — run them as-is
- Local preview: `python3 -m http.server -d <project_path>/svg_final 8000`
