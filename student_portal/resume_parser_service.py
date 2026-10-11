import re
import json
import datetime
from django.utils import timezone
from django.db.models import Q

from students.models import Student, StudentResume, StudentSkill, Project, Certificate
from .resume_analyzer import extract_pdf_text

# ═════════════════════════════════════════════════════════════════════════════
# Categorization Dictionaries for AI Skill Extraction
# ═════════════════════════════════════════════════════════════════════════════

PROGRAMMING_LANGUAGES = [
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'php', 'ruby',
    'swift', 'kotlin', 'go', 'golang', 'rust', 'r', 'matlab', 'scala', 'dart', 'perl',
    'assembly', 'bash', 'powershell', 'sql', 'html', 'css'
]

FRAMEWORKS_AND_DATABASES = {
    'frameworks': [
        'django', 'flask', 'fastapi', 'react', 'reactjs', 'angular', 'vue', 'vuejs',
        'next.js', 'nextjs', 'node.js', 'nodejs', 'express', 'spring', 'spring boot', 'laravel',
        'bootstrap', 'tailwind', 'jquery', 'pandas', 'numpy', 'scikit-learn', 'tensorflow',
        'keras', 'pytorch', 'opencv', 'dotnet', '.net'
    ],
    'databases': [
        'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'mongo', 'redis',
        'oracle', 'dynamodb', 'cassandra', 'firebase', 'elasticsearch', 'mariadb'
    ]
}

TOOLS_AND_CLOUD = [
    'git', 'github', 'gitlab', 'docker', 'kubernetes', 'aws', 'azure', 'gcp',
    'google cloud', 'jenkins', 'linux', 'ubuntu', 'postman', 'jira', 'figma', 'tableau',
    'power bi', 'powerbi', 'vscode', 'intellij', 'pycharm', 'webpack', 'nginx'
]

SOFT_SKILLS = [
    'communication', 'leadership', 'teamwork', 'collaboration', 'problem solving',
    'critical thinking', 'time management', 'adaptability', 'analytical', 'project management',
    'agile', 'scrum', 'creativity', 'decision making'
]


