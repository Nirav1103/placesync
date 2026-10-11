import shutil
from pathlib import Path

files = [
    'static/css/style.css',
    'templates/base.html',
    'templates/dashboard/index.html',
    'templates/students/student_list.html',
    'templates/companies/company_list.html',
    'templates/placements/drive_list.html',
]

src_root = Path('c:/Users/DELL/Desktop/Python/github/PlaceSync')
dst_root = Path('c:/Users/DELL/Desktop/Python/PlaceSync')

for rel_path in files:
    src = src_root / rel_path
    dst = dst_root / rel_path
    shutil.copy2(src, dst)
    print(f"Restored: {rel_path}")

print("Rollback complete across both directories!")
