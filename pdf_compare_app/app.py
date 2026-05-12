import streamlit as st
import fitz
import cv2
import numpy as np
import tempfile
import os
from difflib import SequenceMatcher
from skimage.metrics import structural_similarity as ssim
from PIL import Image

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="PDF Diff Analyzer",
    layout="wide"
)

st.title("PDF Difference Analyzer")
st.write("Compare two PDFs for text, image, and cosmetic changes.")

# =====================================
# SIDEBAR
# =====================================

st.sidebar.header("Upload PDFs")

pdf1 = st.sidebar.file_uploader(
    "Upload Original PDF",
    type=["pdf"]
)

pdf2 = st.sidebar.file_uploader(
    "Upload Modified PDF",
    type=["pdf"]
)

compare_text = st.sidebar.checkbox("Text Comparison", value=True)
compare_images = st.sidebar.checkbox("Image Comparison", value=True)
compare_cosmetic = st.sidebar.checkbox("Cosmetic Comparison", value=True)

compare_btn = st.sidebar.button("Compare PDFs")

# =====================================
# SAVE UPLOADED FILES
# =====================================

def save_uploaded_file(uploaded_file):

    temp_dir = tempfile.mkdtemp()

    file_path = os.path.join(
        temp_dir,
        uploaded_file.name
    )

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    return file_path

# =====================================
# TEXT COMPARISON
# =====================================

