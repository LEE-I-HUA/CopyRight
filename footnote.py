import os
import re
import fitz  # PyMuPDF
from pymongo import MongoClient, UpdateOne


# =========================
# MongoDB config
# =========================
MONGO_URI = "mongodb://*"
DB_NAME = "copyright"

INDEX_COL = "index_todo"
FOOTNOTE_COL = "footNote_testing"

PDF_FOLDER = r"data"

TARGET_FONT = "Helvetica"
SIZE1 = 6.0
SIZE2 = 9.0

BATCH_SIZE = 1000


# =========================
# Load index ranges
# =========================
def load_index_ranges(db):
    """
    Build mapping:
    {
      pdf: [
        { "No": ..., "start": page, "end": end_page or None }
      ]
    }
    """
    ranges = {}

    for idx in db[INDEX_COL].find({}, {"pdf": 1, "page": 1, "end_page": 1, "No": 1}):
        pdf = idx.get("pdf")
        if not pdf:
            continue

        entry = {
            "No": idx.get("No"),
            "start": idx.get("page"),
            "end": idx.get("end_page")
        }
        ranges.setdefault(pdf, []).append(entry)

    # 保證同一 pdf 依 start page 排序（避免錯配）
    for pdf in ranges:
        ranges[pdf].sort(key=lambda x: x["start"])

    return ranges


def find_no_for_page(index_ranges, pdf, page):
    """
    Given pdf + page, find corresponding No.
    """
    if pdf not in index_ranges:
        return None

    for r in index_ranges[pdf]:
        if r["end"] is not None:
            if r["start"] <= page <= r["end"]:
                return r["No"]
        else:
            if page >= r["start"]:
                return r["No"]

    return None


# =========================
# Footnote extraction
# =========================
def extract_footnotes(pdf_path, target_font="Helvetica", size1=6.0, size2=9.0):
    """
    Return rows: List[(page_1based, footnote_text)]
    """
    doc = fitz.open(pdf_path)
    rows = []
    collecting = False
    footnote_text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if "lines" not in b:
                continue

            for line_num, line in enumerate(b["lines"]):
                spans = line.get("spans", [])
                for i, span in enumerate(spans):
                    font_name = span.get("font", "")
                    size = span.get("size", 0)
                    text = span.get("text", "") or ""

                    if collecting:
                        if i < len(spans) - 1:
                            next_text = spans[i + 1].get("text", "") or ""
                            if text.endswith(".") and re.match(r"^[A-Z]", next_text):
                                rows.append((page_num + 1, footnote_text.strip()))
                                collecting = False
                                footnote_text = ""
                                continue
                        footnote_text += " " + text

                    if (
                        not collecting
                        and font_name == target_font
                        and float(size) == float(size1)
                        and i < len(spans) - 1
                        and float(spans[i + 1].get("size", 0)) == float(size2)
                    ):
                        collecting = True
                        footnote_text = text + " " + (spans[i + 1].get("text", "") or "").strip()

                if collecting and line_num == len(b["lines"]) - 1:
                    rows.append((page_num + 1, footnote_text.strip()))
                    collecting = False
                    footnote_text = ""

    if collecting and footnote_text.strip():
        rows.append((page_num + 1, footnote_text.strip()))

    doc.close()
    return rows


# =========================
# Main pipeline
# =========================
def process_pdfs_with_no():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    foot_col = db[FOOTNOTE_COL]

    index_ranges = load_index_ranges(db)

    pdf_files = sorted(f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf"))
    print(f"Found {len(pdf_files)} PDFs")

    ops = []
    total = 0

    for filename in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, filename)
        print(f"\n[PDF] {filename}")

        rows = extract_footnotes(pdf_path, TARGET_FONT, SIZE1, SIZE2)
        print(f"  extracted {len(rows)} footnotes")

        for page, text in rows:
            no_value = find_no_for_page(index_ranges, filename, page)

            doc_filter = {
                "pdf": filename,
                "page": page,
                "Footnote": text
            }

            doc_set = {
                "pdf": filename,
                "page": page,
                "Footnote": text,
                "No": no_value
            }

            ops.append(UpdateOne(doc_filter, {"$set": doc_set}, upsert=True))
            total += 1

            if len(ops) >= BATCH_SIZE:
                res = foot_col.bulk_write(ops, ordered=False)
                print(f"  [WRITE] upserted={len(res.upserted_ids)} modified={res.modified_count}")
                ops.clear()

    if ops:
        res = foot_col.bulk_write(ops, ordered=False)
        print(f"  [WRITE] upserted={len(res.upserted_ids)} modified={res.modified_count}")

    print("\n==== Done ====")
    print(f"Total footnotes processed: {total}")


if __name__ == "__main__":
    process_pdfs_with_no()
