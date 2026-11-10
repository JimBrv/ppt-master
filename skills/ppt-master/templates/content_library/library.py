"""
PPT Master - Shared content layout library.

Structure only. Every builder takes a Layout `l` and draws with color roles
from `l.T` (the template's theme), never with literal colors, so the same
layout renders in any template that has content_src/theme.json and
content_src/shell.svg. Build a template's content/ with:

    uv run python3 skills/ppt-master/scripts/layout_build.py skills/ppt-master/templates/layouts/<template>

Geometry is drawn in the canonical body region (layout_kit.CANONICAL_BODY);
a theme's body_box scales it into a template with a taller header or footer.
The source field records the reference page each layout was derived from.
"""
from layout_kit import Layout, grad


def stage_matrix_evidence(l: Layout):
    T = l.T
    rows = [(148, 138), (300, 138), (452, 138)]
    for n, (y, h) in enumerate(rows, 1):
        l.note(f'stage {n}')
        l.rr(63, y, 493, h, 12, T.primary, .12)
        l.rr(33, y + 39, 60, 60, 10, T.primary)
        l.t(63, y + 76, f'STAGE{n}_LABEL', 20, 50, T.on_accent, True, 'middle')
        for m, (cx, cy) in enumerate([(110, y + 22), (331, y + 22), (110, y + 76), (331, y + 76)], 1):
            l.rr(cx, cy, 209, 41, 6, T.surface, box=f'STAGE{n}_CHIP{m}')
            l.t(cx + 10, cy + 26, f'STAGE{n}_CHIP{m}', 15, 189)
    for y in (272, 424, 566):
        l.poly(f'39,{y} 57,{y} 57,{y+22} 64,{y+22} 48,{y+43} 32,{y+22} 39,{y+22}', T.halo)
    l.note('final stage: single wide chip')
    l.rr(63, 604, 493, 91, 12, T.primary, .12)
    l.rr(33, 619, 60, 60, 10, T.primary)
    l.t(63, 656, 'STAGE4_LABEL', 20, 50, T.on_accent, True, 'middle')
    l.rr(110, 617, 431, 62, 6, T.surface)
    l.t(122, 643, 'STAGE4_L1', 15, 407); l.t(122, 666, 'STAGE4_L2', 15, 407)
    l.note('evidence panel')
    l.rr(602, 148, 629, 376, 12, T.surface, None, T.line, 1)
    l.img(614, 161, 607, 317, 'SCREENSHOT')
    l.t(616, 507, 'CAPTION', 14, 590, T.muted)
    l.note('key results callout')
    l.rr(602, 554, 629, 140, 12, T.primary)
    l.t(640, 618, 'CALLOUT_LABEL_L1', 20, 44, T.on_accent, True, 'middle')
    l.t(640, 646, 'CALLOUT_LABEL_L2', 20, 44, T.on_accent, True, 'middle')
    l.rr(680, 576, 4, 40, 2, T.on_accent); l.rr(680, 640, 4, 40, 2, T.on_accent)
    l.t(696, 590, 'RESULT1_TITLE', 18, 520, T.on_accent, True); l.t(696, 613, 'RESULT1_BODY', 15, 520, T.on_accent)
    l.t(696, 654, 'RESULT2_TITLE', 18, 520, T.on_accent, True); l.t(696, 677, 'RESULT2_BODY', 15, 520, T.on_accent)


def three_pillars(l: Layout):
    T = l.T
    g = T.id_prefix
    l.defs = grad(f'{g}Head', T.strong, T.head_end)
    for n, x in enumerate((40, 447, 854), 1):
        l.note(f'column {n}')
        l.rr(x, 136, 386, 530, 14, T.surface, .85, T.line, 1)
        l.rr(x + 12, 148, 362, 62, 10, f'url(#{g}Head)')
        l.t(x + 193, 189, f'COL{n}_TITLE', 26, 320, T.on_accent, True, 'middle')
        for m in (1, 2, 3):
            y = 222 + (m - 1) * 146
            l.rr(x + 12, y, 362, 134, 10, T.card_tint, .07)
            l.icon(x + 26, y + 12, 28, f'COL{n}_CARD{m}_ICON', T.deep)
            l.t(x + 64, y + 34, f'COL{n}_CARD{m}_TITLE', 20, 290, T.deep, True)
            for k in (1, 2, 3):
                l.t(x + 28, y + 40 + k * 26, f'COL{n}_CARD{m}_L{k}', 16, 330)
    l.t(640, 698, 'CONCLUSION', 22, 1100, T.emphasis, True, 'middle')


def chevron_stages(l: Layout):
    T = l.T

    def bar(pts, fill, slot, cx):
        l.poly(pts, fill); l.t(cx, 184, slot, 21, 240, T.on_accent, True, 'middle')
    bar('0,150 313,150 335,176 313,202 0,202', T.steps[0], 'STEP0_LABEL', 160)
    for n, (x, col) in enumerate(((338, T.steps[1]), (652, T.steps[2]), (967, T.steps[3])), 1):
        bar(f'{x},150 {x+290},150 {x+312},176 {x+290},202 {x},202 {x+22},176', col, f'STEP{n}_LABEL', x + 156)
    l.path('M0,524 Q0,496 28,496 L1252,496 Q1280,496 1280,524 L1280,720 L0,720 Z', T.deep, bleed=True)
    for n, (x, col) in enumerate(zip((71, 462, 853), T.trio_a), 1):
        cx = x + 179
        l.note(f'column {n}')
        l.rr(x, 226, 358, 246, 16, T.surface, .9, T.line, 1)
        l.t(x + 28, 290, f'COL{n}_NAME', 28, 310, T.ink, True)
        l.t(x + 28, 392, f'COL{n}_KEYWORD', 48, 310, col, True, None, True)
        l.icon(x + 288, 410, 48, f'COL{n}_ICON', col)
        l.t(cx, 548, f'COL{n}_TITLE', 22, 340, T.on_accent, True, 'middle')
        for k in (1, 2, 3):
            l.t(cx, 560 + k * 27, f'COL{n}_L{k}', 16, 330, T.on_accent, False, 'middle')


