import os

from time import sleep
from tabulate import tabulate

from design.compression import Compression
from design.flexural import WF_CHN
from design.interaction import Interaction
from properties import wt_ratio as wt

from absl import app, flags
from absl.flags import FLAGS

from tools.steel_section import section_generator

# Flag definition :
# MATERIAL PROPERTIES : default SS400
flags.DEFINE_integer("Fu", 400, "4000ksc, MPa")
flags.DEFINE_integer("Fy", 245, "SD40 main bar, MPa")
flags.DEFINE_integer("Es", 206010, "SR24 traverse, MPa")

flags.DEFINE_float("øc", 0.9, "compression factor")
flags.DEFINE_float("øb", 0.9, "flexural factor")

flags.DEFINE_float("L", 0, "length, m")
flags.DEFINE_float("Lbx", 0, "effective length, m")
flags.DEFINE_float("Lby", 0, "effective length, m")
flags.DEFINE_float("K", 1, "stiffness")

flags.DEFINE_float("Pu", 0, "Axial load, kN")
flags.DEFINE_float("Mux", 0, "Moment, kN-m")
flags.DEFINE_float("Muy", 0, "Moment, kN-m")

flags.DEFINE_float("Cb", 1, "")
flags.DEFINE_float("Mmax", 0, "Moment, kN-m")
flags.DEFINE_float("Ma", 0, "Moment, kN-m")
flags.DEFINE_float("Mb", 0, "Moment, kN-m")
flags.DEFINE_float("Mc", 0, "Moment, kN-m")


# ---------------------------
# Calculated Cb
def cb(Mmax, Ma, Mb, Mc):
    return 12.5 * Mmax / (2.5 * Mmax + 3 * Ma + 4 * Mb + 3 * Mc)


# Calculateed øPn
def compression(label, section):
    # Instancing
    axial = Compression(FLAGS.Fy, FLAGS.Es, FLAGS.øc)

    # if no bracing use full length
    if FLAGS.Lbx == 0 or FLAGS.Lby == 0:
        Lb = FLAGS.L  
    # use bracing length
    else:
        Lb = max(FLAGS.Lbx, FLAGS.Lby)  

    øPn = axial.call(label, FLAGS.K, Lb, section["ry"], section["A"], FLAGS.Pu)
    return øPn

# Calculateed øMn
def flexural(label, flange, section):
    # Cb definition
    if FLAGS.Mmax != 0 and FLAGS.Ma != 0 and FLAGS.Mb != 0 and FLAGS.Mc != 0:
        FLAGS.Cb = cb(FLAGS.Mmax, FLAGS.Ma, FLAGS.Mb, FLAGS.Mc)

    c = 1

    # Instancing
    flex = WF_CHN(FLAGS.Fy, FLAGS.Es)
    flex.h_section_definition(section)

    # major axis
    # H,C : web=C, flang=C --> Y, LTB
    øMn = flex.call(FLAGS.Mux, label, FLAGS.Lbx, c, FLAGS.Cb, flange)  # default Cb=1
    return øMn


