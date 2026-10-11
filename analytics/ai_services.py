import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from django.conf import settings

warnings.filterwarnings('ignore')

from students.models import Student, StudentSkill, Project, Certificate

BASE_DIR = settings.BASE_DIR
MODEL_DIR = os.path.join(BASE_DIR, 'dataset', 'trained_models')

# Global cache for loaded model objects
_MODEL_CACHE = {}


def _get_model_artifact(name, loader_func):
    if name not in _MODEL_CACHE:
        try:
            _MODEL_CACHE[name] = loader_func()
        except Exception as e:
            print(f"Error loading AI artifact '{name}': {e}")
            _MODEL_CACHE[name] = None
    return _MODEL_CACHE[name]


def get_placement_pipeline():
    def load():
        m_path = os.path.join(MODEL_DIR, 'placement_model.pkl')
        s_path = os.path.join(MODEL_DIR, 'placement_scaler.pkl')
        if os.path.exists(m_path) and os.path.exists(s_path):
            return joblib.load(m_path), joblib.load(s_path)
        return None, None
    return _get_model_artifact('placement', load)


def get_salary_pipeline():
    def load():
        m_path = os.path.join(MODEL_DIR, 'salary_model.pkl')
        s_path = os.path.join(MODEL_DIR, 'salary_scaler.pkl')
        if os.path.exists(m_path) and os.path.exists(s_path):
            return joblib.load(m_path), joblib.load(s_path)
        return None, None
    return _get_model_artifact('salary', load)


def get_career_recommender():
    def load():
        m_path = os.path.join(MODEL_DIR, 'career_recommendation_model.pkl')
        v_path = os.path.join(MODEL_DIR, 'skill_vectorizer.pkl')
        r_path = os.path.join(MODEL_DIR, 'career_roles.json')
        if os.path.exists(m_path) and os.path.exists(v_path) and os.path.exists(r_path):
            model = joblib.load(m_path)
            vectorizer = joblib.load(v_path)
            with open(r_path, 'r') as f:
                roles = json.load(f)
            return model, vectorizer, roles
        return None, None, []
    return _get_model_artifact('career', load)


def get_skill_matrix():
    def load():
        m_path = os.path.join(MODEL_DIR, 'role_skill_matrix.json')
        if os.path.exists(m_path):
            with open(m_path, 'r') as f:
                return json.load(f)
        return {}
    return _get_model_artifact('matrix', load)


# ═════════════════════════════════════════════════════════════════════════════
# SERVICE 1: PLACEMENT PREDICTION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

def predict_placement_readiness(student):
    """
    Computes Placement Probability (0-100%) and Placement Readiness Status
    using the trained Extra Trees Classifier model.
    """
    if not student:
        return {'probability': 50, 'status': 'Average', 'readiness_score': 50}

    cgpa = float(student.cgpa or 6.5)
    backlogs = int(student.backlogs or 0)
    internships_count = student.applications.filter(status__in=['SHORTLISTED', 'SELECTED']).count()
    projects_count = student.projects.count()
    certs_count = student.certificates.count()

    active_resume = student.resume_versions.filter(is_active=True).first()
    ats_score = active_resume.ats_score if active_resume else (55 if student.resume else 30)

    # Estimate scores based on student profile data
    skills_count = len([s for s in (student.skills or "").split(',') if s.strip()])
    coding_score = min(95, 45 + skills_count * 6 + projects_count * 5)
    aptitude_score = min(95, int(cgpa * 9.5))
    comm_score = 80 if student.linkedin_url else 65
    reasoning_score = min(95, 50 + skills_count * 5)
    mock_interview_score = min(95, 55 + certs_count * 8 + internships_count * 10)
    attendance_pct = 90.0

    acad_comp = (cgpa / 10.0) * 50.0 + max(0, (100.0 - backlogs * 15.0)) * 0.5
    pract_comp = internships_count * 20.0 + projects_count * 12.0 + certs_count * 10.0
    skill_comp = (coding_score + aptitude_score + comm_score + reasoning_score) / 4.0

    features = [
        cgpa, backlogs, internships_count, projects_count, certs_count,
        coding_score, aptitude_score, comm_score, reasoning_score,
        mock_interview_score, attendance_pct, acad_comp, pract_comp, skill_comp
    ]

    model, scaler = get_placement_pipeline()
    if model and scaler:
        try:
            X_df = pd.DataFrame([features], columns=[
                'cgpa', 'backlogs', 'internships_count', 'projects_count', 'certifications_count',
                'coding_skill_score', 'aptitude_score', 'communication_skill_score', 'logical_reasoning_score',
                'mock_interview_score', 'attendance_percentage', 'academic_composite', 'practical_composite', 'skill_composite'
            ])
            X_scaled = pd.DataFrame(scaler.transform(X_df), columns=X_df.columns)
            prob = float(model.predict_proba(X_scaled)[0][1]) * 100.0
        except Exception as e:
            print(f"Prediction model evaluation error: {e}")
            prob = min(98.0, max(20.0, (cgpa * 7.0) + (projects_count * 5.0) + (skills_count * 3.0) - (backlogs * 10.0)))
    else:
        prob = min(98.0, max(20.0, (cgpa * 7.0) + (projects_count * 5.0) + (skills_count * 3.0) - (backlogs * 10.0)))

    prob_int = round(prob)
    if prob_int >= 80:
        status = 'Excellent'
        badge_cls = 'sp-badge-green'
    elif prob_int >= 65:
        status = 'Good'
        badge_cls = 'sp-badge-sky'
    elif prob_int >= 50:
        status = 'Average'
        badge_cls = 'sp-badge-amber'
    else:
        status = 'Needs Improvement'
        badge_cls = 'sp-badge-rose'

    return {
        'probability': prob_int,
        'status': status,
        'badge_class': badge_cls,
        'readiness_score': prob_int,
    }


