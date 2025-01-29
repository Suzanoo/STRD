import numpy as np


class Compression:
    def __init__(self, Fy, Es, øc):
        self.Fy = Fy
        self.Es = Es
        self.øc = øc

    def eff_length(self):
        self.d = np.floor(self.K * self.Lb * 100 / self.r)  # KL/r
        (
            print(f"KL/r = {self.d:.2f} < {self.limit} : OK")
            if self.d < self.limit
            else print(f"KL/r = {self.d:.2f} > {self.limit} : Slender")
        )

    """
    FB = flexural control
    TB : torsion control
    FTB : flexural-torsional control
    """

    # 4.4 flexural control
    def flexural_control(self):
        Fe = (np.pi**2) * self.Es / self.d**2  # Mpa
        λc = np.sqrt(self.Fy / Fe)

        # Elastic Failure
        if λc > 1.5:
            Fcr = 0.877 * self.Fy / λc**2  # Mpa

        # Inelastic Failure
        else:
            Fcr = self.Fy * 0.658 ** (λc**2)  # Mpa

        print(f"Flexural control, Fcr : {Fcr:.2f} MPa")

        return Fcr

    # TODO
    def torsional_control(self):
        pass

    # TODO
    def flexural_torsional_control(self):
        pass

    # TODO
    def slender_section(self):
        pass

    def call(self, label, K, Lb, r, A, Pu, limit=300):
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
        self.K = K
        self.Lb = Lb
        self.r = r
        self.A = A
        self.limit = limit

        # C, NC : 'H', '[]', 'O', 'composit H'
        if label == 1:
            self.eff_length()
            self.Fcr = self.flexural_control()  # -, m, m, cm, cm

        # C, NC --> 'CHN', 'T'
        if label == 2:
            self.eff_length()
            self.Fcr = self.flexural_control()  # -, m, m, cm, cm

            # TODO
            # Fcrz = self.flexural_torsional_control()
            # self.Fcr = np.min[Fcrx, Fcrz]

        # label = 3 : C, NC -->  'L'
        if label == 3:
            if self.Lb / self.r < 80:
                self.d = np.floor(72 + 0.75 * (self.Lb / self.r))

            if (self.Lb / self.r > 80) and (self.Lb / self.r < 200):
                self.d = np.floor(32 + 1.25 * (self.Lb / self.r))

            (
                print(f"KL/r = {self.d:.2f} < {self.limit} : OK")
                if self.d < self.limit
                else print(f"KL/r = {self.d:.2f} > {self.limit} : Slender")
            )
            self.Fcr = self.flexural_control()  # -, m, m, cm, cm

        # TODO: modify this
        # label = 4 : S --> 'H', 'CHN', '[]', 'O',
        if label == 4:
            self.eff_length()
            self.Fcr = self.flexural_control()  # -, m, m, cm, cm

        # TODO
        # non-compact section --> L, |
        # if self.label == 2:
        # Fcr = Fcr*Q

        øPn = self.øc * self.Fcr * self.A / 10  # kN
        print(f"øPn = {øPn:.2f} kN, Pu = {Pu:.2f} kN")

        if øPn > Pu:
            print(f"øPn > Pu: SECTION OK")
            print()
        else:
            print("INCORRECT SECTION")
            print()
        return øPn
