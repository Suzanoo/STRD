import numpy as np


"""
Failure moode:
Y : yeild
LTB : lateral-torsional bulking
FLB : flange lateral bulking
WLB : web lateral bulking
TFY : tension flange yeild
LLB : leg lateral bulking
LB : lateral bulking
C : compact section
NC : non-compact section
S : slender

Section :
H,C : x-x axis, web=C, flang=C --> Y, LTB
H : x-x axis, web=C, flang=NC,S --> Y, LTB, FLB
H,C : y-y axis, wec=C, flange=C --> Y
H,C : y-y axis, wec=C, flange=NC,S --> Y, FLB

H : web=NC --> Y, LTB, FLB, TFY
H : web=S, flange=C,NC,S --> Y, LTB, FLB, TFY
[] : web=C,NC, flange=C,NC,S --> Y, FLB, WLB
T, double-L : flange=C,NC,S -->Y, LTB ,FLB
L --> Y,LTB,LLB
O --> Y,LB
"""


def cb(Mmax, Ma, Mb, Mc):
    return 12.5 * Mmax / (2.5 * Mmax + 3 * Ma + 4 * Mb + 3 * Mc)


def calc_var(section, Fy, Es, Lb, Sxc, Iyc, Myc):
    Iy = section.Iy * 1e4  # mm4

    h0 = section.H - section.tf  # mm
    hc = section.H - 2 * section.tf  # mm
    h = section.H - 2 * section.tf  # mm
    d = section.H  # mm
    aw = hc * section.tw / (section.B * section.tf)
    rt = section.B / np.sqrt(12 * ((h0 / d) + (aw / 6) + (h * h / (h0 * d))))

    if Iyc / Iy <= 0.23:
        J = 0

    K1 = J / (Sxc * h0)
    K2 = (Lb / rt) ** 2

    FL = 0.7 * Fy
    Lp = 1.1 * rt * np.sqrt(Es / Fy)  # mm
    Lr = (
        1.95 * rt * (Es / (FL)) * np.sqrt(K1 + np.sqrt((K2) + 6.76 * (FL / Es) ** 2))
    )  # mm

    return Lp, Lr, FL, K1, K2


class Yeild:
    def __init__(self, materials):
        self.Fy = materials.Fy
        self.Es = materials.Es

    def major_axis(self, Zx):
        øMp = 0.9 * self.Fy * Zx * 1e-3  # kN-m
        print(f"Yeild : øMp = {øMp:.2f} kN-m")
        return øMp

    # 5.6.1 H, C : minor axis
    def minor_axis(self, Sy, Zy):
        øMpy = (
            0.9
            * (
                self.Fy * Zy
                if self.Fy * Zy < 1.6 * self.Fy * Sy
                else 1.6 * self.Fy * Sy
            )
            * 1e-3
        )  # kN-m
        print(f"Yeild : øMpy = {øMpy:.2f} kN-m")
        return øMpy

    # 5.4.1 H : Major axis : Yc for NC-web
    def nc_web_yc(self, Sxc, Rpc):
        øMn = 0.9 * Rpc * self.Fy * Sxc * 1e-3  # kN-m
        print(f"Flange : Compression yeild, øMn : {øMn:.2f} kN-m")
        return øMn

    # 5.4.1 Major axis : Yt for NC-web
    def nc_web_yt(self, Sxt, Rpt):
        øMn = 0.9 * Rpt * self.Fy * Sxt * 1e-3  # kN-m
        print(f"Flange : Tension yeild, øMn : {øMn:.2f} kN-m")
        return øMn

    # 5.5.1 H : Majoraxis : Slender web


