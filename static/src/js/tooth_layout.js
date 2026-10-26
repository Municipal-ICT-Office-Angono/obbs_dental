/** @odoo-module **/

export const SURFACES = ['T', 'B', 'L', 'R', 'C'];

// Surface numbering used by the DOH oral health forms:
//   1 Buccal | 2 Lingual | 3 Distal | 4 Mesial | 5 Occlusal | 6 Incisal | 7 Labial
// The sector labels depend on the arch (upper/lower) and on whether the tooth is
// an anterior (incisor or canine) or a posterior (premolar or molar) tooth.
const SURFACE_INFO = {
    upper: {
        posterior: { T: [1, 'Buccal'], B: [2, 'Lingual'], L: [3, 'Distal'], R: [4, 'Mesial'], C: [5, 'Occlusal'] },
        anterior: { T: [7, 'Labial'], B: [2, 'Lingual'], L: [3, 'Distal'], R: [4, 'Mesial'], C: [6, 'Incisal'] },
    },
    lower: {
        posterior: { T: [2, 'Lingual'], B: [1, 'Buccal'], L: [3, 'Distal'], R: [4, 'Mesial'], C: [5, 'Occlusal'] },
        anterior: { T: [2, 'Lingual'], B: [7, 'Labial'], L: [3, 'Distal'], R: [4, 'Mesial'], C: [6, 'Incisal'] },
    },
};

/**
 * Return the numbered anatomical label of a surface sector for a given tooth.
 * e.g. getSurfaceInfo(12, 'C') -> { num: 6, name: 'Incisal', label: '6 — Incisal' }
 */
export function getSurfaceInfo(toothNumber, slot) {
    const n = Number(toothNumber);
    if (!n || !slot) {
        return null;
    }
    const quadrant = Math.floor(n / 10);
    const isUpper = quadrant === 1 || quadrant === 2 || quadrant === 5 || quadrant === 6;
    // Primary canines (53/63/73/83) are anterior just like their permanent peers.
    const isAnterior = (n % 10) <= 3;
    const entry = SURFACE_INFO[isUpper ? 'upper' : 'lower'][isAnterior ? 'anterior' : 'posterior'][slot];
    if (!entry) {
        return null;
    }
    let [num, name] = entry;
    // The right half of the chart is mirrored: mesial is on the left, distal on the right.
    const mirrored = quadrant === 2 || quadrant === 3 || quadrant === 6 || quadrant === 7;
    if (mirrored && (slot === 'L' || slot === 'R')) {
        num = slot === 'L' ? 4 : 3;
        name = slot === 'L' ? 'Mesial' : 'Distal';
    }
    return { num, name, label: `${num} — ${name}` };
}

const PX = 56;
const VB_W = 1020;
const VB_H = 316;
const HALF = VB_W / 2;
const PERM_COUNT = 8;
const PED_COUNT = 5;
const Y1 = 30;
const Y2 = 108;
const Y3 = 186;
const Y4 = 264;

// The arch is laid out symmetrically about the midline: the innermost tooth of
// every quadrant sits half a tooth-spacing away from MIDLINE_X and the rest fan
// outward. This keeps 18/28 (and 48/38) equidistant from the centre so nothing
// is pushed off the printed page.
const MID_GAP = PX / 2;

const permLeftX = HALF - MID_GAP;
const permRightX = HALF + MID_GAP;

const pedLeftX = HALF - MID_GAP;
const pedRightX = HALF + MID_GAP;

export const VIEWBOX = `0 0 ${VB_W} ${VB_H}`;
export const MIDLINE_X = HALF;

export const TOOTH_POSITIONS = (() => {
    const pos = {};

    function set(n, x, y) {
        pos[n] = { x, y };
    }

    // Left blocks are mirrored: the innermost tooth is the last entry of the array.
    [18, 17, 16, 15, 14, 13, 12, 11].forEach((n, i) => set(n, permLeftX - (PERM_COUNT - 1 - i) * PX, Y2));
    [21, 22, 23, 24, 25, 26, 27, 28].forEach((n, i) => set(n, permRightX + i * PX, Y2));

    [48, 47, 46, 45, 44, 43, 42, 41].forEach((n, i) => set(n, permLeftX - (PERM_COUNT - 1 - i) * PX, Y3));
    [31, 32, 33, 34, 35, 36, 37, 38].forEach((n, i) => set(n, permRightX + i * PX, Y3));

    [55, 54, 53, 52, 51].forEach((n, i) => set(n, pedLeftX - (PED_COUNT - 1 - i) * PX, Y1));
    [61, 62, 63, 64, 65].forEach((n, i) => set(n, pedRightX + i * PX, Y1));

    [85, 84, 83, 82, 81].forEach((n, i) => set(n, pedLeftX - (PED_COUNT - 1 - i) * PX, Y4));
    [71, 72, 73, 74, 75].forEach((n, i) => set(n, pedRightX + i * PX, Y4));

    return pos;
})();

export const FDI_NUMBERS = [
    55, 54, 53, 52, 51, 61, 62, 63, 64, 65,
    18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28,
    48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38,
    85, 84, 83, 82, 81, 71, 72, 73, 74, 75,
];

export const SURFACE_PATHS = {
    C: 'M0,-7 A7,7 0 1,1 0,7 A7,7 0 1,1 0,-7 Z',
    T: 'M-11.31,-11.31 A16,16 0 0,1 11.31,-11.31 L4.95,-4.95 A7,7 0 0,0 -4.95,-4.95 Z',
    R: 'M11.31,-11.31 A16,16 0 0,1 11.31,11.31 L4.95,4.95 A7,7 0 0,0 4.95,-4.95 Z',
    B: 'M11.31,11.31 A16,16 0 0,1 -11.31,11.31 L-4.95,4.95 A7,7 0 0,0 4.95,4.95 Z',
    L: 'M-11.31,11.31 A16,16 0 0,1 -11.31,-11.31 L-4.95,-4.95 A7,7 0 0,0 -4.95,4.95 Z',
};

export const SURFACE_BBOX = {
    C: [-7, -7, 7, 7],
    T: [-11.31, -11.31, 11.31, 0],
    R: [0, -11.31, 11.31, 11.31],
    B: [-11.31, 0, 11.31, 11.31],
    L: [-11.31, -11.31, 0, 11.31],
};

export function getToothType(toothNumber) {
    const n = +toothNumber;
    if (n >= 51 && n <= 85) return 'pediatric';
    return 'permanent';
}

export function isUpper(toothNumber) {
    const n = +toothNumber;
    return (n >= 11 && n <= 28) || (n >= 51 && n <= 65);
}

export function getToothPosition(toothNumber) {
    return TOOTH_POSITIONS[+toothNumber] || { x: 0, y: 0 };
}

export function hitTestSurface(localX, localY) {
    const dist = Math.sqrt(localX * localX + localY * localY);
    if (dist > 16) return null;
    if (dist <= 7) return 'C';

    const angle = Math.atan2(localY, localX) * 180 / Math.PI;
    if (angle > -135 && angle < -45) return 'T';
    if (angle > -45 && angle < 45) return 'R';
    if (angle > 45 && angle < 135) return 'B';
    return 'L';
}
