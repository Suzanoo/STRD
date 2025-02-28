import sys
import os
from time import sleep

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties, Loads

from utils import select_label, try_section, initialize_section

from applications import compression, tube_section
from tools import width_thickness_ratio as wt


def compression_wt_ratio_check(materials, section):
    C = wt.WT_compression(materials)
    C.tube(section["b"], section["t"])

    sleep(2)

    options = f"""
        C = compact, NC = non-compact, S = slender
        label = 1 : C, NC --> 'H', '[]', 'O', 'composit H'
        label = 4 : S --> 'H', 'CHN', '[]', 'O',
        """
    label = select_label(options, [1, 4])
    return label


def flexural_wt_ratio_check(materials, section):
    # Width-Thickness Ratio Checked
    R = wt.WT_flexural(materials)
    R.tube(section.b, section.h, section.t, section.t)


def flexural_capacity(materials, section, Mu):
    print("[] : web=C,NC, flange=C,NC,S --> Y, FLB, WLB")

    flange = input("flange = ? : [C, NC, S] : ").upper()
    web = input("web = ? : [C, NC, S] : ").upper()

    calc = tube_section.Tube(materials)
    øMn = calc.call(section, flange, web, Mu)
    return øMn


def compression_capacity(materials, section, K, Lb, Pu, label, limit):
    calc = compression.Compression(materials)
    øPn = calc.call(label, K, Lb, section.rx, section.A, Pu, limit)
    return øPn


if __name__ == "__main__":
    Pu = 150
    Mux = 15
    Muy = 5
    K = 1
    Lb = 6
    Cb = 1

    loads = Loads(Pu, Mux, Muy)
    materials = MaterialProperties(Fy=250, Es=200000)

    df = initialize_section(loads, materials, "Rectangular_Tube.csv")

    while True:
        section = try_section(df)

        # Calculate compression capacity
        print("[INFO] : Compression capacity")
        label = compression_wt_ratio_check(materials, section)
        øPn = compression_capacity(materials, section, K, Lb, Pu, label, limit=200)

        # Calculate flexural capacity
        print("[INFO] : Flexural capacity")
        flexural_wt_ratio_check(materials, section)
        flexural_capacity(materials, section, Mux)

        confirm = input("Try Again? Y|N: ").upper()
        if confirm != "Y":
            break


# python app/rect_tube.py
