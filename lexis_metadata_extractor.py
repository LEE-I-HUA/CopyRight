
"""
case_metadata_extractor.py

Purpose
-------
Extract Lexis-style case metadata from a given PDF page and write results
to MongoDB. Designed for U.S. court opinions (Lexis PDFs).

This module can be:
1) imported as a library (extract_case_metadata_from_page)
2) executed directly for single-PDF testing

Author
------
I-Hua Lee (research pipeline version)
"""

import re
import os
import fitz  # PyMuPDF
from typing import Dict, List
from pymongo import MongoClient


# ============================================================
# Core extraction function (LIBRARY)
# ============================================================

def extract_case_metadata_from_page(
    pdf_file_path: str,
    start_page_0based: int,
    *,
    local_scan_pages: int = 2,
    extended_scan_pages: int = 13
) -> Dict[str, object]:
    """
    Extract Lexis-style case metadata starting from a given page.

    Parameters
    ----------
    pdf_file_path : str
        Path to the PDF file.
    start_page_0based : int
        0-based page index.
    local_scan_pages : int
        Pages used for local headers (Core Terms, Prior History).
    extended_scan_pages : int
        Pages used for Counsel / Opinion by / Judges fallback.

    Returns
    -------
    dict
        {
          "core term": List[str],
          "judges": str,
          "counsel": str,
          "plaintiff_defendant": str,
          "opinion by": str,
          "prior history": str,
          "subsequent history": str
        }
    """

    with fitz.open(pdf_file_path) as doc:
        n_pages = len(doc)
        if not (0 <= start_page_0based < n_pages):
            raise ValueError(
                f"start_page out of range: {start_page_0based} / {n_pages}"
            )

        local_text = "\n".join(
            doc[p].get_text("text")
            for p in range(
                start_page_0based,
                min(start_page_0based + local_scan_pages, n_pages)
            )
        )

        extended_text = "\n".join(
            doc[p].get_text("text")
            for p in range(
                start_page_0based,
                min(start_page_0based + extended_scan_pages, n_pages)
            )
        )

        start_page_blocks = doc[start_page_0based].get_text("dict")["blocks"]

    # -------------------------
    # Helper regex functions
    # -------------------------
    def extract_prior_history_loose(text: str) -> str:
        """
        Looser extraction of Prior History section.
        Designed to minimize missingness in Lexis PDFs with layout breaks.
        """
        try:
            pattern = (
                r"Prior History[:\s]+"
                r"([\s\S]+?)"
                r"(?=\n(?:Disposition:|Core Terms|Subsequent History:|"
                r"LexisNexis|Headnotes|HN\d+\[|$))"
            )
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if not m:
                return ""
            content = m.group(1).replace("\n", " ").strip()
            return content
        except Exception:
            return ""


    def extract_section(start_label: str, end_labels: List[str], text: str, max_len=1000) -> str:
        try:
            end_pat = "|".join(end_labels)
            m = re.search(
                rf"{re.escape(start_label)}\s+([\s\S]+?)(?=\n(?:{end_pat}))",
                text,
                flags=re.IGNORECASE
            )
            if not m:
                return ""
            content = m.group(1).replace("\n", " ").strip()
            return content if len(content) <= max_len else ""
        except Exception:
            return ""

    def extract_one_line(label: str, text: str) -> str:
        m = re.search(rf"{re.escape(label)}:\s*(.+)", text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else ""

    # -------------------------
    # Core Terms
    # -------------------------

    core_terms_raw = extract_section(
        "Core Terms",
        end_labels=[
            r"Counsel:",
            r"LexisNexis",
            r"Headnotes",
            r"HN\d+\[",
            r"Opinion by:",
            r"Judges?:"
        ],
        text=local_text,
        max_len=2000
    )
    core_terms = [t.strip() for t in core_terms_raw.split(",")] if core_terms_raw else []

    # -------------------------
    # Judges
    # -------------------------

    judges = extract_section(
        "Judges:",
        [r"Opinion by:", r"Core Terms", r"Counsel:"],
        local_text,
        max_len=300
    )

    if not judges:
        m = re.search(r"\bBefore\s+(.+?)\.", extended_text, flags=re.IGNORECASE)
        if m:
            judges = m.group(1).strip()
    # -------------------------
    # Counsel
    # -------------------------
    counsel = ""
    try:
        match = re.search(
            r'Counsel:\s*(.+?)(?=\n(?:HN\d+\[|Headnotes|Judges?:|Opinion by:|'
            r'Core Terms|Subsequent History:|Prior History:|Disposition:|$))',
            extended_text,
            flags=re.DOTALL | re.IGNORECASE
        )
        if match:
            counsel = match.group(1).replace("\n", " ").strip()
    except Exception:
        counsel = ""

    # -------------------------
    # Opinion by
    # -------------------------

    opinion_by = extract_one_line("Opinion by", extended_text)

    # -------------------------
    # Prior / Subsequent history
    # -------------------------

    # prior_history = ""
    # m = re.search(r"Prior History:\s*(.+)", local_text, flags=re.IGNORECASE)
    # if m:
    #     prior_history = re.sub(r"^\[\*\*\d+\]\s*", "", m.group(1).strip())
    prior_history = extract_prior_history_loose(local_text)

    

    subsequent_history = extract_section(
        "Subsequent History:",
        end_labels=[
            r"Prior History:",
            r"Disposition:",
            r"Core Terms",
            r"LexisNexis",
            r"Headnotes"
        ],
        text=local_text,
        max_len=1000
    )

    # -------------------------
    # Caption (Plaintiff v. Defendant)
    # -------------------------

    def extract_case_title_by_font(blocks) -> str:
        candidate, max_size = "", 0.0
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    size = float(span.get("size", 0))
                    if "v." in txt and size > max_size:
                        candidate, max_size = txt, size
        return candidate

    plaintiff_defendant = extract_case_title_by_font(start_page_blocks)

    return {
        "core term": core_terms,
        "judges": judges or "",
        "plaintiff_defendant": plaintiff_defendant or "",
        "counsel":counsel or "",
        "opinion by": opinion_by or "",
        "prior history": prior_history or "",
        "subsequent history": subsequent_history or ""
    }


# ============================================================
# Executable entry point (SCRIPT)
# ============================================================

def main():
    # ---------- Config (test only) ----------
    MONGO_URI = "mongodb://*"
    DB_NAME = "copyright"
    COL_NAME = "testing_writein"

    PDF_PATH = "./data/cp01.pdf"
    START_PAGE_1BASED = 44
    START_PAGE_0BASED = START_PAGE_1BASED - 1

    # ---------- MongoDB ----------
    client = MongoClient(MONGO_URI)
    col = client[DB_NAME][COL_NAME]

    # ---------- Run ----------
    meta = extract_case_metadata_from_page(
        pdf_file_path=PDF_PATH,
        start_page_0based=START_PAGE_0BASED
    )

    print("\n=== Extracted metadata ===")
    for k, v in meta.items():
        print(f"{k}: {v}")

    col.update_one(
        {
            "pdf": os.path.basename(PDF_PATH),
            "page": START_PAGE_1BASED
        },
        {
            "$set": {
                "pdf": os.path.basename(PDF_PATH),
                "page": START_PAGE_1BASED,
                **meta
            }
        },
        upsert=True
    )


if __name__ == "__main__":
    main()

# output
# === Extracted metadata ===
# core term: ['profits', 'infringement', 'damages', 'printer', 'magazine']
# judges: MILLER, EDGERTON, and ARNOLD, Associate Justices
# plaintiff_defendant: Washingtonian Pub. Co. v. Pearson
# counsel: Mr. Horace S. Whitman, of Washington, D.C., with whom Mr. Gibbs L. Baker, of Washington, D.C., was  on the brief, for appellant.   Mr. Eliot C. Lovett, of Washington, D.C., for appellees.
# opinion by: EDGERTON
# prior history: Appeal from the District Court of the United States for the District of Columbia.
# subsequent history: