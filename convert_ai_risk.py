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
  python convert_ai_risk.py --sheet-name "AI Risk Database v4"
"""

import argparse
import json
import re
import sys
import pandas as pd

BLUE = "\033[94m"
ENDC = "\033[0m"

MAIN_SHEET_HEADER_ROW = 2
METADATA_SHEET_HEADER_ROW = 11
DEFAULT_INPUT_FILE = "The AI Risk Repository V4_03_12_2025.xlsx"

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


def parse_coded_field(value):
    """Parse fields like '2 - AI' into {'code': 2, 'label': 'AI'}"""
    if pd.isna(value) or value is None:
        return None
    value = str(value).strip()
    match = re.match(r'^(\d+)\s*-\s*(.+)$', value)
    if match:
        return {"code": int(match.group(1)), "label": match.group(2).strip()}
    return {"code": None, "label": value}


def parse_domain(value):
    """Parse fields like '6. Socioeconomic and Environmental' into {'code': '6', 'label': '...'}"""
    if pd.isna(value) or value is None:
        return None
    value = str(value).strip()
    match = re.match(r'^(\d+)\.\s*(.+)$', value)
    if match:
        return {"code": match.group(1), "label": match.group(2).strip()}
    return {"code": None, "label": value}


def parse_subdomain(value):
    """Parse fields like '6.5 > Governance failure' into {'code': '6.5', 'label': '...'}"""
    if pd.isna(value) or value is None:
        return None
    value = str(value).strip()
    match = re.match(r'^([\d.]+)\s*>\s*(.+)$', value)
    if match:
        return {"code": match.group(1), "label": match.group(2).strip()}
    return {"code": None, "label": value}


def safe_int(value):
    """Convert to int if possible, else return None"""
    if pd.isna(value) or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_str(value):
    """Convert to string if not null, else return None"""
    if pd.isna(value) or value is None:
        return None
    return str(value).strip() if str(value).strip() else None


def build_record(row, metadata_lookup, record_id):
    """Build a single structured JSON record from a row"""
    quick_ref = safe_str(row.get("quickRef"))
    meta = metadata_lookup.get(quick_ref, {})

    record = {
        "id": record_id,
        "evidenceId": safe_str(row.get("evidenceId")),
        "type": safe_str(row.get("categoryLevel")),
        "description": safe_str(row.get("description")),
        "additionalEvidence": safe_str(row.get("additionalEvidence")),

        "source": {
            "quickRef": quick_ref,
            "paperId": safe_int(row.get("paperId")),
            "title": safe_str(meta.get("title")),
            "authors": {
                "full": safe_str(meta.get("authorsFull")),
                "short": safe_str(meta.get("authorsShort"))
            },
            "year": safe_int(meta.get("year")),
            "doi": safe_str(meta.get("doi")),
            "url": safe_str(meta.get("url")),
            "citations": safe_int(meta.get("citations")),
            "citesPerYear": safe_int(meta.get("citesPerYear")),
            "itemType": safe_str(meta.get("itemType"))
        },

        "classification": {
            "riskCategory": safe_str(row.get("riskCategory")),
            "riskSubcategory": safe_str(row.get("riskSubcategory")),
            "categoryId": safe_int(row.get("categoryId")),
            "subcategoryId": safe_int(row.get("subcategoryId"))
        },

        "causalTaxonomy": {
            "entity": parse_coded_field(row.get("entity")),
            "intent": parse_coded_field(row.get("intent")),
            "timing": parse_coded_field(row.get("timing"))
        },

        "domainTaxonomy": {
            "domain": parse_domain(row.get("domain")),
            "subdomain": parse_subdomain(row.get("subDomain"))
        },

        "references": {
            "definitionPage": safe_int(row.get("definitionPage")),
            "additionalEvidencePage": safe_int(row.get("additionalEvidencePage"))
        }
    }

    return record


def merge_and_transform(main_df: pd.DataFrame, metadata_df: pd.DataFrame) -> list:
    print("Building structured JSON records...")

    # Create metadata lookup by quickRef
    metadata_lookup = {}
    for _, row in metadata_df.iterrows():
        qr = safe_str(row.get("quickRef"))
        if qr:
            metadata_lookup[qr] = row.to_dict()

    records = []
    for idx, row in main_df.iterrows():
        record = build_record(row, metadata_lookup, idx + 1)
        records.append(record)

    return records


def convert_to_json(records: list) -> str:
    print("Converting to JSON...")
    return json.dumps(records, indent=2, ensure_ascii=False)


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
        default="AI Risk Database v4"
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
            "Paper_ID": "paperId",
            "Cat_ID": "categoryId",
            "SubCat_ID": "subcategoryId",
            "AddEv_ID": "additionalEvidenceId",
            "Category level": "categoryLevel",
            "Risk category": "riskCategory",
            "Risk subcategory": "riskSubcategory",
            "Additional ev.": "additionalEvidence",
            "P.Def": "definitionPage",
            "p.AddEv": "additionalEvidencePage",
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
