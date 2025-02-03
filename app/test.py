import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from section_generator import MaterialProperties
from tools import width_thickness_ratio as wt
from utils import df_generator, display_df, get_valid_integer, select_label
from calculator.flexural import Yeild, FLB, LTB

from section_properties import H, Box

Pu = 150
Mux = 25
Muy = 5

materials = MaterialProperties(Fy=250, Es=200000)

#  Create dataframe depend on selected section
df = df_generator("H-Sections.csv")

# Calculated required Z values
Zx = Mux * 1000 / (0.9 * materials.Fy)
Zy = Muy * 1000 / (0.75 * materials.Fy)
print(f"\nInitial Z required = {Zx:.2f} cm3")
print(f"Initial A required = {(Pu /  materials.Fy) * 10:.2f} cm2")

df_filter = df[(df["Zx"] > Zx) & (df["Zy"] > Zy)]
print(f"\nSection Table")
display_df(df_filter.sort_values(by=["Zx"])[:20], index=True)

# Select section
i = get_valid_integer("PLEASE SELECT SECTION : ")
section = df.iloc[i]
display_df(df.filter(items=[i], axis=0), index=True)

# Width-Thickness Ratio Checked
R = wt.WT_flexural(materials)
λpf, λrf, λpw, λrw = R.h_section(section.B, section.H, section.tf, section.tw)

## Calculated section capacity
# Instaciated variables
yeild = Yeild(materials)
flb = FLB(materials)
ltb = LTB(materials)


# Major Axis
print("Major axis")
label, flange = select_label()

# label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
if label == 1:
    H = H(materials)
    J, Cw = H.torsion(section)

    øMp = yeild.major_axis(section.Zx)
    øMn = ltb.hc_major(section, øMp / 0.9, 3, 1, J, Cw)

# label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB, FLB
elif label == 2:
    H = H(materials)
    J, Cw = H.torsion(section)

    øMp = yeild.major_axis(section.Zx)
    øMn = ltb.hc_major(section, øMp / 0.9, 3, 1, 1, J, Cw)
    øMn = flb.hc_major(section, øMp / 0.9, λpf, λrf, flange)

# lebel = 3 : major axis, H : web=NC, --> Yc, Yt, LTB, FLB, TFY
elif label == 3:
    H = H(materials)
    J, Cw = H.torsion(section)

    rpc, sxc, Iyc, Myc = H.Rpc(section, λpw, λrw)
    rpt, sxt, Iyt, Myt = H.Rpc(section, λpw, λrw)

    øMn1 = yeild.nc_web_yc(sxc, rpc)
    øMn2 = yeild.nc_web_yt(sxt, rpt)
    øMn3 = ltb.nc_web(section, 10, sxc, Iyc, Myc, rpc)
    øMn4 = flb.nc_web(section, λpf, λrf, sxc, Myc, rpc, flange)

# lebel = 4 : major axis, H : web=NC, --> Yc, Yt, LTB, FLB, TFY
elif label == 4:
    øMpy = yeild.minor_axis(section.Sy, section.Zy)
    øMn = flb.hc_minor(
        section, section.B / 2, øMpy / 0.9, λpf, λrf, flange
    )  # H section
    # øMn1 = flb.hc_minor(section, section.B, øMpy/0.9, λpf, λrf, flange="C") # C section

# label = 5 : [] : web=C,NC, flange=C,NC,S --> Y, FLB, WLB
elif label == 5:
    box = Box(materials)

    øMp = yeild.major_axis(section.Zx)

    if flange == "S":
        be = box.effective_width(section.b, section.t)
        Se, Sy = box.section_modulus(be, section.h, section.t, section.t)
        øMn = box(section.b, section.t, Se * 1e3, (øMp / 0.9) * 1e6, flange)

    else:
        øMn = box(section.b, section.t, section.S * 1e3, (øMp / 0.9) * 1e6, flange)


# python app/test.py
