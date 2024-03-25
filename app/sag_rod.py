import numpy as np

øt = 0.9
Fy = 2400  # SR24 ksc

Pu = 8.63 * 6.2

D = 4 * Pu / (np.pi * øt * Fy)

print((np.sqrt(D)) * 1e-3)
