# MIT AI Risk Repository Converter

A small utility script that downloads MIT’s [AI Risk Repository](https://airisk.mit.edu/) from Google Sheets (or uses a local Excel file) and converts it into a JSON file. This makes the risk data more portable, letting you incorporate it easily into your own tools, data pipelines, or dashboards.

## Usage

    python convert_ai_risk.py [--input FILE_OR_URL] [--output OUTPUT_JSON] [--sheet-name SHEET_NAME]

### Arguments

- **`--input` / `-i`**  
  Path to a local XLSX file **OR** a direct export URL from Google Sheets.  
  If omitted, the script will fetch from a default Google Sheet URL.

- **`--output` / `-o`**  
  JSON file name to save the filtered data.  
  Default: `Filtered_AI_Risk_Database_with_ID.json`

- **`--sheet-name` / `-s`**  
  The name of the Excel sheet to load.  
  Default: `AI Risk Database v2`

## Installation

1. Clone or download this repository.
2. Install Python dependencies:
    
        pip install pandas requests openpyxl
    
3. Run the script!

## Examples

- **Download the default Google Sheet and convert it to JSON**:
      
        python convert_ai_risk.py
    
- **Use a local XLSX file**:
      
        python convert_ai_risk.py --input path/to/local.xlsx
    
- **Override the output file name**:
      
        python convert_ai_risk.py --output my_risk_data.json
    
- **Specify a different sheet name**:
      
        python convert_ai_risk.py --sheet-name "AI Risk Database v2"

## Credits and Acknowledgments

- **MIT AI Risk Repository**  
  The data in this tool is from MIT’s [AI Risk Repository](https://airisk.mit.edu/). We claim no ownership over that data—big thanks to MIT for making it publicly accessible!

- **Author**  
  [Alexander Hagenah](https://github.com/xaitax/)

- **Contributions**  
  Feedback or contributions? Feel free to open issues or pull requests.