"""SPARSH - AI-assisted switchboard mapping for tactile accessibility.

Module map (matches the system architecture in the report):
  M1 acquisition.py    - load / validate a switchboard photo
  M2 preprocessing.py  - plate localisation, perspective + lighting correction
  M3 detection.py      - switch candidate proposal + confidence scoring
       verifier.py     - learned patch verifier (HOG + logistic regression)
  M4 layout.py         - row clustering + human-readable numbering (S1..Sn)
  M5 mapping.py        - human confirmation state, corrections, validation
  M6 tactile.py        - tactile vocabulary + cap assignment
  M7 guide.py          - printable installation guide (HTML)
  M8 logger.py         - consented study/event logging (CSV/JSONL)
"""
__version__ = "1.0.0"
