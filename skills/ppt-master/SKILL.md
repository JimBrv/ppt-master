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
| Layout templates | `${SKILL_DIR}/templates/layouts/layouts_index.json` | Query available page layout templates |
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
| PDF file | `python3 ${SKILL_DIR}/scripts/pdf_to_md.py <file>` |
| DOCX / Word / Office document | `python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| EPUB / HTML / LaTeX / RST / other | `python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| Web link | `python3 ${SKILL_DIR}/scripts/web_to_md.py <URL>` |
| WeChat / high-security site | `node ${SKILL_DIR}/scripts/web_to_md.cjs <URL>` |
| Markdown | Read directly |

**✅ Checkpoint — Confirm source content is ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown file, user-provided text, or requirements described in conversation are all valid).

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

Format options: `ppt169` (default), `ppt43`, `xhs`, `story`, etc. For the full format list, see `references/canvas-formats.md`.

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF/MD/etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...> --move` |
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

**Template recommendation flow** (only when the user has NOT yet decided):
Query `${SKILL_DIR}/templates/layouts/layouts_index.json` to list available templates and their style descriptions.
**When presenting options, you MUST provide a professional recommendation based on the current PPT topic and content** (recommend a specific template or free design, with reasoning), then ask the user:

> 💡 **AI Recommendation**: Based on your content topic (brief summary), I recommend **[specific template / free design]** because...
>
> Which approach would you prefer?
> **A) Use an existing template** (please specify template name or style preference)
> **B) No template** — free design

After the user confirms option A, copy template files to the project directory:
```bash
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.svg <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/design_spec.md <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.png <project_path>/images/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.jpg <project_path>/images/ 2>/dev/null || true
```

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
4. Style objective
5. Color scheme
6. Icon usage approach
7. Typography plan
8. Image usage approach

If the user has provided images, run the analysis script **before outputting the design spec** (do NOT directly read/open image files — use the script output only):
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> ⚠️ **Image handling rule**: The AI must NEVER directly read, open, or view image files (`.jpg`, `.png`, etc.). All image information must come from the `analyze_images.py` script output or the Design Specification's Image Resource List.

**Output**: `<project_path>/design_spec.md`
> 🚨 **CRITICAL I/O RULE**: To prevent IDE/Watcher deadlocks in this workspace, **NEVER** use standard AI file writing tools (like `write_to_file`) to output `design_spec.md`. You MUST use `python3 ${SKILL_DIR}/scripts/file_write.py <target_path>` and pass the content via STDIN (e.g., using `send_command_input`) terminated by `<<EOF>>`.

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:
```markdown
## ✅ Strategist Phase Complete
- [x] Eight Confirmations completed (user confirmed)
- [x] Design Specification & Content Outline generated
- [ ] **Next**: Auto-proceed to [Image_Generator / Executor] phase
```

**Auto-preview (non-blocking)**: Immediately run
```bash
python3 ${SKILL_DIR}/scripts/preview.py <project_path>
```
and surface the resulting `<project_path>/preview.html` path as a clickable link in your reply,
e.g. "💡 Outline preview ready: [preview.html](<project_path>/preview.html)". This runs once, does
not require user confirmation, and must not block or delay proceeding to the next step.

---

### Step 5: Image_Generator Phase (Conditional)

🚧 **GATE**: Step 4 complete; Design Specification & Content Outline generated and user confirmed.

> **Trigger condition**: Image approach includes "AI generation". If not triggered, skip directly to Step 6 (Step 6 GATE must still be satisfied).

Read `references/image-generator.md`

1. Extract all images with status "pending generation" from the design spec
2. Generate prompt document → `<project_path>/images/image_prompts.md`
3. Generate images (CLI tool recommended):
   ```bash
   python3 ${SKILL_DIR}/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
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

**Design Parameter Confirmation (Mandatory)**: Before generating the first SVG, the Executor MUST review and output key design parameters from the Design Specification (canvas dimensions, color scheme, font plan, body font size) to ensure spec adherence. See executor-base.md Section 2 for details.

**Visual Construction Phase**:
- Generate SVG pages one by one → `<project_path>/svg_output/`
> 🚨 **CRITICAL I/O RULE**: Do NOT use standard AI file writing tools directly to workspace files to create SVGs (to prevent IDE Watcher lock). Additionally, because terminal PTY pseudoterminals have single-command length limits (e.g., 4096 bytes) which cause bash HEREDOCs to hang and drop characters, you MUST use the Python Chunking bypass:
> 1. Create a `tmp/` directory inside the current project (`<project_path>/tmp/`).
> 2. Use `python3 -c 'with open("<project_path>/tmp/page.svg.tmp", "a", encoding="utf-8") as f: f.write("""[CHUNK]""")'` to append small chunks (e.g., < 1000 characters) sequentially into a `.tmp` file.
> 3. Run `python3 ${SKILL_DIR}/scripts/file_write.py <target_path> < <project_path>/tmp/page.svg.tmp` via `run_command` to safely write it into the workspace.
> 4. After the file is successfully written, delete the temporary file/directory (`rm -rf <project_path>/tmp/`).
> ⚠️ **SINGLE PAGE GENERATION RULE (MANDATORY)**: You MUST only generate **ONE SVG page per cycle**. Wait for the command to finish and verify that the SVG file was successfully generated before proceeding to the next page. **NEVER** batch-generate multiple SVGs.

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
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Step 7.2** — SVG post-processing (icon embedding / image crop & embed / text flattening / rounded rect to path):
```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Step 7.3** — Export PPTX (embeds speaker notes by default):
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
# Produces exactly ONE editable native-shapes deck named after the project.
# Re-running overwrites it in place — no timestamped duplicates accumulate.
#   --with-svg-ref  also emit the _svg.pptx reference twin (rarely needed)
#   --timestamp     keep each run as a separate file
```

**Step 7.4 (recommended)** — Verify the export:
```bash
python3 ${SKILL_DIR}/scripts/verify_pptx_text.py <project_path>
```
Renders the deck and asserts every text run survived intact. Use this instead of
rendering page screenshots — it checks all pages at once and names the offender.

> ❌ **NEVER** use `cp` as a substitute for `finalize_svg.py` — it performs multiple critical processing steps
> ❌ **NEVER** export directly from `svg_output/` — MUST use `-s final` to export from `svg_final/`
> ❌ **NEVER** request the `_svg.pptx` twin by default — one deck is the deliverable

**Shortcut** — all of Step 7 as a single fail-fast command:
```bash
python3 ${SKILL_DIR}/scripts/build_pptx.py <project_path> --verify
```
Stages stay serial and abort on first failure; this only removes the round-trips.

**Auto-preview (non-blocking)**: After export (Step 7.3 or the `build_pptx.py` shortcut)
completes, immediately run
```bash
python3 ${SKILL_DIR}/scripts/preview.py <project_path>
```
and surface the resulting `<project_path>/preview.html` path as a clickable link in your reply,
e.g. "💡 Layout preview ready: [preview.html](<project_path>/preview.html)" — it now renders the
real SVG thumbnail gallery plus a plain-text transcript of every page's actual text runs (tabbed
against the outline if design_spec.md is still present). It also writes
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

**After either path, re-run the full pipeline** (whole-project re-run is cheap; there is no
single-page mode for `finalize_svg.py` / `svg_to_pptx.py`, so don't try to hand-patch the exported
`.pptx`):
```bash
python3 ${SKILL_DIR}/scripts/build_pptx.py <project_path> --verify
python3 ${SKILL_DIR}/scripts/preview.py <project_path>
```
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