def stair_steps(l: Layout):
    T = l.T
    l.poly('0,470 420,452 830,330 1280,205 1280,130 830,250 420,400 0,438', T.levels[0], .22, bleed=True)
    l.t(58, 160, 'SUBTITLE', 24, 790, T.secondary, True)
    tops = (295, 295, 271, 243, 198, 141)
    for n, (x, top, col) in enumerate(zip((35, 232, 428, 624, 821, 1019), tops, T.ramp), 1):
        cx = x + 90
        l.note(f'step {n}')
        l.rr(x, top, 181, 400, 12, T.surface, None, T.line, 1)
        l.path(f'M{x},{top+40} L{x},{top+12} Q{x},{top} {x+12},{top} L{x+169},{top} Q{x+181},{top} {x+181},{top+12} L{x+181},{top+40} Z', T.primary)
        l.t(cx, top + 27, f'S{n}_NAME', 16, 165, T.on_accent, True, 'middle')
        l.c(cx, top + 112, 58, col, .2); l.c(cx, top + 112, 40, col)
        l.t(cx, top + 121, f'S{n}_GRADE', 24, 60, T.on_accent, True, 'middle')
        l.t(cx, top + 200, f'S{n}_HEAD1', 16, 163, T.deep, True, 'middle')
        for k in (1, 2):
            l.t(cx, top + 200 + k * 23, f'S{n}_A{k}', 15, 163, T.ink, False, 'middle')
        l.t(cx, top + 276, f'S{n}_HEAD2', 16, 163, T.deep, True, 'middle')
        for k in (1, 2, 3):
            l.t(cx, top + 276 + k * 23, f'S{n}_B{k}', 15, 163, T.ink, False, 'middle')
    l.t(1240, 620, 'AXIS_NOTE', 16, 195, T.secondary, False, 'end')


def layered_rows(l: Layout):
    T = l.T
    l.rr(571, 140, 8, 464, 4, T.line)
    for n, (y, col) in enumerate(zip((140, 256, 372, 488), T.levels), 1):
        mid = y + 52
        l.note(f'layer {n}')
        l.rr(150, y, 998, 104, 8, col, .18)
        l.rr(1143, y, 5, 104, 2, col)
        l.c(575, mid, 30, col)
        l.icon(559, mid - 16, 32, f'R{n}_ICON', T.on_accent)
        l.t(176, mid + 9, f'R{n}_LABEL', 24, 360, T.ink, True)
        l.t(636, mid - 6, f'R{n}_L1', 17, 490); l.t(636, mid + 20, f'R{n}_L2', 17, 490)
    l.rr(186, 620, 915, 56, 10, T.surface, .9, T.line, 1)
    l.t(643, 656, 'CONCLUSION', 21, 860, T.emphasis, True, 'middle')


def hub_numbered_rows(l: Layout):
    T = l.T
    l.c(238, 440, 123, T.deep, .12); l.c(238, 440, 80, T.deep)
    l.icon(205, 407, 66, 'HUB_ICON', T.on_accent)
    for n, (x, y) in enumerate(((20, 300), (120, 222), (262, 246), (20, 540), (258, 585)), 1):
        l.rr(x, y, 110, 52, 12, T.halo, None, T.line_soft, 1, box=f'CALLOUT{n}')
        l.t(x + 55, y + 33, f'CALLOUT{n}', 18, 96, T.deep, True, 'middle')
    l.rr(398, 140, 842, 540, 16, T.surface, .9, T.line, 1)
    l.t(819, 200, 'HEADING', 27, 780, T.deep, True, 'middle')
    for n, (y, col) in enumerate(zip((232, 372, 512), T.trio_a), 1):
        mid = y + 56
        l.note(f'row {n}')
        l.rr(505, y, 705, 112, 14, T.tint, None, T.line, 1)
        l.c(500, mid, 42, T.surface); l.c(500, mid, 31, col)
        l.t(500, mid + 10, f'R{n}_NUM', 28, 30, T.on_accent, True, 'middle')
        l.t(556, mid + 8, f'R{n}_TITLE', 21, 180, T.ink, True)
        l.t(748, mid - 4, f'R{n}_L1', 16, 226); l.t(748, mid + 20, f'R{n}_L2', 16, 226)
        l.rr(985, mid - 23, 205, 46, 10, col, .15)
        l.t(1087, mid + 6, f'R{n}_TAG', 16, 186, col, True, 'middle')


def image_stack_pills(l: Layout):
    T = l.T
    l.c(232, 427, 198, T.halo, .7); l.c(232, 427, 166, T.surface)
    l.img(80, 275, 305, 305, 'HERO')
    xs = (379, 417, 454, 471, 471, 454, 417, 379)
    for n, x in enumerate(xs, 1):
        col = T.pills[(n - 1) % 3]
        y = 150 + (n - 1) * 69
        l.note(f'pill {n}')
        l.rr(x, y, 1240 - x, 45, 22, col, .14)
        l.t(x + 22, y + 30, f'P{n}_TAG', 20, 130, col, True)
        l.t(x + 165, y + 29, f'P{n}_BODY', 16, 590, T.text)


def loop_nodes(l: Layout):
    T = l.T
    for d in ('M300,235 Q430,170 560,210', 'M720,210 Q850,170 975,235', 'M1085,440 Q1085,545 940,530',
              'M795,535 Q640,625 495,535', 'M350,530 Q190,545 180,440'):
        l.path(d, 'none', T.line_soft, 16)
    for n, (cx, cy) in enumerate(((196, 275), (639, 230), (1076, 275), (867, 493), (422, 494)), 1):
        l.note(f'node {n}')
        l.c(cx, cy, 47, T.bright)
        l.icon(cx - 22, cy - 22, 44, f'N{n}_ICON', T.on_accent)
        l.t(cx, cy + 86, f'N{n}_TITLE', 24, 240, T.node_title, True, 'middle')
        l.t(cx, cy + 118, f'N{n}_L1', 18, 250, T.ink, False, 'middle')
        l.t(cx, cy + 144, f'N{n}_L2', 18, 250, T.ink, False, 'middle')


