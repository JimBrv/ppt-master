#!/usr/bin/env python3
"""
PPT Master - One-shot post-processing & export.

Runs the three post-processing stages strictly in order, aborting immediately if
any stage fails, then optionally verifies the exported deck:

    0. preflight           layout_plan_check.py --output: design_spec.md exists at
                           the project root, the plan passes, and every page in
                           svg_output/ is the planned page filled from the planned
                           layout (fails the build); then free_page_check.py: every
                           free-design page keeps the template frame, and no text
                           overflows its box, overlaps or leaves the canvas (fails
                           the build); stray files and a missing or summary-sized
                           source are reported (warnings)
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
    python3 scripts/build_pptx.py <project_path> --no-plan-check   # legacy projects planned before the layout fields existed
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent.parent


def run(label: str, argv: list) -> None:
    print(f"\n{'=' * 60}\n[STAGE] {label}\n{'=' * 60}")
    r = subprocess.run([sys.executable, *argv])
    if r.returncode != 0:
        print(f"\n[ABORT] '{label}' failed (exit {r.returncode}); later stages skipped.")
        sys.exit(r.returncode)


SOURCE_MIN_CHARS = 3000


def hygiene(proj: Path) -> None:
    """Warnings only: leftovers and sources that do not look like the real text."""
    warn = []
    stray = sorted(str(f.relative_to(proj)) for f in proj.rglob('*.json')
                   if f.relative_to(proj).parts[0] not in ('templates',))
    if stray:
        warn.append(f'{len(stray)} .json file(s) left in the project ({", ".join(stray[:4])}{" …" if len(stray) > 4 else ""}); '
                    'values files belong in tmp/ and are deleted when the pages are done')
    if (proj / 'tmp').exists():
        warn.append('tmp/ still exists; delete it once the pages are written')
    src = proj / 'sources'
    files = [f for f in src.rglob('*') if f.is_file() and not f.name.startswith('.')] if src.exists() else []
    if not files:
        warn.append('sources/ is empty; keep the converted source text in the project (Step 1)')
    else:
        md = sum(len(f.read_text(encoding='utf-8', errors='ignore')) for f in files if f.suffix == '.md')
        if md and md < SOURCE_MIN_CHARS and not any(f.suffix != '.md' for f in files):
            warn.append(f'sources/ holds only {md} characters of Markdown; if the source is longer, save the '
                        'converted full text (pdf_to_md / doc_to_md / web_to_md), not a summary')
    warn += environment_changes()
    for w in warn:
        print(f'[WARN] {w}')


def environment_changes() -> list:
    """The skill and its Python environment are not the project's to change."""
    out = []
    try:
        r = subprocess.run(['git', '-C', str(REPO), 'status', '--porcelain', '--', 'skills/ppt-master'],
                           capture_output=True, text=True, timeout=20)
        changed = [line[3:] for line in r.stdout.splitlines() if line.strip()] if r.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        changed = []
    if changed:
        out.append(f'{len(changed)} file(s) under skills/ppt-master changed locally ({", ".join(changed[:3])}'
                   f'{" …" if len(changed) > 3 else ""}); a run must not edit the skill — revert them, or report '
                   'the problem that made the edit seem necessary')
    cfg = REPO / '.venv' / 'pyvenv.cfg'
    py = REPO / '.venv' / 'bin' / 'python'
    if cfg.exists() and py.exists():
        home = next((line.split('=', 1)[1].strip() for line in cfg.read_text().splitlines()
                     if line.startswith('home')), '')
        if home and not os.path.realpath(py).startswith(os.path.realpath(home)):
            out.append(f'.venv/bin/python points to {os.path.realpath(py)}, not the environment\'s own Python '
                       f'({home}); do not repoint the venv — run "uv sync" to repair it')
    return out


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
    ap.add_argument('--no-plan-check', action='store_true',
                    help='Skip the design-spec preflight (only for projects planned before it existed)')
    args = ap.parse_args()

    proj = str(args.project_path)

    hygiene(args.project_path)
    if args.no_plan_check:
        print('[SKIP] stage 0 (--no-plan-check): pages are NOT checked against design_spec.md')
    else:
        run('0/3  preflight: pages match design_spec.md',
            [str(SCRIPTS / 'layout_plan_check.py'), proj, '--output'])
        run('0/3  preflight: free-design pages', [str(SCRIPTS / 'free_page_check.py'), proj])

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
