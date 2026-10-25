import numpy as np

from utils import get_valid_number

"""
A1 : Base plate area
A2 : Pedestal area

Column dim : bf x d
"""
fc = 20  # MPa
Fy = 250  # MPa
P = 1600  # kN
bf = 300  # mm
d = 300  # mm
full_pedestal = False

# Determine plate area
Fp = 0.7 * fc if full_pedestal == False else 0.35 * fc  # MPa
A1 = (P / Fp) * 10  # cm2

# Dimension of plate
delta = 0.5 * (0.95 * d - 0.8 * bf)  # mm
N_req = np.sqrt(A1) * 10 + delta  # mm
B_req = A1 * 100 / N_req  # mm

while True:
    print(f"N-required = {N_req} mm ")
    N = get_valid_number("Determine N in mm : ")

    print(f"B-required = {B_req} mm ")
    B = get_valid_number("Determine B in mm : ")

    # Pressure on concrete footing
    fp = (P / (B * N)) * 1e3  # MPa
    print(f"Pressure on concrete footing check :  fp = {fp:.2f} , Allow Fp = {Fp} MPa")

    confirm = input("Confirm? Y|N: ").strip().upper()
    if confirm == "Y":
        break
    else:
        print("Let's try again.")

# Compute m, n
m = (N - 0.95 * d) / 2
n = (B - 0.8 * bf) / 2
n_prime = (1 / 4) * np.sqrt(d * bf)

# Plate thickness
t = 2 * n_prime * np.sqrt(fp / Fy)
print(f"t-required = {t} mm ")
t = get_valid_number("Determine t in mm : ")

print(f"Base Plate Dimension : B x N x t = {B} x {N} x {t} mm")
