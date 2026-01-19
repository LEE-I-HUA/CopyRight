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
### 🍡​ collection: judges_tidy 

##### 🌸judge.ipynb -> simple webcrawler of Ballopedia

- Websites sometimes block web crawlers
- name are written in different way we need to change the the format to meet the input
- some names are not in ballopedia need, so we need to add them into the collection manually
- some names are too short to be found directly. when the situation happens, find all the posible results from websites and save them into collection. We can match the other information of the profiles and the case.
---
### 🍡​ collection: new_format_opinion

#### 🐦‍⬛​ demo collection: opinion_testing

##### 🌸​ opinion.py -> extracts Opinion sections from legal PDF files using font- and layout-based rules (detecting Opinion headers and body text across pages), aggregates associated hyperlinks, and stores each complete Opinion section into MongoDB with page range metadata for research use.

---

### 🍡​ collection: RST_Preprocessed_SBS

##### 🌸​ link_classify.ipynb  → classify objects under "urls_dic" in RST_Preprocessed_SBS

---

### 🍡​ collection: case_urn

##### 🌸​ buildup_case_urn.ipynb  → build "case_urn" collection by extracting and consolidating citation data from RST_Preprocessed_SBS 

---
