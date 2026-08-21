#!/usr/bin/env python3
"""
PPT Master - Exported-deck text verifier.

Renders the exported PPTX to PDF (LibreOffice) and asserts that every <text>
string in svg_final/ survives into the deck as one contiguous run.  Catches the
class of defect that screenshots are expensive to spot: a text box whose
estimated width was too small, letting the renderer wrap a line mid-sentence.

Usage:
    python3 scripts/verify_pptx_text.py <project_path> [-p deck.pptx]

Exit code 0 = clean, 1 = suspect runs found (listed on stdout).
Requires: soffice + pdftotext on PATH.
"""
import argparse
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

MIN_LEN = 4  # ignore very short strings; too noisy to match reliably


def flatten(s: str) -> str:
    return re.sub(r'\s+', '', s)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project_path', type=Path)
    ap.add_argument('-p', '--pptx', type=Path, default=None,
                    help='Deck to check (default: newest .pptx in the project, ignoring _svg)')
    ap.add_argument('-s', '--source', default='final',
                    help='SVG dir to compare against: final (default) or output')
    args = ap.parse_args()

    proj = args.project_path
    svg_dir = proj / f'svg_{args.source}'
    svgs = sorted(svg_dir.glob('*.svg'))
    if not svgs:
        print(f'[ERROR] no SVGs in {svg_dir}')
        return 1

    deck = args.pptx
    if deck is None:
        cands = [p for p in proj.glob('*.pptx') if not p.stem.endswith('_svg')]
        if not cands:
            print(f'[ERROR] no .pptx found in {proj}')
            return 1
        deck = max(cands, key=lambda p: p.stat().st_mtime)

    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                            '--outdir', td, str(deck)],
                           capture_output=True, text=True, timeout=180)
        pdfs = list(Path(td).glob('*.pdf'))
        if not pdfs:
            print(f'[ERROR] LibreOffice produced no PDF\n{r.stdout}\n{r.stderr}')
            return 1
        txt = Path(td) / 'deck.txt'
        subprocess.run(['pdftotext', '-layout', str(pdfs[0]), str(txt)],
                       capture_output=True, timeout=120)
        pages = [flatten(p) for p in txt.read_text(encoding='utf-8').split('\f')]

    print(f'[SCAN] {deck.name} vs {len(svgs)} page(s) in {svg_dir.name}/')
    total = bad = 0
    for i, svg in enumerate(svgs):
        page = pages[i] if i < len(pages) else ''
        for node in ET.parse(svg).getroot().iter():
            if node.tag.split('}')[-1] != 'text':
                continue
            s = ''.join(node.itertext()).strip()
            if len(s) < MIN_LEN:
                continue
            total += 1
            if flatten(s) not in page:
                bad += 1
                print(f'  [WRAP?] {svg.name}: {s[:60]!r}')

    print(f'\n[SUMMARY] {total} text run(s) checked, {bad} suspect')
    if bad:
        print('  Likely cause: estimated text-box width too small.')
        print('  Tune TEXT_WIDTH_SAFETY in scripts/svg_to_shapes.py, or shorten the string.')
        return 1
    print('[OK] every text run survived export intact')
    return 0


if __name__ == '__main__':
    sys.exit(main())
