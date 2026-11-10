#!/usr/bin/env python3
"""
QAX (奇安信) content layout definitions.

Source of truth for templates/layouts/奇安信/content/. Edit a layout here,
then regenerate the SVGs and layouts.json:

    uv run python3 skills/ppt-master/templates/layouts/奇安信/content_src/build_layouts.py

Verify the library afterwards:

    uv run python3 skills/ppt-master/scripts/layout_stress.py skills/ppt-master/templates/layouts/奇安信

Geometry was taken from a reference QAX deck with scripts/pptx_inspect.py;
the source page of each layout is recorded in its metadata.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))
from layout_kit import Layout, Shell, grad, write_library  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / 'content'
FONT = 'Microsoft YaHei, SimHei, sans-serif'
INK, BLUE, DEEP, TITLE = '#0F1423', '#2C7FEF', '#1E6BEE', '#003893'
HALO, LINE, TINT = '#D9E8FC', '#D4E5FC', '#F4F7FB'
GREEN, TEAL, SKY, LIME = '#28A963', '#30C0B4', '#42AFF0', '#75BD42'

SHELL = Shell(
    name='QAX',
    font=FONT,
    images=[('../images/qax_bg_content.jpg', '0', '0', '1280', '720'),
            ('../images/qax_logo.png', '992.3', '0', '275.2', '110.4')],
    title=(58, 88, 40, TITLE, 22),
    page_num=(1240, 712, 14, '#9CAEC3'),
    image_slot_fill=TINT,
    ink=INK,
)

USAGE = '在 design_spec 的 Layout 字段写版式 ID。slots 的数字是该槽位的最大中文字符数，英文按 0.55 个中文宽度估算；{n} 表示序号。'


def stage_matrix_evidence():
    l = Layout('stage_matrix_evidence', SHELL)
    rows = [(148, 138), (300, 138), (452, 138)]
    for n, (y, h) in enumerate(rows, 1):
        l.note(f'stage {n}')
        l.rr(63, y, 493, h, 12, BLUE, .12)
        l.rr(33, y + 39, 60, 60, 10, BLUE)
        l.t(63, y + 76, f'STAGE{n}_LABEL', 20, 50, '#FFFFFF', True, 'middle')
        for m, (cx, cy) in enumerate([(110, y + 22), (331, y + 22), (110, y + 76), (331, y + 76)], 1):
            l.rr(cx, cy, 209, 41, 6, '#FFFFFF', box=f'STAGE{n}_CHIP{m}')
            l.t(cx + 10, cy + 26, f'STAGE{n}_CHIP{m}', 15, 189)
    for y in (272, 424, 566):
        l.poly(f'39,{y} 57,{y} 57,{y+22} 64,{y+22} 48,{y+43} 32,{y+22} 39,{y+22}', HALO)
    l.note('final stage: single wide chip')
    l.rr(63, 604, 493, 91, 12, BLUE, .12)
    l.rr(33, 619, 60, 60, 10, BLUE)
    l.t(63, 656, 'STAGE4_LABEL', 20, 50, '#FFFFFF', True, 'middle')
    l.rr(110, 617, 431, 62, 6, '#FFFFFF')
    l.t(122, 643, 'STAGE4_L1', 15, 407); l.t(122, 666, 'STAGE4_L2', 15, 407)
    l.note('evidence panel')
    l.rr(602, 148, 629, 376, 12, '#FFFFFF', None, LINE, 1)
    l.img(614, 161, 607, 317, 'SCREENSHOT')
    l.t(616, 507, 'CAPTION', 14, 590, '#64748B')
    l.note('key results callout')
    l.rr(602, 554, 629, 140, 12, BLUE)
    l.t(640, 618, 'CALLOUT_LABEL_L1', 20, 44, '#FFFFFF', True, 'middle')
    l.t(640, 646, 'CALLOUT_LABEL_L2', 20, 44, '#FFFFFF', True, 'middle')
    l.rr(680, 576, 4, 40, 2, '#FFFFFF'); l.rr(680, 640, 4, 40, 2, '#FFFFFF')
    l.t(696, 590, 'RESULT1_TITLE', 18, 520, '#FFFFFF', True); l.t(696, 613, 'RESULT1_BODY', 15, 520, '#FFFFFF')
    l.t(696, 654, 'RESULT2_TITLE', 18, 520, '#FFFFFF', True); l.t(696, 677, 'RESULT2_BODY', 15, 520, '#FFFFFF')
    return l

def three_pillars():
    l = Layout('three_pillars', SHELL)
    l.defs = grad('qaxHead', '#1773ED', '#6C9CE5')
    for n, x in enumerate((40, 447, 854), 1):
        l.note(f'column {n}')
        l.rr(x, 136, 386, 530, 14, '#FFFFFF', .85, LINE, 1)
        l.rr(x + 12, 148, 362, 62, 10, 'url(#qaxHead)')
        l.t(x + 193, 189, f'COL{n}_TITLE', 26, 320, '#FFFFFF', True, 'middle')
        for m in (1, 2, 3):
            y = 222 + (m - 1) * 146
            l.rr(x + 12, y, 362, 134, 10, '#0052CC', .07)
            l.icon(x + 26, y + 12, 28, f'COL{n}_CARD{m}_ICON', DEEP)
            l.t(x + 64, y + 34, f'COL{n}_CARD{m}_TITLE', 20, 290, DEEP, True)
            for k in (1, 2, 3):
                l.t(x + 28, y + 40 + k * 26, f'COL{n}_CARD{m}_L{k}', 16, 330)
    l.t(640, 698, 'CONCLUSION', 22, 1100, '#3182EF', True, 'middle')
    return l

def chevron_stages():
    l = Layout('chevron_stages', SHELL)
    def bar(pts, fill, slot, cx):
        l.poly(pts, fill); l.t(cx, 184, slot, 21, 240, '#FFFFFF', True, 'middle')
    bar('0,150 313,150 335,176 313,202 0,202', '#EE822F', 'STEP0_LABEL', 160)
    for n, (x, col) in enumerate(((338, LIME), (652, TEAL), (967, SKY)), 1):
        bar(f'{x},150 {x+290},150 {x+312},176 {x+290},202 {x},202 {x+22},176', col, f'STEP{n}_LABEL', x + 156)
    l.path('M0,524 Q0,496 28,496 L1252,496 Q1280,496 1280,524 L1280,720 L0,720 Z', DEEP)
    for n, (x, col) in enumerate(((71, DEEP), (462, GREEN), (853, SKY)), 1):
        cx = x + 179
        l.note(f'column {n}')
        l.rr(x, 226, 358, 246, 16, '#FFFFFF', .9, LINE, 1)
        l.t(x + 28, 290, f'COL{n}_NAME', 28, 310, INK, True)
        l.t(x + 28, 392, f'COL{n}_KEYWORD', 48, 310, col, True, None, True)
        l.icon(x + 288, 410, 48, f'COL{n}_ICON', col)
        l.t(cx, 548, f'COL{n}_TITLE', 22, 340, '#FFFFFF', True, 'middle')
        for k in (1, 2, 3):
            l.t(cx, 560 + k * 27, f'COL{n}_L{k}', 16, 330, '#FFFFFF', False, 'middle')
    return l

def stair_steps():
    l = Layout('stair_steps', SHELL)
    l.poly('0,470 420,452 830,330 1280,205 1280,130 830,250 420,400 0,438', '#7995D8', .22)
    l.t(58, 160, 'SUBTITLE', 24, 790, '#4874CB', True)
    tops = (295, 295, 271, 243, 198, 141)
    cols = ('#62CB78', '#62CB78', TEAL, '#4991F1', '#4381DD', DEEP)
    for n, (x, top, col) in enumerate(zip((35, 232, 428, 624, 821, 1019), tops, cols), 1):
        cx = x + 90
        l.note(f'step {n}')
        l.rr(x, top, 181, 400, 12, '#FFFFFF', None, LINE, 1)
        l.path(f'M{x},{top+40} L{x},{top+12} Q{x},{top} {x+12},{top} L{x+169},{top} Q{x+181},{top} {x+181},{top+12} L{x+181},{top+40} Z', BLUE)
        l.t(cx, top + 27, f'S{n}_NAME', 16, 165, '#FFFFFF', True, 'middle')
        l.c(cx, top + 112, 58, col, .2); l.c(cx, top + 112, 40, col)
        l.t(cx, top + 121, f'S{n}_GRADE', 24, 60, '#FFFFFF', True, 'middle')
        l.t(cx, top + 200, f'S{n}_HEAD1', 16, 163, DEEP, True, 'middle')
        for k in (1, 2):
            l.t(cx, top + 200 + k * 23, f'S{n}_A{k}', 15, 163, INK, False, 'middle')
        l.t(cx, top + 276, f'S{n}_HEAD2', 16, 163, DEEP, True, 'middle')
        for k in (1, 2, 3):
            l.t(cx, top + 276 + k * 23, f'S{n}_B{k}', 15, 163, INK, False, 'middle')
    l.t(1240, 620, 'AXIS_NOTE', 16, 195, '#4874CB', False, 'end')
    return l

def layered_rows():
    l = Layout('layered_rows', SHELL)
    l.rr(571, 140, 8, 464, 4, LINE)
    for n, (y, col) in enumerate(zip((140, 256, 372, 488), ('#7995D8', '#4381DD', '#44B4CF', '#62CB78')), 1):
        mid = y + 52
        l.note(f'layer {n}')
        l.rr(150, y, 998, 104, 8, col, .18)
        l.rr(1143, y, 5, 104, 2, col)
        l.c(575, mid, 30, col)
        l.icon(559, mid - 16, 32, f'R{n}_ICON', '#FFFFFF')
        l.t(176, mid + 9, f'R{n}_LABEL', 24, 360, INK, True)
        l.t(636, mid - 6, f'R{n}_L1', 17, 490); l.t(636, mid + 20, f'R{n}_L2', 17, 490)
    l.rr(186, 620, 915, 56, 10, '#FFFFFF', .9, LINE, 1)
    l.t(643, 656, 'CONCLUSION', 21, 860, '#3182EF', True, 'middle')
    return l

def hub_numbered_rows():
    l = Layout('hub_numbered_rows', SHELL)
    l.c(238, 440, 123, DEEP, .12); l.c(238, 440, 80, DEEP)
    l.icon(205, 407, 66, 'HUB_ICON', '#FFFFFF')
    for n, (x, y) in enumerate(((20, 300), (120, 222), (262, 246), (20, 540), (258, 585)), 1):
        l.rr(x, y, 110, 52, 12, HALO, None, '#D1E6FF', 1, box=f'CALLOUT{n}')
        l.t(x + 55, y + 33, f'CALLOUT{n}', 18, 96, DEEP, True, 'middle')
    l.rr(398, 140, 842, 540, 16, '#FFFFFF', .9, LINE, 1)
    l.t(819, 200, 'HEADING', 27, 780, DEEP, True, 'middle')
    for n, (y, col) in enumerate(zip((232, 372, 512), (DEEP, GREEN, SKY)), 1):
        mid = y + 56
        l.note(f'row {n}')
        l.rr(505, y, 705, 112, 14, TINT, None, LINE, 1)
        l.c(500, mid, 42, '#FFFFFF'); l.c(500, mid, 31, col)
        l.t(500, mid + 10, f'R{n}_NUM', 28, 30, '#FFFFFF', True, 'middle')
        l.t(556, mid + 8, f'R{n}_TITLE', 21, 180, INK, True)
        l.t(748, mid - 4, f'R{n}_L1', 16, 226); l.t(748, mid + 20, f'R{n}_L2', 16, 226)
        l.rr(985, mid - 23, 205, 46, 10, col, .15)
        l.t(1087, mid + 6, f'R{n}_TAG', 16, 186, col, True, 'middle')
    return l

def image_stack_pills():
    l = Layout('image_stack_pills', SHELL)
    l.c(232, 427, 198, HALO, .7); l.c(232, 427, 166, '#FFFFFF')
    l.img(80, 275, 305, 305, 'HERO')
    xs = (379, 417, 454, 471, 471, 454, 417, 379)
    cols = (DEEP, TEAL, LIME, DEEP, TEAL, LIME, DEEP, TEAL)
    for n, (x, col) in enumerate(zip(xs, cols), 1):
        y = 150 + (n - 1) * 69
        l.note(f'pill {n}')
        l.rr(x, y, 1240 - x, 45, 22, col, .14)
        l.t(x + 22, y + 30, f'P{n}_TAG', 20, 130, col, True)
        l.t(x + 165, y + 29, f'P{n}_BODY', 16, 590, '#333333')
    return l

def loop_nodes():
    l = Layout('loop_nodes', SHELL)
    for d in ('M300,235 Q430,170 560,210', 'M720,210 Q850,170 975,235', 'M1085,440 Q1085,545 940,530',
              'M795,535 Q640,625 495,535', 'M350,530 Q190,545 180,440'):
        l.path(d, 'none', '#D1E6FF', 16)
    for n, (cx, cy) in enumerate(((196, 275), (639, 230), (1076, 275), (867, 493), (422, 494)), 1):
        l.note(f'node {n}')
        l.c(cx, cy, 47, '#4991F1')
        l.icon(cx - 22, cy - 22, 44, f'N{n}_ICON', '#FFFFFF')
        l.t(cx, cy + 86, f'N{n}_TITLE', 24, 240, '#0860CD', True, 'middle')
        l.t(cx, cy + 118, f'N{n}_L1', 18, 250, INK, False, 'middle')
        l.t(cx, cy + 144, f'N{n}_L2', 18, 250, INK, False, 'middle')
    return l


PURPLE_G = '    <linearGradient id="qaxArrow" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#4874CB"/><stop offset="100%" stop-color="#E54C5E"/></linearGradient>'


def architecture_radial():
    l = Layout('architecture_radial', SHELL)
    l.defs = grad('qaxNodeA', '#1773ED', '#4991F1') + '\n' + grad('qaxNodeB', '#1773ED', '#4874CB')
    l.note('source column')
    l.t(110, 176, 'SRC_TITLE_L1', 18, 130, '#3057A5', True, 'middle')
    l.t(110, 200, 'SRC_TITLE_L2', 18, 130, '#3057A5', True, 'middle')
    l.rr(42, 221, 134, 290, 20, '#E0ECFD')
    for n, y0 in enumerate((258, 342, 426), 1):
        for k in (1, 2, 3):
            l.t(109, y0 + (k - 1) * 22, f'SRC{n}_L{k}', 16, 120, INK, True, 'middle')
    l.raw('<path d="M202,156 L202,576" fill="none" stroke="#2C7FEF" stroke-width="3" stroke-dasharray="4,8"/>')
    l.note('wedges converging on the hub')
    l.path('M355,191 L688,373 L367,570 C300,450 296,310 355,191 Z', '#1773ED', op='0.12')
    l.path('M1013,195 L680,373 L1024,531 C1076,420 1074,300 1013,195 Z', '#4874CB', op='0.12')
    l.t(320, 186, 'INPUT_LABEL', 18, 200, '#1773ED', True, 'middle')
    rows = ((259, 236, 397, 280), (226, 344, 364, 384), (257, 451, 395, 482))
    for n, (px, py, cx, cy) in enumerate(rows, 1):
        l.note(f'input {n}')
        l.rr(px - 15, py, 126, 73, 36, '#FFFFFF', None, '#0070C0', 1)
        l.t(px + 35, py + 31, f'IN{n}_P1', 14, 100, '#1773ED', True, 'middle')
        l.t(px + 35, py + 51, f'IN{n}_P2', 14, 100, '#1773ED', True, 'middle')
        l.c(cx, cy, 43, 'url(#qaxNodeA)')
        l.t(cx, cy - 3, f'IN{n}_C1', 14, 80, '#FFFFFF', True, 'middle')
        l.t(cx, cy + 17, f'IN{n}_C2', 14, 80, '#FFFFFF', True, 'middle')
        tx = cx + 46
        l.poly(f'{tx},{cy-14} {tx+26},{cy} {tx},{cy+14}', '#2C7FEF')
    l.note('hub')
    l.t(681, 178, 'HUB_HEADER', 24, 400, '#2C7FEF', True, 'middle')
    l.c(681, 374, 181, '#FFFFFF')
    l.ring(681, 374, 189, LINE, 1.5)
    for n, (cx, cy) in enumerate(((681, 266), (790, 375), (681, 484), (572, 375)), 1):
        l.c(cx, cy, 40, 'url(#qaxNodeB)')
        l.t(cx, cy - 3, f'NODE{n}_L1', 16, 68, '#FFFFFF', True, 'middle')
        l.t(cx, cy + 19, f'NODE{n}_L2', 16, 68, '#FFFFFF', True, 'middle')
    l.t(681, 368, 'CENTER_L1', 19, 136, '#1773ED', True, 'middle')
    l.t(681, 394, 'CENTER_L2', 19, 136, '#1773ED', True, 'middle')
    l.t(681, 215, 'CAP_TOP', 14, 200, '#64748B', False, 'middle')
    l.t(681, 545, 'CAP_BOTTOM', 14, 240, '#64748B', False, 'middle')
    l.t(790, 432, 'CAP_RIGHT_L1', 14, 130, '#64748B', False, 'middle')
    l.t(790, 452, 'CAP_RIGHT_L2', 14, 130, '#64748B', False, 'middle')
    l.t(572, 432, 'CAP_LEFT_L1', 14, 130, '#64748B', False, 'middle')
    l.t(572, 452, 'CAP_LEFT_L2', 14, 130, '#64748B', False, 'middle')
    l.note('outputs')
    l.t(961, 246, 'OUT_LABEL', 18, 150, '#4874CB', True, 'middle')
    for n, (x, y) in enumerate(((904, 268), (927, 344), (904, 420)), 1):
        l.rr(x, y, 115, 39, 8, '#FFFFFF', None, '#4874CB', 1)
        l.t(x + 57, y + 26, f'OUT{n}', 16, 100, '#4874CB', True, 'middle')
        l.poly(f'{x+117},{y+4} {x+143},{y+19} {x+117},{y+35}', '#4874CB')
    l.rr(1088, 221, 150, 290, 16, '#4874CB')
    for n, y0 in enumerate((262, 350, 438), 1):
        l.t(1163, y0, f'OUTP{n}_L1', 15, 134, '#FFFFFF', True, 'middle')
        l.t(1163, y0 + 22, f'OUTP{n}_L2', 15, 134, '#FFFFFF', True, 'middle')
    l.note('three notes')
    for n, x in enumerate((37, 448, 860), 1):
        l.rr(x, 591, 378, 100, 12, '#FFFFFF', .85, '#D4E5FC', 1)
        l.t(x + 16, 623, f'NOTE{n}_TITLE', 16, 350, INK, True)
        l.t(x + 16, 650, f'NOTE{n}_L1', 15, 350, '#333333')
        l.t(x + 16, 674, f'NOTE{n}_L2', 15, 350, '#333333')
    return l

def probe_tier_channels():
    l = Layout('probe_tier_channels', SHELL)
    l.path('M0,179 L350,179 C465,179 553,272 553,386 C553,500 465,593 350,593 L0,593 Z', BLUE, op='0.08')
    l.path('M0,231 L303,231 C398,231 474,300 474,386 C474,472 398,541 303,541 L0,541 Z', BLUE)
    l.t(29, 326, 'HUB_TITLE', 30, 390, '#FFFFFF', True)
    l.t(30, 360, 'HUB_L1', 14, 380, '#FFFFFF')
    l.t(30, 382, 'HUB_L2', 14, 380, '#FFFFFF')
    l.path('M28,397 L395,397', 'none', '#FFFFFF', 1)
    l.c(66, 451, 38, '#FFFFFF')
    l.icon(50, 435, 32, 'HUB_ICON', BLUE)
    l.t(118, 442, 'HUB_TAG_L1', 20, 280, '#FFFFFF', True)
    l.t(118, 472, 'HUB_TAG_L2', 20, 280, '#FFFFFF', True)
    rows = (('TOP', 505, 218, 587, 181, '#4991F1', 960, 180, 540, 250),
            ('MID', 570, 390, 652, 352, TEAL, 975, 175, 490, 200),
            ('BOT', 505, 561, 587, 524, '#41ACF5', 960, 180, 540, 250))
    for p, cx, cy, px, py, col, hx, hw, lw, nw in rows:
        l.note(f'channel {p}')
        l.c(cx, cy, 47, '#FFFFFF')
        l.ring(cx, cy, 47, LINE, 1)
        l.icon(cx - 18, cy - 18, 36, f'{p}_ICON', BLUE)
        l.rr(px, py, 103, 40, 10, col)
        l.t(px + 51, py + 28, f'{p}_PILL', 20, 90, '#FFFFFF', True, 'middle')
        l.t(px + 113, py + 29, f'{p}_NAME', 22, nw, INK, True)
        l.t(hx, py + 27, f'{p}_HINT', 14, hw, col)
        l.t(px, py + 72, f'{p}_L1', 16, lw)
        l.t(px, py + 100, f'{p}_L2', 16, lw)
        l.t(1213, py + 22, f'{p}_NOTE_L1', 15, 112, col, True, 'middle')
        l.t(1213, py + 46, f'{p}_NOTE_L2', 15, 112, col, True, 'middle')
    l.t(636, 680, 'CONCLUSION', 22, 1100, '#3182EF', True, 'middle')
    return l

def three_track_checklist():
    l = Layout('three_track_checklist', SHELL)
    l.path('M69,224 L1209,224', 'none', LINE, 2)
    for n, (x, col) in enumerate(((69, TEAL), (453, '#F2BA02'), (837, '#4991F1')), 1):
        cx = x + 187
        l.note(f'track {n}')
        l.c(cx, 225, 42, '#FFFFFF')
        l.c(cx, 225, 35, col)
        l.t(cx, 233, f'T{n}_BADGE', 22, 66, '#FFFFFF', True, 'middle')
        l.rr(x, 275, 375, 52, 6, col, .18)
        l.t(cx, 309, f'T{n}_HEAD', 22, 340, '#000000', True, 'middle')
        for m in range(1, 6):
            y = 355 + (m - 1) * 43.5
            l.rr(x + 27, y, 7, 38, 3, col, .8, box=f'T{n}_ITEM{m}')
            l.t(x + 49, y + 26, f'T{n}_ITEM{m}', 16, 312, INK, True)
    l.t(640, 664, 'CONCLUSION', 22, 1100, '#3182EF', True, 'middle')
    return l

def tier_chip_pyramid():
    l = Layout('tier_chip_pyramid', SHELL)
    l.rr(0, 600, 1280, 120, 0, DEEP, .7)
    tiers = (('TOP', 182, 124, '#30BE71', '#28A963', 2, 7, 110, 120, 196, 53),
             ('MID', 325, 124, DEEP, '#4874CB', 2, 4, 150, 165, 341, 51),
             ('BOT', 468, 172, '#F2BA02', '#EE822F', 3, 5, 118, 128, 485, 52))
    for p, y, h, col, tc, rows, cols, w, step, y0, dy in tiers:
        l.note(f'tier {p} band')
        l.rr(70, y, 866, h, 0, col)
    l.poly('898,282 971,155 1045,282', '#30BE71', .35)
    l.poly('870,325 1062,325 1131,452 801,452', DEEP, .35)
    l.poly('772,496 1152,496 1218,640 704,640', '#EE822F', .35)
    l.icon(949, 200, 46, 'TOP_ICON', '#FFFFFF')
    l.icon(947, 335, 48, 'MID_ICON', '#FFFFFF')
    l.icon(944, 512, 56, 'BOT_ICON', '#FFFFFF')
    for p, y, h, col, tc, rows, cols, w, step, y0, dy in tiers:
        n = 0
        for r in range(rows):
            for c in range(cols):
                n += 1
                x, yy = 90 + c * step, y0 + r * dy
                l.rr(x, yy, w, 38, 6, '#FFFFFF', .88, box=f'{p}_C{n}')
                l.t(x + w // 2, yy + 25, f'{p}_C{n}', 14 if p != 'MID' else 15, w - 10, tc, True, 'middle')
    for p, y, col in (('TOP', 255, '#30BE71'), ('MID', 390, DEEP), ('BOT', 585, '#EE822F')):
        l.rr(906, y, 133, 47, 20, col, .85)
        l.t(972, y + 32, f'{p}_LABEL', 24, 120, '#FFFFFF', True, 'middle')
    return l

def chain_core_grid():
    l = Layout('chain_core_grid', SHELL)
    l.defs = grad('qaxCore', '#4874CB', '#1773ED')
    l.note('racetrack ring behind the core band')
    l.raw('<rect x="205" y="312" width="845" height="202" rx="101" fill="none" stroke="#1773ED" stroke-width="20" stroke-opacity="0.3"/>')
    for n, (x, y) in enumerate(((107, 224), (325, 182), (542, 182), (760, 182), (978, 224)), 1):
        cx = x + 94
        l.note(f'chain {n}')
        l.t(cx, y + 34, f'CH{n}_TITLE', 21, 180, '#1773ED', True, 'middle')
        l.t(cx, y + 70, f'CH{n}_BODY', 15, 210, INK, False, 'middle')
    l.rr(247, 342, 761, 142, 24, '#FFFFFF')
    for n, x in enumerate((278, 404, 751, 877), 1):
        l.rr(x, 363, 100, 100, 30, 'url(#qaxCore)')
        l.t(x + 50, 420, f'CORE{n}', 20, 92, '#FFFFFF', True, 'middle')
    l.t(627, 424, 'CENTER', 30, 235, '#1773ED', True, 'middle')
    for n, (x, y) in enumerate(((157, 567), (663, 567), (157, 625), (663, 625)), 1):
        l.rr(x, y, 464, 46, 12, '#FFFFFF', None, '#6C9CE5', 1.5)
        l.t(x + 16, y + 29, f'G{n}_LABEL', 15, 100, '#4874CB', True)
        l.t(x + 448, y + 29, f'G{n}_VALUE', 15, 320, INK, False, 'end')
    return l

def funnel_layers():
    l = Layout('funnel_layers', SHELL)
    rows = ((195, 90, '#7995D8'), (295, 94, '#4381DD'), (399, 87, '#44B4CF'), (497, 79, '#62CB78'))
    for n, (y, h, col) in enumerate(rows, 1):
        l.note(f'layer {n} band')
        l.rr(171, y, 977, h, 4, col, .16)
        l.rr(1143, y, 5, h, 2, col)
    cx = 589
    bands = ((473, 106, 77, 56, '#62CB78'), (378, 107, 109, 79, '#44B4CF'), (287, 104, 152, 110, '#4381DD'), (194, 106, 210, 151, '#7995D8'))
    l.note('funnel, drawn bottom-up so upper layers overlap lower ones')
    for y, h, wt, wb, col in bands:
        l.path(f'M{cx-wt},{y} L{cx+wt},{y} L{cx+wb},{y+h-12} Q{cx},{y+h+8} {cx-wb},{y+h-12} Z', col)
    l.raw(f'<ellipse cx="{cx}" cy="194" rx="209" ry="15" fill="#BCC8E3"/>')
    for n, ((y, h, col), my) in enumerate(zip(rows, (256, 348, 440, 533)), 1):
        l.ring(cx, my, 26, '#FFFFFF', 1.5)
        l.icon(cx - 14, my - 14, 28, f'L{n}_ICON', '#FFFFFF')
        mid = y + h // 2
        l.t(181, mid + 8, f'L{n}_LABEL', 20, 205, INK, True)
        l.t(1135, mid - 5, f'L{n}_D1', 16, 322, INK, False, 'end')
        l.t(1135, mid + 19, f'L{n}_D2', 16, 322, INK, False, 'end')
    l.t(643, 664, 'CONCLUSION', 21, 1000, '#3182EF', True, 'middle')
    return l

def arrow_track_columns():
    l = Layout('arrow_track_columns', SHELL)
    l.defs = '\n'.join((grad('qaxTrackA', '#31C068', '#30C0B4'), grad('qaxTrackB', '#44B4CF', '#4874CB'),
                        grad('qaxBtn', '#4991F1', '#1B71FF'), PURPLE_G))
    l.note('track')
    l.rr(132, 216, 340, 49, 0, 'url(#qaxTrackA)')
    l.rr(470, 216, 384, 49, 0, 'url(#qaxTrackB)')
    l.poly('852,216 1130,216 1130,194 1203,240 1130,287 1130,265 852,265', 'url(#qaxArrow)')
    for n, (x, col, cx, ix) in enumerate(((100, '#31C068', 300, 119), (425, TEAL, 665, 444), (822, '#4874CB', 1010, 841)), 1):
        l.rr(x, 201, 72, 72, 24, col)
        l.icon(ix, 220, 34, f'S{n}_ICON', '#FFFFFF')
        l.t(cx, 250, f'S{n}_LABEL', 26, 300, '#FFFFFF', True, 'middle')
    for n, x in enumerate((160, 546, 931), 1):
        cx = x + 126
        l.note(f'column {n}')
        l.rr(x, 288, 253, 197, 12, '#FFFFFF', .7)
        l.t(cx, 344, f'C{n}_TITLE', 24, 229, '#000000', True, 'middle')
        l.t(cx, 412, f'C{n}_L1', 16, 229, INK, False, 'middle')
        l.t(cx, 442, f'C{n}_L2', 16, 229, INK, False, 'middle')
    l.rr(160, 511, 1024, 95, 14, '#FFFFFF', .7)
    l.rr(215, 533, 184, 50, 6, 'url(#qaxBtn)')
    l.t(307, 566, 'POLICY_BTN', 20, 165, '#FFFFFF', True, 'middle')
    l.t(628, 566, 'POLICY_A', 19, 265, '#4991F1', True, 'middle')
    l.t(961, 566, 'POLICY_B', 19, 370, '#4991F1', True, 'middle')
    return l


META = {
 'three_pillars': dict(label='三栏并列卡片', summary='三个并列主题，各含 3 张图标卡片，底部一句结论', source='P13',
   bestFor=['三个互不包含的主题或方案对比','部署形态、能力分组','每组有 2–3 个可并列的要点'], avoidFor=['有先后顺序的流程','单组要点超过 3 个'],
   items='固定 3 栏；每栏 2–3 张卡片。少于 3 张时删掉整张卡片，其余卡片加高填满栏高，不留空洞'),
 'chevron_stages': dict(label='箭头阶段 + 三列', summary='顶部箭头流程条，下接三列关键词卡片和蓝色说明带', source='P14',
   bestFor=['三阶段递进或分步策略','一个总起概念带出三个阶段'], avoidFor=['阶段超过 3 个','阶段间无先后关系'],
   items='固定 1 个总起 + 3 个阶段'),
 'stair_steps': dict(label='阶梯递进', summary='六级上升阶梯，每级含等级圆和两段说明', source='P18',
   bestFor=['影响、风险或成熟度分级','由低到高的多方案对比'], avoidFor=['无程度差异的并列项','少于 4 级'],
   items='4–6 级。减少时删掉最靠前的列，并让其余列等宽铺满 x=35..1200'),
 'layered_rows': dict(label='分层横带', summary='四层横带贯穿中轴，左标题右说明，底部结论', source='P24（简化）',
   bestFor=['分层架构或检测层级','L1–L4 这类有层次的体系'], avoidFor=['层之间无上下关系','说明超过两行'],
   items='3–4 层。3 层时删掉最后一层，其余行高增到 140'),
 'hub_numbered_rows': dict(label='中心枢纽 + 编号行', summary='左侧枢纽图与环绕标签，右侧三条编号说明', source='P25',
   bestFor=['一个核心概念的三个维度','身份、角色、责任归属'], avoidFor=['超过 3 个维度','需要大段说明'],
   items='固定 3 行；环绕标签 3–5 个，未填的自动删除'),
 'image_stack_pills': dict(label='主图 + 胶囊列表', summary='左侧圆形主图，右侧沿弧线排列的优势胶囊', source='P29',
   bestFor=['产品优势、能力清单','5–8 条短句并列'], avoidFor=['没有合适的主图','每条超过一行'],
   items='5–8 条。减少时按条数重新均分 y=150..678，x 仍取弧线对称值'),
 'loop_nodes': dict(label='闭环五节点', summary='五个节点沿环排列，表达持续闭环', source='P28',
   bestFor=['运营闭环、持续改进流程','首尾相接的 5 步流程'], avoidFor=['单向流程','节点不是 5 个'],
   items='固定 5 个节点，顺序为左上起顺时针'),
 'stage_matrix_evidence': dict(label='阶段矩阵 + 证据图', summary='左侧四阶段要点，右侧系统截图与关键结果', source='P31–P34',
   bestFor=['场景实例、落地案例','有截图佐证的产品功能'], avoidFor=['没有截图或证据图','阶段不足 3 个'],
   items='3–4 个阶段；每阶段 2–4 个要点，未填的要点连同白色小卡自动删除'),
}

META_NEW = {
 'architecture_radial': dict(label='放射式三层架构', summary='左侧来源，中心四节点枢纽，右侧输出，底部三段说明', source='P12',
   bestFor=['端到端产品架构总览','输入、处理、输出三段结构'], avoidFor=['没有明确中心平台','节点文字较长'],
   items='固定 3 个输入、4 个中心节点、3 个输出'),
 'probe_tier_channels': dict(label='统一入口 + 三通道', summary='左侧蓝色半圆总起，右侧沿弧线排列三条接入通道', source='P15',
   bestFor=['一个平台对接多种形态','每条通道有名称、说明和动作'], avoidFor=['通道超过 3 条','通道间有先后顺序'],
   items='固定 3 条通道'),
 'three_track_checklist': dict(label='三轨清单', summary='三个圆形徽标带出三列 5 项清单，底部一句结论', source='P16',
   bestFor=['实施步骤与验收清单','每列有 3–5 条短句'], avoidFor=['单条内容超过一行','需要图标卡片时改用 three_pillars'],
   items='固定 3 列；每列 3–5 条，未填的条目连同左侧色条自动删除'),
 'tier_chip_pyramid': dict(label='分层标签 + 金字塔', summary='三层色带排列标签块，右侧金字塔标注层级', source='P17',
   bestFor=['兼容、适配、支持矩阵','大量短名称按状态分层'], avoidFor=['标签是长句','没有层级差异'],
   items='上层最多 14 个、中层 8 个、下层 15 个标签；未填的标签连同白底自动删除'),
 'chain_core_grid': dict(label='链路 + 核心 + 四宫格', summary='顶部五段链路，中部核心能力带，底部四项约束', source='P23',
   bestFor=['检测或分析机制说明','链路加核心引擎加约束条件'], avoidFor=['没有中心能力','链路不足 3 段'],
   items='固定 5 段链路、4 个核心能力、4 项约束'),
 'funnel_layers': dict(label='漏斗分层', summary='中央四层漏斗贯穿横带，左标题右说明，底部结论', source='P24',
   bestFor=['逐层收敛、过滤、研判','层级有先后筛选关系'], avoidFor=['层间没有收敛关系时改用 layered_rows','超过 4 层'],
   items='固定 4 层'),
 'arrow_track_columns': dict(label='箭头轨道 + 三列 + 策略条', summary='渐变箭头表达三段演进，下接三列说明和策略条', source='P27',
   bestFor=['模式或策略的分段演进','从观察到执行的递进'], avoidFor=['阶段超过 3 个','需要大段说明时改用 chevron_stages'],
   items='固定 3 段'),
}

META.update(META_NEW)

BUILDERS = (three_pillars, chevron_stages, stair_steps, layered_rows, hub_numbered_rows, image_stack_pills, loop_nodes, stage_matrix_evidence, architecture_radial, probe_tier_channels, three_track_checklist, tier_chip_pyramid, chain_core_grid, funnel_layers, arrow_track_columns)


def main():
    index = write_library(OUT, [b() for b in BUILDERS], META, USAGE)
    print(f'[OK] {len(index["layouts"])} layouts -> {OUT}')


if __name__ == '__main__':
    main()
