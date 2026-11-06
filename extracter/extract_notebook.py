
import json
from pathlib import Path

notebook_path = Path("model_source/S2F_final.ipynb")
output_root = Path("model_source")

with open(notebook_path, "r", encoding="utf-8") as f:
    notebook = json.load(f)

count = 0

for cell in notebook["cells"]:
    if cell["cell_type"] != "code":
        continue

    source = cell.get("source", "")
    if isinstance(source, list):
        source = "".join(source)

    lines = source.splitlines()

    if not lines or not lines[0].startswith("%%writefile "):
        continue

    relative_path = lines[0].replace("%%writefile ", "", 1).strip()
    destination = output_root / relative_path

    destination.parent.mkdir(parents=True, exist_ok=True)

    code = "\n".join(lines[1:]) + "\n"
    destination.write_text(code, encoding="utf-8")

    print(f"Extracted: {destination}")
    count += 1

print(f"\nExtraction complete! {count} files extracted.")
