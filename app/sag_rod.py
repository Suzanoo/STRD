import numpy as np


from absl import app, flags
from absl.flags import FLAGS


flags.DEFINE_float("Pu", 0, "Tension, kN")
flags.DEFINE_float("Fy", 240, "Yeild strength, MPa")
flags.DEFINE_float("Fu", 400, "Yeild strength, MPa")


def main(_args):
    Ft = min(0.6 * FLAGS.Fy, 0.33 * FLAGS.Fu)  # MPa

    A_req = FLAGS.Pu * 1e2 / Ft  # cm2

    D = np.sqrt(4 * FLAGS.Pu * 1e3 / (np.pi * Ft))  # mm2

    print("ASD Method:")
    print(f"A.required = {A_req:.2f} cm2")
    print(f"In case of round bar D = {D:.2f} mm")


if __name__ == "__main__":
    app.run(main)

"""
% python app/sag_rod.py --Fy=250 --Fu=400 --Pu=45
"""
