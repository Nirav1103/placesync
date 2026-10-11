import shutil
from pathlib import Path

src = Path('c:/Users/DELL/Desktop/Python/PlaceSync/static/css/style.css')
dst = Path('c:/Users/DELL/Desktop/Python/github/PlaceSync/static/css/style.css')

shutil.copy2(src, dst)
print("Successfully synced style.css from PlaceSync to github/PlaceSync!")
