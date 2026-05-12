PDF Difference Analyzer

A web-based PDF comparison application built using Streamlit that detects and highlights differences between two PDF documents.

The application compares:

Text changes
Image changes
Cosmetic/formatting changes

and generates a highlighted output PDF for easy visual inspection.

##Features
Upload two PDF files
Detect text insertions, deletions, and modifications
Compare embedded images using SSIM
Detect cosmetic formatting changes
Highlight changes directly on the modified PDF
Side-by-side PDF preview
Download annotated comparison PDF
Interactive web-based interface
##Tech Stack
Python
Streamlit
PyMuPDF
OpenCV
NumPy
scikit-image
Pillow
##Project Structure
pdf-difference-analyzer/
│
├── app.py
├── requirements.txt
├── README.md
│
├── outputs/
└── temp/
##Installation
Clone Repository
git clone <your-repository-url>
cd pdf-difference-analyzer
Install Dependencies
pip install -r requirements.txt
##Requirements
streamlit
PyMuPDF
opencv-python
numpy
scikit-image
Pillow
##Run the Application
streamlit run app.py
