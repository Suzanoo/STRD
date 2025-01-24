"""
Code adapted from Prof. Fredy Gabriel Ramírez Villanueva repository
https://github.com/SirPrime/MatrixAnalysis-Beams.git

Tutorial: YouTube Channel วิเคราะห์โครงสร้าง กับ อ.กิจ
https://www.youtube.com/watch?v=hCmXwMQWafk&list=LL&index=6&t=3642s
"""

import sys
import os
import numpy as np

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Add "strd" to sys.path

from utils.utils import (
    get_valid_integer,
    get_valid_number,
    get_valid_list_input,
    xi_coordinate,
)
from plot import Plot

np.set_printoptions(precision=3)


# =========================================================================================
# Beam Analysis Classes
class BeamB:
    """Bernoulli Beam
    Attributes:
        E: Modulus of elasticity
        I: Moment of inertia of the cross-section
        L: Span length
        k: Stiffness matrix of the span
    """

    def __init__(self, E, I, L):
        self.E = E
        self.I = I
        self.L = L
        self.k = (E * I / L**3) * np.array(
            [
                [12.0, 6 * L, -12, 6 * L],
                [6 * L, 4 * L**2, -6 * L, 2 * L**2],
                [-12, -6 * L, 12, -6 * L],
                [6 * L, 2 * L**2, -6 * L, 4 * L**2],
            ]
        )


class Load:
    """Base class for different load types."""

    def __init__(self, load_type):
        self.load_type = load_type

    def describe(self):
        descriptions = {
            0: "Point Load",
            1: "Distributed Load",
            2: "Concentrated Moment",
        }
        print(descriptions.get(self.load_type, "Undefined"))


class PointLoad(Load):
    """Defines a point load."""

    def __init__(self, P=0, a=0):
        super().__init__(0)
        self.P = P
        self.a = a

    def __str__(self):
        return f"Point Load\n   Value: {self.P} N\n   Position: {self.a} m"

    def equivalent_nodal_reactions(self, L):
        a, b = self.a, L - self.a
        return (self.P / L**2) * np.array(
            [
                [b**2 / L * (3 * a + b)],
                [a * b**2],
                [a**2 / L * (a + 3 * b)],
                [-(a**2) * b],
            ]
        )

    def shear_force(self, x, L):
        return -self.P if self.a < x <= L else 0

    def bending_moment(self, x, L):
        if 0 <= x < self.a:
            return (1 - self.a / L) * self.P * x
        elif x <= L:
            return self.a * self.P * (1 - x / L)
        return 0


class DistributedLoad(Load):
    """Defines a uniformly distributed load."""

    def __init__(self, q=0, a=0, l=0):
        super().__init__(1)
        self.q = q
        self.a = a
        self.l = l

    def __str__(self):
        return f"Distributed Load\n  Value: {self.q} N/m\n  From: {self.a} m to {self.a + self.l} m"

    def equivalent_nodal_reactions(self, L):
        q, a, l, b = self.q, self.a, self.l, L - self.a - self.l
        return (q * L / 2) * np.array(
            [
                [
                    1
                    - a / L**4 * (2 * L**3 - 2 * a**2 * L + a**3)
                    - b**3 / L**4 * (2 * L - b)
                ],
                [
                    L
                    / 6
                    * (
                        1
                        - a**2 / L**4 * (6 * L**2 - 8 * a * L + 3 * a**2)
                        - b**3 / L**4 * (4 * L - 3 * b)
                    )
                ],
                [
                    1
                    - a**3 / L**4 * (2 * L - a)
                    - b / L**4 * (2 * L**3 - 2 * b**2 * L + a**3)
                ],
                [
                    -L
                    / 6
                    * (
                        1
                        - a**3 / L**4 * (4 * L - 3 * a)
                        - b**2 / L**4 * (6 * L**2 - 8 * b * L + 3 * b**2)
                    )
                ],
            ]
        )

    def shear_force(self, x, L):
        if self.a <= x < self.a + self.l:
            return -self.q * (x - self.a)
        elif x > self.a + self.l:
            return -self.q * self.l
        return 0

    def bending_moment(self, x, L):
        V1 = self.q * self.l / L * (L - self.a - self.l / 2)
        V2 = self.q * self.l - V1
        if 0 <= x < self.a:
            return V1 * x
        elif x <= self.a + self.l:
            return V1 * x - 0.5 * self.q * (x - self.a) ** 2
        elif x <= L:
            return V2 * (L - x)
        return 0


