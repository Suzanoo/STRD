import numpy as np
from tools.section_modulus import hollow_rect

"""[] : web=C,NC, flange=C,NC,S --> Y,FLB,WLB"""


# 5.7 Tube
class Tube:
    def __init__(self, materials):
        self.Fy = materials.Fy  # MPa
        self.Es = materials.Es  # MPa

    """
    section = symmetry
    Mx or My
    web = C, NC
    flange = C, NC, S"""

    def yeild(self, section):
        øMp = 0.9 * self.Fy * section.Zx * 1e-3  # kN-m
        print(f"øMp : {øMp:.2f} kN-m")
        return øMp

    # flange local buckling
    def FLB(self, section, flange, Mp):
        if flange == "NC":
            FE = np.sqrt(self.Fy / self.Es)
            Sx, Sy = hollow_rect(section.b, section.h, section.t, section.t)  # cm3
            øMn = (
                0.9
                * (
                    Mp * 1e6
                    - (Mp * 1e6 - self.Fy * Sx * 1e3)
                    * (3.57 * (section.b / section.t) * FE - 4)
                )
                * 1e-6
            )
            print(f"NC-Flange : Flange lateral bulking, øMcr = {øMn:.2f} kN-m")
            return øMn

        elif flange == "S":
            be = (
                1.92 * section.t * FE * (1 - (0.38 / (section.b / section.t)) * FE)
            )  # mm
            Se, Sy = hollow_rect(be, section.h, section.t, section.t)  # cm3
            øMn = 0.9 * self.Fy * Se * 1e-3  # kN-m
            print(f"Slender-Flange : Flange lateral bulking, øMcr = {øMn:.2f} kN-m")
            return øMn

        else:
            print("No flange lateral bulking effect, use øMp")
            return 0.9 * Mp

    # web local buckling
    def WLB(self, section, web, Mp):
        if web == "NC":
            Sx, Sy = hollow_rect(section.b, section.h, section.t, section.t)  # cm3
            FE = np.sqrt(self.Fy / self.Es)
            øMn = (
                Mp * 1e6
                - (Mp * 1e6 - self.Fy * Sx * 1e3)
                * (0.305 * (section.h / section.t) * FE - 0.738)
            ) * 1e-6
            print(f"NC-Web : Web lateral bulking, øMcr = {øMn:.2f} kN-m")
            return øMn
        else:
            print("No web lateral bulking effect, use øMp")
            return 0.9 * Mp

    def call(self, section, flange, web, Mu):
        øMp = self.yeild(section)
        øMn1 = self.FLB(section, flange, øMp / 0.9)
        øMn2 = self.WLB(section, web, øMp / 0.9)

        øMn = min(øMp, øMn1, øMn2)

        if øMn > Mu:
            print(f"øMn = {øMn:.2f} kN > Mu {Mu:.2f} kN : SECTION OK")
        else:
            print(f"øMn = {øMn:.2f} kN < Mu {Mu:.2f} kN : INCORRECT SECTION")
