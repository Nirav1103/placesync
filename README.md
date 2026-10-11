# PlaceSync - Campus Placement Management System

**PlaceSync** is a comprehensive campus placement management platform built with Django. It bridges the gap between students, colleges, training & placement officers (TPOs), and recruiters.

---

## 🚀 Key Features

- **Multi-Role Authentication**: Dedicated portals for Students, Staff/Faculty, and Administrators.
- **Student Portal**: Manage profiles, upload resumes, track job opportunities, and view application statuses.
- **Company & Opportunity Management**: Post job openings, internships, eligibility criteria, and drives.
- **Placement Tracking**: End-to-end management of placement drives, shortlisting, interviews, and offer letters.
- **Analytics & Reports**: Visual dashboards and reports for placement statistics, salary packages, and department trends.
- **AI/ML Assisted Predictions**: Placement prediction and career recommendations powered by trained machine learning models.
- **Communication Module**: Announcements and notifications for upcoming campus drives and events.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Django
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (default for development), configurable with PostgreSQL / MySQL
- **Machine Learning**: Scikit-learn, Pandas, NumPy, Joblib

---

## 📦 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Nirav1103/PlaceSync.git
cd PlaceSync
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create a superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Start the development server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

---

## 📂 Project Structure

```
PlaceSync/
├── accounts/           # User authentication & registration
├── analytics/          # Placement analytics & visual insights
├── batches/            # Academic batch management
├── colleges/           # College information
├── communication/      # Notifications & announcements
├── companies/          # Recruiter & company directory
├── dashboard/          # Admin & staff dashboards
├── dataset/            # Datasets & trained ML models
├── departments/        # College departments management
├── opportunities/      # Job postings & internships
├── placements/         # Drive records, applications & offers
├── reports/            # Exportable reports
├── staff_permissions/  # Role-based access control
├── static/             # CSS, JavaScript & static assets
├── student_portal/     # Dedicated student UI & workflows
├── students/           # Student records & profiles
├── templates/          # HTML templates
├── PlaceSync/          # Django project settings and URLs
└── manage.py           # Django CLI
```

---

## 👤 Author

- GitHub: [@Nirav1103](https://github.com/Nirav1103)
