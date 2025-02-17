import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExcelValidator:
    # Update required columns to include brand and created date
    REQUIRED_COLUMNS = ['txn_id', 'revenue', 'sale_amount', 'status', 'brand', 'created']
    
    def __init__(self):
        self.df1: Optional[pd.DataFrame] = None
        self.df2: Optional[pd.DataFrame] = None
        self.file1_name: str = ""
        self.file2_name: str = ""

    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        Read an Excel file and return a pandas DataFrame.
        
        Args:
            file_path (str): Path to the Excel file
            
        Returns:
            pd.DataFrame: DataFrame containing the Excel data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a valid Excel file
        """
        try:
            # Convert string path to Path object
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if file is an Excel file
            if file_path.suffix not in ['.xlsx', '.xls']:
                raise ValueError(f"File must be an Excel file (.xlsx or .xls): {file_path}")
            
            logger.info(f"Reading file: {file_path}")
            df = pd.read_excel(file_path)
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    def validate_dataframe(self, df: pd.DataFrame, file_name: str) -> bool:
        """
        Validate that the DataFrame contains all required columns and proper date format.
        
        Args:
            df (pd.DataFrame): DataFrame to validate
            file_name (str): Name of the file for logging purposes
            
        Returns:
            bool: True if validation passes, False otherwise
            
        Raises:
            ValueError: If required columns are missing or date format is invalid
        """
        try:
            # Check if DataFrame is empty
            if df.empty:
                raise ValueError(f"File {file_name} is empty")
            
            # Convert column names to lowercase for case-insensitive comparison
            df.columns = df.columns.str.lower()
            
            # Check for required columns
            missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
            if missing_columns:
                raise ValueError(
                    f"Missing required columns in {file_name}: {', '.join(missing_columns)}"
                )
            
            # Validate and fix date format
            try:
                # First, ensure the date column is string type
                df['created'] = df['created'].astype(str)
                
                # Function to fix and validate date format
                def fix_date_format(date_str):
                    try:
                        # Split the date string
                        parts = date_str.split('-')
                        if len(parts) != 3:
                            raise ValueError("Invalid date format")
                        
                        year = int(parts[0])
                        month = int(parts[1])
                        day = int(parts[2])
                        
                        # Validate and swap if month > 12
                        if month > 12:
                            month, day = day, month
                        
                        # Validate ranges
                        if not (2000 <= year <= 2100):
                            raise ValueError("Year out of range")
                        if not (1 <= month <= 12):
                            raise ValueError("Month out of range")
                        if not (1 <= day <= 31):
                            raise ValueError("Day out of range")
                        
                        # Return formatted date string
                        return f"{year:04d}-{month:02d}-{day:02d}"
                    except Exception as e:
                        logger.warning(f"Date format issue in {date_str}: {str(e)}")
                        raise ValueError(f"Invalid date format: {date_str}")
                
                # Apply the fix_date_format function and convert to datetime
                df['created'] = df['created'].apply(fix_date_format)
                df['created'] = pd.to_datetime(df['created'], format='%Y-%m-%d')
                
                logger.info(f"Date validation and formatting successful for {file_name}")
                
            except Exception as e:
                raise ValueError(
                    f"Date format error in {file_name}: {str(e)}. "
                    "Please ensure dates are in YYYY-MM-DD format."
                )
            
            logger.info(f"Validation successful for {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed for {file_name}: {str(e)}")
            raise

    def load_files(self, file1_path: str, file2_path: str) -> None:
        """
        Load and validate both Excel files.
        
        Args:
            file1_path (str): Path to the first Excel file
            file2_path (str): Path to the second Excel file
        """
        try:
            # Store file names for later use
            self.file1_name = Path(file1_path).name
            self.file2_name = Path(file2_path).name
            
            # Read both files
            self.df1 = self.read_excel_file(file1_path)
            self.df2 = self.read_excel_file(file2_path)
            
            # Validate both DataFrames
            self.validate_dataframe(self.df1, self.file1_name)
            self.validate_dataframe(self.df2, self.file2_name)
            
            logger.info(f"Both files ({self.file1_name}, {self.file2_name}) loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Error loading files: {str(e)}")
            raise

    def compare_dataframes(self) -> Dict[str, Any]:
        """
        Compare the two DataFrames and identify matching, mismatching, and missing records.
        """
        if self.df1 is None or self.df2 is None:
            raise ValueError("Both DataFrames must be loaded before comparison")

        try:
            logger.info("Starting DataFrame comparison")
            
            # Create copies to avoid modifying original DataFrames
            df1 = self.df1.copy()
            df2 = self.df2.copy()
            
            # Ensure txn_id is string type in both DataFrames
            df1['txn_id'] = df1['txn_id'].astype(str)
            df2['txn_id'] = df2['txn_id'].astype(str)
            
            # Find common and unique transaction IDs
            common_txns = set(df1['txn_id']).intersection(set(df2['txn_id']))
            only_in_df1_txns = set(df1['txn_id']) - set(df2['txn_id'])
            only_in_df2_txns = set(df2['txn_id']) - set(df1['txn_id'])
            
            # Get records present only in each DataFrame
            only_in_df1 = df1[df1['txn_id'].isin(only_in_df1_txns)]
            only_in_df2 = df2[df2['txn_id'].isin(only_in_df2_txns)]
            
            # Initialize lists for matching and mismatching records
            matching_records = []
            mismatched_records = []
            
            # Compare records with matching transaction IDs
            for txn_id in common_txns:
                record1 = df1[df1['txn_id'] == txn_id].iloc[0]
                record2 = df2[df2['txn_id'] == txn_id].iloc[0]
                
                # Compare all columns except txn_id
                differences = {'txn_id': txn_id}
                has_mismatch = False
                
                for column in [col for col in self.REQUIRED_COLUMNS if col != 'txn_id']:
                    val1 = str(record1[column])
                    val2 = str(record2[column])
                    
                    if val1 != val2:
                        has_mismatch = True
                        differences[f"{column}_{self.file1_name}"] = val1
                        differences[f"{column}_{self.file2_name}"] = val2
                
                if has_mismatch:
                    mismatched_records.append(differences)
                else:
                    matching_records.append(record1.to_dict())
            
            # Convert lists to DataFrames
            matching_df = pd.DataFrame(matching_records) if matching_records else pd.DataFrame()
            mismatched_df = pd.DataFrame(mismatched_records) if mismatched_records else pd.DataFrame()
            
            # Create summary
            comparison_results = {
                'matching_records': matching_df,
                'value_mismatches': mismatched_df,
                'only_in_df1': only_in_df1,
                'only_in_df2': only_in_df2,
                'summary': {
                    'total_records_file1': len(df1),
                    'total_records_file2': len(df2),
                    'matching_records_count': len(matching_records),
                    'mismatched_records_count': len(only_in_df1),
                    'only_in_file1_count': len(only_in_df1),
                    'only_in_file2_count': len(only_in_df2)
                }
            }
            
            logger.info("DataFrame comparison completed successfully")
            
            # Print detailed comparison results
            print("\nComparison Results:")
            print("=" * 80)
            print(f"Total records in {self.file1_name}: {len(df1)}")
            print(f"Total records in {self.file2_name}: {len(df2)}")
            print(f"Matching records: {len(matching_records)}")
            print(f"Records with mismatches: {len(only_in_df1)}")
            print(f"Records only in {self.file1_name}: {len(only_in_df1)}")
            print(f"Records only in {self.file2_name}: {len(only_in_df2)}")
            
            # Print detailed mismatch information if any exists
            if mismatched_records:
                print("\nDetailed Mismatches:")
                print("=" * 80)
                for mismatch in mismatched_records:
                    print(f"\nTransaction ID: {mismatch['txn_id']}")
                    for key, value in mismatch.items():
                        if key != 'txn_id':
                            print(f"{key}: {value}")
                    print("-" * 80)
                
                print(f"\nTotal Mismatched Records: {len(mismatched_records)}")
                print(f"Mismatched Transaction IDs: {', '.join(m['txn_id'] for m in mismatched_records)}")
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error during DataFrame comparison: {str(e)}")
            raise

    def _log_comparison_summary(self, summary: Dict[str, int]) -> None:
        """Log the summary of comparison results."""
        logger.info("=== Comparison Summary ===")
        logger.info(f"Total records in {self.file1_name}: {summary['total_records_file1']}")
        logger.info(f"Total records in {self.file2_name}: {summary['total_records_file2']}")
        logger.info(f"Matching records: {summary['matching_records_count']}")
        logger.info(f"Mismatched records: {summary['mismatched_records_count']}")
        logger.info(f"Records only in {self.file1_name}: {summary['only_in_file1_count']}")
        logger.info(f"Records only in {self.file2_name}: {summary['only_in_file2_count']}")

    def calculate_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rates for each brand and date, and aggregate revenue by status.
        """
        try:
            logger.info("Calculating rates by brand and date")
            
            # Create a copy to avoid modifying original DataFrame
            df_calc = df.copy()
            
            # Format date as YYYY-MM-DD string
            df_calc['date_str'] = df_calc['created'].dt.strftime('%Y-%m-%d')
            
            # Calculate rate for each transaction
            df_calc['rate'] = df_calc.apply(
                lambda row: round(row['revenue'] / row['sale_amount'], 2) 
                if row['sale_amount'] != 0 else 0, 
                axis=1
            )
            
            # Calculate status-wise revenue and count
            status_summary = df_calc.groupby('status').agg({
                'revenue': 'sum',
                'txn_id': 'count'
            }).reset_index()
            
            # Group by brand and date
            brand_date_rates = df_calc.groupby(['brand', 'date_str']).agg({
                'revenue': 'sum',
                'sale_amount': 'sum',
                'rate': list,
                'txn_id': 'count',
                'status': list
            }).reset_index()
            
            # Calculate overall rate for each brand-date combination
            brand_date_rates['calculated_rate'] = (
                brand_date_rates['revenue'] / brand_date_rates['sale_amount']
            ).round(2)
            
            # Create a more readable format
            readable_rates = []
            for _, row in brand_date_rates.iterrows():
                brand = row['brand']
                date = row['date_str']
                
                # Get status-wise revenue and count for this brand-date combination
                status_details = df_calc[
                    (df_calc['brand'] == brand) & 
                    (df_calc['date_str'] == date)
                ].groupby('status').agg({
                    'revenue': 'sum',
                    'txn_id': 'count'
                }).reset_index()
                
                # Get rates as a list
                rates = row['rate']
                rates_str = ', '.join([f"{rate:.2f}" for rate in rates])
                
                record = {
                    'brand': brand,
                    'date': date,
                    'rates': rates_str,
                    'total_revenue': row['revenue'],
                    'total_sale_amount': row['sale_amount'],
                    'transaction_count': row['txn_id'],
                    'calculated_rate': row['calculated_rate']
                }
                
                # Add status-wise revenue and count
                for _, status_row in status_details.iterrows():
                    status = status_row['status']
                    record[f'revenue_{status.lower()}'] = status_row['revenue']
                    record[f'count_{status.lower()}'] = status_row['txn_id']
                
                readable_rates.append(record)
            
            result_df = pd.DataFrame(readable_rates)
            
            # Convert status_summary to dictionary format
            status_dict = {}
            for _, row in status_summary.iterrows():
                status_dict[row['status']] = {
                    'revenue': row['revenue'],
                    'txn_id': row['txn_id']
                }
            
            # Add total status-wise summary to the result
            result_df.attrs['status_summary'] = status_dict
            
            logger.info("Rate calculations completed successfully")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating rates: {str(e)}")
            raise

    def compare_rates(self) -> Dict[str, Any]:
        """
        Compare rates between the two files by brand and date.
        
        Returns:
            Dict containing rate comparison results
        """
        try:
            logger.info("Starting rate comparison")
            
            # Calculate rates for both DataFrames
            rates_df1 = self.calculate_rates(self.df1)
            rates_df2 = self.calculate_rates(self.df2)
            
            # Combine the results
            rates_comparison = {
                'rates_file1': rates_df1,
                'rates_file2': rates_df2,
                'summary': {
                    'file1_brands': rates_df1['brand'].nunique(),
                    'file2_brands': rates_df2['brand'].nunique(),
                }
            }
            
            # Calculate rate differences for matching brand-date combinations
            merged_rates = pd.merge(
                rates_df1, 
                rates_df2, 
                on=['brand', 'date'], 
                suffixes=('_file1', '_file2'),
                how='inner'
            )
            
            if not merged_rates.empty:
                merged_rates['rate_difference'] = (
                    merged_rates['calculated_rate_file1'] - 
                    merged_rates['calculated_rate_file2']
                ).round(2)
                
                rates_comparison['rate_differences'] = merged_rates
                rates_comparison['summary']['max_rate_diff'] = abs(merged_rates['rate_difference']).max()
            
            logger.info("Rate comparison completed successfully")
            return rates_comparison
            
        except Exception as e:
            logger.error(f"Error comparing rates: {str(e)}")
            raise
                