class ConcentratedMoment(Load):
    """Defines a concentrated moment."""

    def __init__(self, M=0, a=0):
        super().__init__(2)
        self.M = M
        self.a = a

    def __str__(self):
        return f"Concentrated Moment\n   Value: {self.M} Nm\n   Position: {self.a} m"

    def equivalent_nodal_reactions(self, L):
        a, b = self.a, L - self.a
        return (self.M / L**2) * np.array(
            [
                [-6 * a * b / L],
                [b * (b - 2 * a)],
                [6 * a * b / L],
                [a * (a - 2 * b)],
            ]
        )

    def shear_force(self, x, L):
        return 0

    def bending_moment(self, x, L):
        if 0 <= x < self.a:
            return self.M / L * x
        elif self.a < x <= L:
            return self.M * (x / L - 1)
        return 0


class DisplacementReactionAssembly:
    def __init__(self, spans, supports, elements, loads):
        self.spans = spans
        self.supports = supports
        self.elements = elements
        self.loads = loads
        self.nodes = len(elements) + 1

    def assemble_nodal_displacement(self):
        """
        Assembly displacement matrix : di = ['d1y', 'θ1', 'd2y', 'θ2', 'd3y', 'θ3',...]
        """
        displacement = []
        for i, support in enumerate(self.supports):
            if support == 0:
                displacement.extend([0, 0])
            elif support == 1:
                displacement.extend([f"d{i+1}", 0])
            elif support == 2:
                displacement.extend([0, f"θ{i+1}"])
            elif support == 3:
                displacement.extend([f"d{i+1}", f"θ{i+1}"])
        return displacement

    def assemble_nodal_reactions(self, initial_reactions):
        """
        Assembly reaction matrix : R = ['F1y', 'M1', 'F2y', 'M2', 'F3y', 'M3',...]
        """
        reactions = []
        for i, support in enumerate(self.supports):
            if support == 0:
                reactions.extend([f"F{i+1}", f"M{i+1}"])
            elif support == 1:
                reactions.extend([0, f"M{i+1}"])
            elif support == 2:
                reactions.extend([f"F{i+1}", 0])
            elif support == 3:
                reactions.extend([0, 0])
        if initial_reactions:
            for i in range(len(reactions)):
                if initial_reactions[i]:
                    reactions[i] = initial_reactions[i]
        return reactions


class DisplacementReactionCalculated:
    def __init__(self):
        """
        If we know R, we don't know d.
        If we know d, we don't know R.
        [Ri] = [Ki][di]+[Qfi]
        R = ['0', '0', 'F2y', '0', 'F3y', 'M3', ...] --example
        d = ['d1', 'θ1', '0', 'θ2', '0', '0', ...] --example
        calculate d1, θ1, θ2,... exclude known == 0, 0, ...
        """

    def displacement(self, d0, K, Qf, R0):
        """
        d0 : list of assembly displacement
        K : np.array of global stiffness
        Qf : np.array of global FEF
        R0 = list of nodal external force/reaction
        """
        # If all fixed support
        if all(value == 0 for value in d0):
            di = np.array(d0)
        else:
            # index of unknowm displacement
            J = np.where(np.array(d0) != "0")[0].tolist()
            # index of reaction matched unknowm displacement
            I = J
            R1 = np.zeros((len(J), 1), dtype=float)  # --->Matrix [Ri]
            # Assembly Ki matched index
            K1 = np.zeros((len(I), len(J)))
            for i in range(0, len(I)):
                for j in range(0, len(J)):
                    K1[i][j] = K[I[i]][J[j]]  # --->Matrix [Ki]

            # Assembly Qfi index
            Q01 = []
            for item in I:
                q01 = [Qf[item][0]]
                Q01.append(q01)
            Q01 = np.array(Q01)  # --->Matrix [Qfi]

            # Assembly R index
            for i in range(0, len(I)):
                R1[i][0] = R0[I[i]]

            # Calculate displacement
            # [di] = inv[Ki][Ri]+(-1*[Qfi])
            K1 = np.linalg.inv(K1)  # inverse[K1]

            # unknown displacement
            di = np.dot(K1, R1 + (-1 * Q01))  # dot matrix
        return di  # Unit: displacement = m, θ = radian

    # [R] = [K][d] + [Qf]
    def reaction(self, d0, di, K, Qf):
        # If all fixed support
        if all(value == 0 for value in d0):
            dy = np.array(d0).reshape(-1, 1)

            # Calculated nodal reaction
            R = Qf  # dot matrix
        else:
            # index of d where di will be added
            ii = np.where(np.array(d0) != "0")[0].tolist()

            # added di to displacement d-matrix
            for i in range(len(ii)):
                d0[ii[i]] = di[i][0]

            # Convert to array(ix1)
            dy = np.array(d0).reshape(-1, 1)

            # Calculated nodal reaction
            R = np.dot(K, dy) + Qf  # dot matrix

        print(f"\n[INFO] Nodal Displacement, [dy] : d1, θ1, d2, θ2, ...:")
        print(f"{dy} m, radian,")

        print(f"\n[INFO] Nodal Force, [R] : F1, M1, F2, M2, ... :")
        print("[R] = [K][d] + [Qf]")
        print(f"{R*1e-3} kN, kN-m")

        return dy, R