def architecture_radial(l: Layout):
    T = l.T
    g = T.id_prefix
    l.defs = grad(f'{g}NodeA', T.strong, T.bright) + '\n' + grad(f'{g}NodeB', T.strong, T.secondary)
    l.note('source column')
    l.t(110, 176, 'SRC_TITLE_L1', 18, 130, T.label, True, 'middle')
    l.t(110, 200, 'SRC_TITLE_L2', 18, 130, T.label, True, 'middle')
    l.rr(42, 221, 134, 290, 20, T.panel)
    for n, y0 in enumerate((258, 342, 426), 1):
        for k in (1, 2, 3):
            l.t(109, y0 + (k - 1) * 22, f'SRC{n}_L{k}', 16, 120, T.ink, True, 'middle')
    l.raw(f'<path d="M202,156 L202,576" fill="none" stroke="{T.primary}" stroke-width="3" stroke-dasharray="4,8"/>',
          box=(200, 156, 204, 576))
    l.note('wedges converging on the hub')
    l.path('M355,191 L688,373 L367,570 C300,450 296,310 355,191 Z', T.strong, op='0.12')
    l.path('M1013,195 L680,373 L1024,531 C1076,420 1074,300 1013,195 Z', T.secondary, op='0.12')
    l.t(320, 186, 'INPUT_LABEL', 18, 200, T.strong, True, 'middle')
    rows = ((259, 236, 397, 280), (226, 344, 364, 384), (257, 451, 395, 482))
    for n, (px, py, cx, cy) in enumerate(rows, 1):
        l.note(f'input {n}')
        l.rr(px - 15, py, 126, 73, 36, T.surface, None, T.outline, 1)
        l.t(px + 35, py + 31, f'IN{n}_P1', 14, 100, T.strong, True, 'middle')
        l.t(px + 35, py + 51, f'IN{n}_P2', 14, 100, T.strong, True, 'middle')
        l.c(cx, cy, 43, f'url(#{g}NodeA)')
        l.t(cx, cy - 3, f'IN{n}_C1', 14, 80, T.on_accent, True, 'middle')
        l.t(cx, cy + 17, f'IN{n}_C2', 14, 80, T.on_accent, True, 'middle')
        tx = cx + 46
        l.poly(f'{tx},{cy-14} {tx+26},{cy} {tx},{cy+14}', T.primary)
    l.note('hub')
    l.t(681, 178, 'HUB_HEADER', 24, 400, T.primary, True, 'middle')
    l.c(681, 374, 181, T.surface)
    l.ring(681, 374, 189, T.line, 1.5)
    for n, (cx, cy) in enumerate(((681, 266), (790, 375), (681, 484), (572, 375)), 1):
        l.c(cx, cy, 40, f'url(#{g}NodeB)')
        l.t(cx, cy - 3, f'NODE{n}_L1', 16, 68, T.on_accent, True, 'middle')
        l.t(cx, cy + 19, f'NODE{n}_L2', 16, 68, T.on_accent, True, 'middle')
    l.t(681, 368, 'CENTER_L1', 19, 136, T.strong, True, 'middle')
    l.t(681, 394, 'CENTER_L2', 19, 136, T.strong, True, 'middle')
    l.t(681, 215, 'CAP_TOP', 14, 200, T.muted, False, 'middle')
    l.t(681, 545, 'CAP_BOTTOM', 14, 240, T.muted, False, 'middle')
    l.t(790, 432, 'CAP_RIGHT_L1', 14, 130, T.muted, False, 'middle')
    l.t(790, 452, 'CAP_RIGHT_L2', 14, 130, T.muted, False, 'middle')
    l.t(572, 432, 'CAP_LEFT_L1', 14, 130, T.muted, False, 'middle')
    l.t(572, 452, 'CAP_LEFT_L2', 14, 130, T.muted, False, 'middle')
    l.note('outputs')
    l.t(961, 246, 'OUT_LABEL', 18, 150, T.secondary, True, 'middle')
    for n, (x, y) in enumerate(((904, 268), (927, 344), (904, 420)), 1):
        l.rr(x, y, 115, 39, 8, T.surface, None, T.secondary, 1)
        l.t(x + 57, y + 26, f'OUT{n}', 16, 100, T.secondary, True, 'middle')
        l.poly(f'{x+117},{y+4} {x+143},{y+19} {x+117},{y+35}', T.secondary)
    l.rr(1088, 221, 150, 290, 16, T.secondary)
    for n, y0 in enumerate((262, 350, 438), 1):
        l.t(1163, y0, f'OUTP{n}_L1', 15, 134, T.on_accent, True, 'middle')
        l.t(1163, y0 + 22, f'OUTP{n}_L2', 15, 134, T.on_accent, True, 'middle')
    l.note('three notes')
    for n, x in enumerate((37, 448, 860), 1):
        l.rr(x, 591, 378, 100, 12, T.surface, .85, T.line, 1)
        l.t(x + 16, 623, f'NOTE{n}_TITLE', 16, 350, T.ink, True)
        l.t(x + 16, 650, f'NOTE{n}_L1', 15, 350, T.text)
        l.t(x + 16, 674, f'NOTE{n}_L2', 15, 350, T.text)


def probe_tier_channels(l: Layout):
    T = l.T
    l.path('M0,179 L350,179 C465,179 553,272 553,386 C553,500 465,593 350,593 L0,593 Z', T.primary, op='0.08')
    l.path('M0,231 L303,231 C398,231 474,300 474,386 C474,472 398,541 303,541 L0,541 Z', T.primary)
    l.t(29, 326, 'HUB_TITLE', 30, 390, T.on_accent, True)
    l.t(30, 360, 'HUB_L1', 14, 380, T.on_accent)
    l.t(30, 382, 'HUB_L2', 14, 380, T.on_accent)
    l.path('M28,397 L395,397', 'none', T.on_accent, 1)
    l.c(66, 451, 38, T.surface)
    l.icon(50, 435, 32, 'HUB_ICON', T.primary)
    l.t(118, 442, 'HUB_TAG_L1', 20, 280, T.on_accent, True)
    l.t(118, 472, 'HUB_TAG_L2', 20, 280, T.on_accent, True)
    rows = (('TOP', 505, 218, 587, 181, T.channels[0], 960, 180, 540, 250),
            ('MID', 570, 390, 652, 352, T.channels[1], 975, 175, 490, 200),
            ('BOT', 505, 561, 587, 524, T.channels[2], 960, 180, 540, 250))
    for p, cx, cy, px, py, col, hx, hw, lw, nw in rows:
        l.note(f'channel {p}')
        l.c(cx, cy, 47, T.surface)
        l.ring(cx, cy, 47, T.line, 1)
        l.icon(cx - 18, cy - 18, 36, f'{p}_ICON', T.primary)
        l.rr(px, py, 103, 40, 10, col)
        l.t(px + 51, py + 28, f'{p}_PILL', 20, 90, T.on_accent, True, 'middle')
        l.t(px + 113, py + 29, f'{p}_NAME', 22, nw, T.ink, True)
        l.t(hx, py + 27, f'{p}_HINT', 14, hw, col)
        l.t(px, py + 72, f'{p}_L1', 16, lw)
        l.t(px, py + 100, f'{p}_L2', 16, lw)
        l.t(1213, py + 22, f'{p}_NOTE_L1', 15, 112, col, True, 'middle')
        l.t(1213, py + 46, f'{p}_NOTE_L2', 15, 112, col, True, 'middle')
    l.t(636, 680, 'CONCLUSION', 22, 1100, T.emphasis, True, 'middle')


