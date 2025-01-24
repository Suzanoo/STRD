# rafterER DESIGN : CASE OVERHANG : LRFD METHOD
import sys
import os
import numpy as np

from tabulate import tabulate

from absl import app, flags
from absl.flags import FLAGS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.utils import section_generator

## FLAGS definition
flags.DEFINE_integer("Fu", 490, "ultimate strength, MPa")
flags.DEFINE_integer("Fy", 245, "yeild strength, MPa")
flags.DEFINE_float("Es", 2.04e6, "Youngs modulus, MPA")

flags.DEFINE_float("l", 0, "length, m")
flags.DEFINE_float("a", 1, "overhang length, m")
flags.DEFINE_float("s", 0, "rafter spacing, m")
flags.DEFINE_float("slope", 0, "roof slope, degree")

flags.DEFINE_float("self_wt", 10, "initial rafter weigth, kg/m")
flags.DEFINE_float("DL", 0, "Dead Load, kg/m2")
flags.DEFINE_float("Lr", 0, "Roof live load, kg/m2")
flags.DEFINE_float("WL", 0, "Wind load, kg/m2")

flags.DEFINE_string("section", "Light_Lip_Channel.csv", "rafter section")


# Load Case
def wu(DL, Lr, WL):
    case1 = DL + Lr  # SLS --> w
    case2 = 0.75 * (1.4 * DL + 1.7 * Lr) + 1.6 * WL
    case3 = 0.9 * DL + 1.6 * WL
    return case1, max(case1, case2, case3)  # kN/m2


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
    Fb = FLAGS.Fy
    𝜙Mn = 0.9 * Fb * Zx * 1e-3  # kN-m
    print(f"𝜙Mn = {𝜙Mn:.2f} kN-m, Mu = {Mu:.2f} kN-m")

    if 𝜙Mn >= Mu:
        print("Flexural Resistance OK")
    else:
        print("Flexural Resistance NOT OK")


def eff(Mu, Zx, Pu, A):
    Fb = 0.75 * FLAGS.Fy
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
    Δend = ((10**7) * w * a / (24 * FLAGS.Es * Ix)) * (4 * l * (a**2) - l**3 + 3 * a**3)

    print(f"L/200 = {l*100/200:.2f} cm, Δx = {Δx:.2f} cm, Δend = {Δend:.2f} cm")

    if (Δx < l * 100 / 200) & (Δend < l * 100 / 200):
        print("Deflection OK")
    else:
        print("Deflection NOT OK")


def shear(Vu, A, h, t):
    Fv = FLAGS.Fy
    # Vt = Vu/(A*1000)
    𝜙Vn = 0.9 * Fv * A / 10  # kN
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

    Pu = wux * (l + a)  # Axial force, kN

    R1, R2, Vuy = Vu(wuy, l, a)  # kN
    R1 = R1 / np.cos(np.radians(slope))  # Vertical force
    R2 = R2 / np.cos(np.radians(slope))  # Vertical force

    Muz = Mu(wuy, l, a)  # kN-m
    Zx = Muz * 1000 / (0.9 * FLAGS.Fy)  # cm^3

    return R1, R2, Pu, wy, wuy, Vuy, Muz, Zx


def check(Pu, wy, As, Muz, Vuy):
    flex(Muz, As.Zx)
    eff(Muz, As.Zx, Pu, As.A)
    print("--------------------------------------")

    # check defection
    delta(wy, FLAGS.l, FLAGS.a, As.Ix)  # With Brace
    print("--------------------------------------")

    # check shear
    shear(Vuy, As.A, As.h, As.t)

    # Slenderness in each axis
    print(f"\nSlenderness: ")
    while True:
        K = float(input("Define K: "))  # Kx or Ky
        L = float(input("Define L in m: "))  # Lx or Ly
        r = float(input("Define r in cm: "))  # rx or ry

        print(f"KL/r  = {K * L * 1e2 / r:.0f} : 240")

        ask = input("Finish ??? : Y|N : ").upper()
        if ask == "Y":
            break
        else:
            pass


def report(**kwargs):
    x = kwargs
    print("STEEL RAFTER DESIGN : LRFD Method : CASE OVERHANG")
    print(
        "================================================================================================================================"
    )
    print(
        f"MATERIAL PROPERTIES: \nSteel A36  \nFu = {FLAGS.Fu} MPa \nFy = {FLAGS.Fy} MPa \nEs = {FLAGS.Es} MPa"
    )
    print(
        f"\nLOAD CASE: \n1 = DL+Lr #SLS \n2 = 0.75*(1.4DL + 1.7Lr) +  1.6WL \n3 = 0.9DL + 1.6WL "
    )
    print(
        f"\nGEOMETRY: \nSpan = {x['L']} m \nOverhang = {x['a']} m \nrafter spacing = {x['s']} m \nslope  = {x['slope']} degree"
    )

    print(f"\nCALCULATION")
    print(
        f"DL = {x['DL']:.2f} kg/m2, Lr = {x['Lr']:.2f} kg/m2, WL = {x['WL']:.2f} kg/m2"
    )
    print(f"R1 = {x['R1']:.2f} kN, R2 = {x['R2']:.2f} kN")
    print(f"wuy = {x['wuy']:.2f} kN/m")
    print(f"Pu = {x['Pu']:.2f} kN")
    print(f"Vuy = {x['Vuy']:.2f} kN")
    print(f"Muz = {x['Muz']:.2f} kN-m")
    print(f"Zx required = {x['Zx']:.2f} cm3 ")


def design():
    l = FLAGS.l
    a = FLAGS.a
    s = FLAGS.s
    slope = FLAGS.slope

    # CALCULATION
    DL = FLAGS.DL * FLAGS.s * 0.0098 + FLAGS.self_wt * 0.0098  # kN/m
    Lr = FLAGS.Lr * FLAGS.s * 0.0098  # kN/m
    WL = FLAGS.WL * FLAGS.s * 0.0098  # kN/m

    R1, R2, Pu, wy, wuy, Vuy, Muz, Zx = cal(DL, Lr, WL, slope, l, a)

    context = {
        "L": l,
        "a": a,
        "s": s,
        "slope": slope,
        "DL": FLAGS.DL,
        "Lr": FLAGS.Lr,
        "WL": FLAGS.WL,
        "R1": R1,
        "R2": R2,
        "wuy": wuy,
        "Pu": Pu,
        "Vuy": Vuy,
        "Muz": Muz,
        "Zx": Zx,
    }

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
    % python app/rafter_lrfd.py --l=5 --s=1 --slope=30 --DL=65 --Lr=50 --WL=60

    use TUBE
    % python app/rafter_lrfd.py --l=6 --s=3 --slope=8 --DL=25 --Lr=50 --WL=60 --section=Rectangular_Tube.csv

    use Double-CCL
    % python app/rafter_lrfd.py --l=6 --s=3 --slope=16 --DL=25 --Lr=50 --WL=60 --section=Double_Light_Lip_Channel.csv
    % python app/rafter.py --l=6 --a=1.2 --s=3 --slope=8 --self_wt=12 --DL=25 --Lr=50 --WL=60 --section=Double_Light_Lip_Channel.csv

    another section please see csv file in sections folder
"""
