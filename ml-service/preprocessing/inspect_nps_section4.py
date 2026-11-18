from pathlib import Path
from pypdf import PdfReader

pdf = Path(
    "docs/nps2019/"
    "NPS_2018_2019_Agricultural_Questionnaire.pdf"
)

reader = PdfReader(str(pdf))

keywords = [
    "4. CROPS",
    "LONG RAINY SEASON",
    "SHORT RAINY SEASON",
    "LAST COMPLETED SHORT RAINY",
    "AREA HARVESTED",
    "AMOUNT HARVESTED",
    "QUANTITY HARVESTED",
    "HARVESTED IN THE",
    "ACRES",
    "KG",
    "KILOGRAMS"
]

for page_no, page in enumerate(reader.pages, start=1):

    content = page.extract_text() or ""
    lines = content.splitlines()

    matched = [
        k for k in keywords
        if k.lower() in content.lower()
    ]

    if matched:
        print("\n" + "=" * 80)
        print("PDF PAGE:", page_no)
        print("MATCHES:", matched)
        print("=" * 80)

        for i, line in enumerate(lines):
            if any(k.lower() in line.lower() for k in matched):
                start = max(0, i - 4)
                end = min(len(lines), i + 7)

                print("\n".join(lines[start:end]))
                print("-" * 50)

print("\nSECTION 4 INSPECTION COMPLETE.")
