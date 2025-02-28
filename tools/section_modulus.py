# https://www.omnicalculator.com/physics/section-modulus#section-modulus-formulas-for-a-rectangular-section-and-other-shapes
def hollow_rect(b, d, tf, tw):  # all in mm
    bi = b - 2 * tw
    di = d - 2 * tf

    yc = d / 2
    xc = b / 2
    Ix = (b * d**3 - bi * di**3) / 12
    Iy = (d * b**3 - di * bi**3) / 12

    Sx = Ix / yc
    Sy = Iy / xc

    return Sx * 1e-3, Sy * 1e-3  # cm3


def rectangle(b, h):
    yc = h / 2
    xc = b / 2
    Ix = (b * h**3) / 12
    Iy = (h * b**3) / 12
    Sx = Ix / yc
    Sy = Iy / xc
    return Sx * 1e-3, Sy * 1e-3  # cm3


def wf_equal(B, H, tw, tf):
    d = H - 2 * tf
    yc = H / 2
    xc = B / 2
    Ix = ((B * H**3) - (B - tw) * d**3) / 12
    Iy = ((2 * tf * B**3) + d * tw**3) / 12
    Sx = Ix / yc
    Sy = Iy / xc
    return Sx * 1e-3, Sy * 1e-3  # cm3
