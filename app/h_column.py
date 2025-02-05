import sys
import os
from time import sleep

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties, Loads

from tools import width_thickness_ratio as wt
from applications import compression

from utils import (
    df_generator,
    display_df,
    get_valid_integer,
    select_label,
    select_flange,
)


def try_section(loads, materials):
    df = df_generator("H-Sections.csv")

    # Calculated required Z values
    Zx = loads.Mux * 1000 / (0.9 * materials.Fy)
    Zy = loads.Muy * 1000 / (0.75 * materials.Fy)
    print(f"\nInitial Z required = {Zx:.2f} cm3")
    print(f"Initial A required = {(loads.Pu /  materials.Fy) * 10:.2f} cm2")

    df_filter = df[(df["Zx"] > Zx) & (df["Zy"] > Zy)]
    display_df(df_filter.sort_values(by=["Zx"])[:20], index=True)

    # Try section
    i = get_valid_integer("PLEASE SELECT SECTION : ")
    section = df.iloc[i]
    display_df(df.filter(items=[i], axis=0), index=True)
    return section


# Width-Thickness ratio checked
def wt_ratio_check(materials, section):

    C = wt.WT_compression(materials.Fy, materials.Es)

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

    section = try_section(loads, materials)
    label = wt_ratio_check(materials, section)

    return axial_capacity(materials, section, K, Lb, Pu, label, limit=200)


if __name__ == "__main__":
    Pu = 150
    Mux = 45
    Muy = 15

    K = 1
    Lb = 10

    øPn = call(Pu, Mux, Muy, K, Lb)

# python app/h_column.py
