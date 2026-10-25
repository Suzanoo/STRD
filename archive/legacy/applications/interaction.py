import numpy as np


class Interaction:
    # 7.1.1 symmetry + flexual + compression + Mx + My
    def flex_comp_MxMy(Pu, øPn, Mux, øMnx, Muy, øMny):
        # take care of if there is zero division
        øMnx = 1 if øMnx == 0 else øMnx
        øMny = 1 if øMny == 0 else øMny

        if Pu / øPn >= 0.2:
            r = (Pu / øPn) + (8 / 9) * ((Mux / øMnx) + (Muy / øMny))
            print(f"\n7.1.1: Pu/Pn + 8/9 * (Mux/Mnx + Muy/Mny) = {r:.2f}")
            print("SECTION OK") if r < 1 else print("INCORRECT SECTION")
        else:
            r = (Pu / (2 * øPn)) + ((Mux / øMnx) + (Muy / øMny))
            print(f"\n7.1.1: Pu/2*Pn + (Mux/Mnx + Muy/Mny) = {r:.2f}")
            print("SECTION OK") if r < 1 else print("INCORRECT SECTION")

    # TODO
    # 7.1.2 symmetry + flexual + tension
    # 7.1.3 symmetry + flexual + compression + Mx only
    def flex_comp_Mx(Pu, øPn, Mux, øMnx, Cb=1):
        # take care of if there is zero division
        øMnx = 1 if øMnx == 0 else øMnx

        if Pu / øPn >= 0.2:
            r = (Pu / øPn) + (8 / 9) * (Mux / øMnx)
            print(f"\n7.1.3: Pu/øPn + 8/9 * Mux/øMnx = {r:.2f}")
            print("SECTION OK") if np.abs(r) < 1 else print("INCORRECT SECTION")
        else:
            r = (Pu / (2 * øPn)) + (Mux / øMnx)
            print(f"\n7.1.3: Pu/2*øPn + Mux/øMnx = {r:.2f}")
            print("SECTION OK") if np.abs(r) < 1 else print("INCORRECT SECTION")

        r = (Pu / øPn) * (1.5 - 0.5 * (Pu / øPn)) + (Mux / (Cb * øMnx)) ** 2
        print(f"\n7.1.3: Pu/øPn*(1.5 - 0.5*(Pu/øPn) + (Mux/Cb*øMnx)**2 = {r:.2f}")
        print("SECTION OK") if np.abs(r) < 1 else print("INCORRECT SECTION")
