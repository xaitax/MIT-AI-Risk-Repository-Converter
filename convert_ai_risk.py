#!/usr/bin/env python3

"""
MIT AI Risk Repository Converter

Loads an AI risk repository from a local XLSX file, then filters and converts
it to JSON, including metadata from the "Included resources" sheet.

Usage:
  python convert_ai_risk.py [--input FILE] [--output OUTPUT_JSON] [--sheet-name SHEET_NAME]

Examples:
  python convert_ai_risk.py
  python convert_ai_risk.py --input path/to/local.xlsx
  python convert_ai_risk.py --output my_filtered.json
  python convert_ai_risk.py --sheet-name "AI Risk Database v3"
"""

import argparse
import sys
import pandas as pd

BLUE = "\033[94m"
ENDC = "\033[0m"

MAIN_SHEET_HEADER_ROW = 2
METADATA_SHEET_HEADER_ROW = 11
DEFAULT_INPUT_FILE = "The AI Risk Repository V3_26_03_2025.xlsx"

def display_banner():
    banner = f"""
{BLUE}MIT AI Risk Repository Converter
A tool for converting MIT's AI Risk Repository to JSON.
Alexander Hagenah / @xaitax / ah@primepage.de{ENDC}
"""
    print(banner)


def load_excel_content(file_source, sheet_name: str, header_row: int = 0) -> pd.DataFrame:
    print(f"Reading sheet '{sheet_name}' from {file_source}")
    return pd.read_excel(file_source, sheet_name=sheet_name, header=header_row)


def rename_columns(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    return df.rename(columns=column_mapping)


def validate_columns(df: pd.DataFrame, required_columns: list, sheet_name: str):
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns {missing_columns} in {sheet_name}.")


def load_and_prepare_sheet(file_source, sheet_name, header_row, mapping):
    df = load_excel_content(file_source, sheet_name, header_row)
    df = rename_columns(df, mapping)
    validate_columns(df, ["quickRef"], sheet_name)
    return df


def merge_and_transform(main_df: pd.DataFrame, metadata_df: pd.DataFrame) -> pd.DataFrame:
    print("Merging main DataFrame with metadata based on 'quickRef'...")
    merged_df = pd.merge(main_df, metadata_df, on="quickRef", how="left")
    merged_df.insert(0, "id", range(1, len(merged_df) + 1))

    metadata_columns = [
        "included", "paperId", "title", "authorsFull", "authorsShort",
        "year", "doi", "url", "citations", "citesPerYear", "itemType"
    ]
    metadata_columns = [col for col in metadata_columns if col in merged_df.columns]

    category_columns = ["categoryLevel", "riskCategory", "riskSubcategory"]
    category_columns = [col for col in category_columns if col in merged_df.columns]

    merged_df["metadata"] = merged_df[metadata_columns].to_dict(orient="records")
    merged_df["category"] = merged_df[category_columns].to_dict(orient="records")

    merged_df.drop(columns=metadata_columns + category_columns, inplace=True)
    return merged_df


def convert_to_json(df: pd.DataFrame) -> str:
    print("Converting merged DataFrame to JSON...")
    return df.to_json(orient="records", indent=4)


def save_json_to_file(json_data: str, output_path: str):
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json_file.write(json_data)
        print(f"Filtered JSON with metadata saved to {output_path}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        sys.exit(1)


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Load AI Risk Repository XLSX and convert to filtered JSON, including metadata."
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to a local XLSX file. Defaults to latest local copy.",
        default=DEFAULT_INPUT_FILE
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file name.",
        default="data.json"
    )
    parser.add_argument(
        "--sheet-name", "-s",
        help="Name of the main sheet to load from the Excel file.",
        default="AI Risk Database v3"
    )
    parser.add_argument(
        "--metadata-sheet", "-m",
        help="Name of the metadata sheet to load from the Excel file.",
        default="Included resources"
    )
    return parser.parse_args()


def main():
    display_banner()
    args = parse_cli_args()

    try:
        file_source = args.input.strip()

        main_sheet_mapping = {
            "QuickRef": "quickRef",
            "Title": "title",
            "Description": "description",
            "Ev_ID": "evidenceId",
            "Category level": "categoryLevel",
            "Risk category": "riskCategory",
            "Risk subcategory": "riskSubcategory",
            "Additional ev.": "additionalEvidence",
            "Entity": "entity",
            "Intent": "intent",
            "Timing": "timing",
            "Domain": "domain",
            "Sub-domain": "subDomain"
        }

        metadata_mapping = {
            "QuickRef": "quickRef",
            "Included": "included",
            "Paper_ID": "paperId",
            "Title": "title",
            "Authors (full)": "authorsFull",
            "Authors (short)": "authorsShort",
            "Year": "year",
            "DOI": "doi",
            "URL": "url",
            "Citations (28 May 2024)": "citations",
            "Cites/yr": "citesPerYear",
            "Item type": "itemType"
        }

        ai_risk_database = load_and_prepare_sheet(
            file_source, args.sheet_name, MAIN_SHEET_HEADER_ROW, main_sheet_mapping
        )
        metadata = load_and_prepare_sheet(
            file_source, args.metadata_sheet, METADATA_SHEET_HEADER_ROW, metadata_mapping
        )

        merged_data = merge_and_transform(ai_risk_database, metadata)
        filtered_json = convert_to_json(merged_data)
        save_json_to_file(filtered_json, args.output)

    except Exception as e:
        print(f"Error processing data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
