import os
import re
import numpy as np
import pandas as pd
from tabulate import tabulate

CURR = os.getcwd()


def toNumpy(x):
    x = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", x)
    return np.array([float(n) for n in x])


def get_valid_integer(prompt):
    while True:
        user_input = input(prompt)
        if user_input.isdigit():
            return int(user_input)
        else:
            print("Invalid input. Please enter a valid number.")


def get_valid_number(prompt):
    while True:
        user_input = input(prompt)
        try:
            # Try to convert the input to a float
            value = float(user_input)
            return value
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def get_valid_list_input(prompt, N):
    while True:
        user_input = input(prompt)
        try:
            array = toNumpy(user_input)
            if len(array) == 0:
                raise ValueError("No valid numbers found.")
            if len(array) != N:
                raise ValueError(f"Input length is {len(array)} but must be {N}.")

            confirm = input("Confirm? Y|N: ").strip().upper()
            if confirm == "Y":
                return array  # Return the valid numpy array if confirmed
            else:
                print("Let's try again.")

        except ValueError as e:
            print(
                f"Invalid input: {e}. Please enter a space-separated list of numbers."
            )


def df_generator(section):
    # Dataframe of steel section
    df = pd.read_csv(os.path.join(CURR, "data/sections", section))

    # Drop the unit row (2nd row)
    df = df.iloc[1:]

    # Convert numeric columns to numbers
    numeric_columns = df.columns[1:]  # Exclude the first column
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")

    return df


def display_df(df, index=False):
    print(f"\nDATABASE")
    print(
        tabulate(
            df,
            headers=df.columns,
            floatfmt=".2f",
            showindex=index,
            tablefmt="psql",
        )
    )


def select_label(options, list):
    print(options)
    while True:
        label = get_valid_integer("label = ? : ")
        if label in list:
            break
        else:
            print(f"Label not in {list} Try again!")
    return label


def select_flange(list):
    while True:
        flange = input("flange = ? : [C, NC, S] : ").upper()
        if flange in list:
            break
        else:
            print(f"Flange not in {list} Try again!")
    return flange


def try_section(loads, materials, section):
    df = df_generator(section)

    # Calculated required Z values
    Zx = loads.Mux * 1000 / (0.9 * materials.Fy)
    Zy = loads.Muy * 1000 / (0.75 * materials.Fy)
    print(f"\nInitial Z required = {Zx:.2f} cm3")
    print(f"Initial A required = {(loads.Pu /  materials.Fy) * 10:.2f} cm2")

    df_filter = df[(df["Zx"] > Zx) & (df["Zy"] > Zy)]
    display_df(df_filter.sort_values(by=["Zx"])[:20], index=True)

    # Try section
    i = get_valid_integer("PLEASE SELECT SECTION : ")
    section = df.iloc[i - 1]
    display_df(df.filter(items=[i], axis=0), index=True)
    return section


def try_pipe(loads, materials, section):
    # DN,D,T,W,A,I,Z,i
    df = df_generator(section)

    # Calculated required Z values
    Zx = loads.Mux * 1000 / (0.9 * materials.Fy)
    Zy = loads.Muy * 1000 / (0.75 * materials.Fy)
    print(f"\nInitial Z required = {Zx:.2f} cm3")
    print(f"Initial A required = {(loads.Pu /  materials.Fy) * 10:.2f} cm2")

    df_filter = df[(df["Z"] > Zx) & (df["Z"] > Zy)]
    display_df(df_filter.sort_values(by=["Z"])[:20], index=True)

    # Try section
    i = get_valid_integer("PLEASE SELECT SECTION : ")
    section = df.iloc[i - 1]
    display_df(df.filter(items=[i], axis=0), index=True)
    return section
