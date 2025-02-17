# Instructions

# Excel Validation Automation Requirements

## Overview

Create a Python script to automate the validation of two Excel files by comparing transaction data and calculating revenue rates.

## Input Files

- Two Excel files containing transaction data
- Both files should have the following columns:
    - Transaction ID (txnid)
    - Revenue
    - Sale Amount
    - Status

## Required Functionality

### 1. File Handling

- Implement functions to read both Excel files using pandas
- Allow flexible file path inputs for both source files
- Validate that required columns exist in both files
- Handle potential file reading errors gracefully

### 2. Data Comparison

- Implement VLOOKUP-style functionality using transaction ID (txnid) as the key
- Compare all fields between the two files for matching transaction IDs
- Identify:
    - Matching records
    - Records present in file 1 but missing in file 2
    - Records present in file 2 but missing in file 1
    - Records where values don't match for the same transaction ID

### 3. Calculations

- Calculate the rate for each brand name using the formula: rate = revenue / sale_amount
- Handle potential division by zero errors
- Round the calculated rates to 2 decimal places
- Give rate brand name wise and date/month wise column name is created

### 4. Output Generation

- Create a comparison report containing:
    - Matched records with their calculated rates
    - Mismatched records with highlighting of differences
    - Missing records from either file
- Save the report as a new Excel file with appropriate formatting
- Include summary statistics at the top of the report

### 5. Error Handling

- Implement proper error handling for:
    - Missing files
    - Invalid file formats
    - Missing columns
    - Invalid data types
    - Division by zero cases
    - Empty files

## Technical Requirements

### Libraries to Use

- pandas for Excel file handling and data manipulation
- openpyxl for Excel writing with formatting
- numpy for numerical operations

### Code Structure

- Create modular functions for:
    - File reading
    - Data validation
    - Comparison logic
    - Rate calculation
    - Report generation
- Include proper documentation and type hints
- Add logging for important operations and errors

### Sample Code Structure

```python
def read_excel_file(file_path: str) -> pd.DataFrame:
    # Implementation for reading Excel file

def validate_dataframe(df: pd.DataFrame) -> bool:
    # Implementation for validating required columns

def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> dict:
    # Implementation for comparing dataframes

def calculate_rates(df: pd.DataFrame) -> pd.Series:
    # Implementation for calculating rates

def generate_report(comparison_results: dict, output_path: str) -> None:
    # Implementation for generating final report

```

## Additional Requirements

- Add progress indicators for long-running operations
- Include input validation for file paths
- Provide clear error messages for end users
- Add configuration options for:
    - Column names
    - Output file path
    - Rounding precision
    - Custom comparison rules

## Testing Instructions

- Test with various scenarios:
    - Different file sizes
    - Missing data
    - Invalid data
    - Edge cases
- Validate calculation accuracy
- Check performance with large datasets

## Expected Output Format

The final report should include:

1. Summary section with:
    - Total records processed
    - Number of matches/mismatches
    - Number of missing records
    - Average rates
2. Detailed comparison tables
3. List of discrepancies
4. Calculated rates for all transactions