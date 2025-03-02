# Excel Validator

A web application for comparing and validating Excel files.

## Project Structure

- `server/`: Flask backend
- `client/`: React frontend built with Vite.js and Tailwind CSS

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the Flask server:
   ```
   cd server
   python app.py
   ```

### Frontend Setup

1. Install Node.js dependencies:
   ```
   cd client
   npm install
   ```

2. Run the development server:
   ```
   npm run dev
   ```

3. Build for production:
   ```
   npm run build
   ```

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Upload two Excel files for comparison
3. Map the columns to the required fields
4. Click "Compare Files" to process the files
5. Download the generated report

## Features

- Excel file validation
- Column mapping
- Detailed comparison reports
- Progress tracking
- History of processed files 