# ═════════════════════════════════════════════════════════════════════════════
# SERVICE 2: FRESHER SALARY PREDICTION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

def predict_fresher_salary(student):
    """
    Predicts expected fresher salary CTC package in LPA using the Random Forest Regressor model.
    """
    if not student:
        return 6.0

    cgpa = float(student.cgpa or 6.5)
    backlogs = int(student.backlogs or 0)
    internships_count = student.applications.filter(status__in=['SHORTLISTED', 'SELECTED']).count()
    projects_count = student.projects.count()
    certs_count = student.certificates.count()

    skills_count = len([s for s in (student.skills or "").split(',') if s.strip()])
    coding_score = min(95, 45 + skills_count * 6 + projects_count * 5)
    aptitude_score = min(95, int(cgpa * 9.5))
    comm_score = 80 if student.linkedin_url else 65
    reasoning_score = min(95, 50 + skills_count * 5)

    acad_comp = (cgpa / 10.0) * 50.0 + max(0, (100.0 - backlogs * 15.0)) * 0.5
    pract_comp = internships_count * 20.0 + projects_count * 12.0 + certs_count * 10.0
    skill_comp = (coding_score + aptitude_score + comm_score + reasoning_score) / 4.0

    features = [
        cgpa, backlogs, internships_count, projects_count, certs_count,
        coding_score, aptitude_score, comm_score, reasoning_score,
        acad_comp, pract_comp, skill_comp
    ]

    model, scaler = get_salary_pipeline()
    if model and scaler:
        try:
            X_df = pd.DataFrame([features], columns=[
                'cgpa', 'backlogs', 'internships_count', 'projects_count', 'certifications_count',
                'coding_skill_score', 'aptitude_score', 'communication_skill_score', 'logical_reasoning_score',
                'academic_composite', 'practical_composite', 'skill_composite'
            ])
            X_scaled = pd.DataFrame(scaler.transform(X_df), columns=X_df.columns)
            salary_lpa = float(model.predict(X_scaled)[0])
        except Exception as e:
            print(f"Salary regression error: {e}")
            salary_lpa = 4.5 + (cgpa - 5.0) * 0.8 + (projects_count * 0.5)
    else:
        salary_lpa = 4.5 + (cgpa - 5.0) * 0.8 + (projects_count * 0.5)

    # Respect student explicit expected salary if higher
    if student.expected_salary and float(student.expected_salary) > 0:
        salary_lpa = max(salary_lpa, float(student.expected_salary))

    return round(max(3.5, min(salary_lpa, 36.0)), 2)


# ═════════════════════════════════════════════════════════════════════════════
# SERVICE 3: CAREER RECOMMENDATION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

