class Torsion():

    # H section
    def torsion_h(B, H, tf, tw, Ix, Iy): # mm, mm, mm, mm, cm44, cm4
        b = B
        h0 = H - tf
        Ix = Ix*1e4
        Iy = Iy*1e4
        J = (1/3)*(2*b*(tf**3) + h0*tw**3) # mm4
        Cw = (Iy*h0**2)/4 # mm6
        Ips = Ix + Iy
        return J, Cw
    
    # CHN
    def torsion_chn(b, h, tf, tw):
        J = (1/3)*(2*b*(tf**3) + h*tw**3) # mm4
        q = (3*b*tf + 2*h*tw)/(6*b*tf + h*tw)
        Cw = q * tf*(b**3)*(h**2)/12
        return J, Cw