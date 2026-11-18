from pathlib import Path
from pypdf import PdfReader

pdf = Path(
    "docs/nps2019/"
    "NPS_2018_2019_Agricultural_Questionnaire.pdf"
)

reader = PdfReader(str(pdf))

# PDF page numbers: 15, 16, 17 and 18
pages_to_inspect = [15, 16, 17, 18]

for page_no in pages_to_inspect:

    page = reader.pages[page_no - 1]
    content = page.extract_text() or ""

    print("\n" + "=" * 80)
    print("QUESTIONNAIRE PDF PAGE:", page_no)
    print("=" * 80)

    print(content)

print("\nHARVEST QUESTIONNAIRE PAGES INSPECTION COMPLETE.")