class ForcesCalculator:
    def __init__(self, spans, elements, loads):
        self.spans = spans
        self.elements = elements
        self.loads = loads
        self.nodes = len(elements) + 1

    def global_stiffness_matrix(self):
        K = np.zeros((2 * self.nodes, 2 * self.nodes))
        for i, element in enumerate(self.elements):
            K[2 * i : 2 * i + 4, 2 * i : 2 * i + 4] += element.k
        print(f"\n[INFO] Global Stiffness Matrix : K")
        print(f"{K}")
        return K

    def local_fixed_end_forces(self):
        """
        QF: Equivalent nodal reactions of each stretch
        """
        forces = [np.zeros((4, 1)) for _ in range(len(self.spans))]
        for i in range(len(self.spans)):
            for load in self.loads[i]:
                forces[i] += load.equivalent_nodal_reactions(self.elements[i].L)
        print(f"\n[INFO] Local Fixed Force : \n{np.array(forces)*1e-3} kN, kN-m")
        return forces

    def global_fixed_end_forces(self, local_forces):
        global_forces = np.zeros((2 * self.nodes, 1))
        for i in range(len(self.spans)):
            global_forces[2 * i : 2 * i + 4] += local_forces[i]

        print(
            f"\n[INFO] Global Fixed Force : \n{np.array(global_forces)*1e-3} kN, kN-m"
        )
        return global_forces

    def internal_force(self, dy, QF):
        """
        dy : np.array of displacement
        QF : local fixed-end forces
        stretch : list of beam elements, each with a stiffness matrix 'k'
        """
        # Validate inputs
        u = []
        F = []

        for i in range(len(self.elements)):
            # Slice and reshape displacements
            local_displacement = dy[2 * i : 2 * i + 4, :]
            u.append(local_displacement)

            # Compute internal forces
            # Fi = [ki][ui]+[QFi]
            try:
                internal_force = self.elements[i].k @ local_displacement + QF[i]
                F.append(internal_force)
            except ValueError as e:
                print(f"Error in span {i+1}: {e}")
                raise

        print(
            f"\n[INFO] Internal Force, Fi = [ki][ui]+[QFi] : \n{np.array(F)*1e-3} kN, kN-m"
        )

        return u, F


