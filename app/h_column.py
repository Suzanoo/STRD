import sys
import os
from time import sleep

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties, Loads

from tools import width_thickness_ratio as wt
from applications import compression

from utils import select_label, initialize_section, try_section


# Width-Thickness ratio checked
def wt_ratio_check(materials, section):

    C = wt.WT_compression(materials)

    C.h_section(section["B"], section["H"], section["tf"], section["tw"])

    sleep(2)

    options = f"""
        C = compact, NC = non-compact, S = slender
        label = 1 : C, NC --> 'H', '[]', 'O', 'composit H'
        label = 4 : S --> 'H', 'CHN', '[]', 'O',
        """

    return select_label(options, [1, 4])


# Calculate axial capacity. øPn
def axial_capacity(materials, section, K, Lb, Pu, label, limit):
    calc = compression.Compression(materials)
    øPn = calc.call(label, K, Lb, section.rx, section.A, Pu, limit)
    return øPn


def call(Pu, Mux, Muy, K, Lb):
    loads = Loads(Pu, Mux, Muy)
    materials = MaterialProperties(Fy=250, Es=200000)

    df = initialize_section(loads, materials, "H-Sections.csv")

    while True:
        section = try_section(df)
        label = wt_ratio_check(materials, section)
        axial_capacity(materials, section, K, Lb, Pu, label, limit=200)

        confirm = input("Try Again? Y|N: ").upper()
        if confirm != "Y":
            break


if __name__ == "__main__":
    Pu = 150
    Mux = 45
    Muy = 15

    K = 1
    Lb = 15

    øPn = call(Pu, Mux, Muy, K, Lb)

# python app/h_column.py
