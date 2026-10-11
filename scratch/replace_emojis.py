import os, re

TEMPLATE_DIR = r"c:\Users\DELL\Desktop\Python\f_python\PlaceSync\templates\student_portal"

# Map emoji to FontAwesome HTML replacement
EMOJI_MAP = {
    '✏️': '<i class="fa-solid fa-pen-to-square"></i>',
    '🗑️': '<i class="fa-solid fa-trash"></i>',
    '🗑': '<i class="fa-solid fa-trash"></i>',
    '💡': '<i class="fa-solid fa-lightbulb"></i>',
    '🎯': '<i class="fa-solid fa-bullseye"></i>',
    '📈': '<i class="fa-solid fa-chart-line"></i>',
    '🌱': '<i class="fa-solid fa-seedling"></i>',
    '➕': '<i class="fa-solid fa-plus"></i>',
    '📖': '<i class="fa-solid fa-book-open"></i>',
    '🔒': '<i class="fa-solid fa-lock"></i>',
    '👤': '<i class="fa-solid fa-user"></i>',
    '📧': '<i class="fa-solid fa-envelope"></i>',
    '⚡': '<i class="fa-solid fa-bolt"></i>',
    '📄': '<i class="fa-solid fa-file-lines"></i>',
    '🤖': '<i class="fa-solid fa-robot"></i>',
    '📤': '<i class="fa-solid fa-upload"></i>',
    '📅': '<i class="fa-solid fa-calendar-days"></i>',
    '⏳': '<i class="fa-solid fa-hourglass-half"></i>',
    '❌': '<i class="fa-solid fa-xmark"></i>',
    '💻': '<i class="fa-solid fa-laptop-code"></i>',
    '⚙️': '<i class="fa-solid fa-gears"></i>',
    '🔧': '<i class="fa-solid fa-wrench"></i>',
    '🤝': '<i class="fa-solid fa-handshake"></i>',
    '🎓': '<i class="fa-solid fa-graduation-cap"></i>',
    '💼': '<i class="fa-solid fa-briefcase"></i>',
    '🔨': '<i class="fa-solid fa-hammer"></i>',
    '🏆': '<i class="fa-solid fa-trophy"></i>',
    '📚': '<i class="fa-solid fa-book"></i>',
    '📑': '<i class="fa-solid fa-file-alt"></i>',
    '📥': '<i class="fa-solid fa-download"></i>',
    '🔍': '<i class="fa-solid fa-magnifying-glass"></i>',
    '📦': '<i class="fa-solid fa-box"></i>',
    '👁️': '<i class="fa-solid fa-eye"></i>',
    '👁': '<i class="fa-solid fa-eye"></i>',
    '⚖️': '<i class="fa-solid fa-scale-balanced"></i>',
    '✓': '<i class="fa-solid fa-check"></i>',
    '✔️': '<i class="fa-solid fa-circle-check"></i>',
    '⚠️': '<i class="fa-solid fa-triangle-exclamation"></i>',
    '🔗': '<i class="fa-solid fa-link"></i>',
    '🏢': '<i class="fa-solid fa-building"></i>',
    '📊': '<i class="fa-solid fa-chart-bar"></i>',
    '🚀': '<i class="fa-solid fa-rocket"></i>',
    '⭐': '<i class="fa-solid fa-star"></i>',
    '📝': '<i class="fa-solid fa-pen"></i>',
    '🔔': '<i class="fa-solid fa-bell"></i>',
    '📋': '<i class="fa-solid fa-clipboard"></i>',
    '🛡️': '<i class="fa-solid fa-shield-halved"></i>',
    '🛡': '<i class="fa-solid fa-shield-halved"></i>',
    '🌐': '<i class="fa-solid fa-globe"></i>',
    '💰': '<i class="fa-solid fa-coins"></i>',
    '📌': '<i class="fa-solid fa-thumbtack"></i>',
    '🔥': '<i class="fa-solid fa-fire"></i>',
    '✅': '<i class="fa-solid fa-circle-check"></i>',
    '⬇️': '<i class="fa-solid fa-arrow-down"></i>',
    '⬆️': '<i class="fa-solid fa-arrow-up"></i>',
    '🖊️': '<i class="fa-solid fa-pen"></i>',
    '🖊': '<i class="fa-solid fa-pen"></i>',
    '📜': '<i class="fa-solid fa-scroll"></i>',
    '🎖️': '<i class="fa-solid fa-medal"></i>',
    '🎖': '<i class="fa-solid fa-medal"></i>',
    '🧠': '<i class="fa-solid fa-brain"></i>',
    '💬': '<i class="fa-solid fa-comment"></i>',
    '📞': '<i class="fa-solid fa-phone"></i>',
    '🔐': '<i class="fa-solid fa-lock"></i>',
    '🎮': '<i class="fa-solid fa-gamepad"></i>',
    '🌟': '<i class="fa-solid fa-star"></i>',
    '📂': '<i class="fa-solid fa-folder-open"></i>',
    '🗂️': '<i class="fa-solid fa-folder-open"></i>',
    '🗂': '<i class="fa-solid fa-folder-open"></i>',
    '✨': '<i class="fa-solid fa-sparkles"></i>',
    '🔎': '<i class="fa-solid fa-magnifying-glass"></i>',
    '⏰': '<i class="fa-solid fa-clock"></i>',
    '🕐': '<i class="fa-solid fa-clock"></i>',
    '📮': '<i class="fa-solid fa-inbox"></i>',
    '🏅': '<i class="fa-solid fa-medal"></i>',
    '💎': '<i class="fa-solid fa-gem"></i>',
    '🔄': '<i class="fa-solid fa-arrows-rotate"></i>',
    '➡️': '<i class="fa-solid fa-arrow-right"></i>',
    '⬅️': '<i class="fa-solid fa-arrow-left"></i>',
    '🔀': '<i class="fa-solid fa-shuffle"></i>',
    '📱': '<i class="fa-solid fa-mobile-screen"></i>',
    '🖥️': '<i class="fa-solid fa-desktop"></i>',
    '🖥': '<i class="fa-solid fa-desktop"></i>',
    '💪': '<i class="fa-solid fa-dumbbell"></i>',
    '🎉': '<i class="fa-solid fa-party-horn"></i>',
    '👀': '<i class="fa-solid fa-eye"></i>',
    '📎': '<i class="fa-solid fa-paperclip"></i>',
    '🔑': '<i class="fa-solid fa-key"></i>',
    '⚠': '<i class="fa-solid fa-triangle-exclamation"></i>',
    '🏫': '<i class="fa-solid fa-school"></i>',
    '🗓️': '<i class="fa-solid fa-calendar"></i>',
    '🗓': '<i class="fa-solid fa-calendar"></i>',
    '📆': '<i class="fa-solid fa-calendar-check"></i>',
    '🪪': '<i class="fa-solid fa-id-card"></i>',
    '🆔': '<i class="fa-solid fa-id-badge"></i>',
}

total_replacements = 0
files_changed = 0

for fname in os.listdir(TEMPLATE_DIR):
    if not fname.endswith('.html'):
        continue
    fpath = os.path.join(TEMPLATE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for emoji, icon_html in EMOJI_MAP.items():
        content = content.replace(emoji, icon_html)

    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        count = sum(1 for a, b in zip(original, content) if a != b)
        files_changed += 1
        print(f"  Updated: {fname}")

# Also check base.html
base_path = os.path.join(TEMPLATE_DIR, 'base.html')
if os.path.exists(base_path):
    with open(base_path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for emoji, icon_html in EMOJI_MAP.items():
        content = content.replace(emoji, icon_html)
    if content != original:
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(content)

# Now verify no emojis remain
emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF\U0000FE00-\U0000FE0F\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]')
remaining = 0
for fname in os.listdir(TEMPLATE_DIR):
    if not fname.endswith('.html'):
        continue
    fpath = os.path.join(TEMPLATE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            matches = emoji_pattern.findall(line)
            if matches:
                remaining += len(matches)
                print(f"  REMAINING: {fname}:{i} -> {''.join(matches)}")

print(f"\nFiles changed: {files_changed}")
print(f"Remaining emojis: {remaining}")
