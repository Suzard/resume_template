# HTML to PDF Resume Converter

This project provides a simple web application that converts an HTML resume template to PDF format. It uses Flask for the web server and pdfkit (which requires wkhtmltopdf) for PDF conversion.

## Prerequisites

1. Python 3.7 or higher
2. wkhtmltopdf (required for PDF conversion)

### Installing wkhtmltopdf

#### macOS
```bash
brew install wkhtmltopdf
```

#### Ubuntu/Debian
```bash
sudo apt-get install wkhtmltopdf
```

#### Windows
Download the installer from: https://wkhtmltopdf.org/downloads.html

## Setup

1. Clone this repository or download the files
2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5001
```

3. To download the PDF version of the resume, click on:
```
http://localhost:5001/download-pdf
```

## Customize Resume API

# Resume Customization API

## Endpoint

**POST** `http://localhost:5001/download-resume-custom`

---
## Request Body

Send a JSON payload with the following fields:

```json
{
  "job_description": "Full job description text here",
  "company": "Company Name"
}
```
## Description

Generates a customized resume based on a job description.

- Parses the job description to extract relevant keywords
- Uses the company name for file naming and tracking
- Returns a downloadable customized resume

This endpoint is designed to work well with browser extensions that extract job descriptions and company names from job postings.

---



Use the following `curl` command to generate a customized resume based on a job description. Pairs well with the extension that grabs company name and keywords from a job description by highlighting.
### Example Request

```bash
curl -X POST "http://localhost:5001/download-resume-custom" \
  -H "Content-Type: application/json" \
  -H "Accept: */*" \
  -d '{
    "job_description": "Software Engineer role focusing on backend systems, distributed systems, and AWS.",
    "company": "Google"
  }'


## Customizing the Resume

The resume template is located in `templates/resume.html`. You can modify this file to customize your resume's content and styling. The template includes:

- Professional header with contact information
- Professional summary section
- Work experience section
- Education section
- Skills section

## Notes

- The PDF conversion uses A4 page size with no margins
- The template includes responsive styling for better web viewing
- The PDF will be automatically downloaded when accessing the download-pdf endpoint 