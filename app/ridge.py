# RIDGE DESIGN : CASE OVERHANG : ASD METHOD
# Use reaction from rafter become load to ridge
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
flags.DEFINE_float("a", 0, "overhang length, m")

flags.DEFINE_float("ridge", 15, "initial ridge weigth, kg/m")
flags.DEFINE_float("Wu", 0, "Line load generated from rafter reaction, kg/m")

flags.DEFINE_string("section", "Light_Lip_Channel.csv", "ridge section")  # default


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
    Fv = 0.4 * FLAGS.Fy
    # Vt = Vu/(A*1000)
    𝜙Vn = Fv * A / 10  # kN
    # σv = Vu*10/A #Mpa
    print(f"𝜙Vn = {𝜙Vn:.2f} kN, Vu = {Vu:.2f} kN")

    if 𝜙Vn > Vu:
        print("Shear Resistance OK ")
    else:
        print("Shear Resistance NOT OK ")


def cal(Wu, l, a):
    R1, R2, Vuy = Vu(Wu, l, a)  # kN
    Muz = Mu(Wu, l, a)  # kN-m
    Zx = Muz * 1000 / (0.9 * FLAGS.Fy)  # cm^3

    return R1, R2, Vuy, Muz, Zx


def check(Pu, Wu, As, Muz, Vuy):
    flex(Muz, As.Zx)
    eff(Muz, As.Zx, Pu, As.A)
    print("--------------------------------------")

    # check defection
    delta(Wu, FLAGS.l, FLAGS.a, As.Ix)  # With Brace
    print("--------------------------------------")

    # check shear
    shear(Vuy, As.A, As.h, As.t)


def report(**kwargs):
    x = kwargs
    print("STEEL RIDGE DESIGN : LRFD Method")
    print(
        "================================================================================================================================"
    )
    print(
        f"MATERIAL PROPERTIES: \nSteel A36  \nFu = {FLAGS.FU} MPa \nFy = {FLAGS.Fy} MPa \nEs = {FLAGS.Es} MPa"
    )
    print(
        f"\nLOAD CASE: \n1 = DL+Lr #SLS \n2 = 1.4DL \n3 = 1.2DL+0.5Lr \n4 = 1.2DL+1.6Lr+0.8WL \n5 = 1.2DL+1.3WL+0.5Lr"
    )
    print(f"\nGEOMETRY: \nSpan = {x['L']} m \nOverhang = {x['a']} m ")

    print(f"\nCALCULATION")
    print(f"Wu = {x['Wu']:.2f} kN/m")
    print(f"R1 = {x['R1']:.2f} kN, R2 = {x['R2']:.2f} kN")
    print(f"Vuy = {x['Vuy']:.2f} kN")
    print(f"Muz = {x['Muz']:.2f} kN-m")
    print(f"Zx required = {x['Zx']:.2f} cm3 ")


def design():
    l = FLAGS.l
    a = FLAGS.a

    # CALCULATION
    Wu = FLAGS.Wu  # kN/m

    R1, R2, Vuy, Muz, Zx = cal(Wu, l, a)

    context = {
        "L": l,
        "a": a,
        "Wu": Wu,
        "R1": R1,
        "R2": R2,
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

    # Filter by Zx, Zy
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

    check(0, Wu, As, Muz, Vuy)


def main(_args):
    design()


if __name__ == "__main__":
    app.run(main)

"""
How to used?
- Please see FLAGS definition for unit informations
- 
- run script
    % cd <path to project directory>
    % conda activate <your conda env name>

    use CCL (CCL is default section --> don't provide section flag)
    % python app/ridge.py --l=6 --Wu=8

    use TUBE
    % python app/ridge.py --l=3 --Wu=4.48 --section=Rectangular_Tube.csv

    use Double-CCL
    % python app/ridge.py --l=6 --Wu=8 --section=Double_Light_Lip_Channel.csv

    another section please see csv file in sections folder
"""