class UserInput:
    def __init__(
        self,
    ) -> None:
        pass

    def spans_length(self):
        N = get_valid_integer(f"\nHow many span? : ")
        self.spans = get_valid_list_input(
            "Define array of spans in meters, ex 4 4 5: ", N
        ).tolist()
        return self.spans

    def supports_type(self):
        self.supports = []
        print(
            f"\nDefine support type for each node. You have {len(self.spans)+1} nodes"
        )
        while True:
            for i in range(1, len(self.spans) + 2):
                while True:

                    x = get_valid_integer(
                        f"Node {i} - Support Type = ? : [fixd=0, vert-scroll=1, pin=2, free=3] : "
                    )
                    if x in [0, 1, 2, 3]:
                        self.supports.append(x)
                        print(f"Support type = {self.supports}")
                        break
                    else:
                        print("Choose from [0, 1, 2, 3].Try again")

            if input(f"Try again!  Y|N : ").upper() == "Y":
                self.supports = []
            else:
                break
        return self.supports

    def external_loads(self):
        ## Nodal external loads
        """
        Define external loads for each node.
        For each node first define is Fy(kN), next is M(kN-m)
        Finaly we have [R0] = ['F1y', 'M1', 'F2y', 'M2', 'F3y', 'M3',...]
        """
        R0 = []
        print(
            f"\nDefine external loads(R0) at each node. You have {len(self.supports)} nodes"
        )
        while True:
            for i in range(1, len(self.supports) + 1):
                while True:
                    try:
                        f = get_valid_number(
                            f"Node {i} - External Fy(kN) = ?, Up-, Down+ : "
                        )
                        m = get_valid_number(
                            f"Node {i} - External Moment(kN-m) = ?, counterclockwise + : "
                        )
                        R0.append(f)
                        R0.append(m)
                        print(f"R0 = {R0}")
                        break
                    except Exception as e:
                        print("Badly input.Try again")

            if input(f"Try again!  Y|N : ").upper() == "Y":
                R0 = []
            else:
                break
        return R0

    def loads_type(self):
        # Define loads in each stretch
        """
        q = DistributedLoad (value, start, length), distance between the left end of the span and the start of the load
        P = PointLoad(value, position), Load position with respect to the left end of the section
        M = MomentConcentrated (value, position),  position of the moment with respect to the left end of the section'
        """
        print(f"\nDefine loads in each stretch : unit in --> kN, kN-m")
        print(f"You have {len(self.spans)} stretch")

        loads = [[] for i in range(0, len(self.spans))]  # [[], [], [],...]
        for i in range(0, len(loads)):
            print(f"Define load for stretch {i+1} :")
            while True:
                try:
                    type = input(
                        "Choose load type(P, q , M) or other keyboard type if none : "
                    ).lower()
                    if type in ("p", "q", "m"):
                        if type == "p":
                            value = (
                                get_valid_number(
                                    "Define point load P(kN) , Down+ Up- : "
                                )
                                * 1e3
                            )  # convert kN to N
                            x = get_valid_number(
                                "Define position x(m) with respect to the left end of the section : "
                            )
                            f = PointLoad(value, x)
                            loads[i].append(f)

                        elif type == "q":
                            value = (
                                get_valid_number(
                                    "Define value of line load q(kN/m) , Down+ Up- : "
                                )
                                * 1e3
                            )  # convert kN to N
                            start = get_valid_number(
                                "Define start point x(m) distance between the left end of the span and the start of the load : "
                            )
                            length = get_valid_number(
                                "Define length of line load l(m) : "
                            )
                            f = DistributedLoad(value, start, length)
                            loads[i].append(f)
                        else:
                            value = get_valid_number("Define moment m(N-m) :") * 1e3
                            x = get_valid_number(
                                "Define position x(m) relative to the left node of the stretch, counterclockwise + : "
                            )
                            f = ConcentratedMoment(value, x)
                            loads[i].append(f)
                    else:
                        print(f"None for stretch {i+1}")
                        break

                    if input(f"Finish for stretch {i+1} Y|N : ").upper() == "Y":
                        break
                except:
                    print("Badly input.Try again")
            print("#---------------------------------------------")
        return loads


