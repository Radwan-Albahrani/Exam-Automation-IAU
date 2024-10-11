import os
from math import e
from typing import cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from jpype import JVMNotFoundException
from pandas import DataFrame
from protocols import CalendarService
from tabula.io import read_pdf

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authorize_and_return_service() -> CalendarService | None:
    creds = None
    if os.path.exists("secret/token.json"):
        creds = Credentials.from_authorized_user_file("secret/token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
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
        tables = read_pdf(file_path, pages="all", multiple_tables=True)
    except JVMNotFoundException:
        print("You must instal JVM to use tabula-py")
        exit()
    except Exception:
        print_error(f"An error occurred: {e}")
        exit()
    if tables is None:
        print_error("No tables were found")
        exit()
    if len(tables) == 0:
        print_error("No tables were found")
        exit()

    tables = cast(list[DataFrame], tables)

    exam_table = tables[1]

    if exam_table is None:
        print_error("The table was not found")
        exit()
    # fill na of specific   column

    exam_table["Date"] = exam_table["Date"].ffill()
    exam_table["Time"] = exam_table["Time"].ffill()
    exam_table.drop("Unnamed: 0", axis=1, inplace=True)

    return exam_table


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

    print(f"{colors["red"]}{text}{colors["end"]}")


def print_success(text: str):
    colors = {
        "green": "\033[92m",
        "end": "\033[00m",
    }

    print(f"{colors["green"]}{text}{colors["end"]}")
