PX = 56
VB_W = 1020
VB_H = 316
HALF = VB_W / 2
PERM_COUNT = 8
PED_COUNT = 5
Y1 = 30
Y2 = 108
Y3 = 186
Y4 = 264

VIEWBOX = '0 0 %s %s' % (VB_W, VB_H)
MIDLINE_X = int(HALF)

_MID_GAP = PX / 2

_PERM_LEFT_X = HALF - _MID_GAP
_PERM_RIGHT_X = HALF + _MID_GAP
_PED_LEFT_X = HALF - _MID_GAP
_PED_RIGHT_X = HALF + _MID_GAP

TOOTH_POSITIONS = {}
# Left blocks are mirrored: the innermost tooth is the last entry of the list.
for i, n in enumerate([18, 17, 16, 15, 14, 13, 12, 11]):
    TOOTH_POSITIONS[n] = (int(_PERM_LEFT_X - (PERM_COUNT - 1 - i) * PX), Y2)
for i, n in enumerate([21, 22, 23, 24, 25, 26, 27, 28]):
    TOOTH_POSITIONS[n] = (int(_PERM_RIGHT_X + i * PX), Y2)
for i, n in enumerate([48, 47, 46, 45, 44, 43, 42, 41]):
    TOOTH_POSITIONS[n] = (int(_PERM_LEFT_X - (PERM_COUNT - 1 - i) * PX), Y3)
for i, n in enumerate([31, 32, 33, 34, 35, 36, 37, 38]):
    TOOTH_POSITIONS[n] = (int(_PERM_RIGHT_X + i * PX), Y3)
for i, n in enumerate([55, 54, 53, 52, 51]):
    TOOTH_POSITIONS[n] = (int(_PED_LEFT_X - (PED_COUNT - 1 - i) * PX), Y1)
for i, n in enumerate([61, 62, 63, 64, 65]):
    TOOTH_POSITIONS[n] = (int(_PED_RIGHT_X + i * PX), Y1)
for i, n in enumerate([85, 84, 83, 82, 81]):
    TOOTH_POSITIONS[n] = (int(_PED_LEFT_X - (PED_COUNT - 1 - i) * PX), Y4)
for i, n in enumerate([71, 72, 73, 74, 75]):
    TOOTH_POSITIONS[n] = (int(_PED_RIGHT_X + i * PX), Y4)

FDI_NUMBERS = [
    55, 54, 53, 52, 51, 61, 62, 63, 64, 65,
    18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28,
    48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38,
    85, 84, 83, 82, 81, 71, 72, 73, 74, 75,
]

SURFACES = ['T', 'B', 'L', 'R', 'C']

SURFACE_PATHS = {
    'C': 'M0,-7 A7,7 0 1,1 0,7 A7,7 0 1,1 0,-7 Z',
    'T': 'M-11.31,-11.31 A16,16 0 0,1 11.31,-11.31 L4.95,-4.95 A7,7 0 0,0 -4.95,-4.95 Z',
    'R': 'M11.31,-11.31 A16,16 0 0,1 11.31,11.31 L4.95,4.95 A7,7 0 0,0 4.95,-4.95 Z',
    'B': 'M11.31,11.31 A16,16 0 0,1 -11.31,11.31 L-4.95,4.95 A7,7 0 0,0 4.95,4.95 Z',
    'L': 'M-11.31,11.31 A16,16 0 0,1 -11.31,-11.31 L-4.95,-4.95 A7,7 0 0,0 -4.95,4.95 Z',
}


def build_chart(patient):
    """Return a server-side renderable odontogram for the given dental.patient.

    Mirrors the backend OWL widget (tooth_layout.js + odontogram.xml) but in
    pure read-only structures: per-tooth surface lists with prebuilt path + color.
    """
    conditions_map = {}
    legend = {}
    teeth = []

    teeth_by_number = {}
    for tooth in patient.tooth_ids.sudo():
        teeth_by_number[tooth.tooth_number.strip()] = tooth

    for num in FDI_NUMBERS:
        tn = str(num)
        tooth = teeth_by_number.get(tn)
        surfaces = []
        if tooth:
            surf_by_code = {}
            for srf in tooth.surface_ids.sorted('date', reverse=True):
                if srf.surface not in surf_by_code:
                    surf_by_code[srf.surface] = srf
            for s in SURFACES:
                srf = surf_by_code.get(s)
                cond = srf.condition if srf else None
                color = cond.color if cond else '#fff'
                if cond:
                    legend[cond.code] = {
                        'color': color,
                        'label': cond.name,
                        'code': cond.code,
                    }
                surfaces.append({'path': SURFACE_PATHS[s], 'color': color})
        else:
            for s in SURFACES:
                surfaces.append({'path': SURFACE_PATHS[s], 'color': '#fff'})

        x, y = TOOTH_POSITIONS.get(num, (0, 0))
        teeth.append({
            'number': tn,
            'x': x,
            'y': y,
            'transform': 'translate(%s,%s)' % (x, y),
            'surfaces': surfaces,
        })

    legend_items = sorted(legend.values(), key=lambda item: item['label'].lower())

    return {
        'teeth': teeth,
        'legend': legend_items,
        'viewbox': VIEWBOX,
        'midline_x': MIDLINE_X,
        'viewbox_height': VB_H,
    }