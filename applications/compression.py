import numpy as np


class Compression:
    """
    FB = flexural control
    TB : torsion control
    FTB : flexural-torsional control
    """

    def __init__(self, materials, øc=0.65):
        self.Fy = materials.Fy
        self.Es = materials.Es
        self.øc = øc

    def eff_length(self, K, Lb, r, limit):
        d = np.floor(K * Lb * 100 / r)  # KL/r
        (
            print(f"KL/r = {d:.2f} < {limit} : OK")
            if d < limit
            else print(f"KL/r = {d:.2f} > {limit} : Slender")
        )
        return d

    # 4.4 flexural control
    def flexural_control(self, d):
        Fe = (np.pi**2) * self.Es / d**2  # Mpa
        λc = np.sqrt(self.Fy / Fe)

        a = 4.71 * np.sqrt(self.Es / self.Fy)
        b = self.Fy / Fe

        # Elastic Failure
        if d > a or b <= 2.25:
            Fcr = min(0.877 * Fe, self.Fy)  # Mpa

        # Inelastic Failure
        else:
            Fcr = self.Fy * 0.658 ** (λc**2)  # Mpa

        print(f"Flexural control, Fcr : {Fcr:.2f} MPa")

        return Fcr

    # 4.5
    def flexural_torsional_control(self, Fcry, Fcrz, H):
        Fft = Fcry + Fcrz
        Fcryz = (1 / 2 * H) * Fft * (1 - (1 - (4 * Fcry * Fcrz * H / Fft**2)))
        print(f"Flexural-Torsional control, Fcr : {Fcryz:.2f} MPa")

    # TODO
    def slender_section(self):
        pass

    def call(self, label, K, Lb, r, A, Pu, limit):
        """
        C = compact
        NC = non-compact
        S = slender
        label = 1 : C, NC --> 'H', '[]', 'O', 'composit H'
        label = 2 : C, NC --> 'CHN', 'T'
        label = 3 : C, NC -->  'L'
        label = 4 : S --> 'H', 'CHN', '[]', 'O',
        label = 5 : S --> 'L', 'T'
        """

        # 'H', '[]', 'O', 'composit H'
        if label == 1:
            d = self.eff_length(K, Lb, r, limit)
            Fcr = self.flexural_control(d)  # Mpa

        # 'CHN', 'T'
        if label == 2:
            d = self.eff_length(K, Lb, r, limit)
            Fcr = self.flexural_control(d)  # Mpa

            # TODO
            # Fcrz = self.flexural_torsional_control()
            # self.Fcr = np.min[Fcrx, Fcrz]

        # 'L'
        if label == 3:
            if Lb / r < 80:
                d = np.floor(72 + 0.75 * (Lb / r))

            if (Lb / r > 80) and (Lb / r < 200):
                d = np.floor(32 + 1.25 * (Lb / r))

            (
                print(f"KL/r = {d:.2f} < {limit} : OK")
                if d < limit
                else print(f"KL/r = {d:.2f} > {limit} : Slender")
            )
            Fcr = self.flexural_control(d)  # Mpa

        # 'H', 'CHN', '[]', 'O', --> Slender
        if label == 4:
            d = self.eff_length(K, Lb, r, limit)
            Fcr = self.flexural_control(d)  # Mpa

        # TODO
        # non-compact section --> L, |
        # if self.label == 2:
        # Fcr = Fcr*Q

        øPn = self.øc * Fcr * A / 10  # kN
        print(f"øPn = {øPn:.2f} kN, Pu = {Pu:.2f} kN")

        if øPn > Pu:
            print(f"øPn > Pu: SECTION OK")
            print()
        else:
            print("INCORRECT SECTION")
            print()
        return øPn