def compare_text_changes(doc1, doc2):

    text_changes = []

    total_pages = min(len(doc1), len(doc2))

    for page_num in range(total_pages):

        page1 = doc1[page_num]
        page2 = doc2[page_num]

        words1 = page1.get_text("words")
        words2 = page2.get_text("words")

        text1 = [w[4] for w in words1]
        text2 = [w[4] for w in words2]

        matcher = SequenceMatcher(None, text1, text2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag != "equal":

                for idx in range(j1, j2):

                    if idx < len(words2):

                        x0, y0, x1, y1 = words2[idx][:4]

                        rect = fitz.Rect(
                            x0,
                            y0,
                            x1,
                            y1
                        )

                        annot = page2.add_highlight_annot(rect)

                        annot.set_colors(stroke=(1, 1, 0))
                        annot.update()

                        text_changes.append({
                            "page": page_num + 1,
                            "word": words2[idx][4],
                            "type": tag
                        })

    return text_changes

# =====================================
# IMAGE EXTRACTION
# =====================================

def extract_images(doc, page_num):

    page = doc[page_num]

    image_list = page.get_images(full=True)

    images = []

    for img in image_list:

        xref = img[0]

        base_image = doc.extract_image(xref)

        image_bytes = base_image["image"]

        image_np = np.frombuffer(
            image_bytes,
            np.uint8
        )

        image = cv2.imdecode(
            image_np,
            cv2.IMREAD_COLOR
        )

        images.append(image)

    return images

# =====================================
# IMAGE COMPARISON
# =====================================

def compare_image_changes(doc1, doc2):

    image_changes = []

    total_pages = min(len(doc1), len(doc2))

    for page_num in range(total_pages):

        page2 = doc2[page_num]

        images1 = extract_images(doc1, page_num)
        images2 = extract_images(doc2, page_num)

        min_images = min(
            len(images1),
            len(images2)
        )

        for idx in range(min_images):

            img1 = images1[idx]
            img2 = images2[idx]

            if img1 is None or img2 is None:
                continue

            img1 = cv2.resize(img1, (300, 300))
            img2 = cv2.resize(img2, (300, 300))

            gray1 = cv2.cvtColor(
                img1,
                cv2.COLOR_BGR2GRAY
            )

            gray2 = cv2.cvtColor(
                img2,
                cv2.COLOR_BGR2GRAY
            )

            score, diff = ssim(
                gray1,
                gray2,
                full=True
            )

            if score < 0.95:

                rect = fitz.Rect(
                    50,
                    50,
                    300,
                    300
                )

                page2.draw_rect(
                    rect,
                    color=(1, 0, 0),
                    width=3
                )

                image_changes.append({
                    "page": page_num + 1,
                    "image_index": idx,
                    "similarity": round(score * 100, 2)
                })

    return image_changes

# =====================================
# COSMETIC COMPARISON
# =====================================

def compare_cosmetic_changes(doc1, doc2):

    cosmetic_changes = []

    total_pages = min(len(doc1), len(doc2))

    for page_num in range(total_pages):

        page1 = doc1[page_num]
        page2 = doc2[page_num]

        blocks1 = page1.get_text("dict")
        blocks2 = page2.get_text("dict")

        spans1 = []
        spans2 = []

        for block in blocks1["blocks"]:

            if "lines" in block:

                for line in block["lines"]:

                    for span in line["spans"]:

                        spans1.append(span)

        for block in blocks2["blocks"]:

            if "lines" in block:

                for line in block["lines"]:

                    for span in line["spans"]:

                        spans2.append(span)

        min_spans = min(
            len(spans1),
            len(spans2)
        )

        for idx in range(min_spans):

            s1 = spans1[idx]
            s2 = spans2[idx]

            style_changed = (
                s1["font"] != s2["font"] or
                s1["size"] != s2["size"] or
                s1["color"] != s2["color"]
            )

            if style_changed:

                bbox = s2["bbox"]

                rect = fitz.Rect(bbox)

                page2.draw_rect(
                    rect,
                    color=(0, 0, 1),
                    width=2
                )

                cosmetic_changes.append({
                    "page": page_num + 1,
                    "text": s2["text"]
                })

    return cosmetic_changes

# =====================================
# PDF PAGE RENDER
# =====================================

def render_pdf_page(page):

    pix = page.get_pixmap(
        matrix=fitz.Matrix(2, 2)
    )

    img = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    return img

# =====================================
# MAIN LOGIC
# =====================================

if compare_btn:

    if pdf1 is None or pdf2 is None:

        st.error("Please upload both PDF files.")

    else:

        with st.spinner("Comparing PDFs..."):

            path1 = save_uploaded_file(pdf1)
            path2 = save_uploaded_file(pdf2)

            doc1 = fitz.open(path1)
            doc2 = fitz.open(path2)

            text_results = []
            image_results = []
            cosmetic_results = []

            # =====================================
            # RUN COMPARISONS
            # =====================================

            if compare_text:

                text_results = compare_text_changes(
                    doc1,
                    doc2
                )

            if compare_images:

                image_results = compare_image_changes(
                    doc1,
                    doc2
                )

            if compare_cosmetic:

                cosmetic_results = compare_cosmetic_changes(
                    doc1,
                    doc2
                )

            # =====================================
            # SAVE OUTPUT PDF
            # =====================================

            output_path = "final_diff_output.pdf"

            doc2.save(
                output_path,
                garbage=4,
                deflate=True
            )

            highlighted_doc = fitz.open(output_path)

            st.success("Comparison Completed")

            # =====================================
            # METRICS
            # =====================================

            st.header("Comparison Results")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Text Changes",
                    len(text_results)
                )

            with col2:

                st.metric(
                    "Image Changes",
                    len(image_results)
                )

            with col3:

                st.metric(
                    "Cosmetic Changes",
                    len(cosmetic_results)
                )

            # =====================================
            # PAGE VIEWER
            # =====================================

            st.header("PDF Preview")

            total_pages = min(
                len(doc1),
                len(highlighted_doc)
            )

            selected_page = st.slider(
                "Select Page",
                1,
                total_pages,
                1
            )

            page1 = doc1[selected_page - 1]
            page2 = highlighted_doc[selected_page - 1]

            img1 = render_pdf_page(page1)
            img2 = render_pdf_page(page2)

            left, right = st.columns(2)

            with left:

                st.subheader("Original PDF")

                st.image(
                    img1,
                    use_container_width=True
                )

            with right:

                st.subheader("Modified Highlighted PDF")

                st.image(
                    img2,
                    use_container_width=True
                )

            # =====================================
            # CHANGE DETAILS
            # =====================================

            st.header("Detailed Changes")

            if text_results:

                st.subheader("Text Changes")

                st.json(text_results)

            if image_results:

                st.subheader("Image Changes")

                st.json(image_results)

            if cosmetic_results:

                st.subheader("Cosmetic Changes")

                st.json(cosmetic_results)

            # =====================================
            # DOWNLOAD BUTTON
            # =====================================

            with open(output_path, "rb") as f:

                st.download_button(
                    label="Download Highlighted PDF",
                    data=f,
                    file_name="pdf_diff_result.pdf",
                    mime="application/pdf"
                )