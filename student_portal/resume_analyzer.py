import re
import json
from pypdf import PdfReader

# List of popular tech and soft skill keywords for ATS analysis
PLACEMENT_KEYWORDS = [
    # Programming / Core
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'swift', 'typescript', 'go', 'rust',
    # Frontend / Backend Frameworks
    'django', 'flask', 'fastapi', 'spring', 'react', 'angular', 'vue', 'nodejs', 'express', 'html', 'css', 'bootstrap',
    # Databases
    'sql', 'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'oracle',
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ci/cd', 'linux', 'devops',
    # Data & AI
    'machine learning', 'data science', 'ai', 'deep learning', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
    # Soft Skills & Methodologies
    'communication', 'leadership', 'teamwork', 'problem solving', 'agile', 'scrum', 'project management', 'sdlc',
]

SECTION_KEYWORDS = {
    'education': ['education', 'academic', 'qualification', 'studies', 'coursework', 'degree', 'schooling', 'college', 'university', 'btech', 'mtech', 'b.tech', 'm.tech', 'be', 'b.e', 'bsc', 'msc', 'diploma'],
    'projects': ['projects', 'project', 'key projects', 'academic projects', 'personal projects', 'major project', 'minor project', 'mini project'],
    'skills': ['skills', 'technical skills', 'key skills', 'technologies', 'expertise', 'tools', 'languages', 'core competencies'],
    'certificates': ['certifications', 'certification', 'certificates', 'courses', 'licenses', 'credentials'],
    'experience': ['experience', 'professional experience', 'work experience', 'employment history', 'job history', 'internship', 'intern', 'training', 'professional background'],
}

