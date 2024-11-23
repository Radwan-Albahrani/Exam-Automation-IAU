import os
from logging import getLogger

import numpy as np
import pandas as pd
from camelot import read_pdf
from google.auth.credentials import TokenState
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pandas import DataFrame
from protocols import CalendarService

logger = getLogger("pytorch")
logger.disabled = True

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authorize_and_return_service() -> CalendarService | None:
    creds = None
    if os.path.exists("secret/token.json"):
        creds = Credentials.from_authorized_user_file("secret/token.json")

    if not creds or not creds.valid:
        if creds and creds.token_state != TokenState.INVALID and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print_error(f"An error occurred: {e}")
                return
        else:
            flow = InstalledAppFlow.from_client_secrets_file("secret/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("secret/token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service: CalendarService = build("calendar", "v3", credentials=creds)

        return service
    except HttpError as e:
        print_error(f"An error occurred: {e}")
        return None


def get_exams_table(file_path: str) -> DataFrame:
    file_path = file_path.strip('"')
    if not os.path.exists(file_path):
        print_error("The file does not exist")
        exit()
    try:
        tables = read_pdf(file_path, pages="all")
    except Exception as e:
        print_error(f"An error occurred: {e}")
        exit()
    if tables is None:
        print_error("No tables were found")
        exit()
    if len(tables) == 0:
        print_error("No tables were found")
        exit()

    try:
        exam_table = tables[0].df
        exam_table.columns = exam_table.iloc[0]
        exam_table = exam_table[1:].reset_index(drop=True)

        if exam_table is None:
            print_error("The table was not found")
            exit()

        exam_table = _clean_date(exam_table)
        exam_table.drop(columns=[col for col in exam_table.columns if "Unnamed" in col], inplace=True)
        return exam_table
    except Exception as e:
        print_error(
            f"""
Information Extraction Failed with error: {e}.

Here are some tips to ensure your image is processed correctly:
    1. Ensure the image is clear and has a high resolution.
    2. Ensure the table includes all the columns EXCEPT the "APPROVED" or "DRAFT" sections
    3. Ensure the image is edge to edge. A little white space is fine, but too much can cause issues.
    4. When taking the screenshot, ensure the table is the only thing in the image.

Once you have made the necessary changes, try again.
"""
        )
        exit()


def _clean_date(df):
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def extract_day_date(value):
        if pd.isnull(value):
            return pd.Series({"Day": np.nan, "Date_only": np.nan})
        value = str(value).strip()
        if "\r" in value:
            # Entry contains both day and date
            day_part, date_part = value.split("\r", 1)
            return pd.Series({"Day": day_part.strip(), "Date_only": date_part.strip()})
        elif value in days_of_week:
            # Entry is only a day name
            return pd.Series({"Day": value, "Date_only": np.nan})
        else:
            # Entry is only a date
            return pd.Series({"Day": np.nan, "Date_only": value})

    df[["Day", "Date_only"]] = df["Date"].apply(extract_day_date)
    df["Day"] = df["Day"].astype("object")
    df["Date_parsed"] = pd.to_datetime(df["Date_only"], dayfirst=True, errors="coerce")

    def forward_fill_dates(df):
        last_known_date = None
        for idx in df.index:
            if pd.notnull(df.at[idx, "Date_parsed"]):
                # Known date, update last_known_date
                last_known_date = df.at[idx, "Date_parsed"]
            elif pd.notnull(df.at[idx, "Day"]) and last_known_date is not None:
                # Missing date but day is known
                next_date = last_known_date + pd.Timedelta(days=1)
                while next_date.strftime("%A") != df.at[idx, "Day"]:
                    next_date += pd.Timedelta(days=1)
                df.at[idx, "Date_parsed"] = next_date
                last_known_date = next_date
        return df

    def backward_fill_dates(df):
        last_known_date = None
        for idx in reversed(df.index):
            if pd.notnull(df.at[idx, "Date_parsed"]):
                # Known date, update last_known_date
                last_known_date = df.at[idx, "Date_parsed"]
            elif pd.notnull(df.at[idx, "Day"]) and last_known_date is not None:
                # Missing date but day is known
                prev_date = last_known_date - pd.Timedelta(days=1)
                while prev_date.strftime("%A") != df.at[idx, "Day"]:
                    prev_date -= pd.Timedelta(days=1)
                df.at[idx, "Date_parsed"] = prev_date
                last_known_date = prev_date
        return df

    df = forward_fill_dates(df)
    df = backward_fill_dates(df)
    df.loc[df["Day"].isnull() & df["Date_parsed"].notnull(), "Day"] = df["Date_parsed"].dt.strftime("%A")
    df["Date"] = df.apply(
        lambda row: (
            f"{row['Day']} {row['Date_parsed'].strftime('%d/%m/%Y')}" if pd.notnull(row["Date_parsed"]) else np.nan
        ),
        axis=1,
    )

    df.drop(["Date_only", "Date_parsed", "Day"], axis=1, inplace=True)

    df["Date"] = df["Date"].ffill()
    df["Time"] = df["Time"].replace("", np.nan)
    df["Time"] = df["Time"].ffill()
    df["Course name"] = df["Course name"].replace("", np.nan)
    df = df.dropna(subset=["Course name"])

    return df


def get_major_and_level():
    major = input("Enter the major: ")
    level = input("Enter the level: ")

    try:
        level = int(level)
    except ValueError:
        print_error("Invalid level. Level must be an integer")
        exit()
    if level < 1 or level > 10:
        print_error("Invalid level. Level must be between 1 and 10")
        exit()

    return major, level


def print_error(text: str):
    colors = {
        "red": "\033[91m",
        "end": "\033[00m",
    }

    print(f"{colors['red']}{text}{colors['end']}")


def print_success(text: str):
    colors = {
        "green": "\033[92m",
        "end": "\033[00m",
    }

    print(f"{colors['green']}{text}{colors['end']}")
