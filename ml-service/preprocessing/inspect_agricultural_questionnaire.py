from pathlib import Path
from pypdf import PdfReader

pdf = Path(
    "docs/nps2019/"
    "NPS_2018_2019_Agricultural_Questionnaire.pdf"
)

reader = PdfReader(str(pdf))

keywords = [
    "quantity harvested",
    "area harvested",
    "unit of measurement",
    "unit of measure",
    "long rainy season",
    "short rainy season",
    "harvested",
    "local unit",
    "kilogram",
    "kilograms",
    "bag",
    "bags",
    "AG_SEC_4A",
    "AG_SEC_4B"
]

print("DOCUMENT:", pdf.name)
print("TOTAL PAGES:", len(reader.pages))

for page_no, page in enumerate(reader.pages, start=1):

    content = page.extract_text() or ""
    lower = content.lower()

    matched = [
        keyword for keyword in keywords
        if keyword.lower() in lower
    ]

    if matched:
        print("\n" + "=" * 75)
        print("PAGE:", page_no)
        print("MATCHES:", matched)
        print("=" * 75)
        print(content[:7000])

print("\nAGRICULTURAL QUESTIONNAIRE SEARCH COMPLETE.")
