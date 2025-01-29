from utils import get_valid_integer, get_valid_list_input


def calculate_G_node(Ic, Lc, Ib, Lb):
    """
    Calculate the relative stiffness (G-value) for a node.

    Parameters:
    - Ic: List of column flexural rigidities (EI_c)
    - Lc: List of column lengths (L_c)
    - Ib: List of beam flexural rigidities (EI_b)
    - Lb: List of beam lengths (L_b)

    Returns:
    - G-value for the node.
    """
    # Ensure all input lists have the same length
    if not (len(Ic) == len(Lc)) or not (len(Ib) == len(Lb)):
        raise ValueError("Column and beam input lists must have matching lengths.")

    # Compute sum(EIc / Lc) for all columns
    sum_col = sum(Ic[i] / Lc[i] for i in range(len(Ic)))

    # Compute sum(EIb / Lb) for all beams
    sum_beam = sum(Ib[i] / Lb[i] for i in range(len(Ib)))

    # Compute G-value (Avoid division by zero)
    G = sum_col / sum_beam if sum_beam != 0 else float("inf")

    return G


def call():
    N = get_valid_integer("How many columns at node? : ")
    Ic = get_valid_list_input("Define array of Ic in cm4 : ", N)
    Lc = get_valid_list_input("Define array of Lc in m : ", N) * 1e2

    N = get_valid_integer("How many beams at node? : ")
    Ib = get_valid_list_input("Define array of Ib in cm4 : ", N)
    Lb = get_valid_list_input("Define array of Lb in m : ", N) * 1e2

    G_value = calculate_G_node(Ic, Lc, Ib, Lb)
    print("G-value for the node:", G_value)


if __name__ == "__main__":
    print("[REMINDER] No beams --> G = 10 : ")
    call()
