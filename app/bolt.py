import numpy as np

# A325 in shear plane
Fv = 330  # Mpa, N/mm2
Fb = 620  # Mpa, N/mm2

𝜙t = 0.75
𝜙v = 0.75

bolt = 16  # mm
t = 5  # mm
Pu = 1.7 * 10.89 * 2

dia = bolt + 2 + 2  # mm

Fv = (Fv * 1e-3) * np.pi * bolt * bolt / 4  # kN
Fb = 2.4 * bolt * t * Fb * 1e-3  # kN
print(f"Fv: {Fv:.2f} kN")
print(f"Fb: {Fb:.2f} kN")

Fcr = min(Fv, Fb)

N = Pu / Fcr
print(N)
