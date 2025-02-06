import numpy as np


class H:
    def __init__(self, materials):
        self.Fy = materials.Fy
        self.Es = materials.Es

    def torsion(self, section):  # mm, mm, mm, mm, cm44, cm4
        h0 = section.H - section.tf
        Ix = section.Ix * 1e4
        Iy = section.Iy * 1e4
        J = (1 / 3) * (2 * section.B * (section.tf**3) + h0 * section.tw**3)  # mm4
        Cw = (Iy * h0**2) / 4  # mm6
        Ips = Ix + Iy
        return J, Cw

    # Web plastification factor
    def Rpc(self, section, λpw, λrw):
        Zx = section.Zx * 1e3  # mm3
        Iy = section.Iy * 1e4  # mm4

        Sxc = (
            (1 / 12) * (section.B * section.tf**3)
            + section.tf * section.B * (section.H / 2) ** 2
        ) / (section.H / 2)

        Iyc = section.tf * (section.B**3)

        hc = section.H - 2 * section.tf  # mm
        λ = hc / section.tw

        Mp = (
            self.Fy * Zx if self.Fy * Zx < 1.6 * self.Fy * Sxc else 1.6 * self.Fy * Sxc
        )  # N-mm
        Myc = self.Fy * Sxc  # N-mm

        if Iyc / Iy > 0.23:
            Rpc = (
                Mp / Myc
                if hc / section.tw <= λpw
                else Mp / Myc - ((Mp / Myc - 1) * np.abs((λ - λpw) / (λrw - λpw)))
            )
            Rpc = min(Rpc, Mp / Myc)
        else:
            Rpc = 1

        return Rpc, Sxc * 1e-3, Iyc * 1e-8, Myc * 1e-6  # -, cm3, cm4, kN-m

    def Rpt(self, section, λpw, λrw):
        Zx = section.Zx * 1e3  # mm3
        Iy = section.Iy * 1e4  # mm4

        Sxt = (
            (1 / 12) * (section.B * section.tf**3)
            + section.tf * section.B * (section.H / 2) ** 2
        ) / (section.H / 2)

        Iyt = section.tf * (section.B**3)

        hc = section.H - 2 * section.tf  # mm
        λ = hc / section.tw

        Mp = (
            self.Fy * Zx if self.Fy * Zx < 1.6 * self.Fy * Sxt else 1.6 * self.Fy * Sxt
        )  # N-mm

        Myt = self.Fy * Sxt  # N-mm

        Rpc = (
            Mp / Myt
            if hc / section.tw <= λpw
            else Mp / Myt - ((Mp / Myt - 1) * np.abs((λ - λpw) / (λrw - λpw)))
        )
        Rpc = min(Rpc, Mp / Myt)

        return Rpc, Sxt * 1e-3, Iyt * 1e-8, Myt * 1e-6  # -, cm3, cm4, kN-m


class CHN:
    # HxB,H,B,tf,tw,r1,r2,A,Wt,Cx,Cy,Ix,Iy,rx,ry,Zx,Zy
    def __init__(self, materials):
        self.Fy = materials.Fy
        self.Es = materials.Es

    def torsion_chn(self, section):
        b = section.B
        h = section.H
        tf = section.tf
        tw = section.tw
        J = (1 / 3) * (2 * b * (tf**3) + h * tw**3)  # mm4
        q = (3 * b * tf + 2 * h * tw) / (6 * b * tf + h * tw)
        Cw = q * tf * (b**3) * (h**2) / 12
        return J, Cw

    def section_modulus(self, section):
        b = section.B
        h = section.H
        tw = section.tw
        tf = section.tf

        Ix = ((b * h**3) - (b - tw) * (h - 2 * tf) ** 3) / 12
        Iy = ((2 * tf * b**3) + tw * h**3) / 12
        Sx = Ix / (h / 2) * 1e-3  # cm3
        Sy = Iy / (b / 2) * 1e-3  # cm3
        return Sx, Sy


class Box:
    def __init__(self, materials):
        self.Fy = materials.Fy
        self.Es = materials.Es
        # h,b,t,Wt,A,Ix,Iy,Zx,Zy,rx,ry

    def effective_width(self, b, tf):
        return (
            1.92
            * tf
            * np.sqrt(self.Es / self.Fy)
            * (1 - (0.38 / (b / tf)) * np.sqrt(self.Es / self.Fy))
        )

    def section_modulus(self, b, d, tw, tf):  # all in mm
        bi = b - 2 * tw
        di = d - 2 * tf

        yc = d / 2
        xc = b / 2
        Ix = (b * d**3 - bi * di**3) / 12
        Iy = (d * b**3 - di * bi**3) / 12

        Sx = Ix / yc
        Sy = Iy / xc

        return Sx * 1e-3, Sy * 1e-3  # cm3
