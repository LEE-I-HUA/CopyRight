# CopyRight
## from licensed legal PDFs to structured metadata (research use)

---

### collection: index_todo

##### setting_index.ipynb  
→ extract basic case index information  
(getting No, page, pdf, Court, Date, and Title)

- Remember to check the output in notebook and fix some entries manually if needed.

##### circuit_level.ipynb  
→ derive Court Level / Circuit information for index_todo

##### lexis_metadata_extractor.py  
→ enrich index_todo with Lexis-style opinion front-matter metadata

- Extracts structured metadata from Lexis-formatted PDFs:
  - Core Terms
  - Judges
  - Opinion by
  - Counsel
  - Prior history
  - Subsequent history
- Designed to start from the opinion page (`page`) and scan forward
- Used both for single-case testing and batch backfilling (e.g., missing counsel)
- Output is written back to `index_todo` without overwriting existing fields

---

### collection: RST_Preprocessed_SBS

##### link_classify.ipynb  
→ classify objects under `urls_dic` in RST_Preprocessed_SBS

---

### collection: case_urn

##### buildup_case_urn.ipynb  
→ build `case_urn` collection by extracting and consolidating citation data  
from RST_Preprocessed_SBS
