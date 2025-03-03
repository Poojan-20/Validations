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

    def load_files(self, file1_path: str, file2_path: str, mapping1: dict = None, mapping2: dict = None) -> None:
        """
        Load and validate both Excel files with optional column mapping.
        
        Args:
            file1_path (str): Path to the first Excel file
            file2_path (str): Path to the second Excel file
            mapping1 (dict): Column mapping for first file
            mapping2 (dict): Column mapping for second file
        """
        try:
            # Store file names for later use
            self.file1_name = Path(file1_path).name
            self.file2_name = Path(file2_path).name
            
            # Read both files
            df1 = self.read_excel_file(file1_path)
            df2 = self.read_excel_file(file2_path)
            
            # Apply column mapping if provided
            if mapping1:
                df1 = df1.rename(columns={v: k for k, v in mapping1.items()})
            if mapping2:
                df2 = df2.rename(columns={v: k for k, v in mapping2.items()})
            
            # Store original values (with 2 decimal places) for rate calculations
            df1['original_revenue'] = df1['revenue'].astype(float).round(2)
            df1['original_sale_amount'] = df1['sale_amount'].astype(float).round(2)
            df2['original_revenue'] = df2['revenue'].astype(float).round(2)
            df2['original_sale_amount'] = df2['sale_amount'].astype(float).round(2)
            
            # Round revenue and sale_amount for comparison purposes
            df1['revenue'] = df1['revenue'].astype(float).apply(np.floor)
            df1['sale_amount'] = df1['sale_amount'].astype(float).apply(np.floor)
            df2['revenue'] = df2['revenue'].astype(float).apply(np.floor)
            df2['sale_amount'] = df2['sale_amount'].astype(float).apply(np.floor)
            
            # Store the DataFrames
            self.df1 = df1
            self.df2 = df2
            
            # Validate both DataFrames
            self.validate_dataframe(self.df1, self.file1_name)
            self.validate_dataframe(self.df2, self.file2_name)
            
            logger.info(f"Both files ({self.file1_name}, {self.file2_name}) loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Error loading files: {str(e)}")
            raise

    def apply_validation_rules(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Apply validation rules according to the use case requirements.
        
        Returns:
            Dict containing DataFrames for each validation rule result
        """
        try:
            logger.info("Applying validation rules")
            
            # Initialize result containers
            valid_records = []
            revenue_mismatches = []
            status_mismatches = []
            both_mismatches = []
            status_match_revenue_mismatch = []  # New container for status match but revenue mismatch
            
            # Get common transaction IDs
            common_txns = set(df1['txn_id']).intersection(set(df2['txn_id']))
            
            for txn_id in common_txns:
                record1 = df1[df1['txn_id'] == txn_id].iloc[0]
                record2 = df2[df2['txn_id'] == txn_id].iloc[0]
                
                # Calculate rates
                rate1 = round(record1['revenue'] / record1['sale_amount'], 2) if record1['sale_amount'] != 0 else 0
                rate2 = round(record2['revenue'] / record2['sale_amount'], 2) if record2['sale_amount'] != 0 else 0
                
                # Base record for comparison with dates
                comparison = {
                    'txn_id': txn_id,
                    f'status_{self.file1_name}': record1['status'],
                    f'status_{self.file2_name}': record2['status'],
                    f'revenue_{self.file1_name}': record1['revenue'],
                    f'revenue_{self.file2_name}': record2['revenue'],
                    f'sale_amount_{self.file1_name}': record1['sale_amount'],
                    f'sale_amount_{self.file2_name}': record2['sale_amount'],
                    f'rate_{self.file1_name}': rate1,
                    f'rate_{self.file2_name}': rate2,
                    f'brand_{self.file1_name}': record1['brand'],
                    f'brand_{self.file2_name}': record2['brand'],
                    f'date_{self.file1_name}': record1['created'].strftime('%Y-%m-%d'),
                    f'date_{self.file2_name}': record2['created'].strftime('%Y-%m-%d')
                }
                
                # Check if all relevant fields match exactly
                status_matches = str(record1['status']) == str(record2['status'])
                revenue_matches = str(record1['revenue']) == str(record2['revenue'])
                sale_amount_matches = str(record1['sale_amount']) == str(record2['sale_amount'])
                rates_match = rate1 == rate2
                
                # Rule 1: All fields must match exactly
                if status_matches and revenue_matches and sale_amount_matches and rates_match:
                    comparison['validation_result'] = 'Valid'
                    valid_records.append(comparison)
                
                # Rule 2: Status matches but revenue/sale_amount/rate doesn't
                elif status_matches and not (revenue_matches and sale_amount_matches and rates_match):
                    comparison['validation_result'] = (
                        'Revenue mismatch due to different sale amounts' if rates_match
                        else 'Revenue mismatch due to different rates'
                    )
                    comparison['date_difference'] = (record1['created'] - record2['created']).days
                    revenue_mismatches.append(comparison)
                    
                    # Add to the new status match but revenue mismatch container
                    status_match_revenue_comparison = {
                        'txn_id': txn_id,
                        'status': record1['status'],  # Same for both since status matches
                        f'revenue_{self.file1_name}': record1['revenue'],
                        f'revenue_{self.file2_name}': record2['revenue'],
                        'revenue_difference': record1['revenue'] - record2['revenue'],
                        f'sale_amount_{self.file1_name}': record1['sale_amount'],
                        f'sale_amount_{self.file2_name}': record2['sale_amount'],
                        f'rate_{self.file1_name}': rate1,
                        f'rate_{self.file2_name}': rate2,
                        'rate_difference': rate1 - rate2,
                        f'date_{self.file1_name}': record1['created'].strftime('%Y-%m-%d'),
                        f'date_{self.file2_name}': record2['created'].strftime('%Y-%m-%d'),
                        'date_difference': (record1['created'] - record2['created']).days
                    }
                    status_match_revenue_mismatch.append(status_match_revenue_comparison)
                
                # Rule 3: Status doesn't match but revenue matches
                elif not status_matches and revenue_matches:
                    comparison['validation_result'] = 'Status needs update'
                    comparison['date_difference'] = (record1['created'] - record2['created']).days
                    status_mismatches.append(comparison)
                
                # Rule 4: Both status and revenue don't match
                else:
                    comparison['validation_result'] = (
                        'Status mismatch and revenue mismatch due to different sale amounts' if rates_match
                        else 'Status mismatch and revenue mismatch due to different rates'
                    )
                    comparison['date_difference'] = (record1['created'] - record2['created']).days
                    both_mismatches.append(comparison)
            
            # Convert lists to DataFrames
            validation_results = {
                'valid_records': pd.DataFrame(valid_records) if valid_records else pd.DataFrame(),
                'revenue_mismatches': pd.DataFrame(revenue_mismatches) if revenue_mismatches else pd.DataFrame(),
                'status_mismatches': pd.DataFrame(status_mismatches) if status_mismatches else pd.DataFrame(),
                'both_mismatches': pd.DataFrame(both_mismatches) if both_mismatches else pd.DataFrame(),
                'status_match_revenue_mismatch': pd.DataFrame(status_match_revenue_mismatch) if status_match_revenue_mismatch else pd.DataFrame()
            }
            
            # Sort mismatch DataFrames by date difference if they're not empty
            for key in ['revenue_mismatches', 'status_mismatches', 'both_mismatches', 'status_match_revenue_mismatch']:
                if not validation_results[key].empty:
                    if key == 'status_match_revenue_mismatch':
                        # Sort by revenue difference (absolute value) for the new sheet
                        validation_results[key] = validation_results[key].sort_values(
                            by='revenue_difference',
                            key=abs,
                            ascending=False
                        )
                    else:
                        validation_results[key] = validation_results[key].sort_values(
                            by='date_difference', 
                            ascending=False
                        )
            
            logger.info("Validation rules applied successfully")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error applying validation rules: {str(e)}")
            raise

    def find_duplicate_transactions(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Find duplicate transaction IDs in both files.
        
        Returns:
            Dict containing DataFrames with duplicate transactions
        """
        try:
            logger.info("Checking for duplicate transaction IDs")
            
            # Find duplicates in each DataFrame
            duplicates_df1 = df1[df1.duplicated(subset=['txn_id'], keep=False)].copy()
            duplicates_df2 = df2[df2.duplicated(subset=['txn_id'], keep=False)].copy()
            
            # Add source file indicator
            if not duplicates_df1.empty:
                duplicates_df1['source_file'] = self.file1_name
            if not duplicates_df2.empty:
                duplicates_df2['source_file'] = self.file2_name
            
            # Combine duplicates from both files
            duplicate_records = {
                'duplicates_file1': duplicates_df1,
                'duplicates_file2': duplicates_df2
            }
            
            logger.info(f"Found {len(duplicates_df1)} duplicate records in {self.file1_name}")
            logger.info(f"Found {len(duplicates_df2)} duplicate records in {self.file2_name}")
            
            return duplicate_records
        
        except Exception as e:
            logger.error(f"Error finding duplicate transactions: {str(e)}")
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
            
            # Find duplicate transactions before comparison
            duplicate_records = self.find_duplicate_transactions(df1, df2)
            
            # Remove duplicates from comparison DataFrames
            df1_clean = df1.drop_duplicates(subset=['txn_id'], keep=False)
            df2_clean = df2.drop_duplicates(subset=['txn_id'], keep=False)
            
            # Ensure txn_id is string type in both DataFrames
            df1_clean['txn_id'] = df1_clean['txn_id'].astype(str)
            df2_clean['txn_id'] = df2_clean['txn_id'].astype(str)
            
            # Find common and unique transaction IDs
            common_txns = set(df1_clean['txn_id']).intersection(set(df2_clean['txn_id']))
            only_in_df1_txns = set(df1_clean['txn_id']) - set(df2_clean['txn_id'])
            only_in_df2_txns = set(df2_clean['txn_id']) - set(df1_clean['txn_id'])
            
            # Get records present only in each DataFrame
            only_in_df1 = df1_clean[df1_clean['txn_id'].isin(only_in_df1_txns)]
            only_in_df2 = df2_clean[df2_clean['txn_id'].isin(only_in_df2_txns)]
            
            # Initialize lists for matching and mismatching records
            matching_records = []
            mismatched_records = []
            
            # Compare records with matching transaction IDs
            for txn_id in common_txns:
                record1 = df1_clean[df1_clean['txn_id'] == txn_id].iloc[0]
                record2 = df2_clean[df2_clean['txn_id'] == txn_id].iloc[0]
                
                # Compare all columns except txn_id
                differences = {
                    'txn_id': txn_id,
                    f'brand_{self.file1_name}': record1['brand'],
                    f'brand_{self.file2_name}': record2['brand'],
                    f'revenue_{self.file1_name}': record1['revenue'],
                    f'revenue_{self.file2_name}': record2['revenue'],
                    f'sale_amount_{self.file1_name}': record1['sale_amount'],
                    f'sale_amount_{self.file2_name}': record2['sale_amount']
                }
                has_mismatch = False
                
                for column in [col for col in self.REQUIRED_COLUMNS if col != 'txn_id']:
                    val1 = str(record1[column])
                    val2 = str(record2[column])
                    
                    if val1 != val2:
                        has_mismatch = True
                        if column not in ['brand', 'revenue', 'sale_amount']:  # Skip these as they're already added
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
                    'total_records_file1': len(df1_clean),
                    'total_records_file2': len(df2_clean),
                    'matching_records_count': len(matching_records),
                    'mismatched_records_count': len(only_in_df1)+len(only_in_df2),
                    'only_in_file1_count': len(only_in_df1),
                    'only_in_file2_count': len(only_in_df2)
                }
            }
            
            # Add validation rules results
            validation_results = self.apply_validation_rules(df1_clean, df2_clean)
            comparison_results.update(validation_results)
            
            # Update comparison_results to include duplicate records
            comparison_results.update(duplicate_records)
            
            # Update summary to include duplicate counts
            comparison_results['summary'].update({
                'duplicates_file1_count': len(duplicate_records['duplicates_file1']),
                'duplicates_file2_count': len(duplicate_records['duplicates_file2'])
            })
            
            logger.info("DataFrame comparison completed successfully")
            
            # Print detailed comparison results
            print("\nComparison Results:")
            print("=" * 80)
            print(f"Total records in {self.file1_name}: {len(df1_clean)}")
            print(f"Total records in {self.file2_name}: {len(df2_clean)}")
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
        Calculate distinct rates for each brand with corresponding details.
        """
        try:
            logger.info("Calculating distinct rates by brand")
            
            # Create a copy to avoid modifying original DataFrame
            df_calc = df.copy()
            
            # Convert date to month-year format for date range
            df_calc['date_range'] = df_calc['created'].dt.strftime('%Y-%m')
            
            # Calculate rates using original values (with 2 decimal places)
            df_calc['rate'] = df_calc.apply(
                lambda row: round(row['original_revenue'] / row['original_sale_amount'], 2) 
                if row['original_sale_amount'] != 0 else 0, 
                axis=1
            )
            
            # Initialize list to store rate summaries
            rate_summaries = []
            
            # Process each brand separately
            for brand in df_calc['brand'].unique():
                brand_data = df_calc[df_calc['brand'] == brand]
                
                # Get distinct rates for this brand
                distinct_rates = brand_data['rate'].unique()
                
                # For each distinct rate, gather details
                for rate in distinct_rates:
                    rate_records = brand_data[brand_data['rate'] == rate]
                    
                    # Group by date range for this rate
                    for date_range, date_group in rate_records.groupby('date_range'):
                        # Calculate metrics for this rate and date range
                        total_revenue = date_group['original_revenue'].sum()
                        total_sale_amount = date_group['original_sale_amount'].sum()
                        transaction_count = len(date_group)
                        
                        # Get status-wise breakdown
                        status_breakdown = {}
                        for status, status_group in date_group.groupby('status'):
                            status_breakdown.update({
                                f'revenue_{status.lower()}': status_group['original_revenue'].sum(),
                                f'count_{status.lower()}': len(status_group)
                            })
                        
                        # Get date range details
                        start_date = date_group['created'].min().strftime('%Y-%m-%d')
                        end_date = date_group['created'].max().strftime('%Y-%m-%d')
                        
                        # Create summary record
                        summary = {
                            'brand': brand,
                            'rate': rate,
                            'date_range': date_range,
                            'date_range_start': start_date,
                            'date_range_end': end_date,
                            'total_revenue': total_revenue,
                            'total_sale_amount': total_sale_amount,
                            'transaction_count': transaction_count,
                            **status_breakdown
                        }
                        
                        rate_summaries.append(summary)
            
            # Convert to DataFrame and sort
            result_df = pd.DataFrame(rate_summaries)
            if not result_df.empty:
                # Sort by brand, date_range, and rate
                result_df = result_df.sort_values(
                    by=['brand', 'date_range', 'rate'],
                    ascending=[True, False, False]
                )
            
            # Calculate overall status-wise summary
            status_summary = df_calc.groupby('status').agg({
                'original_revenue': 'sum',
                'txn_id': 'count',
                'original_sale_amount': 'sum'
            }).reset_index()
            
            # Add calculated rate for each status
            status_summary['rate'] = status_summary.apply(
                lambda row: round(row['original_revenue'] / row['original_sale_amount'], 2) 
                if row['original_sale_amount'] != 0 else 0, 
                axis=1
            )
            
            # Store status summary in DataFrame attributes
            status_dict = {}
            for _, row in status_summary.iterrows():
                status_dict[row['status']] = {
                    'revenue': row['original_revenue'],
                    'txn_id': row['txn_id'],
                    'rate': row['rate']
                }
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
                    'file1_brands': rates_df1['brand'].nunique() if not rates_df1.empty else 0,
                    'file2_brands': rates_df2['brand'].nunique() if not rates_df2.empty else 0,
                }
            }
            
            # Calculate rate differences for matching brand-date combinations if needed
            if not rates_df1.empty and not rates_df2.empty:
                try:
                    merged_rates = pd.merge(
                        rates_df1, 
                        rates_df2, 
                        on=['brand', 'date_range'], 
                        suffixes=('_file1', '_file2'),
                        how='inner'
                    )
                    
                    if not merged_rates.empty:
                        # Use the 'rate' column directly since it's already in our DataFrame
                        merged_rates['rate_difference'] = (
                            merged_rates['rate_file1'] - 
                            merged_rates['rate_file2']
                        ).round(2)
                        
                        rates_comparison['rate_differences'] = merged_rates
                        rates_comparison['summary']['max_rate_diff'] = abs(merged_rates['rate_difference']).max()
                except Exception as e:
                    logger.warning(f"Error calculating rate differences: {str(e)}")
                    # Continue without rate differences if there's an error
            
            logger.info("Rate comparison completed successfully")
            return rates_comparison
            
        except Exception as e:
            logger.error(f"Error comparing rates: {str(e)}")
            raise

    def suggest_column_mapping(self, headers):
        """
        Suggests column mapping based on common patterns in header names.
        """
        # Convert headers to lowercase for case-insensitive matching
        headers_lower = [str(h).lower().strip() for h in headers]
        mapping = {}
        
        # Define common patterns for each required field
        patterns = {
            'txn_id': ['txn_id', 'transaction_id', 'txn', 'transaction', 'id', 'order id', 'orderid'],
            'revenue': ['revenue', 'rev', 'earning', 'commission', 'payment', 'payout'],
            'sale_amount': ['sale_amount', 'sale', 'amount', 'price', 'value', 'order sum', 'ordersum', 'order_amount'],
            'status': ['status', 'state', 'condition', 'order_status', 'orderstatus'],
            'brand': ['brand', 'brand_name', 'advertiser', 'merchant', 'campaign_app_name', 'app_name', 'campaign'],
            'created': ['created', 'date', 'created_at', 'created_date', 'transaction_date', 'action time', 'datetime']
        }
        
        # Find best match for each required column
        for required_col, patterns_list in patterns.items():
            # First try exact matches
            for pattern in patterns_list:
                pattern_lower = pattern.lower()
                if pattern_lower in headers_lower:
                    idx = headers_lower.index(pattern_lower)
                    mapping[required_col] = headers[idx]
                    break
            
            # If no exact match found, try partial matches
            if required_col not in mapping:
                for header, header_lower in zip(headers, headers_lower):
                    # Try to find a pattern within the header
                    for pattern in patterns_list:
                        pattern_lower = pattern.lower()
                        if pattern_lower in header_lower or header_lower in pattern_lower:
                            mapping[required_col] = header
                            break
                    if required_col in mapping:
                        break
        
        # Log the mapping results
        logger.info(f"Headers found: {headers}")
        logger.info(f"Suggested mapping: {mapping}")
        
        return mapping

def main():
    validator = ExcelValidator()
    
    try:
        validator.load_files(
            file1_path="C:/Validations/Client_data.xlsx",
            file2_path="C:/Validations/My_data.xlsx"
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
            print(f"Date: {row['date_range']}")
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
            print(f"Date: {row['date_range']}")
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