def parse_resume_file(resume_instance):
    """
    Analyzes an uploaded StudentResume instance and extracts:
    - Programming Languages
    - Frameworks & Databases
    - Tools & Cloud Platforms
    - Soft Skills
    - Education details
    - Experience details
    - Projects
    - Certifications
    - Parser Confidence Score (0-100%)
    Updates and saves the StudentResume model instance.
    """
    if not resume_instance or not resume_instance.file:
        resume_instance.parser_status = 'FAILED'
        resume_instance.save()
        return None

    # Extract raw text from PDF
    try:
        file_path = resume_instance.file.path
        raw_text = extract_pdf_text(file_path)
    except Exception as e:
        print(f"Resume text extraction error: {e}")
        raw_text = ""

    if not raw_text or not raw_text.strip():
        resume_instance.parser_status = 'FAILED'
        resume_instance.parser_confidence = 10
        resume_instance.extracted_text = ""
        resume_instance.save()
        return resume_instance

    resume_instance.extracted_text = raw_text
    lower_text = raw_text.lower()

    # 1. Skill Categorization Extraction
    found_langs = []
    found_frameworks = []
    found_databases = []
    found_tools = []
    found_soft = []

    # Programming Languages
    for lang in PROGRAMMING_LANGUAGES:
        pattern = r'\b' + re.escape(lang) + r'\b'
        if re.search(pattern, lower_text):
            title_name = 'C++' if lang == 'c++' else 'C#' if lang == 'c#' else 'JavaScript' if lang == 'javascript' else 'TypeScript' if lang == 'typescript' else lang.title()
            if title_name not in found_langs:
                found_langs.append(title_name)

    # Frameworks
    for fw in FRAMEWORKS_AND_DATABASES['frameworks']:
        pattern = r'\b' + re.escape(fw) + r'\b'
        if re.search(pattern, lower_text):
            title_name = 'React' if 'react' in fw else 'Vue.js' if 'vue' in fw else 'Node.js' if 'node' in fw else 'Django' if fw == 'django' else fw.title()
            if title_name not in found_frameworks:
                found_frameworks.append(title_name)

    # Databases
    for db in FRAMEWORKS_AND_DATABASES['databases']:
        pattern = r'\b' + re.escape(db) + r'\b'
        if re.search(pattern, lower_text):
            title_name = 'MySQL' if db == 'mysql' else 'PostgreSQL' if 'postgres' in db else 'MongoDB' if 'mongo' in db else db.title()
            if title_name not in found_databases:
                found_databases.append(title_name)

    # Tools & Cloud
    for tool in TOOLS_AND_CLOUD:
        pattern = r'\b' + re.escape(tool) + r'\b'
        if re.search(pattern, lower_text):
            title_name = 'GitHub' if tool == 'github' else 'GitLab' if tool == 'gitlab' else 'Docker' if tool == 'docker' else 'AWS' if tool == 'aws' else tool.title()
            if title_name not in found_tools:
                found_tools.append(title_name)

    # Soft Skills
    for soft in SOFT_SKILLS:
        pattern = r'\b' + re.escape(soft) + r'\b'
        if re.search(pattern, lower_text):
            if soft.title() not in found_soft:
                found_soft.append(soft.title())

    # Combined master skills list
    all_skills_found = list(dict.fromkeys(found_langs + found_frameworks + found_databases + found_tools + found_soft))

    # 2. Section Parsing (Education, Experience, Projects, Certifications)
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    extracted_education = []
    extracted_experience = []
    extracted_projects = []
    extracted_certs = []

    current_section = None
    section_buffer = []

    section_headers = {
        'education': ['education', 'academic qualification', 'academic background', 'studies'],
        'experience': ['experience', 'work experience', 'employment history', 'internships', 'professional background'],
        'projects': ['projects', 'key projects', 'academic projects', 'personal projects'],
        'certificates': ['certifications', 'certificates', 'courses & certifications', 'licenses']
    }

    for line in lines:
        line_lower = line.lower()
        matched_sec = None
        for sec_key, headers in section_headers.items():
            if any(h in line_lower and len(line_lower) < 40 for h in headers):
                matched_sec = sec_key
                break

        if matched_sec:
            if current_section and section_buffer:
                _process_section_buffer(current_section, section_buffer, extracted_education, extracted_experience, extracted_projects, extracted_certs)
            current_section = matched_sec
            section_buffer = []
        elif current_section:
            section_buffer.append(line)

    if current_section and section_buffer:
        _process_section_buffer(current_section, section_buffer, extracted_education, extracted_experience, extracted_projects, extracted_certs)

    # Fallback checks if sections empty
    if not extracted_education:
        for line in lines:
            if any(deg in line.lower() for deg in ['b.tech', 'btech', 'b.e', 'm.tech', 'mtech', 'b.sc', 'm.sc', 'diploma', 'degree', 'university', 'college']):
                extracted_education.append(line)
                if len(extracted_education) >= 3:
                    break

    if not extracted_certs:
        for line in lines:
            if any(cert_kw in line.lower() for cert_kw in ['certified', 'certification', 'certificate', 'aws', 'nptel', 'coursera', 'udemy']):
                extracted_certs.append(line)
                if len(extracted_certs) >= 3:
                    break

    # 3. Confidence Score Calculation
    confidence = 35 # Base for text extraction
    if len(all_skills_found) >= 5: confidence += 20
    elif len(all_skills_found) >= 2: confidence += 10

    if extracted_education: confidence += 15
    if extracted_projects: confidence += 15
    if extracted_experience: confidence += 10
    if extracted_certs: confidence += 5
    
    confidence = min(max(confidence, 30), 98)

    # 4. Save to model fields
    resume_instance.parser_status = 'COMPLETED'
    resume_instance.parsed_at = timezone.now()
    resume_instance.parser_confidence = confidence
    
    resume_instance.skills_found = json.dumps(all_skills_found)
    resume_instance.programming_languages_found = json.dumps(found_langs)
    resume_instance.tools_found = json.dumps(found_tools)
    resume_instance.soft_skills_found = json.dumps(found_soft)

    resume_instance.education_found = json.dumps(extracted_education[:5])
    resume_instance.experience_found = json.dumps(extracted_experience[:5])
    resume_instance.projects_found = json.dumps(extracted_projects[:5])
    resume_instance.certificates_found = json.dumps(extracted_certs[:5])

    resume_instance.save()
    return resume_instance


def _process_section_buffer(sec_key, buffer, edu, exp, proj, cert):
    """Processes section text buffer into concise line items."""
    text_lines = [b for b in buffer if len(b) > 3][:6]
    if sec_key == 'education':
        edu.extend(text_lines)
    elif sec_key == 'experience':
        exp.extend(text_lines)
    elif sec_key == 'projects':
        proj.extend(text_lines)
    elif sec_key == 'certificates':
        cert.extend(text_lines)


