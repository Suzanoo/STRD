import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties, Loads

from utils import select_label, select_flange, initialize_section, try_section, result
from applications.flexural import Yeild, FLB, LTB

from tools import width_thickness_ratio as wt
from tools.section_properties import H


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
    print("[INFO] : Major axis")
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
        øMn = ltb.hc_major(materials, section, øMp / 0.9, Lb, Cb, J, Cw)
        øMnx = øMn

    # label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB, FLB
    elif label == 2:
        h = H(materials)
        J, Cw = h.torsion(section)

        øMp = yeild.major_axis(section.Zx)
        øMn1 = ltb.hc_major(materials, section, øMp / 0.9, Lb, Cb, J, Cw)
        øMn2 = flb.hc_major(section, øMp / 0.9, λpf, λrf, flange)
        øMnx = min(øMn1, øMn2)

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
        øMnx = min(øMn1, øMn2, øMn3, øMn4)

    context = {"øMnx": øMnx, "Mux": loads.Mux}
    result(context, "kN-m")

    if loads.Muy != 0:
        print(f"\n[INFO] : Minor axis :")
        øMpy = yeild.minor_axis(section.Sy, section.Zy)
        øMny = flb.hc_minor(
            section, section.Sy * 1e3, section.B / 2, øMpy / 0.9, λpf, λrf, flange
        )
        context = {"øMny": øMny, "Muy": loads.Muy}
        result(context, "kN-m")


def call(Pu, Mux, Muy, Lb, Cb):
    loads = Loads(Pu, Mux, Muy)
    materials = MaterialProperties(Fy=250, Es=200000)

    df = initialize_section(loads, materials, "H-Sections.csv")

    while True:
        section = try_section(df)
        λpf, λrf, λpw, λrw = wt_ratio_check(materials, section)

        flexural_capacity(loads, materials, section, Lb, Cb, λpf, λrf, λpw, λrw)
        confirm = input("Try Again? Y|N: ").upper()
        if confirm != "Y":
            break


if __name__ == "__main__":
    Pu = 150
    Mux = 45
    Muy = 15
    Lb = 10
    Cb = 1

    call(Pu, Mux, Muy, Lb, Cb)

# python app/h_beam.py