class CurveValueCalculator:
    def __init__(self):
        pass

        # Calculate shear force values

    def shears(self, spans, stretch, loads, F):
        numS, Xt = xi_coordinate(spans)
        Shears = []
        for i in range(len(spans)):  # for each stretch
            # Shear like unsupported beams(Internal Shear)
            Q0 = np.zeros(numS)
            for j in range(len(loads[i])):  # consider all the loads of each stretch
                m = 0  # para enumerar las secciones
                for x in Xt[i]:  # to list the sections
                    Q0[m] += loads[i][j].shear_force(
                        x, stretch[i].L
                    )  # Calculate Qi given xi
                    m += 1

            # Shear at the extreme left, obtained from the calculation
            Q1 = F[i][0]

            # Total shear
            Shears.append(Q0 + Q1)

        # Maximum and minimum shear force values (in each stretch)
        maxShear = []  # Maximum shear for each stretch
        minShear = []  # Minimal shear for each stretch
        XmaxQ = []  # locations of the maxima in each stretch
        XminQ = []  # locations of the minimum in each stretch

        print(f"\nSHEAR")
        for i in range(len(spans)):
            maxQ = max(Shears[i])  # Máximo Shearnte
            minQ = min(Shears[i])  # Mínimo Shearnte
            print(f"Span {i+1} : maxQ = {maxQ/1000:.2f}, minQ = {minQ/1000:.2f} ,kN")

            maxShear.append(maxQ)
            minShear.append(minQ)
            indMaxQ = np.where(Shears[i] == maxQ)[0][0]  # index of maximum shear
            indMinQ = np.where(Shears[i] == minQ)[0][0]  # index of minimum shear
            XmaxQ.append(Xt[i][indMaxQ])  # location of maximum shear
            XminQ.append(Xt[i][indMinQ])  # location of minimum shear
            print(f"At location x = {Xt[i][indMaxQ]:.2f}, {Xt[i][indMinQ]:.2f} ,m")

        # Shear Force Values for Charts
        DFQ = []
        for i in range(len(spans)):
            # Values for list type DFQ
            # Shear = (Shears[i]).tolist() # We go to kN and we convert to list, N
            Shear = (
                Shears[i] / 1000
            ).tolist()  # We go to kN and we convert to list, kN
            DFQ += Shear

        return DFQ, maxShear, minShear, XmaxQ, XminQ

    # Calculate bending moment values
    def moments(self, spans, stretch, loads, F):
        numS, Xt = xi_coordinate(spans)
        Moments = []
        for i in range(len(spans)):  # for each stretch
            # Moments like stretchs simply supported
            M0 = np.zeros(numS)
            for j in range(len(loads[i])):  # consider all the loads of each stretch
                m = 0  # to list the sections
                for x in Xt[i]:  # go through the sections
                    M0[m] += loads[i][j].bending_moment(x, stretch[i].L)
                    m += 1

            # Moments due to embedment or continuity of the beam
            M1 = -F[i][1] + (F[i][3] + F[i][1]) / stretch[i].L * Xt[i]

            # Total moment
            Moments.append(M0 + M1)

        # Maximum and minimum bending moment values (in each stretch)
        maxMoment = []  # Maximum moment in each stretch
        minMoment = []  # Minimum moment in each stretch
        XmaxF = []  # locations of maximum moments by stretch
        XminF = []  # locations of the minimum moments by stretch
        print(f"\nMOMENT")
        for i in range(len(spans)):
            maxF = max(Moments[i])  # Máximo flector
            minF = min(Moments[i])  # Mínimo flector
            print(f"Span {i+1} : maxF = {maxF/1000:.2f}, minF = {minF/1000:.2f} ,kN-m")

            maxMoment.append(-maxF)
            minMoment.append(-minF)
            indMaxF = np.where(Moments[i] == maxF)[0][0]  # index of maximum bending
            indMinF = np.where(Moments[i] == minF)[0][0]  # index of minimum bending
            XmaxF.append(Xt[i][indMaxF])  # location of maximum bending
            XminF.append(Xt[i][indMinF])  # location of minimum bending
            print(f"At location x = {Xt[i][indMaxF]:.2f}, {Xt[i][indMinF]:.2f} ,m")

        # Bending moment values for graphs
        DMF = []
        for i in range(len(spans)):
            Flex = (-1 * Moments[i] / 1000).tolist()  # ***
            DMF += Flex

        return DMF, maxMoment, minMoment, XmaxF, XminF


