import streamlit as st
import os
from PIL import Image
import base64

st.title("Document Viewer App")


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
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="800" type="application/pdf"></iframe>'

    # Display the PDF
    st.markdown(pdf_display, unsafe_allow_html=True)


# Function to display image
def display_image(image_path):
    image = Image.open(image_path)
    st.image(image, caption=os.path.basename(image_path), use_column_width=True)


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
    selected_file = st.selectbox("Select a document to preview:", files)

    if selected_file:
        file_path = os.path.join(directory, selected_file)
        file_extension = os.path.splitext(selected_file)[1].lower()

        # Display file information
        st.write(f"Selected file: **{selected_file}**")
        st.write(f"File type: **{file_extension}**")

        # Display the file based on its type
        if file_extension == ".pdf":
            display_pdf(file_path)
        elif file_extension in [".jpg", ".jpeg", ".png"]:
            display_image(file_path)
        else:
            st.error("Unsupported file type. Please select a PDF, JPG, or PNG file.")


if __name__ == "__main__":
    main()