def sync_extracted_data_to_profile(student, resume_instance):
    """
    Synchronizes parsed resume information cleanly into:
    1. Student Profile & Skills Inventory (StudentSkill records)
    2. Projects table (Project records)
    3. Certificates table (Certificate records)
    4. Career Profile fields

    Avoids duplicate entries by intelligently checking for existing records.
    Returns a summary dict of records created/updated.
    """
    if not student or not resume_instance:
        return {'skills_added': 0, 'projects_synced': 0, 'certificates_synced': 0}

    skills_added = 0
    projects_synced = 0
    certificates_synced = 0

    # ── 1. SKILLS SYNCHRONIZATION ───────────────────────────────────────────
    all_parsed_skills = json.loads(resume_instance.skills_found or '[]')
    prog_langs = json.loads(resume_instance.programming_languages_found or '[]')
    tools_parsed = json.loads(resume_instance.tools_found or '[]')
    soft_parsed = json.loads(resume_instance.soft_skills_found or '[]')

    # Update Student.skills string field
    existing_skills_str = student.skills or ""
    existing_skills_set = set(s.strip().lower() for s in existing_skills_str.split(',') if s.strip())

    new_skills_list = [s.strip() for s in existing_skills_str.split(',') if s.strip()]

    for skill in all_parsed_skills:
        s_clean = skill.strip()
        if s_clean.lower() not in existing_skills_set:
            new_skills_list.append(s_clean)
            existing_skills_set.add(s_clean.lower())

    student.skills = ", ".join(new_skills_list)
    
    # Sync StudentSkill structured entries
    for skill_name in all_parsed_skills:
        s_clean = skill_name.strip()
        if not s_clean:
            continue
        
        # Categorize
        if s_clean in prog_langs:
            cat = StudentSkill.Category.PROGRAMMING
        elif s_clean in tools_parsed:
            cat = StudentSkill.Category.TOOLS
        elif s_clean in soft_parsed:
            cat = StudentSkill.Category.SOFT_SKILLS
        elif any(db_kw in s_clean.lower() for db_kw in ['sql', 'mongo', 'redis', 'postgres', 'db']):
            cat = StudentSkill.Category.DATABASE
        else:
            cat = StudentSkill.Category.FRAMEWORK

        # Check existing StudentSkill record (case-insensitive)
        existing_skill = StudentSkill.objects.filter(student=student, name__iexact=s_clean).first()
        if not existing_skill:
            StudentSkill.objects.create(
                student=student,
                name=s_clean,
                category=cat,
                proficiency=StudentSkill.Proficiency.INTERMEDIATE,
                description="Extracted via AI Resume Parser"
            )
            skills_added += 1

    # ── 2. PROJECTS SYNCHRONIZATION ─────────────────────────────────────────
    parsed_projects = json.loads(resume_instance.projects_found or '[]')
    for proj_line in parsed_projects:
        proj_title = proj_line.split('-')[0].split(':')[0].strip()
        if len(proj_title) < 4:
            continue

        # Check if project already exists for this student
        existing_proj = Project.objects.filter(student=student, title__icontains=proj_title[:20]).first()
        if not existing_proj:
            Project.objects.create(
                student=student,
                title=proj_title[:100],
                short_description=proj_line[:250],
                detailed_description=f"Project extracted from uploaded resume: {proj_line}",
                technologies=", ".join([s for s in all_parsed_skills[:5]]),
                status=Project.Status.COMPLETED,
                project_type=Project.ProjectType.PERSONAL,
                team_type='INDIVIDUAL'
            )
            projects_synced += 1
        else:
            # Update existing project if missing technologies
            if not existing_proj.technologies:
                existing_proj.technologies = ", ".join([s for s in all_parsed_skills[:5]])
                existing_proj.save()

    # ── 3. CERTIFICATES SYNCHRONIZATION ─────────────────────────────────────
    parsed_certs = json.loads(resume_instance.certificates_found or '[]')
    for cert_line in parsed_certs:
        cert_title = cert_line.split('-')[0].split(':')[0].strip()
        if len(cert_title) < 4:
            continue

        # Check if certificate already exists
        existing_cert = Certificate.objects.filter(student=student, title__icontains=cert_title[:20]).first()
        if not existing_cert:
            org = "Coursera / NPTEL / Online Provider"
            if "aws" in cert_line.lower(): org = "Amazon Web Services (AWS)"
            elif "google" in cert_line.lower(): org = "Google Cloud"
            elif "cisco" in cert_line.lower(): org = "Cisco"

            Certificate.objects.create(
                student=student,
                title=cert_title[:100],
                issuing_organization=org,
                purpose=Certificate.Purpose.COURSE_COMPLETION,
                category="Extracted Credential",
                issue_date=datetime.date.today()
            )
            certificates_synced += 1

    # ── 4. CAREER PROFILE & BIO SYNCHRONIZATION ─────────────────────────────
    if not student.bio:
        student.bio = f"Computer Science Student passionate about {', '.join(all_parsed_skills[:4])} development. Experienced in building technical projects and software solutions."
    
    if not student.preferred_job_role:
        if 'python' in [s.lower() for s in all_parsed_skills] or 'django' in [s.lower() for s in all_parsed_skills]:
            student.preferred_job_role = 'Backend Developer'
        elif 'react' in [s.lower() for s in all_parsed_skills] or 'javascript' in [s.lower() for s in all_parsed_skills]:
            student.preferred_job_role = 'Full Stack Developer'
        else:
            student.preferred_job_role = 'Software Engineer'

    student.save()

    return {
        'skills_added': skills_added,
        'projects_synced': projects_synced,
        'certificates_synced': certificates_synced,
    }
