import streamlit as st
import os
from PIL import Image
import base64
import json

from PIL.FontFile import WIDTH
from dotenv import load_dotenv

from llm_services import LLMServices
from ocr_services import OCRServices

# Load environment variables
load_dotenv()

st.set_page_config(layout="wide", page_title="Document Viewer & OCR Tester")

WIDTH = 500

# Initialize session state variables if they don't exist
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = {}
if 'comparison_result' not in st.session_state:
    st.session_state.comparison_result = None
if 'comparison_model' not in st.session_state:
    st.session_state.comparison_model = None
if 'processed' not in st.session_state:
    st.session_state.processed = False

# Function to list files in the specified directory
def list_files(directory):
    if not os.path.exists(directory):
        st.error(f"Directory '{directory}' does not exist. Please create it and add your files.")
        return []

    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return files


# Function to display PDF
def display_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embed PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="{WIDTH}" height="800" type="application/pdf"></iframe>'

    # Display the PDF
    st.markdown(pdf_display, unsafe_allow_html=True)


# Function to display image
def display_image(image_path):
    image = Image.open(image_path)
    st.image(image, caption=os.path.basename(image_path), width=WIDTH)


# Function to process document with OCR services
def process_document(file_path, ocr_services):
    results = {}

    # Create tabs for each OCR service
    ocr_tabs = st.tabs(ocr_services)

    for i, service in enumerate(ocr_services):
        with ocr_tabs[i]:
            if service == "AWS Textract":
                with st.spinner("Processing with AWS Textract..."):
                    result = OCRServices.aws_textract_ocr(file_path)
                    results["AWS Textract"] = result
                    st.text_area("AWS Textract Result", result, height=400)

            elif service == "Landing AI":
                with st.spinner("Processing with Landing AI..."):
                    result = OCRServices.landing_ai_ocr(file_path)
                    results["Landing AI"] = result
                    st.text_area("Landing AI Result", result, height=400)

            elif service == "Mistral OCR":
                with st.spinner("Processing with Mistral OCR..."):
                    result = OCRServices.mistral_ocr(file_path)
                    results["Mistral OCR"] = result
                    st.text_area("Mistral OCR Result", result, height=400)

            elif service == "Claude 3 Haiku":
                with st.spinner("Processing with Claude 3 Haiku..."):
                    result = OCRServices.claude_haiku_ocr(file_path)
                    results["Claude 3 Haiku"] = result
                    st.text_area("Claude 3 Haiku Result", result, height=400)

    # Store results in session state for later comparison
    st.session_state.ocr_results = results
    st.session_state.processed = True

    return results


# Function to compare OCR results using LLM
def compare_results(results, model_choice):
    with st.spinner(f"Analyzing OCR results with {model_choice}..."):
        comparison = LLMServices.compare_ocr_results(results, model_choice)
        st.session_state.comparison_result = comparison
        st.session_state.comparison_model = model_choice
        return comparison


# Main app
def main():
    # Directory path
    directory = "assets/testing_files"

    # List files in the directory
    files = list_files(directory)

    if not files:
        st.info("No files found in the directory. Please add some files to get started.")
        return

    # Create a selectbox for file selection
    selected_file = st.sidebar.selectbox("Select a document:", files)
    file_path = os.path.join(directory, selected_file) if selected_file else None
    file_extension = os.path.splitext(selected_file)[1].lower() if selected_file else None

    st.header("OCR Testing")

    if selected_file:
        st.write(f"Selected file: **{selected_file}**")

        # Display original document
        st.subheader("Original Document")
        if file_extension == ".pdf":
            display_pdf(file_path)
        elif file_extension in [".jpg", ".jpeg", ".png"]:
            display_image(file_path)

        # OCR service selection
        st.subheader("Select OCR Services to Test")
        ocr_services = st.multiselect(
            "Choose one or more OCR services:",
            ["AWS Textract", "Landing AI", "Mistral OCR", "Claude 3 Haiku"],
            default=["AWS Textract"]
        )

        if ocr_services:
            # Process button
            test_button = st.button("Get OCR Results")

            # Process document if button is clicked or if already processed
            if test_button:
                st.session_state.processed = False  # Reset processed state
                st.session_state.comparison_result = None  # Reset comparison result
                st.session_state.comparison_model = None  # Reset comparison model
                st.subheader("OCR Results")
                process_document(file_path, ocr_services)
            elif st.session_state.processed:
                st.subheader("OCR Results")
                # Display previously processed results
                ocr_tabs = st.tabs(list(st.session_state.ocr_results.keys()))
                for i, (service, result) in enumerate(st.session_state.ocr_results.items()):
                    with ocr_tabs[i]:
                        st.text_area(f"{service} Result", result, height=400)

            # Add LLM comparison section if we have results
            if st.session_state.processed and len(st.session_state.ocr_results) > 1:
                st.subheader("LLM Comparison")

                # Model selection dropdown
                model_choice = st.selectbox(
                    "Select LLM model for comparison:",
                    ["OpenAI GPT-4o", "Claude Sonnet 3.5"],
                    index=0
                )

                # Compare button
                compare_button = st.button("Compare Results with LLM")

                if compare_button:
                    comparison = compare_results(st.session_state.ocr_results, model_choice)
                    st.markdown(comparison)
                elif st.session_state.comparison_result:
                    # Display previous comparison result if available
                    if 'comparison_model' in st.session_state:
                        st.write(f"Analysis by: {st.session_state.comparison_model}")
                    st.markdown(st.session_state.comparison_result)
            elif st.session_state.processed and len(st.session_state.ocr_results) <= 1:
                st.info("Select at least two OCR services to enable comparison.")
        else:
            st.info("Please select at least one OCR service to test.")
    else:
        st.info("Please select a document from the sidebar to begin OCR testing.")


if __name__ == "__main__":
    main()
