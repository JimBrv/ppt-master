# PPT Master — AI 驱动的可编辑 PPTX 自动生成工具

[![Version](https://img.shields.io/badge/version-v2.3.x-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Based on](https://img.shields.io/badge/based%20on-hugohe3%2Fppt--master-orange.svg)](https://github.com/hugohe3/ppt-master)

[English](./README.md) | **中文**

---

## 📢 关于本仓库

> **本仓库基于 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 二次开发，在原项目基础上进行了以下优化与扩展。**

### 🔧 主要更新

| 类别 | 更新内容 |
|------|----------|
| **🐛 PTY 终端 I/O 修复** | 彻底解决 AI 写入大文件（SVG / design_spec.md）时因 PTY 缓冲区 4096 字符上限导致的终端挂起问题。废弃 Base64 方案，改为**本地 `tmp/` 目录中转 + 明文分块写入**的稳定流水线，并加固 `file_write.py` 和相关规范文档。 |
| **🖼️ PDF 图片黑底修复** | `pdf_to_md.py` 提取 PDF 内嵌图像时，若图像含透明通道（RGBA/Alpha PNG）直接保存为 JPEG 会导致背景变黑。修复为**使用 Pillow 将 alpha 合并到白色背景**再保存，同时统一输出格式为 JPEG（quality=92），消除扩展名不一致问题。 |
| **📊 Excel 转 Markdown 工具** | 新增 `excel_to_md.py`：支持 `.xlsx / .xlsm / .xltx / .xltm` 格式，多 Sheet 分节输出、合并单元格注释、超链接转 Markdown、单元格批注提取、嵌入图片保存（同步修复黑底问题）、命名范围汇总、日期自动格式化。 |
| **📌 临时文件规范** | 所有生成过程中的临时文件统一写入当前项目的 `tmp/` 子目录，任务完成后自动清理，保持工程目录整洁。已写入 SKILL.md 作为强制规范。 |
| **📦 uv 环境管理** | 本项目统一使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包与虚拟环境管理工具，替代传统 `pip`。所有脚本通过 `uv run python3 <script>` 执行，依赖通过 `uv pip install` 安装，项目配置写入 `pyproject.toml`。 |
| **📋 AGENTS.md 更新** | 更新工具命令速查表，新增 `excel_to_md.py` 条目及 PTY I/O 锁绕过说明。 |
| **🛡️ 奇安信默认模板** | 从奇安信 PPT 提取真实背景与 logo 的品牌模板。未指定模板时默认推荐（仍由用户确认）。 |
| **📐 正文版式** | 22 种正文页版式（大字论断、关键数字、问题→对策、对照、三支柱、阶段、漏斗、金字塔、时间线、四象限等），每个版式标明它表达的内容关系和可验证的视觉暗示。每个版式是带 `{{SLOT}}` 槽位和容量的完整页面，`layout_fill.py` 填充并拒绝超长文字。`奇安信`、`mckinsey`、`pixel_retro` 已配备。 |
| **🧭 按内容关系选版式** | 策略师按内容关系（16 类词汇）为每个正文页选版式，用版式的视觉暗示验证内容，平行章节统一版式，并按文体（议论 / 汇报 / 方案）控制每页文字量。`layout_plan_check.py` 校验规划。 |
| **🧩 共享版式库** | 版式按颜色角色只写一次（`templates/content_library/`）；模板只需提供 `theme.json` + `shell.svg`，由 `layout_build.py` 生成 `content/`。`pptx_inspect.py`、`layout_stress.py` 用于从参考 PPT 吸收新版式并压测。 |
| **🎨 用你的 .pptx 当模板** | `pptx_to_template.py` 把用户提供的 `.pptx` 转成模板，背景与 logo 按原位置还原。 |
| **👀 实时预览** | `preview.py --serve` 提供 设计大纲 / 实际排布 / 实际文字 三个标签页，SVG 逐页生成即自动刷新；`executor_output.md` 记录执行过程。 |
| **📦 一步导出** | `build_pptx.py --verify` 依次执行备注拆分 → finalize → 导出，出错即停，并校验文字无丢失、无断行；默认只输出一份可编辑 PPT。单页修改可用 `--page` 重新处理。 |
| **🤖 多 AI 入口** | `AGENTS.md` 为通用入口，`GEMINI.md` 引用它，Gemini / Codex 可直接使用同一套 skill；`uv.lock` 纳入版本管理，环境可复现。 |

> **致谢**：感谢原作者 [@hugohe3](https://github.com/hugohe3) 的出色设计，本仓库所有功能扩展均遵循原项目 MIT 协议。

---

## 简介

输入 PDF、DOCX、Excel、URL 或 Markdown 文件，AI 自动生成**可原生编辑的 PowerPoint 演示文稿**（真实 DrawingML 形状，非图片嵌入）。每个文本框、图表、图形均为可点击和编辑的原生 PowerPoint 对象。支持 PPT 16:9、社交媒体卡片、营销海报等 10+ 种格式。

> 🔥 **原生可编辑 PPTX** — 默认导出包含**真实 PowerPoint 形状**（DrawingML），文字、图表、图形均可在 PowerPoint 中直接编辑，无需额外操作。
>
> 🎨 **设计理念**：生成的 PPTX 是**设计草稿**，不是成品。AI 负责视觉设计、布局和内容结构，提供一个高质量起点。最终打磨仍需在 PowerPoint 中完成。

---

## 🏗️ 系统架构

```
用户输入 (PDF / DOCX / XLSX / URL / Markdown)
    ↓
[内容格式转换]
    ├── pdf_to_md.py       ← PDF → Markdown（自动提取图像，修复黑底）
    ├── doc_to_md.py       ← DOCX/EPUB/HTML/LaTeX → Markdown（需 pandoc）
    ├── excel_to_md.py     ← Excel → Markdown（NEW: 多 Sheet / 合并单元格 / 图片）
    └── web_to_md.py       ← URL → Markdown
    ↓
[创建项目] → project_manager.py init <project_name> --format ppt169
    ↓
[模板] — 默认奇安信；核心页 + 可选正文版式（content/）
    ↓
[策略师] — 八大确认 & 设计规格；为每个正文页选定版式
    ↓
[图像生成器]（选择 AI 图像生成时）
    ↓
[执行者] — 两阶段生成
    ├── 视觉构建阶段：SVG 页面 → svg_output/
    └── 逻辑构建阶段：演讲备注 → notes/total.md
    ↓
[后处理流水线 — 必须串行执行]
    ├── total_md_split.py  ← 备注拆分为每页文件
    ├── finalize_svg.py    ← 嵌入图像、修正几何
    └── svg_to_pptx.py     ← SVG → 原生 DrawingML PPTX
    （build_pptx.py --verify 一次跑完三步并校验文字）
    ↓
输出：
    └── <项目名>.pptx            ← 原生形状（DrawingML）— 可直接编辑
```

### 📚 文档导航

| 文档 | 说明 |
|------|------|
| 🧭 [AGENTS.md](./AGENTS.md) | 通用 AI 代理入口，工具命令速查 |
| 📖 [SKILL.md](./skills/ppt-master/SKILL.md) | 完整工作流规范与角色定义 |
| 📐 [Canvas Formats](./skills/ppt-master/references/canvas-formats.md) | PPT/小红书/朋友圈/海报等 10+ 格式 |
| 🛠️ [Scripts README](./skills/ppt-master/scripts/README.md) | 工具脚本索引与高频命令 |
| 📊 [Chart Templates](./skills/ppt-master/templates/charts/) | 标准化图表模板库 |
| 🗂️ [Layout Templates](./skills/ppt-master/templates/layouts/README.md) | 21 套页面模板，以及哪些配有正文版式 |
| 📐 [Content Layouts](./skills/ppt-master/scripts/docs/layouts.md) | 正文版式的填充、生成、吸收与压测 |
| 💼 [Examples](./examples/README.md) | 15 个示例项目，229 页 SVG 样例 |

---

## 🚀 快速开始

### 1. 环境准备

#### Python + uv（必须）

Python 3.8+，并使用 **[uv](https://github.com/astral-sh/uv)** 作为包管理与虚拟环境工具。`uv` 比 `pip` 速度快 10-100 倍，且自动管理虚拟环境。

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS / Linux
# 或
brew install uv  # macOS（使用 Homebrew）

# 验证安装
uv --version
python3 --version  # 需要 >= 3.14
```

#### 安装依赖

```bash
git clone <this-repo-url>
cd ppt-master

# 安装项目依赖（自动创建 .venv）
uv sync
```

> 💡 所有脚本**统一使用 `uv run python3`** 执行，确保依赖隔离：
> ```bash
> uv run python3 skills/ppt-master/scripts/pdf_to_md.py input.pdf
> ```

#### Pandoc（可选）

用于 DOCX/EPUB/LaTeX 等文档格式转换：

```bash
brew install pandoc   # macOS
sudo apt install pandoc  # Ubuntu
```

#### Node.js（可选）

用于 `web_to_md.cjs`（微信等高安全性网站转换），需要 node >= 18：

```bash
brew install node  # macOS
```

### 2. 选择 AI 编辑器

| 工具 | 推荐度 | 说明 |
|------|:------:|------|    
| **Antigravity** | ⭐⭐⭐⭐ | 强烈推荐 — gemini-3.x-pro |
| **Claude Code** | ⭐⭐⭐ | 强烈推荐，原生 Opus 支持，上下文窗口最大 |
| **Cursor** | ⭐⭐ | 主流 AI 编辑器，体验好 |
| VS Code + Copilot | ⭐⭐ | 微软官方，性价比高 |
| Codebuddy IDE | ⭐⭐ | 支持国产模型（Kimi / MiniMax） |

**打开 ppt-master 文件夹在你的 AI IDE 中**
**直接和 IDE 对话，说：我需要把一个 PDF 文件做成 PPT。**

### 3. 开始创作

在 AI 对话框中描述你的内容需求：

```
用户：我有一份 Q3 季度报告（report.pdf），需要做成一个 PPT

AI：好的，我先读取文件，然后进行策略师八大确认：
   [Strategist] 1. 画布格式：PPT 16:9（推荐）
   [Strategist] 2. 页数：8-10 页（推荐）
   ...
```

> 💡 **AI 丢失上下文？** 让 AI 先读取 `skills/ppt-master/SKILL.md`；使用 `AGENTS.md` 作为仓库级入口。

---

## 🛠️ 常用命令

```bash
# ── 项目初始化 ──────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
uv run python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <files...>

# ── 内容转换 ────────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/pdf_to_md.py <PDF_file>
uv run python3 skills/ppt-master/scripts/doc_to_md.py <DOCX_or_other>   # 需要 pandoc
uv run python3 skills/ppt-master/scripts/excel_to_md.py <XLSX_or_XLSM>  # 需要 openpyxl pillow
uv run python3 skills/ppt-master/scripts/web_to_md.py <URL>
node skills/ppt-master/scripts/web_to_md.cjs <URL>

# ── 图像工具 ────────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 -o <project>/images
uv run python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images

# ── 模板与正文版式 ──────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/pptx_to_template.py <template.pptx> <project_path>
uv run python3 skills/ppt-master/scripts/layout_fill.py <project_path> --slots <layout_id>
uv run python3 skills/ppt-master/scripts/layout_fill.py <project_path> <layout_id> <values.json> -o <project_path>/svg_output/<page>.svg
uv run python3 skills/ppt-master/scripts/layout_build.py skills/ppt-master/templates/layouts/<template> [--check|--init]
uv run python3 skills/ppt-master/scripts/layout_plan_check.py <project_path> [--output]
uv run python3 skills/ppt-master/scripts/layout_stress.py skills/ppt-master/templates/layouts/<template>
uv run python3 skills/ppt-master/scripts/pptx_inspect.py <deck.pptx> -o <out_dir> --pages 12-35 --render

# ── 后处理与导出（推荐：一次执行，出错即停）──────────────────────
uv run python3 skills/ppt-master/scripts/build_pptx.py <project_path> --verify
# 手动方式（逐条执行，确认无误再下一步）：
#   total_md_split.py <project_path> → finalize_svg.py <project_path> → svg_to_pptx.py <project_path> -s final
# 只重新处理改过的一页：
uv run python3 skills/ppt-master/scripts/finalize_svg.py <project_path> --page <page_name>

# ── 实时预览 ────────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/preview.py <project_path> --serve

# ── SVG 质量检查 ─────────────────────────────────────────────────
uv run python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
```

---

## 📁 项目结构

```text
ppt-master/
├── skills/
│   └── ppt-master/                 # 主 Skill 源码
│       ├── SKILL.md                #   工作流主入口
│       ├── workflows/              #   工作流文件
│       ├── references/             #   角色定义与技术规范
│       ├── scripts/                #   工具脚本
│       │   ├── pdf_to_md.py        #     PDF → Markdown（修复黑底 Bug）
│       │   ├── doc_to_md.py        #     DOCX/EPUB → Markdown
│       │   ├── excel_to_md.py      #     Excel → Markdown（NEW）
│       │   ├── web_to_md.py        #     URL → Markdown
│       │   ├── file_write.py       #     I/O 安全写入（修复 PTY 挂起）
│       │   ├── project_manager.py  #     项目管理
│       │   ├── finalize_svg.py     #     SVG 后处理
│       │   ├── svg_to_pptx.py      #     SVG → PPTX 导出
│       │   ├── build_pptx.py       #     一步导出 + 文字校验
│       │   ├── preview.py          #     实时预览
│       │   ├── pptx_to_template.py #     用户 .pptx → 模板
│       │   ├── layout_*.py         #     正文版式：生成 / 填充 / 压测
│       │   └── image_gen.py        #     AI 图像生成
│       └── templates/
│           ├── layouts/            #     21 套页面模板（默认奇安信）；content/ 为正文版式
│           ├── content_library/    #     22 种正文版式的共享库
│           ├── charts/             #     图表模板
│           └── icons/              #     矢量图标
├── examples/                       # 示例项目（15 个，229 页）
├── projects/                       # 用户项目工作区
├── AGENTS.md                       # 通用 AI 代理入口
├── CLAUDE.md                       # Claude Code 专用入口
└── GEMINI.md                       # Gemini 入口（引用 AGENTS.md）
```

---

## ⚙️ SVG 技术约束

生成 SVG 时，以下特性**禁止使用**（DrawingML 不支持）：

**禁用**: `clipPath` | `mask` | `<style>` | `class` | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<symbol>+<use>`

**替代方案**:

| 禁用 | 使用替代 |
|------|---------|
| `rgba()` | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` | 对每个子元素单独设置 opacity |
| `marker-end` 箭头 | `<polygon>` 三角形 |

**画布格式**:

| 格式 | viewBox |
|------|---------|
| PPT 16:9 | `0 0 1280 720` |
| PPT 4:3 | `0 0 1024 768` |
| 小红书 | `0 0 1242 1660` |
| 朋友圈 | `0 0 1080 1080` |

---

## ❓ 常见问题

<details>
<summary><b>Q: 生成的 PPTX 可以编辑吗？</b></summary>

可以！默认导出的 `.pptx` 包含**原生 PowerPoint 形状**——所有文字、图形、颜色均可在 PowerPoint 中直接编辑，无需任何转换步骤。同时生成的 SVG 参考版（`_svg.pptx`）选中内容后使用「**转换为形状**」即可解锁编辑。需要 **Office 2016** 或更高版本。

</details>

<details>
<summary><b>Q: SVG 文件中有图片时为什么背景是黑色？</b></summary>

这是 PDF 嵌入 PNG（含 Alpha 透明通道）时的已知问题，JPEG 不支持 Alpha，直接写入会将透明像素映射为黑色。**本仓库已修复此问题**：`pdf_to_md.py` 和 `excel_to_md.py` 现在会使用 Pillow 将透明通道合并到白色背景后再保存为 JPEG。

</details>

<details>
<summary><b>Q: AI 写 SVG 时终端卡死（hang）了怎么办？</b></summary>

这是 PTY 伪终端 4096 字符缓冲区限制导致的。**本仓库已修复此问题**：所有 SVG 和大文件写入均改为「本地 `tmp/` 目录中转 + 分块写入 + `file_write.py` 原子转写」的安全流水线，彻底规避缓冲区溢出。详见 `SKILL.md` I/O Lock Bypass 章节。

</details>

<details>
<summary><b>Q: 图表可以编辑数据吗？</b></summary>

图表渲染为**自定义 SVG 图形**转换的原生 PowerPoint 形状——不是 Excel 驱动的图表对象。视觉外观通常优于 PowerPoint 默认图表，但无法在图表编辑器中修改底层数据。如需可编辑数据的动态图表，需在导出后手动替换为 PowerPoint 原生图表。

</details>

<details>
<summary><b>Q: 如何使用 Excel 转 Markdown 工具？</b></summary>

```bash
# 安装依赖
uv pip install openpyxl pillow

# 基本用法
uv run python3 skills/ppt-master/scripts/excel_to_md.py data.xlsx
uv run python3 skills/ppt-master/scripts/excel_to_md.py report.xlsm -o output.md
```

支持特性：多 Sheet 分节、合并单元格注释、超链接、批注提取、嵌入图片（白底）、命名范围、日期格式化。

</details>

> 📖 更多问题参见 [SKILL.md](./skills/ppt-master/SKILL.md) 和 [AGENTS.md](./AGENTS.md)

---

## 🔧 技术设计

**流水线：AI 生成 SVG → 后处理转换为 DrawingML（PPTX）**

**为什么选择 SVG？**

SVG 与 DrawingML 共享同一世界观：两者都是基于绝对坐标的 2D 矢量图形格式，概念完全对应：

| SVG | DrawingML |
|-----|-----------|
| `<path d="...">` | `<a:custGeom>` |
| `<rect rx="...">` | `<a:prstGeom prst="roundRect">` |
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse">` |
| `transform="translate/scale/rotate"` | `<a:xfrm>` |
| `linearGradient` / `radialGradient` | `<a:gradFill>` |
| `fill-opacity` / `stroke-opacity` | `<a:alpha>` |

转换是两种方言之间的翻译，而非格式不匹配。SVG 同时满足流水线中的每个角色：**AI 可以可靠地生成它，人类可以在浏览器中预览和调试它，脚本可以精确地将其转换**——在写第一行 DrawingML 之前这些都已完成。

---

## 🤝 贡献

欢迎贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

**贡献方向**: 🎨 设计模板 · 📊 图表组件 · 📝 文档改进 · 🐛 Bug 报告 · 💡 功能建议

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源，与原始仓库 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 保持相同协议。

---

## 🙏 致谢

- **[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)** — 原始项目，本仓库的基础
- [SVG Repo](https://www.svgrepo.com/) — 开源图标库
- [Robin Williams](https://en.wikipedia.org/wiki/Robin_Williams_(author)) — CRAP 设计原则
- McKinsey、Boston Consulting、Bain — 设计风格灵感

