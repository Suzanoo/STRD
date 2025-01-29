import numpy as np


# width_thickness ratio given by compression
class WT_compression:
    def __init__(self, Fy, Es):
        self.Fy = Fy
        self.Es = Es
        print(f"Width-Thickness ratio given by compression : ")

    def h_section(self, B, H, tf, tw):  # mm
        # NominalSize mm.,Wt.,H,B,tw,tf,r,A,Ix,Iy,rx,ry,Sx,Sy,Zx,Zy
        # flange
        bf = B / 2
        λrf = 0.56 * np.sqrt(self.Es / self.Fy)
        print("flange = compact") if bf / tf < λrf else print(
            "flange = non-compact/slender"
        )

        # web
        h = H - 2 * tf
        λrw = 1.49 * np.sqrt(self.Es / self.Fy)
        print("web = compact") if h / tw < λrw else print("web = non-compact/slender")

    def channels(self, B, H, tf, tw):  # mm
        # 'H', 'B', 't1', 't2', 'r1', 'r2', 'A', 'Wt', 'Cx', 'Cy', 'Ix', 'Iy', 'ix', 'iy', 'Zx', 'Zy'
        # flange
        bf = B
        λrf = 0.56 * np.sqrt(self.Es / self.Fy)
        print("flange = compact") if bf / tf < λrf else print(
            "flange = non-compact/slender"
        )

        # web
        h = H - 2 * tf
        λrw = 1.49 * np.sqrt(self.Es / self.Fy)
        print("web = compact") if h / tw < λrw else print("web = non-compact/slender")

    def tube(self, b, t):
        # h,b,t,Wt,A,Ix,Iy,Zx,Zy,ix,iy
        λr = 1.4 * np.sqrt(self.Es / self.Fy)
        print("section = compact") if (b - 2 * t) / t < λr else print(
            "section = non-compact/slender"
        )

    def pipe(self, D, t):
        λr = 0.11 * np.sqrt(self.Es / self.Fy)
        print("section = compact") if D / t < λr else print("section = non-compact/slender")

    def angle(self, x, t):
        # AxB,x,t,r1,r2,A,wt,Cx,Cy,Ix,Iy,ix,iy,rx,ry,ru,rv,Zx,Zy
        λr = 0.45 * np.sqrt(self.Es / self.Fy)
        print("section = compact") if x / t < λr else print("section = non-compact/slender")


# ----------------------------------------------------------------
# width_thickness ratio given by flexural
class WT_flexural:
    def __init__(self, Fy, Es):
        self.Fy = Fy
        self.Es = Es
        print(f"Width-Thickness ratio given by flexural : ")

    def h_section(self, B, H, tf, tw):  # mm
        # flange
        bf = B / 2
        λpf = 0.38 * np.sqrt(self.Es / self.Fy)
        λrf = np.sqrt(self.Es / self.Fy)

        print("flange = compact") if bf / tf < λpf else (
            print("flange = non-compact") if bf / tf < λrf else print("flange = slender")
        )

        # web
        h = H - 2 * tf
        λpw = 3.76 * np.sqrt(self.Es / self.Fy)
        λrw = 5.70 * np.sqrt(self.Es / self.Fy)

        print("web = compact") if h / tw < λpw else (
            print("web = non-compact") if h / tw < λrw else print("web = slender")
        )

        return λpf, λrf, λpw, λrw

    def channels(self, B, H, tf, tw):  # mm
        # flange
        bf = B
        λpf = 0.38 * np.sqrt(self.Es / self.Fy)
        λrf = np.sqrt(self.Es / self.Fy)

        print("flange = compact") if bf / tf < λpf else (
            print("flange = non-compact") if bf / tf < λrf else print("flange = slender")
        )

        # web
        h = H - 2 * tf
        λpw = 3.76 * np.sqrt(self.Es / self.Fy)
        λrw = 5.70 * np.sqrt(self.Es / self.Fy)

        print("web = compact") if h / tw < λpw else (
            print("web = non-compact") if h / tw < λrw else print("web = slender")
        )

        return λpf, λrf, λpw, λrw

    def tube(self, b, h, tw, tf):
        # h,b,t,Wt,A,Ix,Iy,Zx,Zy,ix,iy
        λp = 1.12 * np.sqrt(self.Es / self.Fy)
        λr = 1.40 * np.sqrt(self.Es / self.Fy)

        # flange
        print("flange = compact") if (b - 2 * tf) / tf < λp else (
            print("flange = non-compact")
            if (b - 2 * tf) / tf < λr
            else print("flange = slender")
        )

        # web
        print("web = compact") if (h - 2 * tw) / tw < λp else (
            print("web = non-compact") if (h - 2 * tw) / tw < λr else print("web = slender")
        )

    def pipe(self, D, t):
        # 'D','T','W','A','I','Zx','i'
        λp = 0.07 * np.sqrt(self.Es / self.Fy)
        λr = 0.31 * np.sqrt(self.Es / self.Fy)

        print("Compact section") if D / t < λp else (
            print("Non-compact section") if D / t < λr else print("Slender section")
        )

    def angle(self, x, t):
        # AxB,x,t,r1,r2,A,wt,Cx,Cy,Ix,Iy,ix,iy,rx,ry,ru,rv,Zx,Zy
        λp = 0.54 * np.sqrt(self.Es / self.Fy)
        λr = 0.91 * np.sqrt(self.Es / self.Fy)

        print("Compact section") if x / t < λp else (
            print("Non-compact section") if x / t < λr else print("Slender section")
        )
