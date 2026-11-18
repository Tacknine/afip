from pathlib import Path
from pypdf import PdfReader

pdf = Path(
    "docs/nps2019/"
    "NPS_2018_2019_Agricultural_Questionnaire.pdf"
)

reader = PdfReader(str(pdf))

print("TOTAL PDF PAGES:", len(reader.pages))

for page_no, page in enumerate(reader.pages, start=1):

    content = page.extract_text() or ""
    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    print("\n" + "=" * 65)
    print("PDF PAGE:", page_no)
    print("=" * 65)

    # Show first 18 lines to identify the page section
    print("\n".join(lines[:18]))

print("\nALL PAGE HEADINGS INSPECTED.")
