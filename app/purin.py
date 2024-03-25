## ASD

import os
import numpy as np

from tabulate import tabulate

from absl import app, flags, logging
from absl.flags import FLAGS

from tools.steel_section import section_generator

## FLAGS definition
flags.DEFINE_integer("FU", 4000, "ultimate strength, ksc")
flags.DEFINE_integer("Fy", 2520, "yeild strength, ksc")
flags.DEFINE_float("Es", 2.04e6, "Youngs modulus, ksc")

flags.DEFINE_float("L", 0, "length, m")
flags.DEFINE_float("s", 0, "purin spacing, m")
flags.DEFINE_float("slope", 0, "roof slope, degree")

flags.DEFINE_float("purin", 5.5, "initial purin weigth, kg/m")
flags.DEFINE_float("DL", 0, "Dead Load, kg/m2")
flags.DEFINE_float("Lr", 0, "Roof live load, kg/m2")
flags.DEFINE_float("WL", 0, "Wind load, kg/m2")

flags.DEFINE_string("section", "Light_Lip_Channel.csv", "purin section")


def wu(DL, Lr, WL):
    case1 = DL + Lr  # SLS
    case2 = DL + WL

    return max(case1, case2)


def Mu(Wux, Wuy):
    Mux = (1 / 8) * Wuy * FLAGS.L**2  # kg-m
    Muy = (1 / 8) * Wux * FLAGS.L**2  # kg-m
    print(f"")

    return Mux, Muy


def flex(Mux, Muy, Zx, Zy):
    Fbx = 0.6 * FLAGS.Fy  # ksc
    Fby = 0.75 * FLAGS.Fy  # ksc
    𝜙Mnx = Fbx * Zx / 100  # kg-m
    𝜙Mny = Fby * Zy / 100  # kg-m

    if 𝜙Mnx > 𝜙Mny:
        𝜙Mn = 𝜙Mnx
        Mu = Mux
        print(f"𝜙Mn = {𝜙Mn:.2f} kN-m, Mu = {Mu:.2f} kN-m")
        if 𝜙Mn >= Mu:
            print("Flexural Resistance OK")
        else:
            print("Flexural Resistance NOT OK")
    else:
        𝜙Mn = 𝜙Mny
        Mu = Muy
        print(f"𝜙Mn = {𝜙Mn:.2f} kN-m, Mu = {Mu:.2f} kN-m")
        if 𝜙Mn >= Mu:
            print("Flexural Resistance OK")
        else:
            print("Flexural Resistance NOT OK")


def eff(Mux, Muy, Zx, Zy):
    Fbx = 0.6 * FLAGS.Fy  # ksc
    Fby = 0.75 * FLAGS.Fy  # ksc

    eff = (Mux * 100 / Zx) / Fbx + (Muy * 100 / Zy) / Fby

    if eff < 1:
        print(f"Interaction Combine = {eff:.2f} < 1 : Section OK")
    else:
        print(f"Interaction Combine= {eff:.2f} > 1 : Incorrect Section")


def deflection(Wux, Wuy, Ix, Iy):
    d = 200
    dx = 5 * (Wux / 100) * ((FLAGS.L * 100) ** 4) / (384 * FLAGS.Es * Iy)
    dy = 5 * (Wuy / 100) * ((FLAGS.L * 100) ** 4) / (384 * FLAGS.Es * Ix)

    print(f"L/{d} = {FLAGS.L*100/d:.2f} cm \ndx = {dx:.2f} cm \ndy = {dy:.2f} cm")

    if (dx < FLAGS.L * 100 / d) & (dy < FLAGS.L * 100 / d):
        print("Deflection OK")
    else:
        print("Deflection NOT OK")


def shear(Wuy, A, H, T):
    Fv = 0.4 * FLAGS.Fy  # ksc
    Vu = 0.5 * Wuy * FLAGS.L  # kg
    𝜙Vnt = Fv * A  # kg
    𝜙Vnh = Fv * H * T / 100  # kg

    print(f"Vu = {Vu:.2f} kg \n𝜙Vnt = {𝜙Vnt:.2f} ksc \n𝜙Vnh = {𝜙Vnh:.2f} ksc")

    if (Vu < 𝜙Vnt) & (Vu < 𝜙Vnh):
        print("Shear Resistance OK ")
    else:
        print("Shear Resistance Not OK ")


