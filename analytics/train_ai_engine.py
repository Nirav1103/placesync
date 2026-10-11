import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    ExtraTreesClassifier,
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    r2_score,
    mean_absolute_error,
    mean_squared_error
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
RAW_DIR = os.path.join(DATASET_DIR, 'raw')
MODEL_DIR = os.path.join(DATASET_DIR, 'trained_models')

os.makedirs(MODEL_DIR, exist_ok=True)

# Standard Skill Catalog for Role Skill Mapping
ROLE_SKILL_MAP = {
    'Backend Developer': [
        'Python', 'Django', 'Flask', 'FastAPI', 'Java', 'Spring', 'SQL', 'PostgreSQL',
        'MySQL', 'Redis', 'Docker', 'REST API', 'Git'
    ],
    'Full Stack Developer': [
        'JavaScript', 'TypeScript', 'React', 'Vue', 'Node.js', 'Express', 'HTML', 'CSS',
        'Tailwind', 'Python', 'Django', 'SQL', 'MongoDB', 'Git'
    ],
    'Software Engineer': [
        'C++', 'Java', 'Python', 'Data Structures', 'Algorithms', 'OOP', 'Git',
        'Linux', 'SQL', 'Unit Testing', 'CI/CD'
    ],
    'Data Analyst / Data Scientist': [
        'Python', 'R', 'SQL', 'Pandas', 'NumPy', 'Scikit-Learn', 'TensorFlow', 'PyTorch',
        'Machine Learning', 'Statistics', 'Tableau', 'Power BI'
    ],
    'Cloud & DevOps Engineer': [
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform', 'Linux',
        'Bash', 'CI/CD', 'Git', 'Networking'
    ],
    'Mobile App Developer': [
        'Flutter', 'React Native', 'Android', 'iOS', 'Swift', 'Kotlin', 'Dart', 'REST API', 'Firebase'
    ],
    'Cyber Security Analyst': [
        'Ethical Hacking', 'Network Security', 'Cryptography', 'Linux', 'Python', 'Wireshark',
        'SIEM', 'Penetration Testing', 'Firewalls'
    ]
}


def clean_placement_dataset():
    """
    Loads and cleans the Student Placement Prediction Dataset 2026.
    Applies imputation, feature engineering, and encoding.
    """
    csv_path = os.path.join(RAW_DIR, 'placement', 'student_placement_prediction_dataset_2026.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Placement dataset not found at {csv_path}")

    print(f"Loading placement dataset from: {csv_path}")
    df = pd.read_csv(csv_path)

    # 1. Fill missing values
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median())

    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        df[col] = df[col].fillna(df[col].mode()[0])

    # 2. Target Encoding
    # Binary Placement Status: 1 if Placed / Intern, 0 if Unplaced
    df['target_placed'] = df['placement_status'].apply(
        lambda x: 1 if str(x).strip().upper() in ['PLACED', 'INTERN', 'PLACED & INTERNSHIP', '1', 'YES'] else 0
    )

    # 3. Feature Engineering
    df['academic_composite'] = (df['cgpa'] / 10.0) * 50.0 + (100.0 - df['backlogs'] * 15.0).clip(lower=0) * 0.5
    df['practical_composite'] = df['internships_count'] * 20.0 + df['projects_count'] * 12.0 + df['certifications_count'] * 10.0
    df['skill_composite'] = (df['coding_skill_score'] + df['aptitude_score'] + df['communication_skill_score'] + df['logical_reasoning_score']) / 4.0

    return df


def train_model1_placement_prediction(df):
    """
    Train and evaluate Placement Prediction Classifier Models.
    Outputs readiness score (0-100%) and placement probability.
    """
    print("\n" + "="*60)
    print("MODEL 1: TRAIN PLACEMENT PREDICTION CLASSIFIER")
    print("="*60)

    feature_cols = [
        'cgpa', 'backlogs', 'internships_count', 'projects_count', 'certifications_count',
        'coding_skill_score', 'aptitude_score', 'communication_skill_score', 'logical_reasoning_score',
        'mock_interview_score', 'attendance_percentage', 'academic_composite', 'practical_composite', 'skill_composite'
    ]

    X = df[feature_cols]
    y = df['target_placed']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

    # Evaluate multiple models
    candidates = {
        'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
        'Hist Gradient Boosting': HistGradientBoostingClassifier(random_state=42),
        'Extra Trees': ExtraTreesClassifier(n_estimators=100, random_state=42),
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42)
    }

    best_name = None
    best_model = None
    best_f1 = -1.0
    evaluation_results = {}

    for name, model in candidates.items():
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)
        probs = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, "predict_proba") else preds

        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        roc = roc_auc_score(y_test, probs)

        evaluation_results[name] = {'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1': f1, 'ROC-AUC': roc}
        print(f"[{name}] Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | ROC: {roc:.4f}")

        if f1 > best_f1:
            best_f1 = f1
            best_name = name
            best_model = model

    print(f"\n--> WINNING MODEL FOR PLACEMENT PREDICTION: {best_name} (F1 Score: {best_f1:.4f})")

    # Save trained model and scaler
    model_path = os.path.join(MODEL_DIR, 'placement_model.pkl')
    scaler_path = os.path.join(MODEL_DIR, 'placement_scaler.pkl')

    joblib.dump(best_model, model_path)
    joblib.dump(scaler, scaler_path)

    # Save feature names list
    with open(os.path.join(MODEL_DIR, 'placement_features.json'), 'w') as f:
        json.dump(feature_cols, f)

    return best_model, scaler, evaluation_results