# flange lateral bulking
class FLB:
    def __init__(self, materials):
        self.Fy = materials.Fy
        self.Es = materials.Es

    # 5.3.2 : H : Major axis, web=C, flang=NC,S --> Y, LTB, FLB
    def hc_major(self, section, Mp, λpf, λrf, flange="NC"):
        Mp = Mp * 1e6  # N-mm
        Sx = section.Sx * 1e3  # mm3

        λ = section.B / (2 * section.tf)

        if flange == "S":  # slender
            h = section.H - section.tf  # mm
            Kc = max(0.76, 4 / np.sqrt(h / section.tw))
            øMn = 0.9 * (0.9 * self.Es * Kc * Sx / (λ**2)) * 1e-6  # KN-m
        else:  # non-compact
            øMn = (
                0.9
                * (Mp - (Mp - 0.7 * self.Fy * Sx * np.abs((λ - λpf) / (λrf - λpf))))
                * 1e-6
            )

        print(f"Flange lateral bulking control, øMcr : {øMn:.2f} kN-m")
        return øMn

    # H,C : Minor axis, web=C, flange=NC,S --> Y, FLB
    def hc_minor(self, section, b, Mpy, λpf, λrf, flange="C"):
        Mpy = Mpy * 1e6  # N-mm
        Sy = section.Sy * 1e3  # mm3

        λ = b / (2 * section.tf)

        if flange == "NC":
            øMn = (
                0.9
                * (Mpy - (Mpy - 0.7 * self.Fy * Sy * np.abs((λ - λpf) / (λrf - λpf))))
                * 1e-6
            )  # kN-m

        elif flange == "S":
            Fcr = 0.69 * self.Es / (b / section.tf) ** 2  # N/mm2
            øMn = 0.9 * (Fcr * self.Fy) * 1e-6  # kN-m

        else:
            print("No Flange lateral bulking effect")
            return

        print(f"flange lateral bulking control, øMcr : {øMn:.2f} kN-m")
        return øMn

    # H : Major axis, NC-Web
    def nc_web(self, section, λpf, λrf, Sxc, Myc, Rpc, flange="NC"):

        Sxc = Sxc * 1e3  # mm3
        Myc = Myc * 1e6  # N-mm

        FL = 0.7 * self.Fy
        λ = section.B / (2 * section.tf)

        if flange == "NC":
            øMn = (
                0.9
                * (Rpc * Myc - (Rpc * Myc - FL * Sxc * np.abs((λ - λpf) / (λrf - λpf))))
                * 1e-6
            )  # kN-m
        elif flange == "S":
            h = section.H - section.tf  # mm
            Kc = max(0.76, 4 / np.sqrt(h / section.tw))
            øMn = 0.9 * (0.9 * self.Es * Kc * Sxc / (λ**2)) * 1e-6  # KN-m
        else:
            print("No Flange lateral bulking effect")
            return

        print(f"Flange lateral bulking control, øMcr : {øMn:.2f} kN-m")
        return øMn

    # TODO # 5.5.3 H : Majoraxis : Slender web


# lateral-torsional bulking
class LTB:
    def __init__(self, materials):
        self.Fy = materials.Fy
        self.Es = materials.Es

    # 5.2.2
    # H,C : x-x axis, web=C, flang=C --> Y, LTB
    # H : x-x axis, web=C, flang=NC,S --> Y, LTB, FLB
    def hc_major(self, section, Mp, Lb, Cb, J, Cw, channel=False):  # m, _unit in table
        Lb = Lb * 1e3  # mm
        ry = section.ry * 10  # mm
        Iy = section.Iy * 1e4  # mm4
        Sx = section.Sx * 1e3  # mm3

        h0 = section.H - section.tf  # mm
        rts = np.sqrt((np.sqrt(Iy * Cw)) / Sx)  # mm
        c = 1

        if channel == True:
            c = (h0 / 2) * np.sqrt(Iy / Cw)

        K1 = J * c / (Sx * h0)
        K2 = (Lb / rts) ** 2

        Lp = 1.76 * ry * np.sqrt(self.Es / self.Fy)  # mm
        Lr = (
            1.95
            * rts
            * (self.Es / (0.7 * self.Fy))
            * np.sqrt(K1 + np.sqrt((K1**2) + 6.76 * (0.7 * self.Fy / self.Es) ** 2))
        )  # mm

        if Lb < Lp:
            print("No lateral-torsional bulking effect")
        elif Lb > Lp and Lb < Lr:
            Mn = (
                Cb * (Mp - (Mp - 0.7 * self.Fy * Sx) * (Lb - Lp) / (Lr - Lp)) * 1e-6
            )  # kN-m
        else:  # Lb > Lr
            Fcr = (Cb * self.Es * np.pi**2) * (np.sqrt(1 + 0.078 * K1 * K2)) / K2  # MPa
            Mn = Fcr * Sx * 1e-6  # N-mm

        øMn = 0.9 * min(Mn, Mp)

        print(f"Lateral-torsional bulking control, øMcr : {øMn:.2f} kN-m")
        return øMn  # kN-m

    # 5.4.2
    # H : Major axis, NC-Web --> Yc, Yt, LTB, FLB, TFY
    def nc_web(self, section, Lb, Sxc, Iyc, Myc, Rpc, Cb=1):  # m, _unit in table
        Lb = Lb * 1e3  # mm
        Iyc = Iyc * 1e4  # mm
        Sxc = Sxc * 1e3  # mm3
        Myc = Myc * 1e6  # N-mm

        Lp, Lr, FL, K1, K2 = calc_var(section, self.Fy, self.Es, Lb, Sxc, Iyc, Myc)

        if Lb < Lp:
            print("No lateral-torsional bulking effect")  # N-mm
            return
        elif Lb > Lp and Lb < Lr:
            øMn = (
                0.9 * Cb * (Rpc * Myc - (Rpc * Myc - FL * Sxc) * (Lb - Lp) / (Lr - Lp))
            ) * 1e-6  # kN-m

        else:  # Lb > Lr

            Fcr = (Cb * self.Es * np.pi**2) * (np.sqrt(1 + 0.078 * K1 * K2)) / K2  # MPa
            øMn = 0.9 * Fcr * Sxc * 1e-6  # kN-m

        print(f"Lateral-torsional bulking control, øMcr : {øMn:.2f} kN-m")
        return øMn  # kN-m

    # 5.5.2 H : Majoraxis : Slender web