def three_track_checklist(l: Layout):
    T = l.T
    l.path('M69,224 L1209,224', 'none', T.line, 2)
    for n, (x, col) in enumerate(zip((69, 453, 837), T.trio_b), 1):
        cx = x + 187
        l.note(f'track {n}')
        l.c(cx, 225, 42, T.surface)
        l.c(cx, 225, 35, col)
        l.t(cx, 233, f'T{n}_BADGE', 22, 66, T.on_accent, True, 'middle')
        l.rr(x, 275, 375, 52, 6, col, .18)
        l.t(cx, 309, f'T{n}_HEAD', 22, 340, T.ink_strong, True, 'middle')
        for m in range(1, 6):
            y = 355 + (m - 1) * 43.5
            l.rr(x + 27, y, 7, 38, 3, col, .8, box=f'T{n}_ITEM{m}')
            l.t(x + 49, y + 26, f'T{n}_ITEM{m}', 16, 312, T.ink, True)
    l.t(640, 664, 'CONCLUSION', 22, 1100, T.emphasis, True, 'middle')


def tier_chip_pyramid(l: Layout):
    T = l.T
    l.rr(0, 600, 1280, 120, 0, T.deep, .7, bleed=True)
    tiers = (('TOP', 182, 124, 0, 2, 7, 110, 120, 196, 53),
             ('MID', 325, 124, 1, 2, 4, 150, 165, 341, 51),
             ('BOT', 468, 172, 2, 3, 5, 118, 128, 485, 52))
    for p, y, h, i, rows, cols, w, step, y0, dy in tiers:
        l.note(f'tier {p} band')
        l.rr(70, y, 866, h, 0, T.tier_fill[i])
    l.poly('898,282 971,155 1045,282', T.tier_mark[0], .35)
    l.poly('870,325 1062,325 1131,452 801,452', T.tier_mark[1], .35)
    l.poly('772,496 1152,496 1218,640 704,640', T.tier_mark[2], .35)
    l.icon(949, 200, 46, 'TOP_ICON', T.on_accent)
    l.icon(947, 335, 48, 'MID_ICON', T.on_accent)
    l.icon(944, 512, 56, 'BOT_ICON', T.on_accent)
    for p, y, h, i, rows, cols, w, step, y0, dy in tiers:
        n = 0
        for r in range(rows):
            for c in range(cols):
                n += 1
                x, yy = 90 + c * step, y0 + r * dy
                l.rr(x, yy, w, 38, 6, T.surface, .88, box=f'{p}_C{n}')
                l.t(x + w // 2, yy + 25, f'{p}_C{n}', 14 if p != 'MID' else 15, w - 10, T.tier_text[i], True, 'middle')
    for p, y, i in (('TOP', 255, 0), ('MID', 390, 1), ('BOT', 585, 2)):
        l.rr(906, y, 133, 47, 20, T.tier_mark[i], .85)
        l.t(972, y + 32, f'{p}_LABEL', 24, 120, T.on_accent, True, 'middle')


def chain_core_grid(l: Layout):
    T = l.T
    g = T.id_prefix
    l.defs = grad(f'{g}Core', T.secondary, T.strong)
    l.note('racetrack ring behind the core band')
    l.raw(f'<rect x="205" y="312" width="845" height="202" rx="101" fill="none" stroke="{T.strong}" '
          f'stroke-width="20" stroke-opacity="0.3"/>', box=(195, 302, 1060, 524))
    for n, (x, y) in enumerate(((107, 224), (325, 182), (542, 182), (760, 182), (978, 224)), 1):
        cx = x + 94
        l.note(f'chain {n}')
        l.t(cx, y + 34, f'CH{n}_TITLE', 21, 180, T.strong, True, 'middle')
        l.t(cx, y + 70, f'CH{n}_BODY', 15, 210, T.ink, False, 'middle')
    l.rr(247, 342, 761, 142, 24, T.surface)
    for n, x in enumerate((278, 404, 751, 877), 1):
        l.rr(x, 363, 100, 100, 30, f'url(#{g}Core)')
        l.t(x + 50, 420, f'CORE{n}', 20, 92, T.on_accent, True, 'middle')
    l.t(627, 424, 'CENTER', 30, 235, T.strong, True, 'middle')
    for n, (x, y) in enumerate(((157, 567), (663, 567), (157, 625), (663, 625)), 1):
        l.rr(x, y, 464, 46, 12, T.surface, None, T.outline_soft, 1.5)
        l.t(x + 16, y + 29, f'G{n}_LABEL', 15, 100, T.secondary, True)
        l.t(x + 448, y + 29, f'G{n}_VALUE', 15, 320, T.ink, False, 'end')


def funnel_layers(l: Layout):
    T = l.T
    rows = ((195, 90), (295, 94), (399, 87), (497, 79))
    for n, ((y, h), col) in enumerate(zip(rows, T.levels), 1):
        l.note(f'layer {n} band')
        l.rr(171, y, 977, h, 4, col, .16)
        l.rr(1143, y, 5, h, 2, col)
    cx = 589
    bands = ((473, 106, 77, 56, 3), (378, 107, 109, 79, 2), (287, 104, 152, 110, 1), (194, 106, 210, 151, 0))
    l.note('funnel, drawn bottom-up so upper layers overlap lower ones')
    for y, h, wt, wb, i in bands:
        l.path(f'M{cx-wt},{y} L{cx+wt},{y} L{cx+wb},{y+h-12} Q{cx},{y+h+8} {cx-wb},{y+h-12} Z', T.levels[i])
    l.raw(f'<ellipse cx="{cx}" cy="194" rx="209" ry="15" fill="{T.shade}"/>', box=(cx - 209, 179, cx + 209, 209))
    for n, ((y, h), my) in enumerate(zip(rows, (256, 348, 440, 533)), 1):
        l.ring(cx, my, 26, T.on_accent, 1.5)
        l.icon(cx - 14, my - 14, 28, f'L{n}_ICON', T.on_accent)
        mid = y + h // 2
        l.t(181, mid + 8, f'L{n}_LABEL', 20, 205, T.ink, True)
        l.t(1135, mid - 5, f'L{n}_D1', 16, 322, T.ink, False, 'end')
        l.t(1135, mid + 19, f'L{n}_D2', 16, 322, T.ink, False, 'end')
    l.t(643, 664, 'CONCLUSION', 21, 1000, T.emphasis, True, 'middle')


def arrow_track_columns(l: Layout):
    T = l.T
    k = T.track
    g = T.id_prefix
    l.defs = '\n'.join((grad(f'{g}TrackA', k[0], k[1]), grad(f'{g}TrackB', k[2], k[3]),
                        grad(f'{g}Btn', T.bright, T.bright_end), grad(f'{g}Arrow', k[3], k[4])))
    l.note('track')
    l.rr(132, 216, 340, 49, 0, f'url(#{g}TrackA)')
    l.rr(470, 216, 384, 49, 0, f'url(#{g}TrackB)')
    l.poly('852,216 1130,216 1130,194 1203,240 1130,287 1130,265 852,265', f'url(#{g}Arrow)')
    for n, (x, col, cx, ix) in enumerate(((100, k[0], 300, 119), (425, k[1], 665, 444), (822, k[3], 1010, 841)), 1):
        l.rr(x, 201, 72, 72, 24, col)
        l.icon(ix, 220, 34, f'S{n}_ICON', T.on_accent)
        l.t(cx, 250, f'S{n}_LABEL', 26, 300, T.on_accent, True, 'middle')
    for n, x in enumerate((160, 546, 931), 1):
        cx = x + 126
        l.note(f'column {n}')
        l.rr(x, 288, 253, 197, 12, T.surface, .7)
        l.t(cx, 344, f'C{n}_TITLE', 24, 229, T.ink_strong, True, 'middle')
        l.t(cx, 412, f'C{n}_L1', 16, 229, T.ink, False, 'middle')
        l.t(cx, 442, f'C{n}_L2', 16, 229, T.ink, False, 'middle')
    l.rr(160, 511, 1024, 95, 14, T.surface, .7)
    l.rr(215, 533, 184, 50, 6, f'url(#{g}Btn)')
    l.t(307, 566, 'POLICY_BTN', 20, 165, T.on_accent, True, 'middle')
    l.t(628, 566, 'POLICY_A', 19, 265, T.bright, True, 'middle')
    l.t(961, 566, 'POLICY_B', 19, 370, T.bright, True, 'middle')


# --------------------------------------------------------------------------
# Layouts designed to fill gaps in the relation vocabulary (no reference
# page): statement, metric, contrast, problem_solution, timeline, matrix.
# --------------------------------------------------------------------------

def hero_statement(l: Layout):
    T = l.T
    l.c(1110, 300, 150, T.halo, .45)
    l.c(1110, 300, 96, T.halo, .6)
    l.t(128, 205, 'KICKER', 20, 640, T.secondary, True)
    l.rr(96, 236, 8, 180, 4, T.primary)
    l.t(128, 300, 'STATEMENT_L1', 46, 1060, T.ink, True)
    l.t(128, 368, 'STATEMENT_L2', 46, 1060, T.ink, True)
    l.t(128, 418, 'ATTRIBUTION', 20, 900, T.muted)
    l.rr(128, 462, 1052, 2, 1, T.line)
    l.t(128, 518, 'SUPPORT_L1', 20, 1050, T.text)
    l.t(128, 550, 'SUPPORT_L2', 20, 1050, T.text)
    for n, x in enumerate((128, 498, 868), 1):
        l.rr(x, 596, 330, 58, 12, T.primary, .1, box=f'TAG{n}')
        l.t(x + 165, 633, f'TAG{n}', 22, 300, T.deep, True, 'middle')


def key_metrics(l: Layout):
    T = l.T
    for n, x in enumerate((44, 448, 852), 1):
        l.note(f'metric {n}')
        l.rr(x, 150, 384, 414, 16, T.surface, .9, T.line, 1)
        l.rr(x + 32, 182, 48, 6, 3, T.primary)
        l.t(x + 32, 292, f'M{n}_NUM', 72, 330, T.primary, True)
        l.t(x + 32, 336, f'M{n}_UNIT', 22, 320, T.secondary, True)
        l.rr(x + 32, 362, 320, 2, 1, T.line)
        l.t(x + 32, 408, f'M{n}_LABEL', 24, 320, T.ink, True)
        for k in (1, 2, 3):
            l.t(x + 32, 422 + k * 28, f'M{n}_L{k}', 17, 320, T.text)
        l.t(x + 32, 542, f'M{n}_SOURCE', 14, 320, T.muted)
    l.rr(44, 590, 1192, 84, 14, T.primary)
    l.t(640, 641, 'TAKEAWAY', 24, 1120, T.on_accent, True, 'middle')


def problem_solution(l: Layout):
    T = l.T
    l.rr(40, 146, 150, 40, 20, T.primary)
    l.t(115, 173, 'SERIES', 18, 130, T.on_accent, True, 'middle')
    l.t(210, 174, 'HOOK', 20, 1020, T.secondary, False, None, True)
    l.note('problem panel')
    l.rr(40, 206, 560, 404, 16, T.tint, None, T.line, 1)
    l.t(72, 248, 'PROBLEM_LABEL', 16, 500, T.muted, True)
    l.t(72, 294, 'PROBLEM_TITLE', 28, 500, T.ink, True)
    l.t(72, 332, 'PROBLEM_L1', 17, 500, T.text)
    l.t(72, 358, 'PROBLEM_L2', 17, 500, T.text)
    l.rr(72, 382, 496, 1.5, 0, T.line)
    l.t(72, 416, 'WHY_LABEL', 18, 500, T.secondary, True)
    for n, y in enumerate((458, 508, 558), 1):
        l.rr(74, y - 12, 9, 9, 2, T.primary, box=f'WHY{n}')
        l.t(96, y, f'WHY{n}', 17, 476, T.ink)
    l.poly('608,390 630,390 630,374 654,410 630,446 630,430 608,430', T.primary)
    l.note('responses')
    l.t(668, 236, 'RESPONSE_LABEL', 20, 560, T.deep, True)
    for n, (y, col) in enumerate(zip((256, 374, 492), T.trio_a), 1):
        l.rr(668, y, 572, 106, 12, T.surface, None, T.line, 1, box=f'R{n}_ACTION')
        l.rr(688, y + 18, 124, 34, 17, col, .15, box=f'R{n}_ACTION')
        l.t(750, y + 41, f'R{n}_ACTOR', 16, 112, col, True, 'middle')
        l.t(830, y + 42, f'R{n}_ACTION', 20, 396, T.ink, True)
        l.t(688, y + 84, f'R{n}_L1', 16, 536, T.text)
    l.rr(40, 628, 1200, 56, 12, T.primary, .1)
    l.t(640, 664, 'CONCLUSION', 21, 1150, T.emphasis, True, 'middle')


def contrast_split(l: Layout):
    T = l.T
    l.rr(40, 150, 570, 64, 12, T.muted)
    l.t(325, 192, 'L_HEAD', 26, 520, T.on_accent, True, 'middle')
    l.rr(670, 150, 570, 64, 12, T.primary)
    l.t(955, 192, 'R_HEAD', 26, 520, T.on_accent, True, 'middle')
    l.c(640, 182, 28, T.surface)
    l.ring(640, 182, 28, T.line, 2)
    l.t(640, 189, 'VS_LABEL', 20, 44, T.deep, True, 'middle')
    for n in range(1, 5):
        y = 234 + (n - 1) * 92
        l.note(f'row {n}')
        l.rr(40, y, 570, 80, 10, T.tint, None, T.line, 1, box=f'L{n}_TITLE')
        l.t(64, y + 34, f'L{n}_TITLE', 20, 520, T.text, True)
        l.t(64, y + 62, f'L{n}_NOTE', 16, 520, T.muted)
        l.rr(624, y + 28, 32, 24, 12, T.primary, .25, box=f'R{n}_TITLE')
        l.rr(670, y, 570, 80, 10, T.primary, .08, T.line, 1, box=f'R{n}_TITLE')
        l.t(694, y + 34, f'R{n}_TITLE', 20, 520, T.deep, True)
        l.t(694, y + 62, f'R{n}_NOTE', 16, 520, T.text)
    l.rr(40, 612, 1200, 64, 12, T.primary)
    l.t(640, 653, 'VERDICT', 22, 1150, T.on_accent, True, 'middle')


def spectrum_position(l: Layout):
    T = l.T
    l.rr(100, 300, 1080, 6, 3, T.line)
    for side, x, mx in (('L', 60, 140), ('R', 880, 1140)):
        l.note(f'extreme {side}')
        l.t(x, 214, f'{side}_NAME', 26, 340, T.muted, True)
        l.t(x, 246, f'{side}_L1', 16, 340, T.muted)
        l.t(x, 270, f'{side}_L2', 16, 340, T.muted)
        l.c(mx, 303, 14, T.muted)
        l.rr(x, 330, 170, 36, 18, T.muted, .15)
        l.t(x + 85, 354, f'{side}_TAG', 16, 150, T.muted, True, 'middle')
    l.note('the position held')
    l.rr(430, 150, 420, 130, 16, T.primary)
    l.t(640, 200, 'M_NAME', 28, 380, T.on_accent, True, 'middle')
    l.t(640, 232, 'M_L1', 16, 380, T.on_accent, False, 'middle')
    l.t(640, 256, 'M_L2', 16, 380, T.on_accent, False, 'middle')
    l.poly('622,280 658,280 640,296', T.primary)
    l.c(640, 303, 22, T.primary, .25)
    l.c(640, 303, 13, T.primary)
    l.t(40, 414, 'PRINCIPLES_LABEL', 18, 600, T.secondary, True)
    for n, x in enumerate((40, 448, 856), 1):
        l.rr(x, 430, 384, 180, 14, T.surface, .9, T.line, 1, box=f'P{n}_TITLE')
        l.rr(x + 24, 450, 40, 6, 3, T.primary, box=f'P{n}_TITLE')
        l.t(x + 24, 492, f'P{n}_TITLE', 22, 336, T.deep, True)
        for k in (1, 2, 3):
            l.t(x + 24, 495 + k * 27, f'P{n}_L{k}', 16, 336, T.text)
    l.t(640, 660, 'CONCLUSION', 22, 1100, T.emphasis, True, 'middle')


def timeline(l: Layout):
    T = l.T
    l.rr(60, 360, 1160, 6, 3, T.line)
    l.poly('1218,350 1244,363 1218,376', T.line)
    for n in range(1, 7):
        cx = 190 + (n - 1) * 180
        up = n % 2 == 1
        y = 180 if up else 396
        slot = f'M{n}_TITLE'
        l.note(f'milestone {n}')
        l.rr(cx - 22, 341, 44, 44, 22, T.primary, .15, box=slot)
        l.rr(cx - 11, 352, 22, 22, 11, T.primary, box=slot)
        l.rr(cx - 1, 330 if up else 375, 2, 21, 0, T.line, box=slot)
        l.rr(cx - 150, y, 300, 150, 12, T.surface, .92, T.line, 1, box=slot)
        l.t(cx, y + 40, f'M{n}_DATE', 24, 270, T.primary, True, 'middle')
        l.t(cx, y + 74, slot, 19, 270, T.ink, True, 'middle')
        l.t(cx, y + 102, f'M{n}_L1', 16, 270, T.text, False, 'middle')
        l.t(cx, y + 126, f'M{n}_L2', 16, 270, T.text, False, 'middle')
    l.t(640, 640, 'CONCLUSION', 22, 1100, T.emphasis, True, 'middle')


def matrix_2x2(l: Layout):
    T = l.T
    l.rr(140, 156, 4, 438, 2, T.muted)
    l.poly('130,160 142,138 154,160', T.muted)
    l.rr(170, 600, 1046, 4, 2, T.muted)
    l.poly('1214,590 1236,602 1214,614', T.muted)
    l.t(126, 180, 'Y_HIGH', 15, 100, T.muted, False, 'end')
    l.t(126, 380, 'Y_LABEL', 16, 110, T.secondary, True, 'end')
    l.t(126, 584, 'Y_LOW', 15, 100, T.muted, False, 'end')
    l.t(170, 634, 'X_LOW', 15, 200, T.muted)
    l.t(693, 634, 'X_LABEL', 16, 400, T.secondary, True, 'middle')
    l.t(1216, 634, 'X_HIGH', 15, 200, T.muted, False, 'end')
    for q, x, y, hot in (('TL', 170, 150, False), ('TR', 715, 150, True), ('BL', 170, 380, False), ('BR', 715, 380, False)):
        l.note(f'quadrant {q}')
        if hot:
            l.rr(x, y, 525, 210, 14, T.primary)
        else:
            l.rr(x, y, 525, 210, 14, T.tint, None, T.line, 1)
        ink, body = (T.on_accent, T.on_accent) if hot else (T.deep, T.text)
        l.t(x + 28, y + 56, f'{q}_TITLE', 24, 465, ink, True)
        l.t(x + 28, y + 100, f'{q}_L1', 17, 469, body)
        l.t(x + 28, y + 128, f'{q}_L2', 17, 469, body)
        l.t(x + 28, y + 156, f'{q}_L3', 17, 469, body)
    l.t(640, 682, 'CONCLUSION', 21, 1100, T.emphasis, True, 'middle')


META = {
 'three_pillars': dict(relations=['parallel'], claim='三栏地位平等，交换顺序不改变意思',
   label='三栏并列卡片', summary='三个并列主题，各含 3 张图标卡片，底部一句结论', source='P13',
   bestFor=['三个互不包含的主题或方案对比', '部署形态、能力分组', '每组有 2–3 个可并列的要点'], avoidFor=['有先后顺序的流程', '单组要点超过 3 个'],
   items='固定 3 栏；每栏 2–3 张卡片。少于 3 张时删掉整张卡片，其余卡片加高填满栏高，不留空洞'),
 'chevron_stages': dict(relations=['sequence'], claim='三个阶段有先后，前一阶段是后一阶段的前提',
   label='箭头阶段 + 三列', summary='顶部箭头流程条，下接三列关键词卡片和蓝色说明带', source='P14',
   bestFor=['三阶段递进或分步策略', '一个总起概念带出三个阶段'], avoidFor=['阶段超过 3 个', '阶段间无先后关系'],
   items='固定 1 个总起 + 3 个阶段'),
 'stair_steps': dict(labels=['SUBTITLE', 'AXIS_NOTE', 'S{n}_HEAD{n}'], relations=['escalation'], claim='每一级都比前一级程度更高，能说出升级的是什么维度',
   label='阶梯递进', summary='六级上升阶梯，每级含等级圆和两段说明', source='P18',
   bestFor=['影响、风险或成熟度分级', '由低到高的多方案对比'], avoidFor=['无程度差异的并列项', '少于 4 级'],
   items='4–6 级。减少时删掉最靠前的列，并让其余列等宽铺满 x=35..1200'),
 'layered_rows': dict(relations=['layering'], claim='下层支撑上层（或由外到内），调换层序会出错',
   label='分层横带', summary='四层横带贯穿中轴，左标题右说明，底部结论', source='P24（简化）',
   bestFor=['分层架构或检测层级', 'L1–L4 这类有层次的体系'], avoidFor=['层之间无上下关系', '说明超过两行'],
   items='3–4 层。3 层时删掉最后一层，其余行高增到 140'),
 'hub_numbered_rows': dict(labels=['HEADING'], relations=['hub'], claim='三行都是中心概念的组成维度，不把问题和对策混排',
   label='中心枢纽 + 编号行', summary='左侧枢纽图与环绕标签，右侧三条编号说明', source='P25',
   bestFor=['一个核心概念的三个维度', '身份、角色、责任归属'], avoidFor=['超过 3 个维度', '需要大段说明'],
   items='固定 3 行；环绕标签 3–5 个，未填的自动删除'),
 'image_stack_pills': dict(relations=['evidence', 'parallel'], claim='有一张真实主图，每一条都在描述这张图的主体',
   label='主图 + 胶囊列表', summary='左侧圆形主图，右侧沿弧线排列的优势胶囊', source='P29',
   bestFor=['产品优势、能力清单', '5–8 条短句并列'], avoidFor=['没有合适的主图', '每条超过一行'],
   items='5–8 条。减少时按条数重新均分 y=150..678，x 仍取弧线对称值'),
 'loop_nodes': dict(relations=['cycle'], claim='最后一个节点的结果回到第一个节点，形成持续运转',
   label='闭环五节点', summary='五个节点沿环排列，表达持续闭环', source='P28',
   bestFor=['运营闭环、持续改进流程', '首尾相接的 5 步流程'], avoidFor=['单向流程', '节点不是 5 个'],
   items='固定 5 个节点，顺序为左上起顺时针'),
 'stage_matrix_evidence': dict(labels=['CALLOUT_LABEL_L{n}'], relations=['evidence', 'sequence'], claim='左侧是有先后的阶段，右侧是一张真实截图作为证据',
   label='阶段矩阵 + 证据图', summary='左侧四阶段要点，右侧系统截图与关键结果', source='P31–P34',
   bestFor=['场景实例、落地案例', '有截图佐证的产品功能'], avoidFor=['没有截图或证据图', '阶段不足 3 个'],
   items='3–4 个阶段；每阶段 2–4 个要点，未填的要点连同白色小卡自动删除'),
 'architecture_radial': dict(labels=['SRC_TITLE_L{n}', 'INPUT_LABEL', 'HUB_HEADER', 'OUT_LABEL'], relations=['hub'], claim='有一个中心系统，左边的输入和右边的输出都直接与它相连',
   label='放射式三层架构', summary='左侧来源，中心四节点枢纽，右侧输出，底部三段说明', source='P12',
   bestFor=['端到端产品架构总览', '输入、处理、输出三段结构'], avoidFor=['没有明确中心平台', '节点文字较长'],
   items='固定 3 个输入、4 个中心节点、3 个输出'),
 'probe_tier_channels': dict(labels=['TOP_PILL', 'MID_PILL', 'BOT_PILL'], relations=['hub'], claim='一个核心通过几条并行通道连接不同对象',
   label='统一入口 + 三通道', summary='左侧蓝色半圆总起，右侧沿弧线排列三条接入通道', source='P15',
   bestFor=['一个平台对接多种形态', '每条通道有名称、说明和动作'], avoidFor=['通道超过 3 条', '通道间有先后顺序'],
   items='固定 3 条通道'),
 'three_track_checklist': dict(relations=['parallel'], claim='三条线相互独立，每条线内部是一份清单',
   label='三轨清单', summary='三个圆形徽标带出三列 5 项清单，底部一句结论', source='P16',
   bestFor=['实施步骤与验收清单', '每列有 3–5 条短句'], avoidFor=['单条内容超过一行', '需要图标卡片时改用 three_pillars'],
   items='固定 3 列；每列 3–5 条，未填的条目连同左侧色条自动删除'),
 'tier_chip_pyramid': dict(relations=['classification'], claim='每个条目只属于一档，越往上越少或越高级',
   label='分层标签 + 金字塔', summary='三层色带排列标签块，右侧金字塔标注层级', source='P17',
   bestFor=['兼容、适配、支持矩阵', '大量短名称按状态分层'], avoidFor=['标签是长句', '没有层级差异'],
   items='上层最多 14 个、中层 8 个、下层 15 个标签；未填的标签连同白底自动删除'),
 'chain_core_grid': dict(relations=['chain_core'], claim='上方是有先后的链路，中间的核心贯穿整条链路，下方是支撑或约束',
   label='链路 + 核心 + 四宫格', summary='顶部五段链路，中部核心能力带，底部四项约束', source='P23',
   bestFor=['检测或分析机制说明', '链路加核心引擎加约束条件'], avoidFor=['没有中心能力', '链路不足 3 段'],
   items='固定 5 段链路、4 个核心能力、4 项约束'),
 'funnel_layers': dict(relations=['convergence'], claim='每一层都比上一层窄，最后得出结果',
   label='漏斗分层', summary='中央四层漏斗贯穿横带，左标题右说明，底部结论', source='P24',
   bestFor=['逐层收敛、过滤、研判', '层级有先后筛选关系'], avoidFor=['层间没有收敛关系时改用 layered_rows', '超过 4 层'],
   items='固定 4 层'),
 'arrow_track_columns': dict(relations=['escalation', 'sequence'], claim='各段沿一个方向递增（强度、权限或成熟度）',
   label='箭头轨道 + 三列 + 策略条', summary='渐变箭头表达三段演进，下接三列说明和策略条', source='P27',
   bestFor=['模式或策略的分段演进', '从观察到执行的递进'], avoidFor=['阶段超过 3 个', '需要大段说明时改用 chevron_stages'],
   items='固定 3 段'),
 'hero_statement': dict(labels=['KICKER'], relations=['statement'], claim='整页只有一个观点，其余文字都在支撑它',
   label='大字论断 / 引语', summary='一到两行大字论断，配出处、两行补充和三个关键词', source='原创（补位：论断）',
   bestFor=['开篇论点、章节转折、结尾号召', '一句值得单独成页的引语', '叙事类文稿的"呼吸页"'],
   avoidFor=['有 3 个以上需要展开的要点', '论断需要数据支撑时改用 key_metrics'],
   items='论断 1–2 行；出处、补充说明、关键词均可不填，未填的关键词连同底块自动删除'),
 'key_metrics': dict(relations=['metric'], claim='每个数字都来自原文，并且能用一句话解读',
   label='三个关键数字', summary='三张大数字卡（数字、单位、标签、说明、来源），底部一句结论', source='原创（补位：数字）',
   bestFor=['规模、速度、比例、预测等关键数据', '用数字建立认知冲击'],
   avoidFor=['原文没有确切数字', '数字只是装饰、与结论无关', '超过 3 个数字时拆页或改用图表'],
   items='固定 3 个数字；每个数字 M{n}_SOURCE 写出处（原文段落或数据来源）'),
 'problem_solution': dict(labels=['SERIES', 'HOOK', 'PROBLEM_LABEL', 'WHY_LABEL', 'RESPONSE_LABEL'], relations=['problem_solution'], claim='右侧每条对策都对应左侧的问题；左侧写清"为什么可能发生"',
   label='问题 → 对策', summary='左侧问题与成因，箭头指向右侧三条分主体的对策，底部一句话', source='原创（补位：问题-对策）',
   bestFor=['风险与应对、痛点与方案', '平行章节反复使用（SERIES 标注 1/5、2/5…）', 'HOOK 放章节的原文小标题或引语'],
   avoidFor=['只有问题没有对策', '对策超过 3 条', '问题和对策之间没有对应关系'],
   items='成因 1–3 条、对策 1–3 条，未填的连同底块自动删除；同一系列的各页保持同样的标签文字'),
 'contrast_split': dict(labels=['VS_LABEL'], relations=['contrast'], claim='每一行左右两项说的是同一件事，构成一一对照',
   label='左右对照', summary='左右两栏逐行对照（误区/事实、现状/目标、之前/之后），底部结论', source='原创（补位：对照）',
   bestFor=['误区与事实', '现状与目标、之前与之后', '两种做法的逐项比较'],
   avoidFor=['两边各说各的、无法逐行对应', '超过两个对象时改用 three_pillars', '要表达"两个极端之间的立场"时改用 spectrum_position'],
   items='2–4 行；未填的行（左右两格）自动删除'),
 'spectrum_position': dict(labels=['PRINCIPLES_LABEL'], relations=['contrast'], claim='两端是两个都要避免的极端，中间才是主张',
   label='两极之间的立场', summary='横轴两端是两个极端，中间高亮所持立场，下方三条原则', source='原创（补位：立场）',
   bestFor=['"既不……也不……"式的立场', '在两种错误倾向之间定位', '方法论、原则的提出'],
   avoidFor=['两端不是同一维度的两极', '简单的二选一时改用 contrast_split'],
   items='两端各 1 个、中间 1 个；原则 1–3 条，未填的连同卡片自动删除'),
 'timeline': dict(relations=['timeline'], claim='节点按真实时间排序，日期可以查证',
   label='时间线', summary='横向时间轴上下交错 3–6 个节点，每个节点有日期、标题和两行说明', source='原创（补位：时间线）',
   bestFor=['发展历程、里程碑', '路线图与预测时间点'],
   avoidFor=['没有日期的步骤（那是顺序，改用 chevron_stages）', '节点超过 6 个'],
   items='3–6 个节点，从 M1 起按时间先后填；未填的节点连同卡片自动删除'),
 'matrix_2x2': dict(labels=['Y_HIGH', 'Y_LABEL', 'Y_LOW', 'X_LOW', 'X_LABEL', 'X_HIGH'], relations=['matrix'], claim='两个维度相互独立，每个条目只落进一个象限；右上象限是重点',
   label='二维四象限', summary='两条坐标轴划出四个象限，右上象限高亮，底部一句结论', source='原创（补位：矩阵）',
   bestFor=['按两个维度定位、分类', '优先级与取舍分析'],
   avoidFor=['两个维度相关或说不清', '条目无法归入唯一象限'],
   items='固定 4 个象限；把要强调的象限放在右上（TR）'),
}

BUILDERS = (three_pillars, chevron_stages, stair_steps, layered_rows, hub_numbered_rows, image_stack_pills,
            loop_nodes, stage_matrix_evidence, architecture_radial, probe_tier_channels, three_track_checklist,
            tier_chip_pyramid, chain_core_grid, funnel_layers, arrow_track_columns,
            hero_statement, key_metrics, problem_solution, contrast_split, spectrum_position, timeline, matrix_2x2)

USAGE = '先按内容关系（relations，见 meta.relations）筛版式，再用 claim 验证内容；在 design_spec 的 Layout 字段写版式 ID。slots 的数字是该槽位的最大中文字符数，英文按 0.55 个中文宽度估算；{n} 表示序号。'
