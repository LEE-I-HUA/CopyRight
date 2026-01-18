import os
import re
import fitz  # PyMuPDF
from pymongo import MongoClient

# ======================================================
# MongoDB configuration
# ======================================================
MONGO_URI = "mongodb://*"
DB_NAME = "copyright"
COLLECTION_NAME = "opinion_testing"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ======================================================
# Patterns for Opinion extraction
# ======================================================
# Trigger keyword for starting an Opinion section
opinion_pattern = r"Opinion"

# Marker indicating the end of the document
end_pattern = r"End of Document"

# Pattern used to remove page number artifacts (e.g., "Page 3 of 25")
page_marker_pattern = re.compile(
    r"Page\s+\d+\s+of\s+\d+",
    flags=re.IGNORECASE
)

# ======================================================
# PDF configuration
# ======================================================
pdf_path = r"data/cp01.pdf"   # Path to the PDF file to be processed
pdf_name = os.path.basename(pdf_path)

doc = fitz.open(pdf_path)

# ======================================================
# State variables for cross-page Opinion extraction
# ======================================================
opinion_started = False            # Whether an Opinion section is currently being collected
page_text = ""                     # Accumulated Opinion text across pages
urls_dic_accumulated = []          # Accumulated hyperlinks across Opinion pages
opinion_id = 0                     # Sequential Opinion identifier
start_page_1based = None           # Starting page of the current Opinion (1-based)

# ======================================================
# Helper function: extract hyperlinks from a page
# ======================================================
def get_page_links(page):
    """
    Extract all URI hyperlinks from a PDF page.
    Each link is stored as a dictionary with raw anchor text and URL.
    """
    urls_dic = []
    for link in page.get_links():
        if "uri" in link:
            uri = link["uri"]
            rect = fitz.Rect(link["from"])
            link_text = page.get_textbox(rect) or ""
            urls_dic.append({
                "raw_text": link_text.strip(),
                "link": uri
            })
    return urls_dic


# ======================================================
# Main extraction loop (page by page)
# ======================================================
for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    page_1based = page_num + 1

    # Collect and accumulate hyperlinks from the current page
    urls_dic = get_page_links(page)
    urls_dic_accumulated += urls_dic

    blocks = page.get_text("dict").get("blocks", [])
    for block in blocks:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            for span in line.get("spans", []):
                text = (span.get("text") or "").strip()
                font = span.get("font")
                size = span.get("size")

                # --------------------------------------------------
                # Detect the start of a new Opinion section
                # Condition:
                #   - Font size: 14.0
                #   - Font: Helvetica-Bold
                #   - Text contains the keyword "Opinion"
                # --------------------------------------------------
                if size == 14.0 and font == "Helvetica-Bold" and re.search(opinion_pattern, text):
                    # If an Opinion is already open, save it before starting a new one
                    if opinion_started and page_text.strip():
                        collection.insert_one({
                            "pdf": pdf_name,
                            "opinion_id": opinion_id,
                            "start_page": start_page_1based,
                            "end_page": page_1based - 1,
                            "content": page_text.strip(),
                            "urls_dic": urls_dic_accumulated
                        })
                        opinion_id += 1
                        page_text = ""
                        urls_dic_accumulated = []

                    opinion_started = True
                    start_page_1based = page_1based
                    continue

                # --------------------------------------------------
                # Collect Opinion body text
                # Condition:
                #   - Opinion section has started
                #   - Font size: 10
                #   - Font family: Helvetica variants
                # --------------------------------------------------
                if opinion_started and size == 10 and font in [
                    "Helvetica",
                    "Helvetica-BoldOblique",
                    "Helvetica-Oblique"
                ]:
                    if text:
                        page_text += " " + text
                        # Remove page number artifacts during accumulation
                        page_text = page_marker_pattern.sub("", page_text).strip()

                # --------------------------------------------------
                # Detect the end of the Opinion section
                # --------------------------------------------------
                if opinion_started and re.search(end_pattern, text):
                    page_text = re.sub(end_pattern, "", page_text).strip()
                    collection.insert_one({
                        "pdf": pdf_name,
                        "opinion_id": opinion_id,
                        "start_page": start_page_1based,
                        "end_page": page_1based,
                        "content": page_text,
                        "urls_dic": urls_dic_accumulated
                    })
                    opinion_id += 1
                    opinion_started = False
                    page_text = ""
                    urls_dic_accumulated = []
                    # Continue scanning remaining content if any

# ======================================================
# Finalization: save any unfinished Opinion at EOF
# ======================================================
if opinion_started and page_text.strip():
    collection.insert_one({
        "pdf": pdf_name,
        "opinion_id": opinion_id,
        "start_page": start_page_1based,
        "end_page": len(doc),
        "content": page_text.strip(),
        "urls_dic": urls_dic_accumulated
    })
    print(f"Final Opinion saved. Total opinions: {opinion_id + 1}")
else:
    print(f"Total opinions saved: {opinion_id}")

doc.close()
