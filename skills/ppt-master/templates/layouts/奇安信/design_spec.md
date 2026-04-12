# QAX Style (奇安信) - Design Specification

> Corporate cybersecurity brand template for Qi An Xin (奇安信). Suitable for business planning, security reports, technical solutions, and corporate presentations.

## I. Template Overview

- **Brand**: 奇安信 Qi An Xin — 新一代网络安全领军者
- **Design Tone**: Authoritative, clean, tech-corporate, precise
- **Key Visual Elements**: 
  - Right-side watermark tiger silhouette (网安虎) with binary digits
  - Top-left QAX logo with gold tiger icon
  - White-to-light-blue bottom gradient background
  - Clean left-aligned title typography

## II. Canvas Specification

- **Aspect Ratio**: 16:9
- **viewBox**: `0 0 1280 720`
- **Source PDF ratio**: 1376×768 (scaled down to 1280×714, mapped to 1280×720)

## III. Color Scheme

### Primary Colors (pixel-extracted from official template)

| Role | HEX | RGB | Usage |
|------|-----|-----|-------|
| **QAX Blue** (Primary) | `#003892` | (0, 56, 146) | Titles, tiger outline, logo text |
| **QAX Gold** (Accent) | `#FAC800` | (250, 200, 0) | Tiger logo, gold highlights |
| **QAX Light Blue** (Accent 2) | `#0884E2` | (8, 132, 226) | Content icons, callout accents |
| **Table Header Blue** | `#4471C4` | (68, 113, 196) | Table header backgrounds |

### Backgrounds

| Role | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Base BG** | `#FFFFFF` | (255, 255, 255) | Top of slides |
| **Bottom Gradient** | `#E8F1FF` | (232, 241, 255) | Bottom edge gradient |
| **Insight Bar BG** | `#E5F2FC` | (229, 242, 252) | Light blue callout bar |
| **Table Row Alt** | `#E9EBF5` | (233, 235, 245) | Alternating table row |

### Text Colors

| Role | HEX | Usage |
|------|-----|-------|
| **Title** | `#003892` | H1 page titles |
| **Body** | `#333333` | Primary body text |
| **Muted** | `#666666` | Captions, dates |
| **Red Accent** | `#E03030` | Subtitle/unit label on cover |

### Tiger Watermark Colors

| Context | HEX | Usage |
|---------|-----|-------|
| **Cover/Ending** (dark) | `#013893` | Bold tiger outline + binary |
| **Chapter/TOC** (light) | `#B4C3DC` | Soft watermark tiger outline |

## IV. Typography System

- **Font Family**: Microsoft YaHei / sans-serif
- **Cover Title**: 54px, bold, `#003892`
- **Page Title (H1)**: 40px, bold, `#003892`
- **Section Title (H2)**: 28px, bold, `#003892`
- **Body Text**: 20px, regular, `#333333`
- **Caption/Source**: 14px, regular, `#666666`
- **Logo Slogan**: 16px, regular, `#003892`, letter-spacing: 4px

## V. Core Design Principles

### QAX Style Characteristics

1. **Data-Driven**: Key data and insights at the core, strengthening argument support
2. **Structured Thinking**: MECE principle, clear logical frameworks
3. **Information Visualization**: Charts, matrices, and funnel models take priority
4. **Professional Whitespace**: Ample breathing room, content coverage < 65%
5. **Grid Alignment**: 40px baseline grid, precise alignment
6. **Minimalist Icons**: Geometric shapes, avoiding ornate decoration
7. **Professional Color Palette**: Avoiding flashy gradients, maintaining restraint

## VI. Page Structure

### Cover (Page 1)
- Logo + gold tiger icon: top-left (~80, 70)
- Slogan "新一代网络安全领军者": below logo
- Main title: left-aligned, vertical center (~80, 380)
- Subtitle in gray bar: below title
- Tiger watermark: right half, extending beyond right edge
- BG: white → `#E8F1FF` bottom gradient

### Chapter/TOC (Page 2)
- Page title: top-left (~60, 55), bold, `#003892`
- QAX logo: top-right corner
- Content items: left-side listing
- Tiger watermark: right half, light blue `#B4C3DC` version
- BG: pure white, no gradient

### Content (Pages 3-4)
- Page title: top-left (~60, 55), bold, `#003892`
- QAX logo: top-right corner
- Content safe area: 60px margins
- Optional bottom insight bar: light blue `#E5F2FC`
- Table headers: `#4471C4` with white text
- BG: pure white

### Ending (Page 5)
- Logo + gold tiger: top-left (~80, 70)
- Thank you text: large, left-aligned, `#003892`
- English "Thanks!": below
- Slogan "让网络更安全 让世界更美好": bottom-left
- Tiger watermark: right half, dark blue version
- BG: white → `#E8F1FF` bottom gradient (same as cover)

## VI. SVG Technical Constraints

- `viewBox="0 0 1280 720"`
- All backgrounds use `<rect>` elements
- Tiger watermark rendered as `<path>` geometric approximation
- Use `fill-opacity` for transparency (NO `rgba()`)
- NO `clipPath`, `mask`, `<foreignObject>`, `<style>`, `class`
- Gradients via `<defs>` + `<linearGradient>`
- Text uses `<text>` + `<tspan>` for wrapping
