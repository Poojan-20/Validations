from flask import Flask, render_template, request, send_file, jsonify, Response
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
        files = []
        for filename in os.listdir(app.config['HISTORY_FOLDER']):
            file_path = os.path.join(app.config['HISTORY_FOLDER'], filename)
            file_stats = os.stat(file_path)
            files.append({
                'name': filename,
                'date': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': f"{file_stats.st_size / (1024*1024):.2f} MB"
            })
        return jsonify(files)
    except Exception as e:
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
            
            # Write existing comparison results
            comparison_results['matching_records'].to_excel(writer, sheet_name='Matching Records', index=False)
            comparison_results['value_mismatches'].to_excel(writer, sheet_name='Mismatches', index=False)
            comparison_results['only_in_df1'].to_excel(writer, sheet_name=f'Only in {file1_name}', index=False)
            comparison_results['only_in_df2'].to_excel(writer, sheet_name=f'Only in {file2_name}', index=False)
            
            # Write rates
            rate_results = validator.compare_rates()
            rate_results['rates_file1'].to_excel(writer, sheet_name=f'Rates {file1_name}', index=False)
            rate_results['rates_file2'].to_excel(writer, sheet_name=f'Rates {file2_name}', index=False)

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

if __name__ == '__main__':
    app.run(debug=True) 