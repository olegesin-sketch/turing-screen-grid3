"""Generate the Grid3_2SSD theme for turing-smart-screen-python.

Usage: python gen_theme.py <output folder> [<res folder of turing-smart-screen-python with fonts>]
Writes theme.yaml, background_base.png, background.png, overlay_ramtemp.png, extra_rows.json.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
RES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'res')
UPSTREAM_RES = os.environ.get('UPSTREAM_RES', RES)
os.makedirs(OUT, exist_ok=True)

W, H = 480, 320
BG = (255, 255, 255)
FG = (0, 0, 0)
COLS = (10, 172, 334)
VAL_X, VAL_R = 58, 112        # value box: from col+VAL_X to col+VAL_R (right-aligned)
TOP = [44, 71, 98, 125, 152]
BOT = [212, 239, 266, 293]
MID_SSD1 = [183, 210]
RAM_TEMP_Y = [98, 125]
MID_SSD2 = [268, 295]
HEAD = {'top': 27, 'mid': 166, 'bot': 193, 'mid2': 251}
VFONT = 'geforce/GeForce-Bold.ttf'
VSIZE = 19

bg = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(bg)
fh = ImageFont.truetype(os.path.join(RES, 'fonts', 'oswald', 'Oswald-SemiBold.ttf'), 25)
fl = ImageFont.truetype(os.path.join(RES, 'fonts', 'oswald', 'Oswald-Medium.ttf'), 18)
cb = fl.getbbox('H', anchor='ls'); cap = cb[3] - cb[1]

def head(text, col, y):
    d.text((COLS[col], y), text, font=fh, fill=FG, anchor='ls')

def label(text, x, cy, dr=None):
    (dr or d).text((x, round(cy + cap / 2)), text, font=fl, fill=FG, anchor='ls')

def box(col, cy, vr=VAL_R, vx=VAL_X, size=VSIZE):
    h = size + 4
    return {'SHOW': True, 'SHOW_UNIT': False, 'X': COLS[col] + vx, 'Y': cy - h // 2,
            'WIDTH': vr - vx, 'HEIGHT': h, 'ANCHOR': 'rm', 'FONT': VFONT, 'FONT_SIZE': size,
            'FONT_COLOR': '0, 0, 0', 'BACKGROUND_IMAGE': 'background.png'}

def row(col, cy, lab, unit, vr=VAL_R):
    label(lab, COLS[col], cy)
    label(unit, COLS[col] + vr + 6, cy)
    return box(col, cy, vr)

stats = {'CPU': {}, 'GPU': {'INTERVAL': 1}, 'MEMORY': {'INTERVAL': 2, 'VIRTUAL': {}}, 'DATE': {'INTERVAL': 1},
         'CUSTOM': {'INTERVAL': 2}}

# left column
head('CPU', 0, HEAD['top'])
stats['CPU']['TEMPERATURE'] = {'INTERVAL': 2, 'TEXT': row(0, TOP[0], 'temp:', '°C')}
stats['CPU']['FREQUENCY'] = {'INTERVAL': 2, 'TEXT': row(0, TOP[1], 'clock:', 'GHz')}
stats['CPU']['PERCENTAGE'] = {'INTERVAL': 1, 'TEXT': row(0, TOP[2], 'usage:', '%')}
stats['CUSTOM']['CpuFanRpm'] = {'TEXT': row(0, TOP[3], 'fan:', 'rpm')}
stats['CUSTOM']['CpuPower'] = {'TEXT': row(0, TOP[4], 'power:', 'W')}
head('GPU', 0, HEAD['bot'])
stats['GPU']['TEMPERATURE'] = {'TEXT': row(0, BOT[0], 'temp:', '°C')}
stats['GPU']['MEMORY_USED'] = {'TEXT': row(0, BOT[1], 'vram:', 'MB')}
stats['GPU']['PERCENTAGE'] = {'TEXT': row(0, BOT[2], 'usage:', '%')}
stats['CUSTOM']['GpuFanRpm'] = {'TEXT': row(0, BOT[3], 'fan:', 'rpm')}

# middle column
head('RAM', 1, HEAD['top'])
stats['MEMORY']['VIRTUAL']['USED'] = row(1, TOP[0], 'used:', 'MB')
stats['MEMORY']['VIRTUAL']['PERCENT_TEXT'] = row(1, TOP[1], 'usage:', '%')
stats['CUSTOM']['RamTemp1'] = {'TEXT': box(1, RAM_TEMP_Y[0])}   # labels on overlay_ramtemp.png
stats['CUSTOM']['RamTemp2'] = {'TEXT': box(1, RAM_TEMP_Y[1])}
head('SSD 1', 1, HEAD['mid'])
stats['CUSTOM']['Ssd1Temp'] = {'TEXT': row(1, MID_SSD1[0], 'temp:', '°C')}
stats['CUSTOM']['Ssd1Used'] = {'TEXT': row(1, MID_SSD1[1], 'usage:', '%')}
head('SSD 2', 1, HEAD['mid2'])
stats['CUSTOM']['Ssd2Temp'] = {'TEXT': row(1, MID_SSD2[0], 'temp:', '°C')}
stats['CUSTOM']['Ssd2Used'] = {'TEXT': row(1, MID_SSD2[1], 'usage:', '%')}

# right column
head('TIME', 2, HEAD['top'])
t = box(2, 57, vr=140, vx=0, size=40); t.update({'ANCHOR': 'lm', 'FORMAT': 'HH:mm'})
stats['DATE']['HOUR'] = {'TEXT': t}
dd = box(2, 91, vr=140, vx=0, size=22); dd.update({'ANCHOR': 'lm', 'FORMAT': 'dd.MM.yyyy'})
stats['DATE']['DAY'] = {'TEXT': dd}
# uptime rows under the date: since power on / since last restart
UP_Y = [115, 137]
for (cls, lab), y in zip((('UptimeOn', 'on:'), ('UptimeReboot', 'reboot:')), UP_Y):
    label(lab, COLS[2], y)
    stats['CUSTOM'][cls] = {'TEXT': box(2, y, vr=140, vx=50, size=18)}
# up to three user temperature sensors (optional rows); their labels are drawn by TuringScreen.exe
# at startup from config.yaml, positions are stored in extra_rows.json
EXTRA_Y = [186]
EXTRA_VR = 116
for i, y in enumerate(EXTRA_Y, 1):
    stats['CUSTOM']['ExtraTemp%d' % i] = {'TEXT': box(2, y, vr=EXTRA_VR, vx=50)}
head('NETWORK', 2, HEAD['mid2'])
stats['CUSTOM']['NetUp'] = {'TEXT': row(2, MID_SSD2[0], 'up:', 'MB/s', vr=98)}
stats['CUSTOM']['NetDown'] = {'TEXT': row(2, MID_SSD2[1], 'down:', 'MB/s', vr=98)}

for x in (COLS[1] - 10, COLS[2] - 10):
    d.line([(x, 10), (x, 310)], fill=(170, 170, 170), width=1)
# base background + transparent overlays with the labels of optional rows;
# TuringScreen.exe composes background.png from them according to config.yaml
bg.save(os.path.join(OUT, 'background_base.png'))
bg.save(os.path.join(OUT, 'background.png'))

def overlay(name, rows):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for text, x, y in rows:
        label(text, x, y, od)
    ov.save(os.path.join(OUT, name))

overlay('overlay_ramtemp.png', [r for i, y in enumerate(RAM_TEMP_Y, 1)
                                for r in (('temp %d:' % i, COLS[1], y), ('°C', COLS[1] + VAL_R + 6, y))])
import json
# label baseline = baseline of the value digits (GeForce font) so that label and number sit on one line
_vf = ImageFont.truetype(os.path.join(UPSTREAM_RES, 'fonts', 'geforce', 'GeForce-Bold.ttf'), VSIZE)
_vb = _vf.getbbox('0', anchor='lm')
json.dump({'font': 'fonts/oswald/Oswald-Medium.ttf', 'size': 18, 'color': list(FG),
           'rows': [{'label_x': COLS[2], 'unit_x': COLS[2] + EXTRA_VR + 6,
                     'baseline': round(y + _vb[3])} for y in EXTRA_Y]},
          open(os.path.join(OUT, 'extra_rows.json'), 'w'), indent=1)

# ---------- YAML (hand-written emitter, keeps key order and comments) ----------
def emit(o, ind=0):
    out = []
    for k, v in o.items():
        if isinstance(v, dict):
            out.append(' ' * ind + f'{k}:')
            out += emit(v, ind + 2)
        else:
            if isinstance(v, bool):
                v = 'True' if v else 'False'
            elif isinstance(v, str) and (':' in v or v.startswith(('d', 'H'))):
                v = f'"{v}"'
            out.append(' ' * ind + f'{k}: {v}')
    return out

head_txt = '''---
# Grid3_2SSD: three columns (CPU/GPU | RAM/SSD 1/SSD 2 | time/date/network) for Turing 3.5" (rev. A), landscape.
# Values marked as CUSTOM come from classes in library/sensors/sensors_custom.py (block "Grid3_2SSD").
author: "TuringScreen Grid3_2SSD"

display:
  DISPLAY_SIZE: 3.5"
  DISPLAY_ORIENTATION: landscape
  DISPLAY_RGB_LED: 0, 0, 255

static_images:
  BACKGROUND:
    PATH: background.png
    X: 0
    Y: 0
    WIDTH: 480
    HEIGHT: 320

'''
open(os.path.join(OUT, 'theme.yaml'), 'w', encoding='utf-8', newline='\n').write(
    head_txt + '\n'.join(emit({'STATS': stats})) + '\n')
print('ok')
