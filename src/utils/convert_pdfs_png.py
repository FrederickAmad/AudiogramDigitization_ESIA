import os
import fitz  # PyMuPDF
from PIL import Image

def pdf_to_png(pdf_path, output_dir):
    # Open the PDF file
    document = fitz.open(pdf_path)
    
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the base name of the PDF file without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Iterate over each page in the PDF
    for page_number in range(len(document)):
        # Load the page
        page = document.load_page(page_number)
        
        # Render the page to a pixmap (image)
        pix = page.get_pixmap()
        
        # Define the output file path
        output_file = os.path.join(output_dir, f'{base_name}_page_{page_number + 1}.png')
        
        # Save the pixmap as a PNG
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        image.save(output_file, "PNG")
        
        print(f'Saved {output_file}')
    
    # Close the document
    document.close()

def process_pdfs(input_path, output_dir):
    if os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
        # Process a single PDF file
        pdf_to_png(input_path, output_dir)
    elif os.path.isdir(input_path):
        # Process all PDFs in the directory
        for filename in os.listdir(input_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(input_path, filename)
                pdf_to_png(pdf_path, output_dir)
    else:
        print("Invalid input path. Please provide a PDF file or a directory containing PDF files.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python convert_pdfs_png.py <input_path> <output_directory>")
        print("input_path can be a single PDF file or a directory containing PDF files")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    # Process PDFs
    process_pdfs(input_path, output_dir)