import numpy as np

from tools import width_thickness_ratio as wt
from tools import torsion_props as tor
from tools.section_modulus import hollow_rect

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

H : web=C,NC, flang=C,NC,S --> Y, LTB, FLB, TFY
H : web=S, flange=C,NC,S --> Y, LTB, FLB, TFY
[] : web=C,NC, flange=C,NC,S --> Y,FLB,WLB
T, double-L : flange=C,NC,S -->Y,LTB,FLB
L --> Y,LTB,LLB
O --> Y,LB
"""


def cb(Mmax, Ma, Mb, Mc):
    return 12.5 * Mmax / (2.5 * Mmax + 3 * Ma + 4 * Mb + 3 * Mc)


# ==============================
## WF, H, CHN
# ==============================
class WF_CHN:
    def __init__(self, Fy, Es):
        self.Fy = Fy  # MPa
        self.Es = Es  # MPa

    def h_section_definition(self, section):
        self.H = section["H"]
        self.B = section["B"]
        self.tw = section["tw"]
        self.tf = section["tf"]
        self.A = section["A"]
        self.Ix = section["Ix"]
        self.Iy = section["Iy"]
        self.rx = section["rx"]
        self.ry = section["ry"]
        self.Sx = section["Sx"]
        self.Sy = section["Sy"]
        self.Zx = section["Zx"]
        self.Zy = section["Zy"]

        T = tor.Torsion
        self.J, self.Cw = T.torsion_h(
            self.B, self.H, self.tf, self.tw, self.Ix, self.Iy
        )  # mm4, mm6

    def chn_definition(self, section):
        # ['H', 'B', 'tf', 'tw', 'r1', 'r2', 'A', 'Wt', 'Cx', 'Cy', 'Ix', 'Iy', 'rx', 'ry', 'Zx', 'Zy']
        self.H = section["H"]
        self.B = section["B"]
        self.tw = section["tw"]
        self.tf = section["tf"]
        self.A = section["A"]
        self.Ix = section["Ix"]
        self.Iy = section["Iy"]
        self.rx = section["rx"]
        self.ry = section["ry"]
        self.Sx = section["Zx"]
        self.Sy = section["Zy"]
        self.Zx = section["Zx"]
        self.Zy = section["Zy"]

        T = tor.Torsion
        self.J, self.Cw = T.torsion_chn(self.B, self.H, self.tf, self.tw)  # mm4, mm6

    # ==============================
    # H,C : x-x axis, web=C, flang=C --> Y, LTB
    # H : x-x axis, web=C, flang=NC,S --> Y, LTB, FLB
    # for major axis
    def yeild(self):
        self.Mp = self.Fy * self.Zx * 1e-3  # kN-m
        print(f"plastic moment, øMp : {0.9*self.Mp:.2f} kN-m")

    # LTB for major axis
    def ltb(self, Lb, c, Cb):  # m, _unit in table
        Lb = Lb * 1e3  # mm
        ry = self.ry * 10  # mm
        Iy = self.Iy * 1e4  # mm4
        Sx = self.Sx * 1e3  # mm3

        Lp = 1.76 * ry * np.sqrt(self.Es / self.Fy)  # mm

        h0 = self.H - self.tf  # mm
        K = self.J * c / (Sx * h0)
        rts = np.sqrt((np.sqrt(Iy * self.Cw)) / Sx)  # mm
        Lr = (
            1.95
            * rts
            * (self.Es / (0.7 * self.Fy))
            * np.sqrt(K + np.sqrt((K**2) + 6.76 * (0.7 * self.Fy / self.Es) ** 2))
        )  # mm
        Cb = Cb
        Mp = self.Mp * 1e6  # N-mm

        if Lb < Lp:
            Mn = Mp  # N-mm
        elif Lb > Lp and Lb < Lr:
            Mn = Cb * (Mp - (Mp - 0.7 * self.Fy * Sx) * (Lb - Lp) / (Lr - Lp))  # N-mm
        else:  # Lb > Lr
            R = (Lb / rts) ** 2
            Fcr = (Cb * self.Es * np.pi**2) * (np.sqrt(1 + 0.0078 * K * R)) / R  # MPa
            Mn = Fcr * Sx  # N-mm

        øMn = 0.9 * Mn * 1e-6 if Mn < Mp else 0.9 * Mp * 1e-6  # kN-m
        print(f"lateral-torsional bulking, øMcr : {øMn:.2f} kN-m")
        return øMn  # kN-m

    # FLB for major axis
    def flb(self, flange="NC"):
        Sx = self.Sx * 1e3  # mm3
        R = wt.WT_flexural(self.Fy, self.Es)
        λpf, λrf, λpw, λrw = R.h_section(self.B, self.H, self.tf, self.tw)
        λ = self.B / (4 * self.tf)
        if flange == "NC":  # non-compact
            Mp = self.Mp * 1e6  # N-mm
            Mn = Mp - (Mp - 0.7 * self.Fy * Sx * np.abs((λ - λpf) / (λrf - λpf)))
        if flange == "S":  # slender
            h = self.H - self.tf
            Kc = max(0.35, 4 / np.sqrt(h / self.tw))
            Mn = 0.9 * self.Es * Kc * Sx / (λ**2)
        øMn = 0.9 * Mn * 1e-6  # KN-m
        print(f"flange lateral bulking, øMcr : {øMn:.2f} kN-m")
        return øMn

    # --------------------------------
    # H,C : y-y axis, wec=C, flange=C --> Y
    # H,C : y-y axis, wec=C, flange=NC,S --> Y, FLB

    # for minor axis
    def yeild_minor(self):
        Sy = self.Sy * 1e3  # mm3
        Zy = self.Zy * 1e3  # mm3

        Mpy = self.Fy * Zy  # N-mm
        self.Mpy = Mpy if Mpy < 1.6 * self.Fy * Sy else 1.6 * self.Fy * Sy  # N-mm
        print(f"plastic moment, øMpy : {0.9*self.Mpy*1e-6:.2f} kN-m")

    # for minor axis
    def flb_minor(self, flange="C"):
        Sy = self.Sy * 1e3  # mm3
        R = wt.WT_flexural(self.Fy, self.Es)
        λpf, λrf, λpw, λrw = R.h_section(self.B, self.H, self.tf, self.tw)
        λ = self.B / (4 * self.tf)

        if flange == "C":
            Mn = self.Mpy  # N-mm
        if flange == "NC":
            Mn = self.Mpy - (
                self.Mpy - 0.7 * self.Fy * Sy * np.abs((λ - λpf) / (λrf - λpf))
            )  # N-mm
        if flange == "S":
            Fcr = 0.69 * self.Es / (self.B / 2 / self.tf) ** 2  # N/mm2
            Mn = Fcr * self.Fy  # N-mm
        øMn = 0.9 * Mn * 1e-6  # kN-m
        print(f"flange lateral bulking : minor axis, øMcr : {øMn:.2f} kN-m")
        return øMn

    # --------------------------------
    # TODO
    """
    # H : web=C,NC, flang=C,NC,S --> Yc, Yt, LTB, FLB, TFY
    # 5.4.1 Yc for NC-web : for major axis
    def flange_compression_yeild(self):
        Zx = self.Zx*1e3 # mm3
        Iy = self.Iy*1e4 # mm4
        R = wt.WT_flexural(self.Fy, self.Es)
        λpf, λrf, λpw, λrw = R.h_section(self.B, self.H, self.tf, self.tw)
        λ = hc/self.tw

        Cb = Cb
        self.Mp = self.Fy*Zx if self.Fy*Zx < 1.6*self.Fy*Sxc else 1.6*self.Fy*Sxc # N-mm
        self.Myc = self.Fy*Sxc # N-mm

        if Iyc/Iy > 0.23:
            Rpc = self.Mp/self.Myc if hc/self.tw <= λpw else self.Mp/self.Myc - ((self.Mp/self.Myc -1)*np.abs((λ-λpw)/(λrw - λpw))) # N-mm
            self.Rpc = np.min(Rpc, self.Mp/self.Myc)
        else:
            self.Rpc = 1

        Mn = self.Rpc*self.Fy*Sxc*1e-3 # kN-m
        print(f"flange yeid, øMn : {0.9*Mn} kN-m")

    # 5.4.2 LTB for NC-web
    def ltb_nc(self, Lb, Cb): # m, _unit in table
        Lb = Lb*1e3 # mm
        ry = ry*10 # mm
        Iy = Iy*1e4 # mm4
        Sx = Sx*1e3 # mm3

        bfc = self.B
        tfc = self.tf
        h0 = self.H - self.tf # mm
        h = self.H - self.tf
        d = self.H
        aw = hc*self.tw/(bfc*tfc)
        rt = bfc/np.sqrt(12*((h0/d)+(aw/6)*(h*h/(h0*d))))

        Lp = 1.1*rt*np.sqrt(self.Es/self.Fy) # mm

        FL = 0.70*self.Fy if Sxt/Sxc >= 0.7 else self.Fy*Sxt/Sxc
        FL = np.max([FL, 0.5*Fy])

        J = 0 if Iyc/Iy <= 0.23 else self.J
        K = J/(Sxc*h0)        
        Lr = 1.95*rt*(self.Es/FL)*np.sqrt(K + np.sqrt((K**2) + 6.76*(FL/self.Es)**2)) # mm

        if Lb < Lp:
            Mn = self.Mp
        elif Lb > Lp and Lb < Lr:
            Mn = Cb*(self.Rpc*self.Myc-(self.Rpc*self.Myc - FL*Sxc)*(Lb-Lp)/(Lr-Lp))
        else: # Lb > Lr
            R = (Lb/rt)**2
            Fcr = (Cb*self.Es*np.pi**2)*(np.sqrt(1 + 0.078*K*R))/R # MPa
            Mn = Fcr*Sx 
        øMn = 0.9*Mn*1e-6 if Mn < self.Rpc*self.Myc else 0.9*self.Rpc*self.Myc*1e-6      
        print(f"lateral-torsional bulking for NC-web, øMcr : {øMn:.2f} kN-m")
        return øMn # kN-m 
    """

    # TODO
    # FLB for NC-web
    # TODO
    # Yt for NC-web

    # --------------------------------
    def call(self, Mu, label, Lb, c=1, Cb=1, flange="C"):
        """
        5.2.label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
        5.3.label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB
        5.6.label = 3 : minor axis, H, C : web=C, flang=NC,S --> Y, LTB
        5.4.lebel = 4 : NC-web, H : web=C,NC, flang=C,NC,S --> Yc, Yt, LTB, FLB, TFY
        """
        # major axis
        # H,C : web=C, flang=C --> Y, LTB
        if label == 1:
            self.yeild()
            øMn = self.ltb(Lb, c, Cb)  # default Cb=1

        if label == 2:
            # major axis
            # H : web=C, flang=NC,S --> Y, LTB
            self.yeild()
            øMn1 = self.ltb(Lb, c, Cb)  # default Cb=1
            øMn2 = self.flb(flange=flange)
            øMn = min(øMn1, øMn2)

        # minor axis
        # H, C : web=C, flang=NC,S --> Y, LTB
        if label == 3:
            self.yeild_minor()
            øMn = self.flb_minor(flange=flange)

        # NC-web
        # H : web=C,NC, flang=C,NC,S --> Yc, Yt, LTB, FLB, TFY
        if label == 4:
            self.flange_compression_yeild()
            øMn = self.ltb_nc(Lb, Cb)

        print(f"øMn = {øMn:.2f} kN, Mu = {Mu:.2f} kN")

        if øMn > Mu:
            print(f"øMn > Mu: SECTION OK")
            print()
        else:
            print("INCORRECT SECTION")
            print()
        return øMn


# ==============================
## TUBE
# ==============================
"""[] : web=C,NC, flange=C,NC,S --> Y,FLB,WLB"""


class Tube:
    def __init__(self, Fy, Es):
        self.Fy = Fy  # MPa
        self.Es = Es  # MPa

    # h,b,t,Wt,A,Ix,Iy,Zx,Zy,rx,ry
    def tube_definition(self, section):
        self.H = section["h"]
        self.B = section["b"]
        self.tw = section["t"]
        self.tf = section["t"]
        self.A = section["A"]
        self.Ix = section["Ix"]
        self.Iy = section["Iy"]
        self.rx = section["rx"]
        self.ry = section["ry"]
        self.Zx = section["Zx"]
        self.Zy = section["Zy"]

    """
    section = symmetry
    Mx or My
    web = C, NC
    flange = C, NC, S"""

    def yeild(self):
        self.Mp = self.Fy * self.Zx * 1e-3  # kN-m
        print(f"plastic moment, øMp : {0.9*self.Mp:.2f} kN-m")

    # flange local buckling
    def FLB(self, flange):
        if flange == "NC":
            FE = np.sqrt(self.Fy / self.E)
            øMn = (
                self.Mp * 1e6
                - (self.Mp * 1e6 - self.Fy * self.Zx * 1e3)
                * (3.57 * (self.B / self.tf) * FE - 4)
            ) * 1e-6
            return øMn

        elif flange == "S":
            be = 1.92 * self.tf * FE * (1 - (0.38 / (self.B / self.tf)) * FE)  # mm
            Se, Sy = hollow_rect(be, self.H, self.tf, self.tw)  # cm3
            øMn = 0.9 * self.Fy * Se * 1e-3  # kN-m
            return øMn

        else:
            return 0.9 * self.Mp

    # web local buckling
    def WLB(self, web):
        if web == "NC":
            FE = np.sqrt(self.Fy / self.E)
            øMn = (
                self.Mp * 1e6
                - (self.Mp * 1e6 - self.Fy * self.Zx * 1e3)
                * (0.305 * (self.H / self.tw) * FE - 4)
            ) * 1e-6
            return øMn
        else:
            return 0.9 * self.Mp

    def call(self, flange, web, Mu):
        self.yeild()
        øMn1 = self.FLB(flange)
        øMn2 = self.WLB(web)
        øMn = min(0.9 * self.Mp, øMn1, øMn2)

        if øMn > Mu:
            print(f"øMn = {øMn:.2f} kN > Mu {Mu:.2f} kN : SECTION OK")
            print()
        else:
            print("INCORRECT SECTION")
            print()

        return øMn


# ==============================
## PIPE
# ==============================
"""ø  --> Y, LB"""


class Pipe:
    def __init__(self, Fy, Es, øb):
        self.Fy = Fy  # MPa
        self.Es = Es  # MPa
        self.øb = øb

    # ['D','T','W','A','I','Zx','i']
    def pipe_definition(self, section):
        self.D = section["D"]
        self.t = section["T"]
        self.W = section["W"]
        self.A = section["A"]
        self.Ix = section["I"]
        self.Iy = section["I"]
        self.rx = section["i"]
        self.ry = section["i"]
        self.Zx = section["Zx"]
        self.Zy = section["Zx"]

    # YT
    def yeild(self):
        self.Mp = self.Fy * self.Zx * 1e-3  # kN-m
        print(f"plastic moment, øMp : {0.9*self.Mp:.2f} kN-m")

    # local buckling
    def LB(self, flange):
        if flange == "NC":
            øMn = (
                self.øb
                * self.Zx
                * (self.Fy + 0.021 * self.Es / (self.D / self.t))
                * 1e-6
            )  # kN-m
            return øMn
        elif flange == "S":
            Fcr = 0.33 * self.Es / (self.D / self.t)
            øMn = self.øb * Fcr * self.Zx * 1e-3  # kN-m
            return øMn
        else:
            return self.øb * self.Mp

    def call(self, flange, Mu):
        self.yeild()
        øMn1 = self.LB(flange)

        øMn = min(self.øb * self.Mp, øMn1)
        print(f"øMn = {øMn:.2f}")

        if øMn > Mu:
            print(f"øMn > Mu: SECTION OK")
            print()
        else:
            print("INCORRECT SECTION")
            print()

        return øMn
