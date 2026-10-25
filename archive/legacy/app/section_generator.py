class MaterialProperties:
    def __init__(self, Fy, Es):
        self.Fy = Fy  # MPa
        self.Es = Es  # Elastic modulus (MPa)

    def __str__(self):
        return f"Materials:  Fy: {self.Fy}, Es: {self.Es} mPa"


class Loads:
    def __init__(self, Pu=0, Mux=0, Muy=0) -> None:
        self.Pu = Pu
        self.Mux = Mux
        self.Muy = Muy