def extract_pdf_text(file_path_or_file):
    """
    Extracts text page-by-page from a PDF file using pypdf.
    """
    text = ""
    try:
        reader = PdfReader(file_path_or_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def analyze_resume_text(text):
    """
    Analyzes raw resume text and computes:
    - ATS Score
    - Completion Score
    - Formatting Score
    - Extracted Sections Found
    - Match/Missing Keywords
    - Suggestions
    """
    if not text or not text.strip():
        return {
            'ats_score': 30,
            'completion_score': 10,
            'formatting_score': 30,
            'projects_found': [],
            'education_found': [],
            'skills_found': [],
            'certificates_found': [],
            'experience_found': [],
            'missing_keywords': ['Python', 'SQL', 'Git', 'HTML', 'CSS', 'React', 'Agile', 'Docker'],
            'suggestions': ["No readable text found. Please upload a digital PDF resume (scanned PDF image resumes cannot be read)."]
        }

    # Normalize text for searches
    lower_text = text.lower()

    # 1. Check for Sections using header match
    sections_found = {}
    section_positions = []

    for section_name, keywords in SECTION_KEYWORDS.items():
        found = False
        first_pos = -1
        for kw in keywords:
            # Match section keywords as whole lines or at line starts
            # E.g. "EDUCATION" or "PROJECTS"
            pattern = r'\b' + re.escape(kw) + r'\b'
            match = re.search(pattern, lower_text)
            if match:
                found = True
                first_pos = match.start()
                break
        sections_found[section_name] = found
        if found:
            section_positions.append((first_pos, section_name))

    # Sort positions to extract text between sections
    section_positions.sort()
    extracted_sections_data = {
        'projects': [],
        'education': [],
        'skills': [],
        'certificates': [],
        'experience': [],
    }

    for i in range(len(section_positions)):
        pos, sec_name = section_positions[i]
        next_pos = len(lower_text)
        if i + 1 < len(section_positions):
            next_pos = section_positions[i+1][0]
        
        # Grab segment text
        segment = text[pos:next_pos].strip()
        lines = [line.strip() for line in segment.split('\n')[1:] if line.strip()] # Skip header line
        # Store first few bullet items or details
        extracted_sections_data[sec_name] = lines[:5] # Max 5 details

    # 2. Contact Details Check
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', lower_text)
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', lower_text)
    linkedin_match = "linkedin.com" in lower_text
    github_match = "github.com" in lower_text

    # 3. Match Placement Keywords
    matched_kws = []
    missing_kws = []
    for kw in PLACEMENT_KEYWORDS:
        if kw in lower_text:
            matched_kws.append(kw.title())
        else:
            missing_kws.append(kw.title())

    # Limit lists
    skills_found_list = matched_kws[:12]
    missing_kws_list = missing_kws[:8]

    # 4. Compute Scores
    # A. Completion Score (out of 100)
    # 20 pts for each main section found: education, experience, projects, skills = 80 pts
    # 10 pts for certificates section = 90 pts
    # 10 pts for contact details (4 for email, 3 for phone, 3 for LinkedIn/GitHub)
    comp_score = 0
    if sections_found.get('education'): comp_score += 20
    if sections_found.get('experience'): comp_score += 20
    if sections_found.get('projects'): comp_score += 20
    if sections_found.get('skills'): comp_score += 20
    if sections_found.get('certificates'): comp_score += 10
    
    if email_match: comp_score += 4
    if phone_match: comp_score += 3
    if linkedin_match or github_match: comp_score += 3

    # B. Formatting Score (out of 100)
    # Word count: 300 to 900 is ideal (40 pts), 150-299 or 900-1500 (20 pts), else (5 pts)
    words = text.split()
    word_count = len(words)
    format_score = 0
    if 300 <= word_count <= 900:
        format_score += 40
    elif 150 <= word_count < 300 or 900 < word_count <= 1500:
        format_score += 20
    else:
        format_score += 5

    # Bullet points / list items check: count lines starting with bullet characters or hyphens
    bullet_count = sum(1 for line in text.split('\n') if line.strip().startswith(('•', '-', '*', 'o', '▪')) or (line.strip() and line.strip()[0].isdigit() and '.' in line.strip()[:3]))
    if bullet_count >= 8:
        format_score += 30
    elif 3 <= bullet_count < 8:
        format_score += 15
    else:
        format_score += 5

    # Contact section presentation: 30 points
    contact_points = 0
    if email_match: contact_points += 10
    if phone_match: contact_points += 10
    if linkedin_match or github_match: contact_points += 10
    format_score += contact_points

    # C. ATS Score (out of 100)
    # Weighted average: 40% Completion, 30% Formatting, 30% Keywords matching density
    keyword_score = min(len(matched_kws) * 10, 100) # 10 matched keywords = 100%
    ats_score = int((comp_score * 0.40) + (format_score * 0.30) + (keyword_score * 0.30))
    ats_score = min(max(ats_score, 30), 99) # limit to max 99 for realism unless perfect

    # 5. Generate Suggestions
    suggestions = []
    if not sections_found.get('projects'):
        suggestions.append("Add a detailed 'Projects' section describing 2-3 academic or personal projects and technologies used.")
    if not sections_found.get('experience'):
        suggestions.append("Add a 'Work Experience' or 'Internships' section. Detail your roles, responsibilities, and achievements using action verbs.")
    if not sections_found.get('certificates'):
        suggestions.append("Add a 'Certifications' section to display courses completed outside your college curriculum.")
    if not sections_found.get('skills'):
        suggestions.append("List technical skills in a separate section, grouped by category (e.g., Languages, Frameworks, Databases, Tools).")
    
    if word_count < 300:
        suggestions.append("The resume is too short (under 300 words). Expand details of your projects, skills, and coursework.")
    elif word_count > 900:
        suggestions.append("The resume is quite long (over 900 words). Try to condense it to a single page for clarity and quick scanning.")
    
    if bullet_count < 5:
        suggestions.append("Format project details and experience responsibilities as bullet points (•) rather than block paragraphs. It improves readability significantly.")
    
    if not email_match or not phone_match:
        suggestions.append("Ensure your contact phone number and professional email address are clearly visible at the top of the page.")
    if not linkedin_match:
        suggestions.append("Create and add your LinkedIn profile link to your header to allow recruiters to review your online presence.")
    if not github_match and sections_found.get('skills'):
        suggestions.append("Add a GitHub profile link to showcase your coding history and repository projects.")

    if len(matched_kws) < 5:
        suggestions.append("Incorporate more relevant technical keywords matched to placement descriptions (e.g. Database names, Git, specific frameworks).")

    if not suggestions:
        suggestions.append("Your resume meets all general ATS layout standards. Continue to update keywords tailored to specific job roles.")

    return {
        'ats_score': ats_score,
        'completion_score': comp_score,
        'formatting_score': format_score,
        'projects_found': extracted_sections_data['projects'],
        'education_found': extracted_sections_data['education'],
        'skills_found': skills_found_list,
        'certificates_found': extracted_sections_data['certificates'],
        'experience_found': extracted_sections_data['experience'],
        'missing_keywords': missing_kws_list,
        'suggestions': suggestions[:5], # top 5 suggestions
    }
