import os
import sys
import re
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PlaceSync.settings')
django.setup()

from django.template import Engine, TemplateSyntaxError

template_engine = Engine.get_default()

dirs_to_check = [
    BASE_DIR / 'templates',
    Path('c:/Users/DELL/Desktop/Python/github/PlaceSync/templates')
]

for TEMPLATES_DIR in dirs_to_check:
    if not TEMPLATES_DIR.exists():
        continue

    print("\n==========================================")
    print("Scanning templates directory:", TEMPLATES_DIR)
    print("==========================================")

    broken_files = []

    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html') or file.endswith('.txt'):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(TEMPLATES_DIR)
                
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check 1: Multiline broken {{ ... }} or {% ... %} tags
                multiline_var_matches = re.findall(r'\{\{\s*\n[^\}]*\}\}', content)
                multiline_tag_matches = re.findall(r'\{\%\s*\n[^\%]*\%\}', content)
                
                if multiline_var_matches or multiline_tag_matches:
                    print("[SPLIT TAG]", rel_path, "Found multiline var:", len(multiline_var_matches), "tag:", len(multiline_tag_matches))
                    broken_files.append((str(rel_path), full_path, "SPLIT_TAGS", multiline_var_matches + multiline_tag_matches))
                    
                # Check 2: Django Template Compilation
                try:
                    template_engine.from_string(content)
                except TemplateSyntaxError as e:
                    print("[SYNTAX ERROR]", rel_path, ":", e)
                    broken_files.append((str(rel_path), full_path, "SYNTAX_ERROR", str(e)))
                except Exception as e:
                    print("[ERROR]", rel_path, ":", e)
                    broken_files.append((str(rel_path), full_path, "OTHER_ERROR", str(e)))

    print("\n--- SUMMARY FOR", TEMPLATES_DIR.parent.name, "---")
    print("Total template files checked:", sum(1 for _ in TEMPLATES_DIR.rglob('*.html')) + sum(1 for _ in TEMPLATES_DIR.rglob('*.txt')))
    print("Broken files count:", len(broken_files))
    for file_info in broken_files:
        print(" -", file_info[0], "(", file_info[2], ")")
