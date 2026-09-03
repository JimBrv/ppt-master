#!/usr/bin/env python3
"""
PPT Master - SVG Post-processing Tool (Unified Entry Point)

Processes SVG files from svg_output/ and outputs them to svg_final/.
By default, all processing steps are executed. You can also specify
individual steps via arguments.

Usage:
    # Execute all processing steps (recommended)
    python3 scripts/finalize_svg.py <project_directory>

    # Execute only specific steps
    python3 scripts/finalize_svg.py <project_directory> --only embed-icons fix-rounded

Examples:
    python3 scripts/finalize_svg.py projects/my_project
    python3 scripts/finalize_svg.py examples/ppt169_demo --only embed-icons

Processing options:
    embed-icons   - Replace <use data-icon="..."/> with actual icon SVG
    crop-images   - Smart crop images based on preserveAspectRatio="slice"
    fix-aspect    - Fix image aspect ratio (prevent stretching during PPT shape conversion)
    embed-images  - Convert external images to Base64 embedded
    flatten-text  - Convert <tspan> to independent <text> (for special renderers)
    fix-rounded   - Convert <rect rx="..."/> to <path> (for PPT shape conversion)
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Import finalize helpers from the internal package.
sys.path.insert(0, str(Path(__file__).parent))
from svg_finalize.crop_images import process_svg_images as crop_images_in_svg
from svg_finalize.embed_icons import process_svg_file as embed_icons_in_file
from svg_finalize.embed_images import embed_images_in_svg
from svg_finalize.fix_image_aspect import fix_image_aspect_in_svg


def safe_print(text):
    """Safe print that handles Windows terminal encoding issues"""
    try:
        print(text)
    except UnicodeEncodeError:
        text = text.replace('✅', '[OK]').replace('❌', '[ERROR]')
        text = text.replace('📁', '[DIR]').replace('📄', '[FILE]')
        print(text)


def process_flatten_text(svg_file: Path, verbose: bool = False) -> bool:
    """Flatten text in a single SVG file (in-place modification)"""
    try:
        from svg_finalize.flatten_tspan import flatten_text_with_tspans
        from xml.etree import ElementTree as ET

        tree = ET.parse(str(svg_file))
        changed = flatten_text_with_tspans(tree)

        if changed:
            tree.write(str(svg_file), encoding='unicode', xml_declaration=False)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: text flattened")
        return changed
    except Exception as e:
        if verbose:
            safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return False


def process_rounded_rect(svg_file: Path, verbose: bool = False) -> int:
    """Convert rounded rectangles in a single SVG file (in-place modification)"""
    try:
        from svg_finalize.svg_rect_to_path import process_svg

        with open(svg_file, 'r', encoding='utf-8') as f:
            content = f.read()

        processed, count = process_svg(content, verbose=False)

        if count > 0:
            with open(svg_file, 'w', encoding='utf-8') as f:
                f.write(processed)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: {count} rounded rectangle(s)")
        return count
    except Exception as e:
        if verbose:
            safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return 0


def finalize_project(project_dir: Path, options: dict, dry_run: bool = False, quiet: bool = False,
                     pages=None):
    """
    Finalize SVG files in the project

    Args:
        project_dir: Project directory path
        options: Processing options dictionary
        dry_run: Preview only, do not execute
        quiet: Quiet mode, reduce output
    """
    svg_output = project_dir / 'svg_output'
    svg_final = project_dir / 'svg_final'
    icons_dir = Path(__file__).parent.parent / 'templates' / 'icons'

    # Incremental mode: when `pages` is given, only those pages are re-synced
    # and re-processed; every other page already in svg_final/ is left exactly
    # as it is. Turns a one-word fix into a seconds-long run instead of a full
    # rebuild of the whole deck.
    page_filter = set(pages or [])

    # Check if svg_output exists
    if not svg_output.exists():
        safe_print(f"[ERROR] svg_output directory not found: {svg_output}")
        return False

    # Get list of SVG files
    svg_files = list(svg_output.glob('*.svg'))
    if not svg_files:
        safe_print(f"[ERROR] No SVG files in svg_output")
        return False

    if page_filter:
        matched = [f for f in svg_files
                   if f.name in page_filter or f.stem in page_filter]
        unknown = page_filter - {f.name for f in svg_files} - {f.stem for f in svg_files}
        if unknown:
            safe_print(f"[ERROR] No such page(s) in svg_output: {', '.join(sorted(unknown))}")
            return False
        svg_files = matched

    if not quiet:
        print()
        safe_print(f"[DIR] Project: {project_dir.name}")
        safe_print(f"[FILE] {len(svg_files)} SVG file(s)")

    if dry_run:
        safe_print("[PREVIEW] Preview mode, no operations will be performed")
        return True

    # Step 1: Sync svg_output -> svg_final
    # NOTE: on managed / mounted filesystems (e.g. the Cowork device bridge, some
    # network shares) unlink() and rmdir() are denied while ordinary writes still
    # succeed.  A plain rmtree() aborts the entire run there, so fall back to an
    # in-place overwrite sync instead of failing.
    if page_filter:
        # Copy just the requested pages over; leave the rest of svg_final/ alone.
        svg_final.mkdir(parents=True, exist_ok=True)
        for src in svg_files:
            shutil.copy2(src, svg_final / src.name)
        if not quiet:
            safe_print(f"[SYNC] Incremental: {len(svg_files)} page(s) -> svg_final/")
    elif not svg_final.exists():
        shutil.copytree(svg_output, svg_final)
    else:
        try:
            shutil.rmtree(svg_final)
            shutil.copytree(svg_output, svg_final)
        except PermissionError:
            svg_final.mkdir(parents=True, exist_ok=True)
            for src in sorted(svg_output.rglob('*')):
                dst = svg_final / src.relative_to(svg_output)
                if src.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)  # truncating write, no unlink needed
            stale = ({p.name for p in svg_final.glob('*.svg')}
                     - {p.name for p in svg_output.glob('*.svg')})
            if stale:
                safe_print(
                    "[WARN] svg_final/ holds stale page(s) this filesystem will not let "
                    "us delete: " + ", ".join(sorted(stale))
                )
                safe_print("[WARN] Remove them manually or they will be exported too.")

    if not quiet:
        print()

    # Pages each processing step below should touch.
    def target_pages():
        if page_filter:
            return [svg_final / f.name for f in svg_files]
        return sorted(svg_final.glob('*.svg'))

    # Step 2: Embed icons
    if options.get('embed_icons'):
        if not quiet:
            safe_print("[1/6] Embedding icons...")
        icons_count = 0
        for svg_file in target_pages():
            count = embed_icons_in_file(svg_file, icons_dir, dry_run=False, verbose=False)
            icons_count += count
        if not quiet:
            if icons_count > 0:
                safe_print(f"      {icons_count} icon(s) embedded")
            else:
                safe_print("      No icons")

    # Step 3: Smart crop images (based on preserveAspectRatio="slice")
    if options.get('crop_images'):
        if not quiet:
            safe_print("[2/6] Smart cropping images...")
        crop_count = 0
        crop_errors = 0
        for svg_file in target_pages():
            count, errors = crop_images_in_svg(str(svg_file), dry_run=False, verbose=False)
            crop_count += count
            crop_errors += errors
        if not quiet:
            if crop_count > 0:
                safe_print(f"      {crop_count} image(s) cropped")
            else:
                safe_print("      No cropping needed (no images with slice attribute)")

    # Step 4: Fix image aspect ratio (prevent stretching during PPT shape conversion)
    if options.get('fix_aspect'):
        if not quiet:
            safe_print("[3/6] Fixing image aspect ratios...")
        aspect_count = 0
        for svg_file in target_pages():
            count = fix_image_aspect_in_svg(str(svg_file), dry_run=False, verbose=False)
            aspect_count += count
        if not quiet:
            if aspect_count > 0:
                safe_print(f"      {aspect_count} image(s) fixed")
            else:
                safe_print("      No images")

    # Step 5: Embed images
    if options.get('embed_images'):
        if not quiet:
            safe_print("[4/6] Embedding images...")
        images_count = 0
        for svg_file in target_pages():
            count, _ = embed_images_in_svg(str(svg_file), dry_run=False)
            images_count += count
        if not quiet:
            if images_count > 0:
                safe_print(f"      {images_count} image(s) embedded")
            else:
                safe_print("      No images")

    # Step 6: Flatten text
    if options.get('flatten_text'):
        if not quiet:
            safe_print("[5/6] Flattening text...")
        flatten_count = 0
        for svg_file in target_pages():
            if process_flatten_text(svg_file, verbose=False):
                flatten_count += 1
        if not quiet:
            if flatten_count > 0:
                safe_print(f"      {flatten_count} file(s) processed")
            else:
                safe_print("      No processing needed")

    # Step 7: Convert rounded rects to Path
    if options.get('fix_rounded'):
        if not quiet:
            safe_print("[6/6] Converting rounded rects to Path...")
        rounded_count = 0
        for svg_file in target_pages():
            count = process_rounded_rect(svg_file, verbose=False)
            rounded_count += count
        if not quiet:
            if rounded_count > 0:
                safe_print(f"      {rounded_count} rounded rectangle(s) converted")
            else:
                safe_print("      No rounded rectangles")

    # Done
    if not quiet:
        print()
        safe_print("[OK] Done!")
        print()
        print("Next steps:")
        print(f"  python scripts/svg_to_pptx.py \"{project_dir}\" -s final")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='PPT Master - SVG Post-processing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s projects/my_project           # Execute all processing (default)
  %(prog)s projects/my_project --only embed-icons fix-rounded
  %(prog)s projects/my_project -q        # Quiet mode
  %(prog)s projects/my_project --page 07_arch     # Re-process ONE page only

Processing options (for --only):
  embed-icons   Embed icons
  crop-images   Smart crop images (based on preserveAspectRatio)
  fix-aspect    Fix image aspect ratio (prevent stretching during PPT shape conversion)
  embed-images  Embed images
  flatten-text  Flatten text
  fix-rounded   Convert rounded rects to Path
        '''
    )

    parser.add_argument('project_dir', type=Path, help='Project directory path')
    parser.add_argument('--only', nargs='+', metavar='OPTION',
                        choices=['embed-icons', 'crop-images', 'fix-aspect', 'embed-images', 'flatten-text', 'fix-rounded'],
                        help='Execute only specified processing steps (default: all)')
    parser.add_argument('--page', nargs='+', metavar='PAGE', default=None,
                        help='Only re-process these page(s) (filename or stem, e.g. 07_arch '
                             'or 07_arch.svg). Every other page in svg_final/ is left '
                             'untouched -- use after editing a single slide.')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview only, do not execute')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode, reduce output')

    args = parser.parse_args()

    if not args.project_dir.exists():
        safe_print(f"[ERROR] Project directory does not exist: {args.project_dir}")
        sys.exit(1)

    # Determine processing options
    if args.only:
        # Execute only specified steps
        options = {
            'embed_icons': 'embed-icons' in args.only,
            'crop_images': 'crop-images' in args.only,
            'fix_aspect': 'fix-aspect' in args.only,
            'embed_images': 'embed-images' in args.only,
            'flatten_text': 'flatten-text' in args.only,
            'fix_rounded': 'fix-rounded' in args.only,
        }
    else:
        # Execute all by default
        options = {
            'embed_icons': True,
            'crop_images': True,
            'fix_aspect': True,
            'embed_images': True,
            'flatten_text': True,
            'fix_rounded': True,
        }

    success = finalize_project(args.project_dir, options, args.dry_run, args.quiet,
                               pages=args.page)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
