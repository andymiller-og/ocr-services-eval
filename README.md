# OCR Testing & Experimentation

## Introduction

This repository is a collection of experiments and tests with Optical Character Recognition (OCR) tools and libraries. The goal is to understand the capabilities and limitations of different OCR tools and libraries, and to explore how they can be used in various applications.

## OCR Services 

### AWS Textract
Link: [Analyze Expense Endpoint](https://docs.aws.amazon.com/textract/latest/dg/API_AnalyzeExpense.html)

### Landing AI Agentic Document Extraction 
Link: [Landing AI Agentic Document Extraction](https://support.landing.ai/docs/document-extraction)

### Mistral AI OCR 
Link: [Mistral AI OCR](https://docs.mistral.ai/api/#tag/ocr)

## Getting Started

- Clone the repository
- Install the required dependencies using poetry via `poetry install`
- Install poppler via `brew install poppler` (for MacOS) which is required for pdf2image
- In terminal, run `streamlit run app.py` to start the Streamlit app

## Notes 
- AWS Textract 
  - Note that we do have to convert PDFs to images as this endpoint take bytes as the input.
  - Pros: 
    - Fast
  - Cons: 
    - Only supports six languages! 
    - Does not have some of the advanced features like descriptions of the images in the output
  
- Landing AI Agentic Document Extraction
  - Pros: 
    - Handles PDFs without the need to convert to images
    - Handles many languages 
    - Descriptions of the images in the output
  - Cons:
    - Slow
    - Unsure of pricing for the service
    - Unsure of batch processing capabilities

- Mistral AI OCR
  - Pros: 
    - Looks to be super cheap - 1000 pages / $ (and approximately double the pages per dollar with batch inference)
    - Processing up to 2000 pages per minute on a single node.
    - Handles all languages
  - Cons:
    - For purposes of this demo, we do have to send the files to the cloud such that we can provide the OCR endpoint with the required document url. 