# ---------------------------
def design():
    print("STEEL ANALYSIS : LRFD METHOD")
    print(
        "================================================================================================================================"
    )

    Fu = FLAGS.Fu
    Fy = FLAGS.Fy
    Es = FLAGS.Es
    øc = FLAGS.øc
    øb = FLAGS.øb

    L = FLAGS.L
    Lbx = FLAGS.Lbx
    Lby = FLAGS.Lby
    K = FLAGS.K

    Pu = FLAGS.Pu
    Mux = FLAGS.Mux
    Muy = FLAGS.Muy

    # display parameter
    print(f"\n[INFO] Criteria parameters")
    keys = ["Fu", "Fy", "Es", "øc", "øb", "L", "Lbx", "Lby", "K", "Pu", "Mux", "Muy"]
    values = [Fu, Fy, Es, øc, øb, L, Lbx, Lby, K, Pu, Mux, Muy]
    units = ["MPa", "MPa", "Mpa", "", "", "m", "m", "m", "", "kN", "kN-m", "kN-m"]

    for j in range(len(keys)):
        print(f"{keys[j]} : {values[j]} {units[j]}")
    print()

    # ---------------------------
    #  Create dataframe depend on selected section
    df = section_generator("H-Sections.csv")

    Zx = Mux * 1000 / (0.9 * Fy)
    Zy = Muy * 1000 / (0.75 * Fy)
    print(f"\nInitial Z required = {Zx:.2f} cm3")
    print(f"Initial A required = {(Pu /  FLAGS.Fy) * 10:.2f} cm2")

    df_filter = df[(df["Zx"] > Zx) & (df["Zy"] > Zy)]
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

    # select from table index
    print(f"\nDESIGN")
    i = int(input("PLEASE SELECT SECTION : "))
    section = df.iloc[i]

    print(
        tabulate(
            df.filter(items=[i], axis=0),
            headers=df.columns,
            floatfmt=".2f",
            showindex=True,
            tablefmt="psql",
        )
    )

    # ---------------------------
    # COMPRESSION
    # width-thickness ratio check for compression
    print(f"\n[INFO] Compression Design")
    C = wt.WT_compression(Fy, Es)
    C.h_section(section["B"], section["H"], section["tf"], section["tw"])
    sleep(2)

    print(
        f"""
        C = compact
        NC = non-compact
        S = slender
        label = 1 : C, NC --> 'H', '[]', 'O', 'composit H'
        label = 2 : C, NC --> 'CHN', 'T'
        label = 3 : C, NC -->  'L'
        label = 4 : S --> 'H', 'CHN', '[]', 'O',
        label = 5 : S --> 'L', 'T'
    """
    )
    while True:
        label = input("label = ? : ")
        if label not in ["1", "4"]:
            print("Label for H-section is 1 or 4, Try again!")
        else:
            break

    print("")
    øPn = compression(int(label), section)

    # ---------------------------
    # FLEXURAL
    if FLAGS.Mux == 0 and FLAGS.Muy == 0:
        øMnx = 0
        øMny = 0
    else:
        # width-thickness ratio check for flexural
        print(f"\n[INFO] Flexural Design")
        R = wt.WT_flexural(Fy, Es)
        R.h_section(section["B"], section["H"], section["tf"], section["tw"])
        sleep(2)

        print(
            f"""
        label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
        label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB
        label = 3 : minor axis, H : web=C, flang=NC,S --> Y, LTB
        lebel = 4 : NC-web, H : web=C,NC, flang=C,NC,S --> Yc, Yt, LTB, FLB, TFY
        """
        )

        # X-X Axis
        print("X-X AXIS")
        label = input("label = ? : ")
        flange = input("flange = ? : [C, NC, S] : ")
        print("")
        øMnx = flexural(int(label), flange.upper(), section)

        # Y_Y Axis
        if Muy != 0:
            print("Y-Y AXIS")
            # swap variable
            FLAGS.Mux, FLAGS.Muy = FLAGS.Muy, FLAGS.Mux
            FLAGS.Lbx, FLAGS.Lby = FLAGS.Lby, FLAGS.Lbx
            label = 3
            øMny = flexural(label, flange.upper(), section)
        else:
            øMny = 0

    return øPn, øMnx, øMny
    # ---------------------------


def main(_argv):
    øPn, øMnx, øMny = design()
    if (FLAGS.Mux != 0) & (FLAGS.Muy != 0):
        Interaction.flex_comp_MxMy(FLAGS.Pu, øPn, FLAGS.Mux, øMnx, FLAGS.Muy, øMny)
    elif (FLAGS.Mux != 0) & (FLAGS.Muy == 0):
        Interaction.flex_comp_Mx(FLAGS.Pu, øPn, FLAGS.Muy, øMny, FLAGS.Cb)
    else:
        pass


# ---------------------------
if __name__ == "__main__":
    app.run(main)

"""
How to used?
-Please see FLAGS definition for unit informations
-Make sure you are in the project directory run python in terminal(Mac) or command line(Windows)
-run script

    % cd <path to "project-directory" directory>
    % conda activate <your conda env name>

    Axial load only:
    % python app/h_section.py --L=5 --Pu=150 

    Axial load + Flexural
    % python app/h_section.py --L=5 --Lbx=2.5 --Pu=150 --Mux=25
    % python app/h_section.py --L=5 --Lbx=2.5 --Lby=2.5 --Pu=150 --Mux=25 --Muy=5
"""
