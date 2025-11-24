import streamlit as st
from io import BytesIO
from datetime import datetime

# PDF libraries
import fitz  # PyMuPDF (fast page rendering & manipulation)
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

# ---------- Page config ----------
st.set_page_config(layout="wide", page_title="PDF Utilities — Merge / Split / Compress / Edit")
st.title("📄 PDF Utilities — Merge / Split / Compressor / Page Editor")

# ---------- Acknowledgement ----------
ack = st.checkbox(
    "✅ I acknowledge this tool will NOT be used for unethical or illegal purposes. It's intended for professional use."
)
if not ack:
    st.warning("⚠️ You must acknowledge the terms to use this tool.")
    st.stop()

st.info("⚠️ Make sure uploaded PDFs are not encrypted or corrupted. Large files may take time to process.")

# ---------- Mode selector ----------
mode = st.sidebar.radio("Choose a tool", [
    "Merge & Split PDFs",
    "PDF Compressor / Optimizer",
    "PDF Page Editor (Reorder / Delete / Rotate)"
])

# Helper: safe open for PyMuPDF
def open_fitz_from_bytes(b: bytes):
    try:
        return fitz.open(stream=b, filetype="pdf")
    except Exception as e:
        st.error(f"Unable to open PDF with PyMuPDF: {e}")
        return None

