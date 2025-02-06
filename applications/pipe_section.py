"""
ø  --> Y, LB
DN,D,t,W,A,I,Z,i
"""


# 5.8
class Pipe:
    def __init__(self, materials, øb=0.9):
        self.Fy = materials.Fy  # MPa
        self.Es = materials.Es  # MPa
        self.øb = øb

    # YT
    def yeild(self, section):
        øMp = 0.9 * self.Fy * section.Z * 1e-3  # kN-m
        print(f"Yeild, øMp : {øMp:.2f} kN-m")
        return øMp

    # local buckling
    def LB(self, section, flange, Mp):
        if flange == "NC":
            øMn = (
                self.øb
                * section.Z
                * (self.Fy + 0.021 * self.Es / (section.D / section.t))
                * 1e-6
            )  # kN-m
            print(f"Local bulking, øMcr = {øMn:.2f} kN-m")
            return øMn
        elif flange == "S":
            Fcr = 0.33 * self.Es / (section.D / section.t)
            øMn = self.øb * Fcr * section.Z * 1e-3  # kN-m
            print(f"Local bulking, øMcr = {øMn:.2f} kN-m")
            return øMn
        else:
            print("No local bulking effect")
            return self.øb * Mp

    def call(self, section, flange, Mu):
        øMp = self.yeild(section)
        øMn = self.LB(section, flange, øMp / self.øb)
        øMn = min(øMp, øMn)

        if øMn > Mu:
            print(f"øMn = {øMn:.2f} kN > Mu {Mu:.2f} kN : SECTION OK")
        else:
            print(f"øMn = {øMn:.2f} kN < Mu {Mu:.2f} kN : INCORRECT SECTION")

        return øMn
