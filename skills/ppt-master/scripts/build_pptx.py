#!/usr/bin/env python3
"""
PPT Master - One-shot post-processing & export.

Runs the three post-processing stages strictly in order, aborting immediately if
any stage fails, then optionally verifies the exported deck:

    1. total_md_split.py   split speaker notes
    2. finalize_svg.py     embed icons/images, flatten text, rects -> paths
    3. svg_to_pptx.py      export ONE editable native-shapes deck from svg_final/
    4. verify_pptx_text.py (with --verify) assert no text wrapped on export

The stages stay serial and fail-fast -- this wrapper exists only so the whole
pipeline is a single invocation instead of three separate round-trips.

Usage:
    python3 scripts/build_pptx.py <project_path>
    python3 scripts/build_pptx.py <project_path> --verify
    python3 scripts/build_pptx.py <project_path> --skip-notes -o deck.pptx
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run(label: str, argv: list) -> None:
    print(f"\n{'=' * 60}\n[STAGE] {label}\n{'=' * 60}")
    r = subprocess.run([sys.executable, *argv])
    if r.returncode != 0:
        print(f"\n[ABORT] '{label}' failed (exit {r.returncode}); later stages skipped.")
        sys.exit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project_path', type=Path)
    ap.add_argument('-o', '--output', default=None, help='Explicit output .pptx path')
    ap.add_argument('--skip-notes', action='store_true',
                    help='Skip stage 1 (notes/total.md unchanged since last build)')
    ap.add_argument('--with-svg-ref', action='store_true',
                    help='Also emit the _svg.pptx reference twin')
    ap.add_argument('--verify', action='store_true',
                    help='After export, check no text run wrapped (needs soffice + pdftotext)')
    args = ap.parse_args()

    proj = str(args.project_path)

    if not args.skip_notes:
        run('1/3  split speaker notes', [str(SCRIPTS / 'total_md_split.py'), proj])
    else:
        print('[SKIP] stage 1 (--skip-notes)')

    run('2/3  finalize SVG', [str(SCRIPTS / 'finalize_svg.py'), proj])

    export = [str(SCRIPTS / 'svg_to_pptx.py'), proj, '-s', 'final']
    if args.output:
        export += ['-o', args.output]
    if args.with_svg_ref:
        export += ['--with-svg-ref']
    run('3/3  export PPTX', export)

    if args.verify:
        run('4/4  verify exported text', [str(SCRIPTS / 'verify_pptx_text.py'), proj])

    print('\n[DONE] build complete.')


if __name__ == '__main__':
    main()
