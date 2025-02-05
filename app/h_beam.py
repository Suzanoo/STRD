import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties, Loads

from utils import (
    df_generator,
    display_df,
    get_valid_integer,
    select_label,
    select_flange,
)
from applications.flexural import Yeild, FLB, LTB

from tools import width_thickness_ratio as wt
from tools.section_properties import H


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


def wt_ratio_check(materials, section):
    # Width-Thickness Ratio Checked
    R = wt.WT_flexural(materials)
    λpf, λrf, λpw, λrw = R.h_section(section.B, section.H, section.tf, section.tw)
    return λpf, λrf, λpw, λrw


def flexural_capacity(loads, materials, section, Lb, Cb, λpf, λrf, λpw, λrw):

    ## Calculated section capacity, øMn
    # Instaciated variables
    yeild = Yeild(materials)
    flb = FLB(materials)
    ltb = LTB(materials)

    # Major Axis
    print("Major axis")
    options = f"""
        label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
        label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB, FLB
        lebel = 3 : major axis, H : web=NC, --> Yc, Yt, LTB, FLB, TFY
        """

    label = select_label(options, [1, 2, 3])
    flange = select_flange()

    # label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
    if label == 1:
        h = H(materials)
        J, Cw = h.torsion(section)

        øMp = yeild.major_axis(section.Zx)
        øMn = ltb.hc_major(section, øMp / 0.9, Lb, Cb, J, Cw)
        return øMn

    # label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB, FLB
    elif label == 2:
        h = H(materials)
        J, Cw = h.torsion(section)

        øMp = yeild.major_axis(section.Zx)
        øMn1 = ltb.hc_major(section, øMp / 0.9, Lb, Cb, J, Cw)
        øMn2 = flb.hc_major(section, øMp / 0.9, λpf, λrf, flange)
        return min(øMn1, øMn2)

    # lebel = 3 : major axis, H : web=NC, --> Yc, Yt, LTB, FLB, TFY
    elif label == 3:
        h = H(materials)
        J, Cw = h.torsion(section)

        rpc, sxc, Iyc, Myc = h.Rpc(section, λpw, λrw)
        rpt, sxt, Iyt, Myt = h.Rpt(section, λpw, λrw)

        øMn1 = yeild.nc_web_yc(sxc, rpc)
        øMn2 = yeild.nc_web_yt(sxt, rpt)
        øMn3 = ltb.nc_web(section, Lb, sxc, Iyc, Myc, rpc)
        øMn4 = flb.nc_web(section, λpf, λrf, sxc, Myc, rpc, flange)
        return min(øMn1, øMn2, øMn3, øMn4)

    if loads.Muy != 0:
        print(f"\nMinor axis :")
        øMpy = yeild.minor_axis(section.Sy, section.Zy)
        øMn = flb.hc_minor(section, section.B / 2, øMpy / 0.9, λpf, λrf, flange)
        return øMn


def call(Pu, Mux, Muy, Lb, Cb):
    loads = Loads(Pu, Mux, Muy)
    materials = MaterialProperties(Fy=250, Es=200000)

    section = try_section(loads, materials)
    λpf, λrf, λpw, λrw = wt_ratio_check(materials, section)

    return flexural_capacity(loads, materials, section, Lb, Cb, λpf, λrf, λpw, λrw)


if __name__ == "__main__":
    Pu = 150
    Mux = 45
    Muy = 15
    Lb = 10
    Cb = 1

    øMn = call(Pu, Mux, Muy, Lb, Cb)

# python app/h_beam.py
