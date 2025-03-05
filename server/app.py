from flask import Flask, render_template, request, send_file, jsonify, Response, send_from_directory
from werkzeug.utils import secure_filename
import os
from excel_validator import ExcelValidator
import pandas as pd
import tempfile
import logging
import json
import time
from datetime import datetime
import shutil
import numpy as np
from openpyxl.styles import PatternFill, Font, Alignment

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Add new config for history folder
HISTORY_FOLDER = 'processed_files'
if not os.path.exists(HISTORY_FOLDER):
    os.makedirs(HISTORY_FOLDER)
app.config['HISTORY_FOLDER'] = HISTORY_FOLDER

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Add a global variable to track progress
progress_data = {
    'step': 'loading',
    'percentage': 0,
    'stats': {},
    'complete': False
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_headers', methods=['POST'])
def get_headers():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format'}), 400

        # Read Excel headers
        df = pd.read_excel(file)
        headers = df.columns.tolist()
        
        # Convert headers to strings
        headers = [str(h) for h in headers]

        # Get suggested mapping
        validator = ExcelValidator()
        suggested_mapping = validator.suggest_column_mapping(headers)

        response_data = {
            'headers': headers,
            'suggested_mapping': suggested_mapping
        }
        
        logger.info(f"Sending response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error reading headers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress')
def progress():
    def generate():
        while not progress_data['complete']:
            # Send progress data
            yield f"data: {json.dumps(progress_data)}\n\n"
            time.sleep(0.5)
        # Send final update
        yield f"data: {json.dumps(progress_data)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/get_processed_files')
def get_processed_files():
    try:
        logger.info("Fetching list of processed files")
        files = []
        
        # Check if directory exists
        if not os.path.exists(app.config['HISTORY_FOLDER']):
            logger.warning(f"History folder does not exist: {app.config['HISTORY_FOLDER']}")
            return jsonify([])
            
        # Get files sorted by modification time (newest first)
        file_list = []
        for filename in os.listdir(app.config['HISTORY_FOLDER']):
            file_path = os.path.join(app.config['HISTORY_FOLDER'], filename)
            if os.path.isfile(file_path) and filename.endswith(('.xlsx', '.xls')):
                file_stats = os.stat(file_path)
                file_list.append({
                    'name': filename,
                    'path': file_path,
                    'mtime': file_stats.st_mtime,
                    'size': file_stats.st_size
                })
        
        # Sort by modification time (newest first)
        file_list.sort(key=lambda x: x['mtime'], reverse=True)
        
        # Format the response
        for file_info in file_list:
            files.append({
                'name': file_info['name'],
                'date': datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S'),
                'size': f"{file_info['size'] / (1024*1024):.2f} MB"
            })
            
        logger.info(f"Found {len(files)} processed files")
        return jsonify(files)
    except Exception as e:
        logger.error(f"Error getting processed files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_processed/<filename>')
def download_processed(filename):
    try:
        return send_file(
            os.path.join(app.config['HISTORY_FOLDER'], filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        global progress_data
        progress_data = {
            'step': 'loading',
            'percentage': 0,
            'stats': {},
            'complete': False
        }

        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400

        file1 = request.files['file1']
        file2 = request.files['file2']
        mapping1 = json.loads(request.form['mapping1'])
        mapping2 = json.loads(request.form['mapping2'])

        if file1.filename == '' or file2.filename == '':
            return jsonify({'error': 'No selected files'}), 400

        if not (allowed_file(file1.filename) and allowed_file(file2.filename)):
            return jsonify({'error': 'Invalid file format. Only Excel files are allowed.'}), 400

        # Save files temporarily
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))
        
        file1.save(file1_path)
        file2.save(file2_path)

        # Get file names without extensions for sheet names
        file1_name = os.path.splitext(file1.filename)[0]
        file2_name = os.path.splitext(file2.filename)[0]

        # Update progress for loading
        progress_data.update({
            'step': 'loading',
            'percentage': 20,
        })

        # Process files with column mapping
        validator = ExcelValidator()
        validator.load_files(file1_path, file2_path, mapping1, mapping2)
        
        # Update progress for validation
        progress_data.update({
            'step': 'validation',
            'percentage': 40,
        })
        
        # Get comparison results
        comparison_results = validator.compare_dataframes()
        
        # Get unique brand names from both files
        brands_df1 = validator.df1['brand'].unique()
        brands_df2 = validator.df2['brand'].unique()
        all_brands = sorted(set(brands_df1) | set(brands_df2))  # Combine unique brands
        brands_str = '-'.join(all_brands) if len(all_brands) <= 3 else f"{all_brands[0]}-and-others"

        # Create timestamp and filename
        timestamp = datetime.now().strftime('%Y-%m-%d')
        result_filename = f'{brands_str}-validation-results-{timestamp}.xlsx'
        # Clean filename by removing invalid characters
        result_filename = "".join(c for c in result_filename if c.isalnum() or c in ('-', '_', '.')).lower()
        result_path = os.path.join(app.config['HISTORY_FOLDER'], result_filename)

        # Create Excel writer
        with pd.ExcelWriter(result_path, engine='openpyxl') as writer:
            # Write summary
            pd.DataFrame([comparison_results['summary']]).to_excel(writer, sheet_name='Summary', index=False)
            
            # Write validation rule results
            comparison_results['valid_records'].to_excel(writer, sheet_name='Valid Records', index=False)
            comparison_results['revenue_mismatches'].to_excel(writer, sheet_name='Revenue Mismatches', index=False)
            comparison_results['status_mismatches'].to_excel(writer, sheet_name='Status Mismatches', index=False)
            comparison_results['both_mismatches'].to_excel(writer, sheet_name='Both Mismatches', index=False)
            
            # Write the new status match but revenue mismatch sheet
            if not comparison_results['status_match_revenue_mismatch'].empty:
                comparison_results['status_match_revenue_mismatch'].to_excel(
                    writer, 
                    sheet_name='Status Match Revenue Mismatch',
                    index=False
                )
            
            # Write existing comparison results
            comparison_results['matching_records'].to_excel(writer, sheet_name='Matching Records', index=False)
            comparison_results['value_mismatches'].to_excel(writer, sheet_name='Mismatches', index=False)
            comparison_results['only_in_df1'].to_excel(writer, sheet_name=f'Only in {file1_name}', index=False)
            comparison_results['only_in_df2'].to_excel(writer, sheet_name=f'Only in {file2_name}', index=False)
            
            # Write rates with better formatting
            rate_results = validator.compare_rates()
            
            # Write rates for file1
            if not rate_results['rates_file1'].empty:
                rates_sheet1 = rate_results['rates_file1']
                
                # Write to Excel
                rates_sheet1.to_excel(
                    writer, 
                    sheet_name=f'Rates {file1_name}',
                    index=False
                )
                
                # Get the worksheet
                worksheet = writer.sheets[f'Rates {file1_name}']
                
                # Format headers using openpyxl styles
                header_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
                header_font = Font(bold=True)
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column = list(column)
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            # Write rates for file2
            if not rate_results['rates_file2'].empty:
                rates_sheet2 = rate_results['rates_file2']
                
                # Write to Excel
                rates_sheet2.to_excel(
                    writer, 
                    sheet_name=f'Rates {file2_name}',
                    index=False
                )
                
                # Get the worksheet
                worksheet = writer.sheets[f'Rates {file2_name}']
                
                # Format headers
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column = list(column)
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

            # Write duplicate records
            if not comparison_results['duplicates_file1'].empty:
                comparison_results['duplicates_file1'].to_excel(
                    writer, 
                    sheet_name=f'Duplicates in {file1_name}',
                    index=False
                )
            if not comparison_results['duplicates_file2'].empty:
                comparison_results['duplicates_file2'].to_excel(
                    writer, 
                    sheet_name=f'Duplicates in {file2_name}',
                    index=False
                )

            # Write click_id mismatches
            if not comparison_results['click_id_mismatches'].empty:
                comparison_results['click_id_mismatches'].to_excel(
                    writer,
                    sheet_name='Click ID Mismatches',
                    index=False
                )

        # Clean up uploaded files
        os.remove(file1_path)
        os.remove(file2_path)

        # Update progress for completion
        progress_data.update({
            'step': 'report',
            'percentage': 100,
            'complete': True
        })

        return send_file(
            result_path,
            as_attachment=True,
            download_name=result_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        progress_data['complete'] = True
        logger.error(f"Error processing files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_summary_stats/<filename>')
def get_summary_stats(filename):
    try:
        logger.info(f"Fetching summary stats for file: {filename}")
        
        # Validate filename to prevent directory traversal
        if '..' in filename or '/' in filename:
            logger.error(f"Invalid filename: {filename}")
            return jsonify({'error': 'Invalid filename'}), 400
            
        file_path = os.path.join(app.config['HISTORY_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404

        # Check if file is an Excel file
        if not filename.endswith(('.xlsx', '.xls')):
            logger.error(f"Not an Excel file: {filename}")
            return jsonify({'error': 'Not an Excel file'}), 400

        # Get available sheet names
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            logger.info(f"Available sheets: {sheet_names}")
            
            if 'Summary' not in sheet_names:
                logger.error("Summary sheet not found in the Excel file")
                return jsonify({'error': 'Summary sheet not found in the Excel file'}), 400
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            return jsonify({'error': f'Error reading Excel file: {str(e)}'}), 500

        # Read the Summary sheet from the Excel file
        logger.info(f"Reading Summary sheet from {file_path}")
        df = pd.read_excel(file_path, sheet_name='Summary')
        
        if df.empty:
            logger.error("Summary sheet is empty")
            return jsonify({'error': 'Summary data is empty'}), 400
        
        # Convert the first row to a dictionary
        summary_stats = df.iloc[0].to_dict()
        logger.info(f"Base summary stats: {summary_stats}")
        
        # Initialize revenue values
        summary_stats.update({
            'total_revenue_file1': 0,
            'total_revenue_file2': 0,
            'status_revenue_file1': {},
            'status_revenue_file2': {}
        })
        
        # Find the Rates sheets for both files
        rates_file1_sheet = None
        rates_file2_sheet = None
        
        for sheet_name in sheet_names:
            if sheet_name.startswith('Rates ') and 'file1' in sheet_name.lower():
                rates_file1_sheet = sheet_name
            elif sheet_name.startswith('Rates ') and 'file2' in sheet_name.lower():
                rates_file2_sheet = sheet_name
        
        # If we don't find sheets with file1/file2 in the name, try to find by other patterns
        if not rates_file1_sheet or not rates_file2_sheet:
            for sheet_name in sheet_names:
                if sheet_name.startswith('Rates ') and rates_file1_sheet is None:
                    rates_file1_sheet = sheet_name
                elif sheet_name.startswith('Rates ') and rates_file1_sheet is not None and rates_file2_sheet is None:
                    rates_file2_sheet = sheet_name
        
        logger.info(f"Found rates sheets: File1={rates_file1_sheet}, File2={rates_file2_sheet}")
        
        # Calculate total revenue and status-wise revenue from Rates sheets
        try:
            if rates_file1_sheet and rates_file1_sheet in sheet_names:
                logger.info(f"Reading rates from {rates_file1_sheet}")
                rates_df1 = pd.read_excel(file_path, sheet_name=rates_file1_sheet)
                
                # Get total revenue
                if 'total_revenue' in rates_df1.columns:
                    summary_stats['total_revenue_file1'] = rates_df1['total_revenue'].sum()
                    logger.info(f"Total revenue from {rates_file1_sheet}: {summary_stats['total_revenue_file1']}")
                
                # Get status-wise revenue
                status_cols = [col for col in rates_df1.columns if col.startswith('revenue_')]
                for col in status_cols:
                    status = col.replace('revenue_', '').title()
                    if status and not pd.isna(rates_df1[col].sum()):
                        summary_stats['status_revenue_file1'][status] = float(rates_df1[col].sum())
            
            if rates_file2_sheet and rates_file2_sheet in sheet_names:
                logger.info(f"Reading rates from {rates_file2_sheet}")
                rates_df2 = pd.read_excel(file_path, sheet_name=rates_file2_sheet)
                
                # Get total revenue
                if 'total_revenue' in rates_df2.columns:
                    summary_stats['total_revenue_file2'] = rates_df2['total_revenue'].sum()
                    logger.info(f"Total revenue from {rates_file2_sheet}: {summary_stats['total_revenue_file2']}")
                
                # Get status-wise revenue
                status_cols = [col for col in rates_df2.columns if col.startswith('revenue_')]
                for col in status_cols:
                    status = col.replace('revenue_', '').title()
                    if status and not pd.isna(rates_df2[col].sum()):
                        summary_stats['status_revenue_file2'][status] = float(rates_df2[col].sum())
            
            logger.info(f"Status-wise revenue for file1: {summary_stats['status_revenue_file1']}")
            logger.info(f"Status-wise revenue for file2: {summary_stats['status_revenue_file2']}")
        except Exception as e:
            logger.warning(f"Error calculating revenue from rates sheets: {str(e)}")
        
        # If we still don't have revenue, try to get it from Matching Records and Mismatches
        if summary_stats['total_revenue_file1'] == 0 or summary_stats['total_revenue_file2'] == 0:
            try:
                # Read additional sheets for revenue calculations if they exist
                if 'Matching Records' in sheet_names:
                    logger.info("Reading Matching Records sheet")
                    matching_records = pd.read_excel(file_path, sheet_name='Matching Records')
                    
                    # Calculate total revenue for both files
                    file1_revenue_cols = [col for col in matching_records.columns if col.startswith('revenue_') and '_file1' in col]
                    file2_revenue_cols = [col for col in matching_records.columns if col.startswith('revenue_') and '_file2' in col]
                    
                    logger.info(f"Revenue columns found - File 1: {file1_revenue_cols}, File 2: {file2_revenue_cols}")
                    
                    # Sum revenue from matching records
                    if not matching_records.empty and file1_revenue_cols and file2_revenue_cols:
                        summary_stats['total_revenue_file1'] += matching_records[file1_revenue_cols[0]].sum()
                        summary_stats['total_revenue_file2'] += matching_records[file2_revenue_cols[0]].sum()
                
                if 'Mismatches' in sheet_names:
                    logger.info("Reading Mismatches sheet")
                    mismatches = pd.read_excel(file_path, sheet_name='Mismatches')
                    
                    # Calculate total revenue for both files from mismatches
                    file1_revenue_cols = [col for col in mismatches.columns if col.startswith('revenue_') and '_file1' in col]
                    file2_revenue_cols = [col for col in mismatches.columns if col.startswith('revenue_') and '_file2' in col]
                    
                    # Sum revenue from mismatches
                    if not mismatches.empty and file1_revenue_cols and file2_revenue_cols:
                        summary_stats['total_revenue_file1'] += mismatches[file1_revenue_cols[0]].sum()
                        summary_stats['total_revenue_file2'] += mismatches[file2_revenue_cols[0]].sum()
                
                logger.info(f"Final summary stats with revenue: {summary_stats}")
            except Exception as e:
                logger.warning(f"Error calculating revenue from matching/mismatches: {str(e)}")
        
        # Ensure all numeric values are properly converted to numbers
        for key, value in summary_stats.items():
            if pd.isna(value):
                summary_stats[key] = 0
            elif isinstance(value, (np.int64, np.float64)):
                summary_stats[key] = float(value)
        
        # Verify that status-wise revenue sums up to total revenue
        if summary_stats['status_revenue_file1']:
            status_sum_file1 = sum(summary_stats['status_revenue_file1'].values())
            if abs(status_sum_file1 - summary_stats['total_revenue_file1']) > 1:  # Allow for small rounding differences
                logger.warning(f"Status-wise revenue sum ({status_sum_file1}) doesn't match total revenue ({summary_stats['total_revenue_file1']}) for file1")
        
        if summary_stats['status_revenue_file2']:
            status_sum_file2 = sum(summary_stats['status_revenue_file2'].values())
            if abs(status_sum_file2 - summary_stats['total_revenue_file2']) > 1:  # Allow for small rounding differences
                logger.warning(f"Status-wise revenue sum ({status_sum_file2}) doesn't match total revenue ({summary_stats['total_revenue_file2']}) for file2")
        
        return jsonify(summary_stats)
    except Exception as e:
        logger.error(f"Error getting summary stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join('../client/dist', path)):
        return send_from_directory('../client/dist', path)
    else:
        return send_from_directory('../client/dist', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 