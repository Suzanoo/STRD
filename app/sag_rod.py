import numpy as np


from absl import app, flags
from absl.flags import FLAGS


flags.DEFINE_float("Tu", 0, "Tension, kN")
flags.DEFINE_float("Fy", 240, "Yeild strength, MPa")

def main(_args):
    øt = 0.9
    Fy = FLAGS.Fy  # MPa
    Pu = FLAGS.Tu # kN

    A_req = Pu * 1e2 / (øt * Fy) # cm2

    D = np.sqrt(4 * Pu * 1e3/ (np.pi * øt * Fy) ) # mm2

    print(f"A.required = {A_req:.2f} cm2")

    print(f"In case of round bar D = {D:.2f} mm")



if __name__ == "__main__":
    app.run(main)

'''
% python app/sag_rod.py --Fy=450 --Tu=50
'''
