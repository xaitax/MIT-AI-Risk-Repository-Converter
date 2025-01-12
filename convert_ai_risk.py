#!/usr/bin/env python3

"""
MIT AI Risk Repository Converter

Downloads an AI risk repository from a default Google Sheets link (or uses
a user-provided XLSX file), then filters and converts it to JSON.

Usage:
  python convert_ai_risk.py [--input FILE_OR_URL] [--output OUTPUT_JSON] [--sheet-name SHEET_NAME]

Examples:
  python convert_ai_risk.py
  python convert_ai_risk.py --input path/to/local.xlsx
  python convert_ai_risk.py --input https://docs.google.com/spreadsheets/d/.../export?format=xlsx
  python convert_ai_risk.py --output my_filtered.json
  python convert_ai_risk.py --sheet-name "AI Risk Database v2"
"""

import argparse
import sys
from io import BytesIO
import requests
import pandas as pd

BLUE = "\033[94m"
ENDC = "\033[0m"

DEFAULT_GOOGLE_SHEET_EXPORT = (
    "https://docs.google.com/spreadsheets/d/1evwjF4XmpykycpeZFq0FUteEAt7awx2i2oE6kMrV_xE/export?format=xlsx"
)

def display_banner():
    banner = f"""
{BLUE}MIT AI Risk Repository Converter
A tool for downloading and converting MIT's AI Risk Repository to JSON.
Alexander Hagenah / @xaitax / ah@primepage.de{ENDC}
"""
    print(banner)

def download_google_sheet(url: str) -> BytesIO:
    """
    Downloads a Google Sheet as an XLSX file and returns a BytesIO object.
    Raises an exception if the download fails.
    """
    print(f"Downloading Google Sheet from: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def load_excel_content(file_source, sheet_name: str) -> pd.DataFrame:
    """
    Loads the Excel content into a DataFrame. `file_source` can be:
      - A BytesIO object (downloaded content)
      - A local file path (string)
    """
    source_type = file_source if isinstance(file_source, str) else "downloaded data"
    print(f"Reading sheet '{sheet_name}' from {source_type}")
    return pd.read_excel(file_source, sheet_name=sheet_name, header=2)

def filter_and_convert_to_json(df: pd.DataFrame) -> str:
    """
    Filters the given DataFrame, adds a unique ID, and converts to JSON.
    Returns the JSON string.
    """
    df.insert(0, "ID", range(1, len(df) + 1))

    columns_to_keep = [
        "ID", "Title", "QuickRef", "Ev_ID", "Category level", "Risk category",
        "Risk subcategory", "Description", "Additional ev.",
        "Entity", "Intent", "Timing", "Domain", "Sub-domain"
    ]

    df_filtered = df[columns_to_keep]

    return df_filtered.to_json(orient="records", indent=4)

def main():
    display_banner()

    parser = argparse.ArgumentParser(
        description="Download/Load AI Risk Repository XLSX and convert to filtered JSON."
    )
    parser.add_argument(
        "--input", "-i",
        help=(
            "Path to a local XLSX file OR a direct export URL from Google Sheets. "
            "If not provided, the default Google Sheet will be downloaded."
        ),
        default=None
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file name.",
        default="Filtered_AI_Risk_Database_with_ID.json"
    )
    parser.add_argument(
        "--sheet-name", "-s",
        help="Name of the sheet to load from the Excel file.",
        default="AI Risk Database v2"
    )

    args = parser.parse_args()

    if args.input:
        file_source = args.input.strip()
    else:
        print("No input provided; using default Google Sheets link.")
        file_source = download_google_sheet(DEFAULT_GOOGLE_SHEET_EXPORT)

    try:
        ai_risk_database = load_excel_content(file_source, sheet_name=args.sheet_name)
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        sys.exit(1)

    filtered_json_str = filter_and_convert_to_json(ai_risk_database)

    output_path = args.output
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json_file.write(filtered_json_str)
        print(f"Filtered JSON saved to {output_path}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