def recommend_career_roles(student):
    """
    Recommends career roles based on student skills, projects, certifications,
    and career profile using TF-IDF Vectorizer + Nearest Neighbors matching.
    """
    if not student:
        return []

    # Gather all student skill terms
    student_skills_list = [s.strip().lower() for s in (student.skills or "").split(',') if s.strip()]
    for se in student.skill_entries.all():
        if se.name.lower() not in student_skills_list:
            student_skills_list.append(se.name.lower())

    for proj in student.projects.all():
        for t in proj.technology_list:
            if t.lower() not in student_skills_list:
                student_skills_list.append(t.lower())

    skill_text = " ".join(student_skills_list)
    model, vectorizer, roles = get_career_recommender()

    role_skill_matrix = get_skill_matrix()

    recommendations = []

    if model and vectorizer and roles:
        try:
            vec = vectorizer.transform([skill_text])
            distances, indices = model.kneighbors(vec, n_neighbors=min(5, len(roles)))

            for i in range(len(indices[0])):
                idx = indices[0][i]
                dist = distances[0][i]
                role_name = roles[idx]
                match_pct = max(30, int((1.0 - dist) * 100))

                required_skills = role_skill_matrix.get(role_name, ['Python', 'SQL', 'Git'])
                matching_skills = [s for s in required_skills if s.lower() in student_skills_list]

                recommendations.append({
                    'title': role_name,
                    'confidence': match_pct,
                    'matching_skills': matching_skills[:5] or required_skills[:3],
                    'required_skills': required_skills,
                })
        except Exception as e:
            print(f"Career recommender error: {e}")

    # Fallback if recommender not initialized or returned empty
    if not recommendations:
        for r_name, req_skills in role_skill_matrix.items():
            matching = [s for s in req_skills if s.lower() in student_skills_list]
            match_pct = min(95, 40 + len(matching) * 12)
            recommendations.append({
                'title': r_name,
                'confidence': match_pct,
                'matching_skills': matching[:5] or req_skills[:3],
                'required_skills': req_skills,
            })

    recommendations = sorted(recommendations, key=lambda x: x['confidence'], reverse=True)
    return recommendations[:4]


# ═════════════════════════════════════════════════════════════════════════════
# SERVICE 4: SKILL GAP ANALYSIS & ROADMAP SERVICE
# ═════════════════════════════════════════════════════════════════════════════

def analyze_skill_gaps(student, target_role=None):
    """
    Identifies missing skills required for the target career role
    and generates a personalized 4-step learning roadmap.
    """
    if not student:
        return {'missing_skills': [], 'roadmap': []}

    role_skill_matrix = get_skill_matrix()

    if not target_role:
        target_role = student.preferred_job_role or 'Backend Developer'

    # Find closest role in matrix
    matched_role = None
    for r_name in role_skill_matrix.keys():
        if target_role.lower() in r_name.lower() or r_name.lower() in target_role.lower():
            matched_role = r_name
            break

    if not matched_role:
        matched_role = list(role_skill_matrix.keys())[0] if role_skill_matrix else 'Backend Developer'

    required_skills = role_skill_matrix.get(matched_role, ['Python', 'Django', 'SQL', 'Git', 'Docker'])

    student_skills_list = [s.strip().lower() for s in (student.skills or "").split(',') if s.strip()]
    for se in student.skill_entries.all():
        if se.name.lower() not in student_skills_list:
            student_skills_list.append(se.name.lower())

    acquired_skills = [s for s in required_skills if s.lower() in student_skills_list]
    missing_skills = [s for s in required_skills if s.lower() not in student_skills_list]

    # Generate Personalized Roadmap Steps
    roadmap = [
        {
            'step': 1,
            'title': 'Core Programming & Data Structures',
            'duration': '2-3 Weeks',
            'desc': f"Master core language syntax and DSA concepts in {acquired_skills[0] if acquired_skills else 'Python/Java'}."
        },
        {
            'step': 2,
            'title': f"Master Missing Skills ({', '.join(missing_skills[:3]) if missing_skills else 'Frameworks'})",
            'duration': '3-4 Weeks',
            'desc': f"Learn essential role technologies: {', '.join(missing_skills[:4]) if missing_skills else 'Advanced APIs and Database Architecture'}."
        },
        {
            'step': 3,
            'title': 'Build Portfolio Project',
            'duration': '2 Weeks',
            'desc': f"Build a full-fledged application implementing {missing_skills[0] if missing_skills else 'REST APIs'} and upload it to GitHub."
        },
        {
            'step': 4,
            'title': 'Resume Optimization & Mock Interviews',
            'duration': '1 Week',
            'desc': "Add project credentials to your PlaceSync profile, run ATS analysis, and practice technical interview questions."
        }
    ]

    return {
        'target_role': matched_role,
        'acquired_skills': acquired_skills,
        'missing_skills': missing_skills,
        'roadmap': roadmap,
    }
