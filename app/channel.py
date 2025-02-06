import sys
import os

from time import sleep
from tabulate import tabulate

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  #

from section_generator import Loads, MaterialProperties

from applications.flexural import Yeild, FLB, LTB
from applications import compression

from tools import width_thickness_ratio as wt
from tools.section_properties import CHN

from utils import select_label, select_flange, initialize_section, try_section, result


# ---------------------------
def cb(Mmax, Ma, Mb, Mc):
    return 12.5 * Mmax / (2.5 * Mmax + 3 * Ma + 4 * Mb + 3 * Mc)


# Width-Thickness ratio checked
def compression_wt_ratio_check(materials, section):

    C = wt.WT_compression(materials)
    C.channels(section.B, section.H, section.tf, section.tw)

    sleep(2)

    options = f"""
        C = compact, NC = non-compact, S = slender
        label = 2 : C, NC --> 'CHN', 'T'
        label = 4 : S --> 'H', 'CHN', '[]', 'O',

        HxB,H,B,tf,tw,r1,r2,A,Wt,Cx,Cy,Ix,Iy,rx,ry,Zx,Zy
        """

    return select_label(options, [2, 4])


# Width-Thickness Ratio Checked
def flexural_wt_ratio_check(materials, section):

    R = wt.WT_flexural(materials)
    λpf, λrf, λpw, λrw = R.h_section(section.B, section.H, section.tf, section.tw)
    return λpf, λrf, λpw, λrw


# Calculate axial capacity. øPn
def compression_capacity(materials, section, K, Lb, Pu, label, limit):
    calc = compression.Compression(materials)
    øPn = calc.call(label, K, Lb, section.rx, section.A, Pu, limit)
    return øPn


# Calculate flexural capacity
def flexural_capacity(loads, materials, section, Lb, Cb, λpf, λrf):
    yeild = Yeild(materials)
    flb = FLB(materials)
    ltb = LTB(materials)

    """
    label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
    lebel = 4 : minor axis, H,C : web=C, flang=NC,S --> Y, LTB
    """

    flange = select_flange()

    chn = CHN(materials)
    J, Cw = chn.torsion_chn(section)
    Sx, Sy = chn.section_modulus(section)

    # label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
    print(f"\n[INFO] : Major axis :")
    øMp = yeild.major_axis(section.Zx)
    øMn1 = ltb.hc_major(materials, section, øMp / 0.9, Lb, Cb, J, Cw, channel=True)
    øMcrx = min(øMp, øMn1)
    context = {"øMcrx": øMcrx, "Mux": loads.Mux}
    result(context, "kN-m")

    # lebel = 4 : minor axis, H,C : web=C, flang=NC,S --> Y, LTB
    if loads.Muy != 0:
        print(f"\n[INFO] : Minor axis :")
        øMpy = yeild.minor_axis(Sy, section.Zy)
        øMn2 = flb.hc_minor(
            section, Sy * 1e6, section.B / 2, øMpy / 0.9, λpf, λrf, flange
        )
        øMcry = min(øMpy, øMn2)
        context = {"øMcry": øMcry, "Muy": loads.Muy}
        result(context, "kN-m")


if __name__ == "__main__":
    Pu = 150
    Mux = 15
    Muy = 5
    K = 1
    Lb = 5
    Cb = 1

    loads = Loads(Pu, Mux, Muy)
    materials = MaterialProperties(Fy=250, Es=200000)

    df = initialize_section(loads, materials, "Channels.csv")

    while True:
        section = try_section(df)

        # Calculate compression capacity
        label = compression_wt_ratio_check(materials, section)
        øPn = compression_capacity(materials, section, K, Lb, Pu, label, limit=200)

        # Calculate flexural capacity
        λpf, λrf, λpw, λrw = flexural_wt_ratio_check(materials, section)
        flexural_capacity(loads, materials, section, Lb, Cb, λpf, λrf)

        confirm = input("Try Again? Y|N: ").upper()
        if confirm != "Y":
            break


# python app/channel.py
