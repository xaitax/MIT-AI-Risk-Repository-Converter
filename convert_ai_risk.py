#!/usr/bin/env python3

"""
MIT AI Risk Repository Converter

Downloads an AI risk repository from a default Google Sheets link (or uses
a user-provided XLSX file), then filters and converts it to JSON, including
metadata from the "Included resources" sheet.

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


def load_excel_content(file_source, sheet_name: str, header_row: int = 0) -> pd.DataFrame:
    """
    Loads the specified sheet from the Excel content into a DataFrame. `file_source` can be:
      - A BytesIO object (downloaded content)
      - A local file path (string)
    """
    source_type = file_source if isinstance(
        file_source, str) else "downloaded data"
    print(f"Reading sheet '{sheet_name}' from {source_type}")
    return pd.read_excel(file_source, sheet_name=sheet_name, header=header_row)


def filter_and_convert_to_json(main_df: pd.DataFrame, metadata_df: pd.DataFrame) -> str:
    """
    Merges the main DataFrame with metadata, adds a unique ID, and converts to JSON.
    Returns the JSON string.
    """
    print("Preparing metadata DataFrame...")

    metadata_df = metadata_df.rename(
        columns={col: f"Metadata_{col}" if col !=
                 "QuickRef" else col for col in metadata_df.columns}
    )

    print("Merging main DataFrame with metadata based on 'QuickRef'...")
    merged_df = pd.merge(main_df, metadata_df, on="QuickRef", how="left")

    merged_df.insert(0, "ID", range(1, len(merged_df) + 1))

    metadata_columns = [
        "Metadata_Included",
        "Metadata_Paper_ID",
        "Metadata_Title",
        "Metadata_Authors (full)",
        "Metadata_Authors (short)",
        "Metadata_Year",
        "Metadata_DOI",
        "Metadata_URL",
        "Metadata_Citations (28 May 2024)",
        "Metadata_Cites/yr",
        "Metadata_Item type"
    ]

    main_columns = [
        "ID",
        "Title",
        "QuickRef",
        "Ev_ID",
        "Category level",
        "Risk category",
        "Risk subcategory",
        "Description",
        "Additional ev.",
        "Entity",
        "Intent",
        "Timing",
        "Domain",
        "Sub-domain"
    ]

    final_columns = [col for col in metadata_columns +
                     main_columns if col in merged_df.columns]
    df_filtered = merged_df[final_columns]

    print("Converting merged DataFrame to JSON...")
    return df_filtered.to_json(orient="records", indent=4)


def main():
    display_banner()

    parser = argparse.ArgumentParser(
        description="Download/Load AI Risk Repository XLSX and convert to filtered JSON, including metadata."
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
        default="Filtered_AI_Risk_Database_with_Metadata.json"
    )
    parser.add_argument(
        "--sheet-name", "-s",
        help="Name of the main sheet to load from the Excel file.",
        default="AI Risk Database v2"
    )
    parser.add_argument(
        "--metadata-sheet", "-m",
        help="Name of the metadata sheet to load from the Excel file.",
        default="Included resources"
    )

    args = parser.parse_args()

    if args.input:
        file_source = args.input.strip()
    else:
        print("No input provided; using default Google Sheets link.")
        file_source = download_google_sheet(DEFAULT_GOOGLE_SHEET_EXPORT)

    try:
        ai_risk_database = load_excel_content(
            file_source, sheet_name=args.sheet_name, header_row=2)

        metadata = load_excel_content(
            file_source, sheet_name=args.metadata_sheet, header_row=11)
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        sys.exit(1)

    if 'QuickRef' not in ai_risk_database.columns:
        print("Error: 'QuickRef' column not found in the main sheet.")
        sys.exit(1)
    if 'QuickRef' not in metadata.columns:
        print("Error: 'QuickRef' column not found in the metadata sheet.")
        sys.exit(1)

    filtered_json_str = filter_and_convert_to_json(ai_risk_database, metadata)

    output_path = args.output
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json_file.write(filtered_json_str)
        print(f"Filtered JSON with metadata saved to {output_path}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
