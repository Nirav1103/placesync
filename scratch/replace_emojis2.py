import os

TEMPLATE_DIR = r"c:\Users\DELL\Desktop\Python\f_python\PlaceSync\templates\student_portal"

# Additional emoji replacements not caught in first pass
EMOJI_MAP_2 = {
    '🗺️': '<i class="fa-solid fa-map"></i>',
    '🗺': '<i class="fa-solid fa-map"></i>',
    '🐙': '<i class="fa-brands fa-github"></i>',
    '📺': '<i class="fa-solid fa-video"></i>',
    '💾': '<i class="fa-solid fa-floppy-disk"></i>',
    '🎨': '<i class="fa-solid fa-palette"></i>',
    '🍏': '<i class="fa-brands fa-apple"></i>',
    '📁': '<i class="fa-solid fa-folder"></i>',
    '💯': '<i class="fa-solid fa-hundred-points"></i>',
    '🕒': '<i class="fa-solid fa-clock"></i>',
    '✍️': '<i class="fa-solid fa-pen-nib"></i>',
    '✍': '<i class="fa-solid fa-pen-nib"></i>',
    '🛠️': '<i class="fa-solid fa-screwdriver-wrench"></i>',
    '🛠': '<i class="fa-solid fa-screwdriver-wrench"></i>',
    '🛑': '<i class="fa-solid fa-ban"></i>',
    '🧬': '<i class="fa-solid fa-dna"></i>',
    '👋': '',
    '🎒': '<i class="fa-solid fa-backpack"></i>',
    '🟢': '<i class="fa-solid fa-circle" style="color:#22c55e;font-size:0.5rem;"></i>',
    '☆': '<i class="fa-regular fa-star"></i>',
    '☰': '<i class="fa-solid fa-bars"></i>',
    '⚙': '<i class="fa-solid fa-gear"></i>',
    '🤓': '<i class="fa-solid fa-code"></i>',
    '👨‍🍳': '<i class="fa-solid fa-code"></i>',
    '👔': '<i class="fa-brands fa-linkedin"></i>',
    '🌍': '<i class="fa-solid fa-earth-americas"></i>',
    '🌅': '<i class="fa-solid fa-sun"></i>',
    '🏷️': '<i class="fa-solid fa-tag"></i>',
    '🏷': '<i class="fa-solid fa-tag"></i>',
    '📇': '<i class="fa-solid fa-address-card"></i>',
    '🔮': '<i class="fa-solid fa-chart-line"></i>',
    '👀': '<i class="fa-solid fa-eye"></i>',
}

files_changed = 0
for fname in os.listdir(TEMPLATE_DIR):
    if not fname.endswith('.html'):
        continue
    fpath = os.path.join(TEMPLATE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for emoji, icon_html in EMOJI_MAP_2.items():
        content = content.replace(emoji, icon_html)
    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        files_changed += 1
        print(f"  Updated: {fname}")

print(f"\nFiles changed: {files_changed}")
print("Done!")
