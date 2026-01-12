# CopyRight
## from licensed legal PDFs to structured metadata (research use)
### collection: index_todo
##### setting_index.ipynb -> getting No, page, pdf Court, Date, and Title of index_todo collection 
- Remember to check the output in note book to fix some data manually.
##### circuit_level.ipynb -> getting Court Level of index_todo collection
### collection: RST_Preprocessed_SBS
##### link_classify.ipynb -> get category of objects under urls_dic in RST_Preprocessed_SBS collection
### collection: buildup_case_urn.ipynb
##### write in case_urn collection by extracting data from RST_Preprocessed_SBS collection
=================
## Case Metadata Extraction Notebook
This notebook implements a research-oriented pipeline for extracting case-level metadata
from Lexis-style U.S. judicial opinion PDFs.
It focuses on editorial metadata (e.g., Core Terms, Judges, Opinion by, procedural history)
and writes structured results directly into MongoDB.
The notebook reflects an evolved prototype combining regex-based and block-level extraction.
It is intended as a reference implementation rather than a production entry point.
