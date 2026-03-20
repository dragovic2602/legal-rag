"""
fill_document.py

Udfylder {{ PLACEHOLDER }}-tags i en Word .docx-skabelon via docxtpl (Jinja2).
Al formatering (fonte, justering, fed) bevares automatisk.

Brug:
    python fill_document.py <docx_sti> <json_sti>

Scriptet gemmer den udfyldte fil paa samme sti (overskriver skabelonen).
"""

import json
import sys
from pathlib import Path

try:
    from docxtpl import DocxTemplate
except ImportError:
    print("FEJL: docxtpl er ikke installeret. Koel: pip install docxtpl")
    sys.exit(1)


def fill_document(docx_path: str, context: dict) -> None:
    doc = DocxTemplate(docx_path)

    # Find alle variabler defineret i skabelonen
    template_vars = doc.get_undeclared_template_variables()

    # Rapporteer variabler der mangler i context
    missing = sorted(template_vars - set(context.keys()))

    doc.render(context)
    doc.save(docx_path)
    print(f"Gemt: {docx_path}")

    if missing:
        print(f"\nFoelgende {len(missing)} placeholders er endnu ikke udfyldt:")
        for tag in missing:
            print(f"  {{{{ {tag} }}}}")
    else:
        print("Alle placeholders er udfyldt.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Brug: python fill_document.py <docx_sti> <json_sti>")
        sys.exit(1)

    docx_path = sys.argv[1]
    json_path = sys.argv[2]

    if not Path(docx_path).exists():
        print(f"FEJL: Filen findes ikke: {docx_path}")
        sys.exit(1)

    if not Path(json_path).exists():
        print(f"FEJL: JSON-filen findes ikke: {json_path}")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    fill_document(docx_path, data)