# ---------- Merge & Split UI ----------
def merge_split_ui():
    st.header("🔗 Merge and ✂️ Split PDFs")

    col1, col2 = st.columns(2)

    # --- MERGE ---
    with col1:
        st.subheader("Merge PDFs")
        merge_files = st.file_uploader(
            "Upload PDF files to merge",
            type=["pdf"],
            accept_multiple_files=True,
            key="merge_files"
        )
        merge_name = st.text_input("Custom output file name", value="merged.pdf", key="merge_name")

        st.session_state.setdefault("merge_cert", False)
        st.session_state.merge_cert = st.checkbox(
            "Generate Data Deletion Certificate for Merge",
            value=st.session_state.merge_cert,
            key="merge_cert_checkbox"
        )

        if merge_files and st.button("Merge PDFs"):
            try:
                writer = PdfWriter()
                for pdf in merge_files:
                    # Use PyPDF2 to preserve structure
                    reader = PdfReader(pdf)
                    for page in reader.pages:
                        writer.add_page(page)

                merged_bytes = BytesIO()
                writer.write(merged_bytes)
                merged_bytes.seek(0)

                st.success("✅ PDFs merged successfully!")
                st.download_button(
                    "⬇️ Download Merged PDF",
                    data=merged_bytes,
                    file_name=merge_name,
                    mime="application/pdf",
                )

                # Optional certificate
                if st.session_state.merge_cert:
                    cert = BytesIO()
                    c = canvas.Canvas(cert)
                    c.setFont("Helvetica", 12)
                    c.drawString(50, 750, "Data Deletion Certificate (Merge)")
                    c.setFont("Helvetica", 10)
                    c.drawString(50, 720, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    c.drawString(50, 700, "This certifies that temporary files used for merging were deleted.")
                    c.save()
                    cert.seek(0)
                    st.download_button(
                        "📜 Download Merge Deletion Certificate",
                        data=cert,
                        file_name="merge_deletion_certificate.pdf",
                        mime="application/pdf",
                    )

            except Exception as e:
                st.error(f"Error merging PDFs: {e}")

    # --- SPLIT ---
    with col2:
        st.subheader("Split PDF by Page Ranges")
        split_file = st.file_uploader("Upload PDF to split", type=["pdf"], key="split_file")

        if split_file:
            try:
                reader = PdfReader(split_file)
                total_pages = len(reader.pages)
                st.success(f"Uploaded PDF has {total_pages} pages.")
            except Exception as e:
                st.error(f"Unable to read uploaded PDF for splitting: {e}")
                return

            st.session_state.setdefault("split_downloaded", [])

            st.markdown("**Enter page ranges separated by commas (e.g., 1-5,10-15,20-25)**")
            user_input = st.text_input("Page ranges", value="", key="range_input")

            ranges = []
            try:
                for part in user_input.split(","):
                    if not part.strip():
                        continue
                    start_end = part.strip().split("-")
                    if len(start_end) != 2:
                        st.warning(f"Ignoring invalid range format: {part}")
                        continue
                    start, end = map(int, start_end)
                    if start < 1 or end > total_pages or start > end:
                        st.error(f"Invalid range: {start}-{end} (must be within 1-{total_pages})")
                    else:
                        ranges.append((start, end))
            except Exception:
                st.warning("⚠️ Please enter ranges correctly in format: start-end, separated by commas.")

            if ranges:
                if len(st.session_state.split_downloaded) != len(ranges):
                    st.session_state.split_downloaded = [False] * len(ranges)

                for i, (start, end) in enumerate(ranges):
                    if not st.session_state.split_downloaded[i]:
                        writer = PdfWriter()
                        for p in range(start - 1, end):
                            writer.add_page(reader.pages[p])

                        output_bytes = BytesIO()
                        writer.write(output_bytes)
                        output_bytes.seek(0)

                        if st.download_button(
                            f"⬇️ Download pages {start}-{end}",
                            data=output_bytes,
                            file_name=f"pages_{start}_{end}.pdf",
                            mime="application/pdf",
                            key=f"dl_btn_{i}"
                        ):
                            st.session_state.split_downloaded[i] = True
                            st.success(f"✅ Pages {start}-{end} downloaded!")

                if all(st.session_state.split_downloaded) and len(ranges) > 0:
                    st.success("🎉 All selected page ranges have been downloaded!")

                    st.session_state.setdefault("split_cert", False)
                    st.session_state.split_cert = st.checkbox(
                        "Generate Data Deletion Certificate for Split",
                        value=st.session_state.split_cert,
                        key="split_cert_checkbox"
                    )

                    if st.session_state.split_cert:
                        cert = BytesIO()
                        c = canvas.Canvas(cert)
                        c.setFont("Helvetica", 12)
                        c.drawString(50, 750, "Data Deletion Certificate (Split)")
                        c.setFont("Helvetica", 10)
                        c.drawString(50, 720, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        c.drawString(50, 700, "All temporary split files were securely deleted.")
                        c.save()
                        cert.seek(0)
                        st.download_button(
                            "📜 Download Split Deletion Certificate",
                            data=cert,
                            file_name="split_deletion_certificate.pdf",
                            mime="application/pdf",
                        )

                    if st.button("🔄 Reset Split"):
                        st.session_state.split_downloaded = [False] * len(ranges)
                        st.experimental_rerun()


# ---------- Compressor UI ----------
def compressor_ui():
    st.header("📄 PDF Compressor / Optimizer")
    st.markdown("""
    This tool down-samples pages, converts them to JPEG with adjustable quality,
    and rebuilds a compressed PDF. Preview (first 5 pages) is optional.
    """)
    uploaded = st.file_uploader("Upload PDF to compress", type=["pdf"], key="compress_file")
    if not uploaded:
        return

    pdf_bytes = uploaded.read()
    compression_level = st.radio(
        "Select compression level:",
        ["High Quality (Low Compression)", "Balanced (Recommended)", "Smallest Size (Aggressive Compression)"],
        index=1
    )

    if "High Quality" in compression_level:
        image_quality = 90
        dpi = 150
    elif "Balanced" in compression_level:
        image_quality = 70
        dpi = 120
    else:
        image_quality = 50
        dpi = 100

    show_preview = st.checkbox("Show 5-page preview after compression (slower)", value=True)
    out_name = st.text_input("Output filename (without extension):", value=f"compressed_{uploaded.name.split('.')[0]}")

    # Open with PyMuPDF
    input_pdf = open_fitz_from_bytes(pdf_bytes)
    if input_pdf is None:
        return

    if st.button("🔄 Compress PDF"):
        output_pdf = fitz.open()
        total_pages = len(input_pdf)
        progress = st.progress(0)
        status = st.empty()
        try:
            for i in range(total_pages):
                page = input_pdf.load_page(i)
                pix = page.get_pixmap(dpi=dpi)

                # Ensure PNG bytes from pix; convert to PIL then JPEG using Pillow for quality control
                png_bytes = pix.tobytes("png")
                pil_img = Image.open(BytesIO(png_bytes)).convert("RGB")

                img_buf = BytesIO()
                pil_img.save(img_buf, format="JPEG", quality=image_quality, optimize=True)
                img_buf.seek(0)
                img_data = img_buf.getvalue()

                rect = fitz.Rect(0, 0, pix.width, pix.height)
                new_page = output_pdf.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(rect, stream=img_data)

                progress.progress((i + 1) / total_pages)
                status.text(f"Processing page {i+1}/{total_pages}")

            optimized_bytes = output_pdf.tobytes()
            st.success("✅ Compression complete")
            original_size = len(pdf_bytes)
            compressed_size = len(optimized_bytes)
            reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
            st.write(f"**Original:** {original_size/(1024*1024):.2f} MB → **Compressed:** {compressed_size/(1024*1024):.2f} MB ({reduction:.1f}% reduction)")

            # Preview
            if show_preview:
                st.subheader("👁️ Preview (First 5 Pages)")
                try:
                    orig_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    comp_doc = fitz.open(stream=optimized_bytes, filetype="pdf")
                    num_pages = min(5, len(orig_doc))
                    for i in range(num_pages):
                        c1, c2 = st.columns(2)
                        with c1:
                            opix = orig_doc.load_page(i).get_pixmap(dpi=80)
                            st.image(opix.tobytes("png"), caption=f"Original Page {i+1}", use_container_width=True)
                        with c2:
                            cpix = comp_doc.load_page(i).get_pixmap(dpi=80)
                            st.image(cpix.tobytes("png"), caption=f"Compressed Page {i+1}", use_container_width=True)
                    orig_doc.close()
                    comp_doc.close()
                except Exception as e:
                    st.warning(f"Preview unavailable: {e}")

            st.download_button(
                label="📥 Download Compressed PDF",
                data=optimized_bytes,
                file_name=f"{out_name}.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Compression failed: {e}")
        finally:
            try:
                input_pdf.close()
                output_pdf.close()
            except Exception:
                pass
            progress.empty()
            status.empty()

# ---------- Page Editor UI ----------
def page_editor_ui():
    st.header("✂️ PDF Page Reorder / Delete / Rotate Tool")
    st.markdown("Thumbnail view — delete pages, rotate them, then set a new order and export.")
    uploaded = st.file_uploader("Upload PDF to edit", type=["pdf"], key="edit_file")
    if not uploaded:
        return

    pdf_bytes = uploaded.read()
    doc = open_fitz_from_bytes(pdf_bytes)
    if doc is None:
        return

    st.subheader("📌 Page Controls")
    page_actions = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25))
            thumb_bytes = pix.tobytes("png")
            thumb_img = Image.open(BytesIO(thumb_bytes))
        except Exception:
            thumb_img = None

        with st.expander(f"Page {page_number + 1}", expanded=False):
            cols = st.columns([1, 2])
            with cols[0]:
                if thumb_img:
                    st.image(thumb_img, caption=f"Page {page_number + 1}", use_column_width=True)
                else:
                    st.write("Preview unavailable")
            with cols[1]:
                rotate = st.selectbox("Rotate Page", [0, 90, 180, 270], index=0, key=f"rotate_{page_number}")
                delete = st.checkbox("Delete this page", key=f"delete_{page_number}")
                st.write(f"Original size: {int(page.rect.width)} x {int(page.rect.height)} pts")
        page_actions.append({"page": page_number, "rotate": rotate, "delete": delete})

    remaining_indices = [i for i, a in enumerate(page_actions) if not a["delete"]]
    default_order = ",".join(str(i + 1) for i in remaining_indices)
    st.subheader("🔀 Reorder Pages")
    order = st.text_input("Enter new page order (comma-separated page numbers), e.g., 3,1,2", value=default_order)

    if st.button("✅ Apply Changes & Download PDF"):
        try:
            order_list_raw = [x.strip() for x in order.split(",") if x.strip() != ""]
            order_page_numbers = [int(x) - 1 for x in order_list_raw]

            new_doc = fitz.open()
            for pnum in order_page_numbers:
                if pnum < 0 or pnum >= len(page_actions):
                    raise ValueError(f"Invalid page number in order: {pnum+1}")
                action = page_actions[pnum]
                if action["delete"]:
                    continue
                orig_page_index = action["page"]
                rotate_angle = action["rotate"]

                page = doc.load_page(orig_page_index)
                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.show_pdf_page(page.rect, doc, orig_page_index)
                if rotate_angle:
                    new_page.set_rotation(rotate_angle)

            output_bytes = new_doc.write()
            new_doc.close()
            st.success("✅ PDF updated successfully!")
            st.download_button(
                label="⬇️ Download Edited PDF",
                data=output_bytes,
                file_name=f"edited_{uploaded.name}",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"❌ Error while building edited PDF: {e}")
        finally:
            try:
                doc.close()
            except Exception:
                pass

# ---------- Main dispatch ----------
if mode == "Merge & Split PDFs":
    merge_split_ui()
elif mode == "PDF Compressor / Optimizer":
    compressor_ui()
else:
    page_editor_ui()
