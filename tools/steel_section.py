import os
import pandas as pd

CURR = os.getcwd()


def section_generator(section):
    # Dataframe of steel section
    df = pd.read_csv(os.path.join(CURR, "data/sections", section))

    # Convert string to numeric depend on selected section
    # CCL
    if section == "Light_Lip_Channel.csv" or section == "Double_Light_Lip_Channel.csv":
        col = [
            "h",
            "b",
            "d",
            "t",
            "A",
            "Wt",
            "Cx",
            "Cy",
            "Ix",
            "Iy",
            "ix",
            "iy",
            "Zx",
            "Zy",
            "Sx",
            "Sy",
        ]
        df[col] = df[col].apply(pd.to_numeric, errors="coerce", axis="columns")

    # Tube
    if (section == "Rectangular_Tube.csv") | (section == "Square_Tube.csv"):
        col = ["h", "b", "t", "Wt", "A", "Ix", "Iy", "Zx", "Zy", "rx", "ry"]
        df[col] = df[col].apply(pd.to_numeric, errors="coerce", axis="columns")

    # CHN
    if section == "Channels.csv":
        col = [
            "H",
            "B",
            "tf",
            "tw",
            "r1",
            "r2",
            "A",
            "Wt",
            "Cx",
            "Cy",
            "Ix",
            "Iy",
            "rx",
            "ry",
            "Zx",
            "Zy",
        ]
        df[col] = df[col].apply(pd.to_numeric, errors="coerce", axis="columns")

    # Pipe
    if section == "Pipe.csv":
        col = ["D", "T", "W", "A", "I", "Zx", "i"]
        df[col] = df[col].apply(pd.to_numeric, errors="coerce", axis="columns")

    # Double equal-angles
    if section == "Double_Equal_Angles.csv":
        col = [
            "x",
            "t",
            "r1",
            "r2",
            "A",
            "wt",
            "Cx",
            "Cy",
            "Ix",
            "Iy",
            "rx",
            "ry",
            "Zx",
            "Zy",
        ]
        df[col] = df[col].apply(pd.to_numeric, errors="coerce", axis="columns")

    if section == "Equal_Angles.csv":
        col = [
            "x",
            "t",
            "r1",
            "r2",
            "A",
            "wt",
            "Cx",
            "Cy",
            "Ix",
            "Iy",
            "ix",
            "iy",
            "rx",
            "ry",
            "ru",
            "rv",
            "Zx",
            "Zy",
        ]
        df[col] = df[col].apply(pd.to_numeric, errors="coerce", axis="columns")

    return df
