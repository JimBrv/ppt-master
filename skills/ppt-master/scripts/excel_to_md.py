#!/usr/bin/env python3
"""
Excel to Markdown Converter

Uses openpyxl to parse Excel workbooks (.xlsx / .xlsm / .xltx / .xltm)
and exports all sheets as structured Markdown, suitable for LLM analysis
and PPT content extraction.

Supports:
  - Multi-sheet workbooks (each sheet = a section)
  - Merged cells (content shown at top-left cell)
  - Basic number/date formatting
  - Named ranges (exported as a reference table)
  - Embedded images (saved to _files/ directory)
  - Sheet-level notes / comments
  - Empty row/column trimming
  - Hyperlinks in cells

Dependency:
  pip install openpyxl pillow
  (pillow is needed for embedded image extraction)
"""

import argparse
import io
import re
import sys
from datetime import datetime, date, time
from pathlib import Path


# ── Supported extensions ──────────────────────────────────────────────────────

SUPPORTED_EXTS = {".xlsx", ".xlsm", ".xltx", ".xltm"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _cell_value(cell) -> str:
    """Convert a cell value to a clean string representation."""
    val = cell.value
    if val is None:
        return ""
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        # Try to format using the cell's number format if it looks date-like
        fmt = cell.number_format or ""
        if any(k in fmt.lower() for k in ("yy", "mm", "dd", "hh", "ss")):
            try:
                from openpyxl.utils.datetime import from_excel
                dt = from_excel(val)
                if isinstance(dt, datetime):
                    return dt.strftime("%Y-%m-%d %H:%M:%S").rstrip(" 00:00:00") or dt.strftime("%Y-%m-%d")
                if isinstance(dt, date):
                    return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        # Regular number: strip trailing zeros for floats
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        return str(val)
    if isinstance(val, (datetime, date, time)):
        if isinstance(val, datetime):
            s = val.strftime("%Y-%m-%d %H:%M:%S")
            return s.rstrip(" 00:00:00") or val.strftime("%Y-%m-%d")
        if isinstance(val, date):
            return val.strftime("%Y-%m-%d")
        return str(val)
    # String — strip control chars, collapse internal newlines to space
    text = str(val)
    text = re.sub(r"[\r\n\t]+", " ", text).strip()
    # Escape markdown pipe
    text = text.replace("|", "\\|")
    return text


def _trim_grid(grid: list[list[str]]) -> list[list[str]]:
    """Remove fully-empty trailing rows and columns."""
    if not grid:
        return grid

    # Trim trailing empty rows
    while grid and all(c == "" for c in grid[-1]):
        grid.pop()
    if not grid:
        return grid

    # Find last non-empty column
    max_col = max(
        (i for row in grid for i, c in enumerate(row) if c != ""),
        default=0,
    )
    return [row[: max_col + 1] for row in grid]


def _make_md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format a list of rows as a Markdown table."""
    if not headers and not rows:
        return ""

    # Pad all rows to same width as headers
    n = len(headers)
    padded_rows = [row + [""] * max(0, n - len(row)) for row in rows]

    # Calculate column widths
    widths = [max(len(h), max((len(r[i]) for r in padded_rows), default=0))
              for i, h in enumerate(headers)]

    def fmt_row(cells):
        return "| " + " | ".join(
            str(c).ljust(widths[i]) for i, c in enumerate(cells)
        ) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [fmt_row(headers), sep]
    lines += [fmt_row(r[:n] + [""] * max(0, n - len(r))) for r in padded_rows]
    return "\n".join(lines)


# ── Core conversion ───────────────────────────────────────────────────────────

def convert_excel_to_markdown(input_path: str, output_path: str = None) -> str:
    """
    Convert an Excel workbook to Markdown.

    Args:
        input_path:  Path to the .xlsx / .xlsm file.
        output_path: Output .md path (default: same directory, .md extension).

    Returns:
        The generated Markdown string (also written to output_path).
    """
    try:
        import openpyxl
    except ImportError:
        print("[ERROR] openpyxl is not installed.")
        print("   Install: pip install openpyxl")
        return ""

    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[ERROR] File not found: {input_path}")
        return ""

    if input_file.suffix.lower() not in SUPPORTED_EXTS:
        print(f"[ERROR] Unsupported file type: {input_file.suffix}")
        print(f"   Supported: {', '.join(sorted(SUPPORTED_EXTS))}")
        return ""

    print(f"[INFO] Loading workbook: {input_file.name}")
    try:
        wb = openpyxl.load_workbook(input_file, data_only=True)
    except Exception as e:
        print(f"[ERROR] Failed to open workbook: {e}")
        return ""

    # Determine output paths
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = input_file.with_suffix(".md")

    rel_img_dir = f"{out_file.stem}_files"
    img_dir = out_file.parent / rel_img_dir
    img_count = 0

    md_parts: list[str] = []

    # ── Document title ────────────────────────────────────────────────────────
    title = input_file.stem
    md_parts.append(f"# {title}\n")
    md_parts.append(f"> Source: `{input_file.name}` · Sheets: {len(wb.sheetnames)}\n")

    # ── Named ranges ──────────────────────────────────────────────────────────
    named_ranges = []
    try:
        for nr in wb.defined_names:
            if not nr.is_external:
                named_ranges.append((nr.name, str(nr.value)))
    except Exception:
        pass

    if named_ranges:
        md_parts.append("\n## Named Ranges\n")
        headers = ["Name", "Reference"]
        rows = [[n, v] for n, v in named_ranges]
        md_parts.append(_make_md_table(headers, rows))
        md_parts.append("")

    # ── Sheets ────────────────────────────────────────────────────────────────
    for sheet_idx, sheet_name in enumerate(wb.sheetnames, 1):
        ws = wb[sheet_name]
        print(f"[INFO]   Processing sheet {sheet_idx}/{len(wb.sheetnames)}: {sheet_name!r}")

        md_parts.append(f"\n---\n\n## Sheet {sheet_idx}: {sheet_name}\n")

        # Sheet dimensions
        if ws.max_row and ws.max_column:
            md_parts.append(
                f"> Dimensions: {ws.max_row} rows × {ws.max_column} columns"
            )

        # Sheet-level tab color (cosmetic info)
        if ws.sheet_properties.tabColor:
            md_parts.append(f" · Tab color: `#{ws.sheet_properties.tabColor.rgb}`")
        md_parts.append("\n")

        # ── Merged cells report ───────────────────────────────────────────────
        merged_ranges = list(ws.merged_cells.ranges)
        if merged_ranges:
            merge_info = ", ".join(str(m) for m in merged_ranges[:8])
            if len(merged_ranges) > 8:
                merge_info += f", …(+{len(merged_ranges) - 8} more)"
            md_parts.append(f"> Merged cells: {merge_info}\n")

        # ── Build cell grid ───────────────────────────────────────────────────
        # Collect merged ranges: map top-left cell to span info
        merged_map: dict[tuple, str] = {}
        merged_covered: set[tuple] = set()
        for mr in merged_ranges:
            top_left = (mr.min_row, mr.min_col)
            merged_map[top_left] = str(mr)
            for r in range(mr.min_row, mr.max_row + 1):
                for c in range(mr.min_col, mr.max_col + 1):
                    if (r, c) != top_left:
                        merged_covered.add((r, c))

        # Build grid (list of lists of strings)
        grid: list[list[str]] = []
        for row in ws.iter_rows():
            row_data = []
            for cell in row:
                coord = (cell.row, cell.column)
                if coord in merged_covered:
                    row_data.append("")
                else:
                    text = _cell_value(cell)
                    # Append hyperlink if present
                    if cell.hyperlink and cell.hyperlink.target:
                        url = cell.hyperlink.target
                        if text:
                            text = f"[{text}]({url})"
                        else:
                            text = f"<{url}>"
                    # Append merge annotation for top-left cell
                    if coord in merged_map:
                        span = merged_map[coord]
                        text = f"{text} *(merged: {span})*" if text else f"*(merged: {span})*"
                    row_data.append(text)
            grid.append(row_data)

        grid = _trim_grid(grid)

        if not grid:
            md_parts.append("\n> *(Empty sheet)*\n")
        else:
            # Use first row as header if it looks like a header
            # (non-empty cells, and second row has data)
            headers = grid[0] if grid else []
            # Ensure consistent column count
            n_cols = max(len(r) for r in grid) if grid else 0
            headers_padded = (headers + [""] * n_cols)[:n_cols]
            data_rows = grid[1:] if len(grid) > 1 else []

            if not any(headers_padded):
                # No real header — generate Col A, Col B…
                from openpyxl.utils import get_column_letter
                headers_padded = [get_column_letter(i + 1) for i in range(n_cols)]

            md_parts.append("\n")
            md_parts.append(_make_md_table(headers_padded, data_rows))
            md_parts.append("\n")

        # ── Cell comments / notes ─────────────────────────────────────────────
        comments = []
        for row in ws.iter_rows():
            for cell in row:
                if cell.comment:
                    text = cell.comment.text or ""
                    text = text.strip().replace("\n", " ")
                    if text:
                        comments.append((cell.coordinate, text))

        if comments:
            md_parts.append("\n### Cell Comments\n")
            md_parts.append(_make_md_table(
                ["Cell", "Comment"],
                [[coord, note] for coord, note in comments]
            ))
            md_parts.append("\n")

        # ── Embedded images ───────────────────────────────────────────────────
        images = list(ws._images) if hasattr(ws, "_images") else []
        if images:
            img_dir.mkdir(parents=True, exist_ok=True)
            md_parts.append(f"\n### Embedded Images ({len(images)})\n")
            for img_obj in images:
                try:
                    from PIL import Image as PILImage

                    img_data = img_obj._data()
                    pil_img = PILImage.open(io.BytesIO(img_data))

                    # Flatten alpha to white background
                    if pil_img.mode in ("RGBA", "LA", "P"):
                        bg = PILImage.new("RGB", pil_img.size, (255, 255, 255))
                        if pil_img.mode == "P":
                            pil_img = pil_img.convert("RGBA")
                        if pil_img.mode in ("RGBA", "LA"):
                            bg.paste(pil_img, mask=pil_img.split()[-1])
                        else:
                            bg.paste(pil_img)
                        pil_img = bg
                    elif pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")

                    safe_sheet = re.sub(r"[^\w]", "_", sheet_name)
                    img_name = f"{out_file.stem}_{safe_sheet}_{img_count}.jpeg"
                    img_path = img_dir / img_name
                    pil_img.save(img_path, "JPEG", quality=92)

                    size_str = f"{pil_img.size[0]}×{pil_img.size[1]}"
                    md_parts.append(f"![{img_name} ({size_str})]({rel_img_dir}/{img_name})\n")
                    print(f"  [OK] Extracted image: {img_name} ({size_str})")
                    img_count += 1
                except Exception as e:
                    md_parts.append(f"> *(Image extraction failed: {e})*\n")

    # ── Finalize ──────────────────────────────────────────────────────────────
    markdown = "\n".join(md_parts)
    # Collapse excessive blank lines
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(markdown, encoding="utf-8")

    size = out_file.stat().st_size
    print(f"[OK] Saved Markdown to: {out_file} ({_format_size(size)})")
    if img_count:
        print(f"   Extracted {img_count} image(s) → {img_dir}")

    return markdown


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel workbooks to Markdown (for LLM / PPT analysis)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python excel_to_md.py data.xlsx                  # Convert to data.md
  python excel_to_md.py data.xlsx -o report.md     # Specify output path
  python excel_to_md.py report.xlsm                # Macro-enabled workbook

Supported formats: .xlsx  .xlsm  .xltx  .xltm

Features:
  - All sheets exported as separate Markdown sections
  - Merged cells annotated inline
  - Hyperlinks converted to Markdown links
  - Cell comments extracted as a table
  - Embedded images saved to <name>_files/ directory
  - Named ranges listed in a reference table
  - Dates formatted as YYYY-MM-DD
  - Empty rows/columns trimmed automatically
        """,
    )
    parser.add_argument("input", help="Excel file (.xlsx / .xlsm / .xltx / .xltm)")
    parser.add_argument("-o", "--output", help="Output Markdown file path")

    args = parser.parse_args()
    result = convert_excel_to_markdown(args.input, args.output)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
