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
    # Display cases
    # print(
    #     f"""
    #     label = 1 : major axis, H,C : web=C, flang=C --> Y, LTB
    #     label = 2 : major axis, H : web=C, flang=NC,S --> Y, LTB, FLB
    #     lebel = 3 : major axis, H : web=NC, --> Yc, Yt, LTB, FLB, TFY
    #     """
    # )
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
