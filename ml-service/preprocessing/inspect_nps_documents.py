from pathlib import Path
from pypdf import PdfReader

folder = Path("docs/nps2019")

files = [
    folder / "NPS_2018_2019_Agricultural_Questionnaire.pdf",
    folder / "NPS_2019_2020_BID.pdf"
]

keywords = [
    "quantity harvested",
    "unit",
    "kilogram",
    "kilograms",
    "kg",
    "bag",
    "bags",
    "long rainy",
    "short rainy",
    "AG_SEC_4A",
    "AG_SEC_4B",
    "harvested area",
    "crop"
]

for file in files:

    print("\n" + "=" * 80)
    print("DOCUMENT:", file.name)
    print("=" * 80)

    reader = PdfReader(str(file))

    print("TOTAL PAGES:", len(reader.pages))

    matches = 0

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""
        lines = text.splitlines()

        for index, line in enumerate(lines):

            if any(
                keyword.lower() in line.lower()
                for keyword in keywords
            ):

                start = max(0, index - 2)
                end = min(len(lines), index + 4)

                print(f"\nPAGE {page_number}:")

                for context_line in lines[start:end]:
                    print(context_line)

                matches += 1

    print("\nMATCHES FOUND:", matches)

print("\nDOCUMENT INSPECTION COMPLETE.")