def train_model2_salary_prediction(df):
    """
    Train and evaluate Fresher Salary Regressor Models.
    Predicts expected fresher package in LPA.
    """
    print("\n" + "="*60)
    print("MODEL 2: TRAIN SALARY REGRESSION MODEL")
    print("="*60)

    # Filter placed students with valid positive salary package
    df_placed = df[(df['target_placed'] == 1) & (df['salary_package_lpa'] > 0)].copy()

    feature_cols = [
        'cgpa', 'backlogs', 'internships_count', 'projects_count', 'certifications_count',
        'coding_skill_score', 'aptitude_score', 'communication_skill_score', 'logical_reasoning_score',
        'academic_composite', 'practical_composite', 'skill_composite'
    ]

    X = df_placed[feature_cols]
    y = df_placed['salary_package_lpa']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

    candidates = {
        'Random Forest Regressor': RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting Regressor': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'Extra Trees Regressor': ExtraTreesRegressor(n_estimators=100, random_state=42),
        'Ridge Regression': Ridge(alpha=1.0)
    }

    best_name = None
    best_model = None
    best_r2 = -999.0
    evaluation_results = {}

    for name, model in candidates.items():
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)

        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))

        evaluation_results[name] = {'R2': r2, 'MAE': mae, 'RMSE': rmse}
        print(f"[{name}] R2 Score: {r2:.4f} | MAE: {mae:.4f} LPA | RMSE: {rmse:.4f} LPA")

        if r2 > best_r2:
            best_r2 = r2
            best_name = name
            best_model = model

    print(f"\n--> WINNING MODEL FOR SALARY PREDICTION: {best_name} (R2 Score: {best_r2:.4f})")

    joblib.dump(best_model, os.path.join(MODEL_DIR, 'salary_model.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'salary_scaler.pkl'))
    with open(os.path.join(MODEL_DIR, 'salary_features.json'), 'w') as f:
        json.dump(feature_cols, f)

    return best_model, scaler, evaluation_results


def train_model3_career_recommendation():
    """
    Train TF-IDF & Cosine Similarity / Nearest Neighbors Career Role Recommender.
    Recommends top career roles based on student skill set.
    """
    print("\n" + "="*60)
    print("MODEL 3: TRAIN CAREER RECOMMENDATION ENGINE")
    print("="*60)

    # Build corpus from ROLE_SKILL_MAP and job dataset if available
    job_csv = os.path.join(RAW_DIR, 'jobs', 'ai_job_dataset1.csv')
    role_corpus = {}

    for role, skills in ROLE_SKILL_MAP.items():
        role_corpus[role] = " ".join(skills)

    if os.path.exists(job_csv):
        try:
            df_jobs = pd.read_csv(job_csv)
            if 'job_title' in df_jobs.columns and 'required_skills' in df_jobs.columns:
                for _, row in df_jobs.dropna(subset=['job_title', 'required_skills']).iterrows():
                    title = str(row['job_title']).strip()
                    skills_text = str(row['required_skills']).strip()
                    if title in role_corpus:
                        role_corpus[title] += " " + skills_text
                    else:
                        role_corpus[title] = skills_text
        except Exception as e:
            print(f"Warning loading job dataset: {e}")

    roles = list(role_corpus.keys())
    texts = [role_corpus[r] for r in roles]

    vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b[\w\+\#\.]+\b', lowercase=True)
    X_tfidf = vectorizer.fit_transform(texts)

    nn_model = NearestNeighbors(n_neighbors=min(5, len(roles)), metric='cosine')
    nn_model.fit(X_tfidf)

    joblib.dump(vectorizer, os.path.join(MODEL_DIR, 'skill_vectorizer.pkl'))
    joblib.dump(nn_model, os.path.join(MODEL_DIR, 'career_recommendation_model.pkl'))
    with open(os.path.join(MODEL_DIR, 'career_roles.json'), 'w') as f:
        json.dump(roles, f)

    print(f"--> Trained Career Recommender across {len(roles)} role categories!")
    return nn_model, vectorizer, roles


def train_model4_skill_gap_matrix():
    """
    Builds Skill Gap Analysis & Learning Roadmap Matrix.
    """
    print("\n" + "="*60)
    print("MODEL 4: BUILD SKILL GAP ANALYSIS & ROADMAP MATRIX")
    print("="*60)

    matrix_path = os.path.join(MODEL_DIR, 'role_skill_matrix.json')
    with open(matrix_path, 'w') as f:
        json.dump(ROLE_SKILL_MAP, f, indent=2)

    print("--> Saved Role Skill Matrix for Skill Gap Analysis!")
    return ROLE_SKILL_MAP


def main():
    print("="*60)
    print("STARTING PLACESYNC AI ENGINE TRAINING PIPELINE")
    print("="*60)

    # Step 1: Clean data
    df_placement = clean_placement_dataset()

    # Step 2: Model 1 - Placement Prediction
    m1, s1, eval1 = train_model1_placement_prediction(df_placement)

    # Step 3: Model 2 - Salary Prediction
    m2, s2, eval2 = train_model2_salary_prediction(df_placement)

    # Step 4: Model 3 - Career Recommendation
    m3, v3, r3 = train_model3_career_recommendation()

    # Step 5: Model 4 - Skill Gap Matrix
    m4 = train_model4_skill_gap_matrix()

    print("\n" + "="*60)
    print("ALL 4 MACHINE LEARNING MODELS TRAINED & SAVED SUCCESSFULLY!")
    print(f"Models directory: {MODEL_DIR}")
    print("="*60)


if __name__ == '__main__':
    main()