def report(**kwargs):
    x = kwargs
    print("STEEL PURIN DESIGN : ASD Method")
    print(
        "================================================================================================================================"
    )
    print(
        f"MATERIAL PROPERTIES: \nSteel A36  \nFu = 5000 ksc \nFy = 2520 ksc \nEs = 2.04x10^6 ksc"
    )
    print(f"\nLOAD CASE: \n1 = DL + Lr  \n2 = DL + WL")
    print(
        f"\nGEOMETRY: \nRafter spacing = {x['L']} m \nPurin spacing = {x['s']} m \nSlope  = {x['slope']} degree"
    )

    print(f"\nCALCULATION")
    print(f"DL = {x['DL']:.2f} kg/m, Lr = {x['Lr']:.2f} kg/m, WL = {x['WL']:.2f} kg/m")
    print(f"Wux = {x['Wux']:.2f} kg/m, Wuy = {x['Wuy']:.2f} kg/m")
    print(f"Mux = {x['Mux']:.2f} kg-m, Muy = {x['Muy']:.2f} kg-m")
    print(f"Zx required = {x['Zx']:.2f} cm3 , Zy required = {x['Zy']:.2f} cm3 ")


# ------------------------------------------------------------------------
def design():
    CURR = os.getcwd()

    # Capture input
    Fy = FLAGS.Fy
    slope = FLAGS.slope
    s = FLAGS.s
    L = FLAGS.L

    purin = FLAGS.purin  # kg/m
    DL = FLAGS.DL  # kg/m2
    Lr = FLAGS.Lr  # kg/m2
    WL = FLAGS.WL  # kg/m2

    # Callculated load
    DL = DL * s + purin  # kg/m
    Lr = Lr * s  # kg/m
    WL = WL * slope / 45  # kg/m -- >Ketchum formular

    Wux = wu(DL * np.sin(np.radians(slope)), Lr * np.sin(np.radians(slope)), 0)
    Wuy = wu(DL * np.cos(np.radians(slope)), Lr * np.cos(np.radians(slope)), WL)

    Mux, Muy = Mu(Wux, Wuy)
    Zx = Mux * 100 / (0.6 * Fy)
    Zy = Muy * 100 / (0.75 * Fy)

    # Information organization
    context = {
        "L": L,
        "s": s,
        "slope": slope,
        "DL": DL,
        "Live": Lr,
        "Wind": WL,
        "DL": DL,
        "Lr": Lr,
        "WL": WL,
        "Wux": Wux,
        "Wuy": Wuy,
        "Mux": Mux,
        "Muy": Muy,
        "Zx": Zx,
        "Zy": Zy,
    }

    # Display information
    report(**context)

    # Display image
    # from PIL import Image

    # img = Image.open(os.path.join(CURR, "images", "simple_uniform.png"))
    # img.show()

    #  Create dataframe of selected secction
    df = section_generator(FLAGS.section)

    # Filter by Zx, Zy
    df_filter = df[(df["Zx"] > Zx) & (df["Zy"] > Zy)]

    # Display table
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

    # design
    print(f"\nDESIGN")
    i = int(input("PLEASE SELECT SECTION : "))
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

    # CHECK
    flex(Mux, Muy, As["Zx"], As["Zy"])
    print("--------------------------------------")

    eff(Mux, Muy, As["Zx"], As["Zy"])
    print("--------------------------------------")

    deflection(Wux, Wuy, As["Ix"], As["Iy"])
    print("--------------------------------------")

    shear(Wuy, As.A, int(As["h"]), int(As["t"]))


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
    % python app/purin.py --L=4 --s=1 --slope=8 --DL=25 --Lr=50 --WL=50

    use TUBE
    % python app/purin.py --L=4 --s=1 --slope=8 --DL=25 --Lr=50 --WL=50 --section=Rectangular_Tube.csv

    use SQR-TUBE
    % python app/purin.py --L=4 --s=1 --slope=8 --DL=25 --Lr=50 --WL=50 --section=Square_Tube.csv

    another section please see csv file in sections folder

"""
