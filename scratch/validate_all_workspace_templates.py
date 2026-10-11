import os
import re

for root, dirs, files in os.walk('.'):
    # Skip standard system/venv directories
    if any(k in root.replace('\\', '/').split('/') for k in ['.git', '.gemini', 'venv', 'env', 'site-packages', '.idea', 'node_modules']):
        continue
        
    for filename in files:
        if filename.endswith('.html'):
            path = os.path.join(root, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Count tag occurrences
            div_open = len(re.findall(r'<div\b', content))
            div_close = len(re.findall(r'</div>', content))
            
            # Check Django block pairs
            if_open = len(re.findall(r'{%\s*if\b', content))
            if_close = len(re.findall(r'{%\s*endif\s*%}', content))
            
            for_open = len(re.findall(r'{%\s*for\b', content))
            for_close = len(re.findall(r'{%\s*endfor\s*%}', content))
            
            with_open = len(re.findall(r'{%\s*with\b', content))
            with_close = len(re.findall(r'{%\s*endwith\s*%}', content))
            
            block_open = len(re.findall(r'{%\s*block\b', content))
            block_close = len(re.findall(r'{%\s*endblock\s*%}', content))
            
            issues = []
            if div_open != div_close:
                issues.append(f"divs mismatch ({div_open} open vs {div_close} close)")
            if if_open != if_close:
                issues.append(f"ifs mismatch ({if_open} open vs {if_close} close)")
            if for_open != for_close:
                issues.append(f"fors mismatch ({for_open} open vs {for_close} close)")
            if with_open != with_close:
                issues.append(f"with mismatch ({with_open} open vs {with_close} close)")
            if block_open != block_close:
                issues.append(f"block mismatch ({block_open} open vs {block_close} close)")
                
            if issues:
                print(f"File: {path}")
                for issue in issues:
                    print(f"  [ERROR] {issue}")