def main():
    validator = ExcelValidator()
    
    try:
        validator.load_files(
            file1_path="C:/Users/Poojan1.Patel/OneDrive - Reliance Corporate IT Park Limited/Desktop/Validations/Client_data.xlsx",
            file2_path="C:/Users/Poojan1.Patel/OneDrive - Reliance Corporate IT Park Limited/Desktop/Validations/My_data.xlsx"
        )
        print("Files loaded successfully!")
        
        # Perform data comparison
        comparison_results = validator.compare_dataframes()
        
        # Calculate and compare rates
        rate_results = validator.compare_rates()
        
        # Print comparison results
        print("\nComparison Results:")
        print("=" * 80)
        print(f"Total records in {validator.file1_name}: {comparison_results['summary']['total_records_file1']}")
        print(f"Total records in {validator.file2_name}: {comparison_results['summary']['total_records_file2']}")
        print(f"Matching records: {comparison_results['summary']['matching_records_count']}")
        print(f"Records with mismatches: {comparison_results['summary']['mismatched_records_count']}")
        print(f"Records only in {validator.file1_name}: {comparison_results['summary']['only_in_file1_count']}")
        print(f"Records only in {validator.file2_name}: {comparison_results['summary']['only_in_file2_count']}")
        
        # Print status-wise revenue and count totals for both files
        print(f"\nStatus-wise Summary in {validator.file1_name}:")
        print("=" * 80)
        for status, summary in rate_results['rates_file1'].attrs['status_summary'].items():
            print(f"{status.title()}:")
            print(f"  Revenue: {summary['revenue']:,.2f}")
            print(f"  Count: {summary['txn_id']}")
            
        print(f"\nStatus-wise Summary in {validator.file2_name}:")
        print("=" * 80)
        for status, summary in rate_results['rates_file2'].attrs['status_summary'].items():
            print(f"{status.title()}:")
            print(f"  Revenue: {summary['revenue']:,.2f}")
            print(f"  Count: {summary['txn_id']}")
        
        # Display rates for File 1
        print(f"\nRates in {validator.file1_name}:")
        print("=" * 80)
        rates_df1 = rate_results['rates_file1']
        for _, row in rates_df1.iterrows():
            print(f"Brand: {row['brand']}")
            print(f"Date: {row['date']}")
            print(f"Individual Rates: {row['rates']}")
            print(f"Calculated Rate: {row['calculated_rate']}")
            print(f"Total Revenue: {row['total_revenue']}")
            print("Status-wise Summary:")
            for col in row.index:
                if col.startswith('revenue_'):
                    status = col.replace('revenue_', '').title()
                    count_col = f"count_{status.lower()}"
                    if count_col in row:
                        print(f"  {status}:")
                        print(f"    Revenue: {row[col]:,.2f}")
                        # Handle NaN values for count
                        count = row[count_col]
                        count_str = '0' if pd.isna(count) else f"{int(count)}"
                        print(f"    Count: {count_str}")
            print(f"Total Sale Amount: {row['total_sale_amount']}")
            print(f"Transaction Count: {row['transaction_count']}")
            print("-" * 80)
        
        # Display similar information for File 2
        print(f"\nRates in {validator.file2_name}:")
        print("=" * 80)
        rates_df2 = rate_results['rates_file2']
        for _, row in rates_df2.iterrows():
            print(f"Brand: {row['brand']}")
            print(f"Date: {row['date']}")
            print(f"Individual Rates: {row['rates']}")
            print(f"Calculated Rate: {row['calculated_rate']}")
            print(f"Total Revenue: {row['total_revenue']}")
            print("Status-wise Summary:")
            for col in row.index:
                if col.startswith('revenue_'):
                    status = col.replace('revenue_', '').title()
                    count_col = f"count_{status.lower()}"
                    if count_col in row:
                        print(f"  {status}:")
                        print(f"    Revenue: {row[col]:,.2f}")
                        # Handle NaN values for count
                        count = row[count_col]
                        count_str = '0' if pd.isna(count) else f"{int(count)}"
                        print(f"    Count: {count_str}")
            print(f"Total Sale Amount: {row['total_sale_amount']}")
            print(f"Transaction Count: {row['transaction_count']}")
            print("-" * 80)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 