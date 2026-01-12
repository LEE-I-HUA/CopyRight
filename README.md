# CopyRight
## from licensed legal PDFs to structured metadata (research use)

---

### 🍡 ​collection: index_todo
#### 🐦‍⬛​ demo collection: testing_writein

##### 🌸​ setting_index.ipynb  
→ extract basic case index information  
(getting No, page, pdf, Court, Date, and Title)

- Remember to check the output in notebook and fix some entries (title) manually if needed.

##### 🌸​ circuit_level.ipynb  
→ derive Court Level / Circuit information for index_todo

##### 🌸​ lexis_metadata_extractor.py  
→ enrich index_todo with Lexis-style opinion front-matter metadata

- Extracts structured metadata from Lexis-formatted PDFs:
  - Core Terms
  - Judges
  - Opinion by
  - Counsel
  - Prior history
  - Subsequent history
- Designed to start from the opinion page (`page`) and scan forward
- Used both for single-case testing and batch backfilling
- Does not overwrite existing core index fields

##### 🌸​ index_preprocess.py  
→ post-extraction normalization and cleanup for index_todo

- Removes Lexis footnote markers (e.g. `[*1]`, `[**12]`) from selected textual fields
- Normalizes date-related fields (`Argued`, `Decided`, `Others`) into timezone-aware
  datetime objects (Asia/Taipei, GMT+8)
- Uses batch updates (`bulk_write`) and only modifies documents when values change
- Designed to be re-runnable and schema-preserving (idempotent normalization)

---

### 🍡​ collection: RST_Preprocessed_SBS

##### 🌸​ link_classify.ipynb  
→ classify objects under `urls_dic` in RST_Preprocessed_SBS
---

### 🍡​ collection: case_urn

##### 🌸​ buildup_case_urn.ipynb  
→ build `case_urn` collection by extracting and consolidating citation data  
from RST_Preprocessed_SBS
---
### 🍡​ collection: judges_tidy
---
### 🍡​ collection: headNote_todo
---
### 🍡​ collection: opinion_todo
---
### 🍡​ collection: footNote_todo
---
