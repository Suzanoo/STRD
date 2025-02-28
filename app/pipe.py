import sys
import os
from time import sleep

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties, Loads

from utils import (
    select_label,
    select_flange,
    try_pipe,
)

from applications import compression, pipe_section
from tools import width_thickness_ratio as wt


def compression_wt_ratio_check(materials, section):
    C = wt.WT_compression(materials)
    C.pipe(section.D, section.t)

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
    R.pipe(section.D, section.t)


def flexural_capacity(materials, section, Mu):
    print(
        """
    ø  --> Y, LB
    """
    )

    flange = select_flange()

    calc = pipe_section.Pipe(materials)
    øMn = calc.call(section, flange, Mu)
    return øMn


def compression_capacity(materials, section, K, Lb, Pu, label, limit):
    calc = compression.Compression(materials)
    øPn = calc.call(label, K, Lb, section.i, section.A, Pu, limit)
    return øPn


if __name__ == "__main__":
    Pu = 150
    Mux = 15
    Muy = 5
    K = 1
    Lb = 5
    Cb = 1

    loads = Loads(Pu, Mux, Muy)
    materials = MaterialProperties(Fy=250, Es=200000)

    while True:
        section = try_pipe(loads, materials, "Pipe.csv")

        # Calculate compression capacity
        print("[INFO] : Compression capacity")
        label = compression_wt_ratio_check(materials, section)
        øPn = compression_capacity(materials, section, K, Lb, Pu, label, limit=200)

        # Calculate flexural capacity
        print("[INFO] : Flexural capacity")
        flexural_wt_ratio_check(materials, section)
        øMn = flexural_capacity(materials, section, Mux)

        confirm = input("Try Again? Y|N: ").upper()
        if confirm != "Y":
            break


# python app/pipe.py
