# rafter DESIGN : CASE OVERHANG : ASD METHOD
import os
import numpy as np
import pandas as pd

from tabulate import tabulate

from absl import app, flags, logging
from absl.flags import FLAGS

from tools.steel_section import section_generator

## FLAGS definition
flags.DEFINE_integer("FU", 490, "ultimate strength, MPa")
flags.DEFINE_integer("Fy", 245, "yeild strength, MPa")
flags.DEFINE_float("Es", 2.04e6, "Youngs modulus, MPA")

flags.DEFINE_float("l", 0, "length, m")
flags.DEFINE_float("a", 1, "overhang length, m")
flags.DEFINE_float("w", 0, "width of area load, m")
flags.DEFINE_float("b", 0, "length of area load, m")
flags.DEFINE_float("slope", 0, "roof slope, degree")

flags.DEFINE_float("hip", 14, "initial hip weigth, kg/m")
flags.DEFINE_float("DL", 0, "Dead Load, kg/m2")
flags.DEFINE_float("Lr", 0, "Roof live load, kg/m2")
flags.DEFINE_float("WL", 0, "Wind load, kg/m2")

flags.DEFINE_string("section", "Light_Lip_Channel.csv", "rafter section")


# Load Case
def wu(DL, Lr, WL):
    case1 = DL + Lr  # SLS --> w
    case2 = 1.4 * DL  # ULS --> wu
    case3 = 1.2 * DL + 0.5 * Lr  # ULS --> wu
    case4 = 1.2 * DL + 1.6 * Lr + 0.8 * WL  # ULS --> wu
    case5 = 1.2 * DL + 1.3 * WL + 0.5 * Lr  # ULS --> wu
    return case1, max(case1, case2, case3, case4, case5)  # kN/m2


# Method
def Vu(w, l, a):
    V1 = (0.5 * w / l) * (l * l - a * a)  # shear at left support
    V2 = w * a  # possitive shear at right support
    V3 = -(0.5 * w / l) * (l * l + a * a)  # negative shear at left support

    R1 = V1
    R2 = (0.5 * w / l) * (l + a) ** 2
    Vu = max(np.abs(V1), np.abs(V2), np.abs(V3))
    # print(f"V1 = {V1} kN, V2 = {V2} kN, V3 = {V3} kN")
    return R1, R2, Vu


def Mu(w, l, a):
    M1 = w * (l + a) * (l + a) * (l - a) * (l - a) / (8 * l * l)
    M2 = w * a * a / 2
    # print(f"M1 = {M1} N-m, M2 = {M2} N-m")
    return max(np.abs(M1), np.abs(M2))


def flex(Mu, Zx):
    Fb = 0.9 * FLAGS.Fy
    𝜙Mn = Fb * Zx / 1000  # kN-m
    print(f"𝜙Mn = {𝜙Mn:.2f} kN-m, Mu = {Mu:.2f} kN-m")

    if 𝜙Mn >= Mu:
        print("Flexural Resistance OK")
    else:
        print("Flexural Resistance NOT OK")


def eff(Mu, Zx, Pu, A):
    Fb = 0.9 * FLAGS.Fy
    eff_ = (Mu * 100 / Zx) / Fb + (Pu * 1e-2 / A) / Fb

    print("--------------------------------------")
    if eff_ < 1:
        print(f"Interaction Combine = {eff_:.2f} < 1 : Section OK")
    else:
        print(f"Interaction Combine = {eff_:.2f} > 1 : Incorrect Section")


def delta(w, l, a, Ix):
    x = 0.5 * l * (1 - (a**2) / (l**2))
    Δx = ((10**7) * w * x / (24 * FLAGS.Es * l * Ix)) * (
        l**4
        - 2 * (l**2) * (x**2)
        + l * (x**3)
        - 2 * (a**2) * (l**2)
        + 2 * (a**2) * x**2
    )
    Δend = ((10**7) * w * a / (24 * FLAGS.Es * Ix)) * (
        4 * l * (a**2) - l**3 + 3 * a**3
    )

    print(f"L/200 = {l*100/200:.2f} cm, Δx = {Δx:.2f} cm, Δend = {Δend:.2f} cm")

    if (Δx < l * 100 / 200) & (Δend < l * 100 / 200):
        print("Deflection OK")
    else:
        print("Deflection NOT OK")


def shear(Vu, A, h, t):
    Fv = 0.75 * FLAGS.Fy
    # Vt = Vu/(A*1000)
    𝜙Vn = Fv * A / 10  # kN
    # σv = Vu*10/A #Mpa
    print(f"𝜙Vn = {𝜙Vn:.2f} kN, Vu = {Vu:.2f} kN")

    if 𝜙Vn > Vu:
        print("Shear Resistance OK ")
    else:
        print("Shear Resistance NOT OK ")