class BeamAnalysis:
    def __init__(self, E, I):
        userInput = UserInput()
        report = Report()

        self.E = E  # GPa
        self.I = I  # m4
        self.spans = userInput.spans_length()
        self.supports = userInput.supports_type()
        self.R0 = userInput.external_loads()
        self.loads = userInput.loads_type()

        report.report(self.spans, self.supports, self.R0, self.loads)

        self.coords = CurveValueCalculator()

    def calculators_force(self):
        # Bernoulli Beam
        print(f"\n[INFO] Bernoulli Beam : ")
        self.stretch = []
        for i in range(len(self.spans)):
            st = BeamB(self.E, self.I, self.spans[i])
            print(f"K{i+1}")
            print(f"{st.k}")
            self.stretch.append(st)

        # Calculate stiffness K, Fixend forces
        forces = ForcesCalculator(self.spans, self.stretch, self.loads)

        K = forces.global_stiffness_matrix()
        QF = forces.local_fixed_end_forces()
        Qf = forces.global_fixed_end_forces(QF)

        # Calculate the displacement and reaction forces
        dr_assembly = DisplacementReactionAssembly(
            self.spans, self.supports, self.stretch, self.loads
        )
        d0 = dr_assembly.assemble_nodal_displacement()
        R = dr_assembly.assemble_nodal_reactions(self.R0)

        dr_calculator = DisplacementReactionCalculated()
        di = dr_calculator.displacement(d0, K, Qf, R)
        dy, Ri = dr_calculator.reaction(d0, di, K, Qf)

        u, self.F = forces.internal_force(dy, QF)

    def plot_diagram(self):
        plot = Plot()

        # Calculate shears coordinate for plotting
        shearDFQ, maxShear, minShear, XmaxQ, XminQ = self.coords.shears(
            self.spans, self.stretch, self.loads, self.F
        )

        # Calculate moments coordinate for plotting
        momentDMF, maxMoment, minMoment, XmaxF, XminF = self.coords.moments(
            self.spans, self.stretch, self.loads, self.F
        )

        # Total length of the beam
        Ltotal = 0
        for i in range(len(self.stretch)):
            Ltotal += self.stretch[i].L

        # Plot method
        fig = plot.plot_curves(
            self.spans,
            Ltotal,
            self.stretch,
            shearDFQ,
            momentDMF,
            maxShear,
            minShear,
            XmaxQ,
            XminQ,
            maxMoment,
            minMoment,
            XmaxF,
            XminF,
        )

        fig.show()
        return fig


class Report:
    def __init__(
        self,
    ) -> None:
        pass

    def report(self, spans, supports, R0, loads):
        print("[INFO] Materials Properties :")
        print(f"Es = {E*1e3:.2f} MPa, ")

        print(f"\n[INFO] GEOMETRY :")
        for i in range(len(spans)):
            print(f"Span {i+1} : {spans[i]:.2f} m")

        support_type = {
            "0": "Fixed: Embedement",
            "1": "Allows vertical scroll",
            "2": "Pined: Allow rotation but no scroll",
            "3": "Free: Cantilever",
        }

        for i in range(len(spans) + 1):
            print(f"Support {i+1} = {support_type.get(str(supports[i]))}")

        print(f"\n[INFO] NODAL EXTERNAL FORCE, R0 :")
        # Define known/unknown vector of external force/reaction (+Up, -Down)
        print(f"[R0] = ['F1y', 'M1', 'F2y', 'M2', 'F3y', 'M3',...]")
        print(f"[R0] = {R0}  N, N-m...")

        print(f"\n[INFO] LOADS :")
        for i in range(0, len(loads)):
            print(f"Load in stretch {i+1} : ")
            print(*loads[i], sep="\n")


# =========================================================================================
# Main Functionality
if __name__ == "__main__":

    print("=============== BEAM ANALYSIS : METRIX STIFFNESS METHOD ===============")
    print("Code adopt from Prof. Fredy Gabriel Ramírez Villanueva repository")
    print("https://github.com/SirPrime/MatrixAnalysis-Beams.git")
    print("")
    print(
        "Tutorial: https://www.youtube.com/watch?v=hCmXwMQWafk&list=LL&index=6&t=3642s"
    )
    print(
        "https://www.erbakan.edu.tr/storage/files/department/insaatmuhendisligi/editor/DersSayfalari/YapSt2/06_Matrix_Beam.pdf"
    )

    E = 200  # GPa
    I = (1000 * np.power(24, 3)) * 1e-8  # m4

    analysis = BeamAnalysis(E, I)
    analysis.calculators_force()
    analysis.plot_diagram()

"""
python analysis/beam_analysis.py
"""
