import os
import boto3
import requests
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OCRServices:
    @staticmethod
    def convert_pdf_to_image_bytes(file_path):
        """
        Convert a PDF file to a list of image bytes ready for OCR processing

        Args:
            file_path (str): Path to the PDF file

        Returns:
            list: List of tuples (page_number, image_bytes) for each page of the PDF
            None: If conversion fails
        """
        try:
            from pdf2image import convert_from_path
            import io
            
            # Convert PDF to images
            images = convert_from_path(file_path)
            
            if not images:
                return None
            
            # Convert each image to bytes
            image_bytes_list = []
            for page_num, image in enumerate(images):
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
                image_bytes_list.append((page_num + 1, image_bytes))
                
            return image_bytes_list
            
        except ImportError:
            raise ImportError("PDF processing requires pdf2image library. Install with: pip install pdf2image")
        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")

    @staticmethod
    def aws_textract_ocr(file_path):
        """
        Process document using AWS Textract, handling PDFs by converting to images if needed

        Args:
            file_path (str): Path to the document file

        Returns:
            str: Extracted text and structured data from the document
        """
        try:
            # Initialize AWS client with credentials from environment variables
            textract_client = boto3.client(
                'textract',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'eu-west-1')
            )

            # Determine file type
            file_extension = os.path.splitext(file_path)[1].lower()

            # For PDFs, we need to convert to images first for analyze_expense
            if file_extension == '.pdf':
                try:
                    # Convert PDF to image bytes using our helper method
                    image_bytes_list = OCRServices.convert_pdf_to_image_bytes(file_path)
                    
                    if not image_bytes_list:
                        return "Failed to extract images from PDF"
                    
                    # Process all pages and collect responses
                    all_responses = []
                    
                    for page_num, image_bytes in image_bytes_list:
                        # Use analyze_expense on the image bytes
                        response = textract_client.analyze_expense(
                            Document={'Bytes': image_bytes}
                        )
                        # Clean the response to remove Geometry, BoundingBox, and Polygon fields
                        cleaned_response = OCRServices._clean_textract_response(response)
                        all_responses.append((page_num, cleaned_response))
                    
                    # Format the combined responses - only include the summary, not the full JSON
                    combined_summary = "AWS Textract Analysis Summary (Multiple Pages):\n\n"
                    
                    for page_num, response in all_responses:
                        # Extract key information based on the API used
                        if 'ExpenseDocuments' in response:
                            # This is an analyze_expense response
                            combined_summary += f"--- PAGE {page_num} ---\n"
                            
                            for doc_idx, doc in enumerate(response['ExpenseDocuments']):
                                combined_summary += f"Document {doc_idx + 1}:\n"
                                
                                # Extract summary fields
                                if 'SummaryFields' in doc:
                                    combined_summary += "  Summary Fields:\n"
                                    for field in doc['SummaryFields']:
                                        field_type = field.get('Type', {}).get('Text', 'Unknown')
                                        field_value = field.get('ValueDetection', {}).get('Text', 'N/A')
                                        combined_summary += f"    {field_type}: {field_value}\n"
                                
                                # Extract line item groups
                                if 'LineItemGroups' in doc:
                                    for group_idx, group in enumerate(doc['LineItemGroups']):
                                        combined_summary += f"  Line Item Group {group_idx + 1}:\n"
                                        if 'LineItems' in group:
                                            for item_idx, item in enumerate(group['LineItems']):
                                                combined_summary += f"    Item {item_idx + 1}:\n"
                                                if 'LineItemExpenseFields' in item:
                                                    for field in item['LineItemExpenseFields']:
                                                        field_type = field.get('Type', {}).get('Text', 'Unknown')
                                                        field_value = field.get('ValueDetection', {}).get('Text', 'N/A')
                                                        combined_summary += f"      {field_type}: {field_value}\n"
                    
                    # Return only the summary, not the full JSON response
                    return combined_summary

                except ImportError as ie:
                    return f"PDF processing error: {str(ie)}"
                except Exception as pdf_error:
                    # Fallback to detect_document_text if conversion fails
                    with open(file_path, 'rb') as document:
                        image_bytes = document.read()

                    response = textract_client.detect_document_text(
                        Document={'Bytes': image_bytes}
                    )
                    
                    # Clean the response to remove Geometry, BoundingBox, and Polygon fields
                    cleaned_response = OCRServices._clean_textract_response(response)
                    
                    # Extract text from response
                    summary = "AWS Textract Analysis Summary (DetectDocumentText):\n\n"
                    extracted_text = ""
                    for item in cleaned_response.get("Blocks", []):
                        if item.get("BlockType") == "LINE":
                            extracted_text += item.get("Text", "") + "\n"
                    
                    summary += "Extracted Text:\n" + extracted_text
                    
                    # Return only the summary, not the full JSON response
                    return summary
            else:
                # For images, directly read the file
                with open(file_path, 'rb') as document:
                    image_bytes = document.read()

                # Use analyze_expense for images
                response = textract_client.analyze_expense(
                    Document={'Bytes': image_bytes}
                )
                
                # Clean the response to remove Geometry, BoundingBox, and Polygon fields
                cleaned_response = OCRServices._clean_textract_response(response)
                
                # Extract key information based on the API used
                if 'ExpenseDocuments' in cleaned_response:
                    # This is an analyze_expense response
                    summary = "AWS Textract Analysis Summary (AnalyzeExpense):\n\n"

                    for doc_idx, doc in enumerate(cleaned_response['ExpenseDocuments']):
                        summary += f"Document {doc_idx + 1}:\n"

                        # Extract summary fields
                        if 'SummaryFields' in doc:
                            summary += "  Summary Fields:\n"
                            for field in doc['SummaryFields']:
                                field_type = field.get('Type', {}).get('Text', 'Unknown')
                                field_value = field.get('ValueDetection', {}).get('Text', 'N/A')
                                summary += f"    {field_type}: {field_value}\n"

                        # Extract line item groups
                        if 'LineItemGroups' in doc:
                            for group_idx, group in enumerate(doc['LineItemGroups']):
                                summary += f"  Line Item Group {group_idx + 1}:\n"
                                if 'LineItems' in group:
                                    for item_idx, item in enumerate(group['LineItems']):
                                        summary += f"    Item {item_idx + 1}:\n"
                                        if 'LineItemExpenseFields' in item:
                                            for field in item['LineItemExpenseFields']:
                                                field_type = field.get('Type', {}).get('Text', 'Unknown')
                                                field_value = field.get('ValueDetection', {}).get('Text', 'N/A')
                                                summary += f"      {field_type}: {field_value}\n"
                
                # Return only the summary, not the full JSON response
                return summary

        except Exception as e:
            return f"Error processing with AWS Textract: {str(e)}"

    @staticmethod
    def _clean_textract_response(response):
        """
        Remove Geometry, BoundingBox, and Polygon fields from AWS Textract response
        
        Args:
            response (dict): The original AWS Textract response
            
        Returns:
            dict: The cleaned response with unwanted fields removed
        """
        # Create a deep copy of the response to avoid modifying the original
        full_response = json.loads(json.dumps(response))
        
        # Fields to remove (expanded list to catch variations)
        fields_to_remove = [
            'Geometry', 'BoundingBox', 'Polygon', 'Relationships',
            'RowIndex', 'ColumnIndex', 'RowSpan', 'ColumnSpan',
            'CellGeometry', 'TableGeometry', 'TableBoundingBox', 'TablePolygon'
        ]
        
        # Helper function to recursively remove fields from a dictionary
        def remove_fields(obj):
            if isinstance(obj, dict):
                # Remove unwanted fields
                for field in fields_to_remove:
                    if field in obj:
                        del obj[field]
                
                # Process remaining fields recursively
                for key, value in list(obj.items()):
                    obj[key] = remove_fields(value)
                return obj
            elif isinstance(obj, list):
                # Process list items recursively
                return [remove_fields(item) for item in obj]
            else:
                # Return primitive values as is
                return obj
        
        # Clean the response
        cleaned = remove_fields(full_response)
        
        # For debugging: print the size reduction
        original_size = len(json.dumps(response))
        cleaned_size = len(json.dumps(cleaned))
        reduction_percent = ((original_size - cleaned_size) / original_size) * 100 if original_size > 0 else 0
        print(f"AWS Textract response cleaning: Original size: {original_size}, Cleaned size: {cleaned_size}, Reduction: {reduction_percent:.2f}%")
        
        return cleaned

    @staticmethod
    def landing_ai_ocr(file_path):
        """
        Process document using Landing AI's agentic-document-analysis API

        Args:
            file_path (str): Path to the document file

        Returns:
            str: Extracted text and analysis from the document
        """
        try:
            # Get API credentials from environment variables
            api_key = os.getenv('LANDING_AI_API_KEY')
            api_url = os.getenv('LANDING_AI_ENDPOINT', 'https://api.va.landing.ai/v1/tools/agentic-document-analysis')

            if not api_key:
                return "Landing AI credentials not configured in .env file"

            # Determine file type and prepare request
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension in ['.jpg', '.jpeg', '.png']:
                files = {
                    "image": open(file_path, "rb")
                }
            elif file_extension == '.pdf':
                files = {
                    "pdf": open(file_path, "rb")
                }
            else:
                return f"Unsupported file type for Landing AI: {file_extension}"

            # Prepare headers
            headers = {
                "Authorization": f"Basic {api_key}"
            }

            # Make API request
            response = requests.post(api_url, files=files, headers=headers)

            if response.status_code == 200:
                result = response.json()
                # Format the response for display
                formatted_response = json.dumps(result, indent=2)
                return formatted_response
            else:
                return f"Landing AI API error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error processing with Landing AI: {str(e)}"

    @staticmethod
    def mistral_ocr(file_path):
        """
        Process document using Mistral OCR API with file upload

        Args:
            file_path (str): Path to the document file

        Returns:
            str: Extracted text and structured data from the document
        """
        try:
            # Get API key from environment variables
            api_key = os.getenv('MISTRAL_API_KEY')
            
            if not api_key:
                return "Mistral OCR credentials not configured in .env file"

            # Determine file type
            file_extension = os.path.splitext(file_path)[1].lower()
            file_name = os.path.basename(file_path)
            
            # Check if file type is supported
            if file_extension not in ['.pdf', '.jpg', '.jpeg', '.png']:
                return f"Unsupported file type for Mistral OCR: {file_extension}"
            
            # For PDFs and images, we'll use base64 encoding
            with open(file_path, 'rb') as file:
                file_bytes = file.read()
                
            # Base64 encode the file
            encoded_file = base64.b64encode(file_bytes).decode('utf-8')
            
            # Prepare headers for OCR request
            ocr_headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepare the OCR payload based on file type
            if file_extension == '.pdf':
                ocr_payload = {
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "document_base64",
                        "document_base64": encoded_file,
                        "document_name": file_name
                    }
                }
            else:  # Image files
                # Create a data URL for the image
                mime_type = f"image/{file_extension[1:]}" if file_extension != '.jpg' else "image/jpeg"
                data_url = f"data:{mime_type};base64,{encoded_file}"
                
                ocr_payload = {
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "image_url",
                        "image_url": data_url
                    }
                }
            
            # Make the OCR request
            ocr_url = "https://api.mistral.ai/v1/ocr"
            ocr_response = requests.post(ocr_url, headers=ocr_headers, json=ocr_payload)
            
            # Check if the OCR request was successful
            if ocr_response.status_code != 200:
                return f"Mistral OCR API error: {ocr_response.status_code} - {ocr_response.text}"
            
            # Process the OCR response
            result = ocr_response.json()
            
            # Format the response for display
            formatted_response = json.dumps(result, indent=2)
            
            # Create a summary of the OCR results
            summary = "Mistral OCR Analysis Summary:\n\n"
            
            # Extract text content from the response
            if 'pages' in result:
                for page in result['pages']:
                    page_num = page.get('index', 0)
                    summary += f"--- PAGE {page_num} ---\n"
                    
                    # Add page dimensions if available
                    if 'dimensions' in page:
                        dimensions = page['dimensions']
                        summary += f"Dimensions: {dimensions.get('width', 'N/A')}x{dimensions.get('height', 'N/A')} (DPI: {dimensions.get('dpi', 'N/A')})\n"
                    
                    # Add number of images if available
                    if 'images' in page:
                        summary += f"Images: {len(page['images'])}\n"
                    
                    # Add markdown content if available
                    if 'markdown' in page:
                        summary += f"\nText Content:\n{page['markdown']}\n\n"
            
            # Return both the summary and the full response
            return f"{summary}\n\nFull Response:\n{formatted_response}"

        except Exception as e:
            return f"Error processing with Mistral OCR: {str(e)}"
