## LRFD
import sys
import os
import numpy as np


from tabulate import tabulate

from absl import app, flags
from absl.flags import FLAGS

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from utils.utils import section_generator

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

flags.DEFINE_boolean("sagrod", False, "Sag rod at center")


# Load Case
def wu(DL, Lr, WL):
    case1 = DL + Lr  # SLS --> w
    case2 = 0.75 * (1.4 * DL + 1.7 * Lr) + 1.6 * WL
    case3 = 0.9 * DL + 1.6 * WL
    return case1, max(case1, case2, case3)  # kN/m2


def Mu(Wux, Wuy):
    Mux = (1 / 8) * Wuy * FLAGS.L**2  # kg-m

    if FLAGS.sagrod == False:
        Muy = (1 / 8) * Wux * FLAGS.L**2  # kg-m
    else:
        Muy = (1 / 8) * Wux * (0.5 * FLAGS.L) ** 2  # kg-m
    print(f"")

    return Mux, Muy


def flex(Mux, Muy, Zx, Zy):
    𝜙Mnx = 0.9 * FLAGS.Fy * Zx / 100  # kg-m
    𝜙Mny = 0.9 * FLAGS.Fy * Zy / 100  # kg-m

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


def shear(Wuy, A, H, T):
    Fv = FLAGS.Fy  # ksc
    Vu = 0.5 * Wuy * FLAGS.L  # kg

    𝜙Vnt = 0.9 * Fv * A  # kg
    𝜙Vnh = 0.9 * Fv * H * T / 100  # kg

    print(f"Vu = {Vu:.2f} kg \n𝜙Vnt = {𝜙Vnt:.2f} kg \n𝜙Vnh = {𝜙Vnh:.2f} kg")

    if (Vu < 𝜙Vnt) & (Vu < 𝜙Vnh):
        print("Shear Resistance OK ")
    else:
        print("Shear Resistance Not OK ")


def eff(Mux, Muy, Zx, Zy):
    Fbx = 0.9 * FLAGS.Fy  # ksc
    Fby = 0.75 * FLAGS.Fy  # ksc

    eff = (Mux * 100 / Zx) / Fbx + (Muy * 100 / Zy) / Fby

    if eff < 1:
        print(f"Interaction Combine = {eff:.2f} < 1 : Section OK")
    else:
        print(f"Interaction Combine= {eff:.2f} > 1 : Incorrect Section")


def deflection(Wx, Wy, Ix, Iy):
    d = 160

    if FLAGS.sagrod == False:
        dx = 5 * (Wx / 100) * ((FLAGS.L * 100) ** 4) / (384 * FLAGS.Es * Iy)
    else:
        dx = 5 * (Wx / 100) * ((0.5 * FLAGS.L * 100) ** 4) / (384 * FLAGS.Es * Iy)

    dy = 5 * (Wy / 100) * ((FLAGS.L * 100) ** 4) / (384 * FLAGS.Es * Ix)

    print(f"L/{d} = {FLAGS.L*100/d:.2f} cm \ndx = {dx:.2f} cm \ndy = {dy:.2f} cm")

    if (dx < FLAGS.L * 100 / d) & (dy < FLAGS.L * 100 / d):
        print("Deflection OK")
    else:
        print("Deflection NOT OK")


def report(**kwargs):
    x = kwargs
    print("STEEL PURIN DESIGN : LRFD Method")
    print(
        "================================================================================================================================"
    )

    if FLAGS.section == "Z.csv":
        print(
            f"MATERIAL PROPERTIES: \n'ROLLFORM' High Tensile Galvanized Purlin  \nFy = {FLAGS.Fy} ksc \nEs = 2.04x10^6 ksc"
        )
    else:
        print(
            f"MATERIAL PROPERTIES: \nSteel ASTM A36  \nFy = {FLAGS.Fy} ksc \nEs = 2.04x10^6 ksc"
        )

    print(
        f"\nLOAD CASE: \n1 = DL+Lr #SLS \n2 = 0.75*(1.4DL + 1.7Lr) +  1.6WL \n3 = 0.9DL + 1.6WL "
    )
    print(
        f"\nGEOMETRY: \nRafter spacing = {x['L']} m \nPurin spacing = {x['s']} m \nSlope  = {x['slope']} degree"
    )

    print(f"\nCALCULATION")
    print(
        f"DL = {x['DL']:.2f} kg/m2, Lr = {x['Lr']:.2f} kg/m2, WL = {x['WL']:.2f} kg/m2"
    )
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

    Wx, Wux = wu(DL * np.sin(np.radians(slope)), Lr * np.sin(np.radians(slope)), 0)
    Wy, Wuy = wu(DL * np.cos(np.radians(slope)), Lr * np.cos(np.radians(slope)), WL)

    Mux, Muy = Mu(Wux, Wuy)
    Zx = Mux * 100 / (0.9 * Fy)
    Zy = Muy * 100 / (0.75 * Fy)

    # Information organization
    context = {
        "L": L,
        "s": s,
        "slope": slope,
        "DL": FLAGS.DL,
        "Lr": FLAGS.Lr,
        "WL": FLAGS.WL,
        "Wux": Wux,
        "Wuy": Wuy,
        "Mux": Mux,
        "Muy": Muy,
        "Zx": Zx,
        "Zy": Zy,
    }

    # Display information
    report(**context)

    #  Create dataframe of selected section
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

    while True:
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

        deflection(Wx, Wy, As["Ix"], As["Iy"])
        print("--------------------------------------")

        shear(Wuy, As.A, int(As["h"]), int(As["t"]))

        ask = input("Select again : Y|N : ").upper()
        if ask == "Y":
            pass
        else:
            break

    # Slenderness in each axis
    print(f"\nSlenderness Check : ")
    while True:
        K = float(input("Define Kx or Ky: "))  # Kx or Ky
        L = float(input("Define Lx or Ly in m: "))  # Lx or Ly
        r = float(input("Define rx or ry in cm: "))  # rx or ry

        print(f"KL/r  = {K * L * 1e2 / r:.0f} : 240")

        ask = input("Finish ??? : Y|N : ").upper()
        if ask == "Y":
            break
        else:
            pass


def main(_args):
    design()


if __name__ == "__main__":
    app.run(main)

"""
How to used?
-Please see FLAGS definition for unit informations

-Make sure you are in the project directory 

-Activate Conda env
    % cd <path to project directory>
    % conda activate <your conda env name>

-Run script
    use CCL (CCL is default section --> don't provide section flag)
    % python app/purin_lrfd.py --L=6 --s=1 --slope=8 --DL=25 --Lr=50 --WL=60
    % python app/purin_lrfd.py --L=6 --s=1 --slope=8 --DL=30 --Lr=50 --WL=60 --sagrod=True

    use TUBE
    % python app/purin_lrfd.py --L=4 --s=1 --slope=8 --DL=25 --Lr=50 --WL=50 --section=Rectangular_Tube.csv

    use SQR-TUBE
    % python app/purin_lrfd.py --L=4 --s=1 --slope=8 --DL=25 --Lr=50 --WL=50 --section=Square_Tube.csv

    use Z
    % python app/purin_lrfd.py --L=8 --s=1.45 --slope=7 --DL=28 --Lr=30 --WL=80 --section=Z.csv --Fy=4587 --purin=5.74

    another section please see csv file in sections folder

"""