def cal(DL, Lr, WL, slope, l, a):
    wx, wux = wu(
        DL * np.sin(np.radians(slope)),
        Lr * np.sin(np.radians(slope)),
        WL * np.cos(np.radians(slope)),
    )  # kN/m
    wy, wuy = wu(
        DL * np.cos(np.radians(slope)),
        Lr * np.cos(np.radians(slope)),
        WL * np.sin(np.radians(slope)),
    )  # kN/m

    Pn = wx * (l + a)  # Axial force, kN
    Pu = wux * (l + a)  # Axial force, kN

    R1, R2, Vuy = Vu(wuy, l, a)  # kN
    Muz = Mu(wuy, l, a)  # kN-m
    Zx = Muz * 1000 / (0.9 * FLAGS.Fy)  # cm^3

    return R1, R2, Pn, Pu, wy, wuy, Vuy, Muz, Zx


def check(Pu, wy, As, Muz, Vuy):
    flex(Muz, As.Zx)
    eff(Muz, As.Zx, Pu, As.A)
    print("--------------------------------------")

    # check defection
    delta(wy, FLAGS.l, FLAGS.a, As.Ix)  # With Brace
    print("--------------------------------------")

    # check shear
    shear(Vuy, As.A, As.h, As.t)


def report(**kwargs):
    x = kwargs
    print("STEEL HIP DESIGN : LRFD Method : CASE OVERHANG")
    print(
        "================================================================================================================================"
    )
    print(
        f"MATERIAL PROPERTIES: \nSteel A36  \nFu = {FLAGS.FU} MPa \nFy = {FLAGS.Fy} MPa \nEs = {FLAGS.Es} MPa"
    )
    print(
        f"\nLOAD CASE: \n1 = DL+Lr #SLS \n2 = 1.4DL \n3 = 1.2DL+0.5Lr \n4 = 1.2DL+1.6Lr+0.8WL \n5 = 1.2DL+1.3WL+0.5Lr"
    )
    print(
        f"\nGEOMETRY: \nSpan = {x['L']} m \nOverhang = {x['a']} m \nslope  = {x['slope']} degree"
    )

    print(f"\nCALCULATION")
    print(f"DL = {x['DL']:.2f} kN/m, Lr = {x['Lr']:.2f} kN/m, WL = {x['WL']:.2f} kN/m")
    print(f"R1 = {x['R1']:.2f} kN, R2 = {x['R2']:.2f} kN")
    print(f"wuy = {x['wuy']:.2f} kN/m")
    print(f"Vuy = {x['Vuy']:.2f} kN")
    print(f"Muz = {x['Muz']:.2f} kN-m")
    print(f"Zx required = {x['Zx']:.2f} cm3 ")


def design():
    l = FLAGS.l
    a = FLAGS.a
    w = FLAGS.w
    b = FLAGS.b
    slope = FLAGS.slope

    # CALCULATION
    DL = ((FLAGS.DL * w * b / l) + FLAGS.hip) * 0.0098  # kN/m
    Lr = (FLAGS.Lr * w * b / l) * 0.0098  # kN/m
    WL = (FLAGS.WL * w * b / l) * 0.0098  # kN/m

    R1, R2, Pn, Pu, wy, wuy, Vuy, Muz, Zx = cal(DL, Lr, WL, slope, l, a)

    context = {
        "L": l,
        "a": a,
        "slope": slope,
        "DL": DL,
        "Lr": Lr,
        "WL": WL,
        "R1": R1,
        "R2": R2,
        "wuy": wuy,
        "Vuy": Vuy,
        "Muz": Muz,
        "Zx": Zx,
    }

    # CURR = os.getcwd()

    # from PIL import Image

    # img = Image.open(os.path.join(CURR, "images", "beam_overhang.png"))
    # img.show()

    report(**context)

    #  Create dataframe of selected secction
    df = section_generator(FLAGS.section)

    df_filter = df[(df["Zx"] > Zx)]
    print(f"\nSection Table")
    print(
        tabulate(
            df_filter.sort_values(by=["Zx"])[:20],
            headers=df_filter.columns,
            floatfmt=".2f",
            showindex=True,
            tablefmt="psql",
        )
    )

    # ======================
    # DESIGN
    print(f"\nDESIGN")
    i = int(input("SELECT SECTION : "))
    As = df.iloc[i]
    print(
        tabulate(
            df.filter(items=[i], axis=0),
            headers=df.columns,
            floatfmt=".2f",
            showindex=True,
            tablefmt="psql",
        )
    )

    check(Pu, wy, As, Muz, Vuy)


def main(_args):
    design()


if __name__ == "__main__":
    app.run(main)

"""
How to used?
-Please see FLAGS definition for unit informations
-Make sure you are in the project directory run python in terminal(Mac) or command line(Windows)
-run script
    % cd <path to project directory>
    % conda activate <your conda env name>

    use CCL (CCL is default section --> don't provide section flag)
    % python app/hip.py --l=3.5  --slope=15 --DL=79 --Lr=30 --WL=50 --w=6--b=6

    use TUBE
    % python app/hip.py --l=3.5  --slope=23 --DL=94 --Lr=30 --WL=50 --w=6.9 --b=3.9 --section=Rectangular_Tube.csv

    use Double-CCL
    % python app/hip.py --l=6 --slope=30 --DL=80 --Lr=30 --WL=50 --w=6 --b=6 --section=Double_Light_Lip_Channel.csv

    another section please see csv file in sections folder
"""
