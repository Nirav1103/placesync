from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Student(models.Model):
    class PlacementStatus(models.TextChoices):
        UNPLACED = 'UNPLACED', 'Unplaced'
        PLACED = 'PLACED', 'Placed'
        INTERN = 'INTERN', 'Internship'
        PLACED_AND_INTERN = 'PLACED_AND_INTERN', 'Placed & Internship'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )
    college = models.ForeignKey(
        'colleges.College',
        on_delete=models.CASCADE,
        related_name='students'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='students'
    )
    batch = models.ForeignKey(
        'batches.Batch',
        on_delete=models.CASCADE,
        related_name='students'
    )

    roll_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CGPA out of 10"
    )
    spi = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Semester Performance Index"
    )
    cpi = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cumulative Performance Index"
    )
    backlogs = models.PositiveIntegerField(
        default=0,
        help_text="Number of active backlogs"
    )
    semester = models.PositiveSmallIntegerField(
        default=1,
        help_text="Current semester"
    )
    division = models.CharField(
        max_length=10,
        blank=True,
        help_text="Class division/section"
    )

    placement_status = models.CharField(
        max_length=20,
        choices=PlacementStatus.choices,
        default=PlacementStatus.UNPLACED
    )
    package_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="LPA package amount if placed"
    )
    stipend_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly stipend amount if doing internship"
    )

    # ── Student Portal fields ──────────────────────────────
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True)
    leetcode_url = models.URLField(blank=True)
    codechef_url = models.URLField(blank=True)
    hackerrank_url = models.URLField(blank=True)
    preferred_job_role = models.CharField(max_length=100, blank=True)
    preferred_industry = models.CharField(max_length=100, blank=True)
    preferred_city = models.CharField(max_length=100, blank=True)
    preferred_country = models.CharField(max_length=100, blank=True, default="India")
    preferred_work_location = models.CharField(max_length=100, blank=True)
    work_preference = models.CharField(
        max_length=20,
        choices=[
            ('REMOTE', 'Remote'),
            ('HYBRID', 'Hybrid'),
            ('ONSITE', 'Onsite'),
            ('ANY', 'Open to Any')
        ],
        default='ANY'
    )
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected Salary in LPA"
    )
    career_objective = models.CharField(
        max_length=50,
        choices=[
            ('JOB', 'Placement Job'),
            ('HIGHER_STUDIES', 'Higher Studies'),
            ('ENTREPRENEURSHIP', 'Entrepreneurship'),
            ('BOTH', 'Job & Higher Studies')
        ],
        default='JOB'
    )
    higher_studies = models.CharField(max_length=255, blank=True, help_text="e.g. MS in CS, MBA")
    willing_to_relocate = models.BooleanField(default=True)
    
    # ── Academic fields managed by Admin ───────────────────
    tenth_board = models.CharField(max_length=100, blank=True)
    tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    twelfth_board = models.CharField(max_length=100, blank=True)
    twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="12th/Diploma Percentage")
    degree = models.CharField(max_length=100, blank=True, default="B.Tech")
    current_academic_year = models.CharField(max_length=50, blank=True, help_text="e.g. 1st Year, 2nd Year, etc.")
    admission_year = models.PositiveIntegerField(null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    course = models.CharField(max_length=100, blank=True, default="Computer Science & Engineering")

    bio = models.TextField(blank=True, help_text="Short personal introduction")
    address = models.CharField(max_length=500, blank=True)
    skills = models.TextField(
        blank=True,
        help_text="Comma-separated skills e.g. Python, Django, SQL"
    )
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    resume = models.FileField(
        upload_to='student_resumes/',
        blank=True,
        null=True,
        help_text="Upload PDF resume"
    )
    resume_uploaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['college', 'roll_number'],
                name='unique_college_roll_number'
            ),
        ]
        ordering = ['roll_number']

    def __str__(self):
        return f"{self.name} ({self.roll_number}) - {self.batch.name}"

    # ── Computed scores (pure Python) ─────────────────────
    def profile_completion(self):
        fields = [
            self.name, self.email, self.phone, self.bio,
            self.address, self.skills, self.linkedin_url,
            self.github_url, self.cgpa, self.resume,
            self.photo, self.date_of_birth, self.gender,
            self.leetcode_url, self.codechef_url, self.hackerrank_url,
            self.preferred_job_role, self.preferred_work_location
        ]
        filled = sum(1 for f in fields if f)
        return round(filled / len(fields) * 100)

    def ats_score(self):
        active_resume = self.resume_versions.filter(resume_type='RESUME', is_active=True).first()
        if active_resume:
            return active_resume.ats_score
        if not self.resume:
            return 30
        score = 55
        if self.skills:
            score += 15
        if self.linkedin_url:
            score += 10
        if self.github_url:
            score += 10
        return min(score, 100)

    def placement_readiness(self):
        cgpa_score = float(self.cgpa or 0) / 10 * 40
        try:
            app_count = self.applications.count()
        except Exception:
            app_count = 0
        app_score = min(app_count * 5, 30)
        profile_score = self.profile_completion() * 0.20
        skill_count = len([s for s in self.skills.split(',') if s.strip()]) if self.skills else 0
        skill_score = min(skill_count * 2, 10)
        return round(cgpa_score + app_score + profile_score + skill_score)

    def career_score(self):
        try:
            app_count = self.applications.count()
            shortlisted = self.applications.filter(
                status__in=['SHORTLISTED', 'SELECTED']
            ).count()
        except Exception:
            app_count = 0
            shortlisted = 0
        base = min(app_count * 8, 50)
        interview_bonus = min(shortlisted * 15, 40)
        resume_bonus = 10 if self.resume else 0
        return min(base + interview_bonus + resume_bonus, 100)


# ─────────────────────────────────────────────────────────────────────────────
# StudentSkill — structured skill entries per student
# ─────────────────────────────────────────────────────────────────────────────

class StudentSkill(models.Model):
    """A single skill entry owned by a student with category and proficiency."""

    class Category(models.TextChoices):
        PROGRAMMING  = 'PROGRAMMING',  'Programming'
        DATABASE     = 'DATABASE',     'Database'
        CLOUD        = 'CLOUD',        'Cloud'
        FRAMEWORK    = 'FRAMEWORK',    'Framework'
        TOOLS        = 'TOOLS',        'Tools'
        SOFT_SKILLS  = 'SOFT_SKILLS',  'Soft Skills'

    class Proficiency(models.TextChoices):
        BEGINNER     = 'BEGINNER',     'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED     = 'ADVANCED',     'Advanced'

    # Proficiency display order weights (used for sorting / progress bar)
    PROFICIENCY_WEIGHT = {
        'BEGINNER':     33,
        'INTERMEDIATE': 66,
        'ADVANCED':     100,
    }

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='skill_entries'
    )
    name = models.CharField(max_length=100, help_text="Skill name e.g. Python, MySQL, Docker")
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.PROGRAMMING
    )
    proficiency = models.CharField(
        max_length=20,
        choices=Proficiency.choices,
        default=Proficiency.BEGINNER
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional short note e.g. 3 years of experience"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'name'],
                name='unique_student_skill_name'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_proficiency_display()}) — {self.student.name}"

    @property
    def proficiency_pct(self):
        """Return integer 0-100 for progress bar rendering."""
        return self.PROFICIENCY_WEIGHT.get(self.proficiency, 33)

    @property
    def proficiency_css(self):
        """CSS color class for the proficiency badge."""
        return {
            'BEGINNER':     'sp-badge-amber',
            'INTERMEDIATE': 'sp-badge-sky',
            'ADVANCED':     'sp-badge-green',
        }.get(self.proficiency, 'sp-badge-gray')

    @property
    def category_icon(self):
        return {
            'PROGRAMMING': '💻',
            'DATABASE':    '🗄️',
            'CLOUD':       '☁️',
            'FRAMEWORK':   '⚙️',
            'TOOLS':       '🔧',
            'SOFT_SKILLS': '🤝',
        }.get(self.category, '🏷️')

    @property
    def bar_color_css(self):
        return {
            'BEGINNER':     'bar-amber',
            'INTERMEDIATE': 'bar-sky',
            'ADVANCED':     'bar-green',
        }.get(self.proficiency, 'bar-violet')


# ─────────────────────────────────────────────────────────────────────────────
# StudentResume — Tracks resume/CV file uploads, versions, and analysis
# ─────────────────────────────────────────────────────────────────────────────

class StudentResume(models.Model):
    class ResumeType(models.TextChoices):
        RESUME = 'RESUME', 'Resume'
        CV = 'CV', 'CV'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='resume_versions'
    )
    resume_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom name for the resume"
    )
    file = models.FileField(upload_to='student_resumes/')
    file_size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    resume_type = models.CharField(
        max_length=10,
        choices=ResumeType.choices,
        default=ResumeType.RESUME
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Mark as default resume")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Analysis metrics
    extracted_text = models.TextField(blank=True)
    ats_score = models.PositiveIntegerField(default=0)
    completion_score = models.PositiveIntegerField(default=0)
    formatting_score = models.PositiveIntegerField(default=0)

    # JSON results for parsed categories/feedback
    # Using TextField with JSON formatting for compatibility
    projects_found = models.TextField(blank=True, default='[]')
    education_found = models.TextField(blank=True, default='[]')
    skills_found = models.TextField(blank=True, default='[]')
    certificates_found = models.TextField(blank=True, default='[]')
    experience_found = models.TextField(blank=True, default='[]')
    missing_keywords = models.TextField(blank=True, default='[]')
    suggestions = models.TextField(blank=True, default='[]')

    # AI Resume Parser extended fields
    parser_status = models.CharField(
        max_length=20,
        default='PENDING',
        choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')]
    )
    parsed_at = models.DateTimeField(null=True, blank=True)
    parser_confidence = models.PositiveIntegerField(default=0, help_text="0-100% confidence score")
    programming_languages_found = models.TextField(blank=True, default='[]')
    tools_found = models.TextField(blank=True, default='[]')
    soft_skills_found = models.TextField(blank=True, default='[]')

    class Meta:
        ordering = ['-is_default', '-uploaded_at']

    def __str__(self):
        return f"{self.display_name} ({self.get_resume_type_display()}) — {self.student.name}"

    @property
    def display_name(self):
        if self.resume_name and self.resume_name.strip():
            return self.resume_name.strip()
        import os
        return os.path.basename(self.file.name)

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)

    @property
    def formatted_file_size(self):
        size = self.file_size
        if not size:
            try:
                size = self.file.size
            except Exception:
                size = 0
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def set_as_default(self):
        """Sets this resume as default and unsets default for all other resumes of this student."""
        StudentResume.objects.filter(student=self.student).update(is_default=False)
        self.is_default = True
        self.is_active = True
        self.save()
        if self.resume_type == 'RESUME':
            self.student.resume = self.file
            self.student.save()


# ─────────────────────────────────────────────────────────────────────────────
# Project — Tracks student technical projects and achievements
# ─────────────────────────────────────────────────────────────────────────────

class Project(models.Model):
    class Category(models.TextChoices):
        WEB_DEV = 'WEB_DEV', 'Web Development'
        MOBILE_DEV = 'MOBILE_DEV', 'Mobile Development'
        DESKTOP = 'DESKTOP', 'Desktop Application'
        AI = 'AI', 'Artificial Intelligence'
        ML = 'ML', 'Machine Learning'
        DATA_SCIENCE = 'DATA_SCIENCE', 'Data Science'
        CYBER_SEC = 'CYBER_SEC', 'Cyber Security'
        CLOUD = 'CLOUD', 'Cloud Computing'
        BLOCKCHAIN = 'BLOCKCHAIN', 'Blockchain'
        IOT = 'IOT', 'IoT'
        GAME_DEV = 'GAME_DEV', 'Game Development'
        AUTOMATION = 'AUTOMATION', 'Automation'
        API_DEV = 'API_DEV', 'API Development'
        OTHER = 'OTHER', 'Other'

    class ProjectType(models.TextChoices):
        ACADEMIC = 'ACADEMIC', 'Academic Project'
        PERSONAL = 'PERSONAL', 'Personal Project'
        HACKATHON = 'HACKATHON', 'Hackathon Project'
        INTERNSHIP = 'INTERNSHIP', 'Internship Project'
        FREELANCE = 'FREELANCE', 'Freelance Project'
        CLIENT = 'CLIENT', 'Client Project'
        OPEN_SOURCE = 'OPEN_SOURCE', 'Open Source Project'

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        ONGOING = 'ONGOING', 'Ongoing'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        ARCHIVED = 'ARCHIVED', 'Archived'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=500)
    detailed_description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.WEB_DEV
    )
    project_type = models.CharField(
        max_length=50,
        choices=ProjectType.choices,
        default=ProjectType.PERSONAL
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.COMPLETED
    )
    technologies = models.TextField(help_text="Comma-separated technologies e.g. Python, Django, PostgreSQL")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    team_type = models.CharField(
        max_length=20,
        choices=[('INDIVIDUAL', 'Individual'), ('TEAM', 'Team Project')],
        default='INDIVIDUAL'
    )
    image = models.ImageField(upload_to='project_images/', null=True, blank=True)
    
    # Project Links
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    google_drive_url = models.URLField(blank=True)
    figma_url = models.URLField(blank=True)
    play_store_url = models.URLField(blank=True)
    app_store_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Multiple features and achievements (comma-separated or newline-separated)
    key_features = models.TextField(blank=True, help_text="Comma-separated features e.g. User Authentication, REST API")
    achievements = models.TextField(blank=True, help_text="Comma-separated achievements e.g. Hackathon Winner, Innovation Award")

    # Featured Project
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.title} — {self.student.name}"

    @property
    def technology_list(self):
        if not self.technologies:
            return []
        return [t.strip() for t in self.technologies.split(',') if t.strip()]

    @property
    def feature_list(self):
        if not self.key_features:
            return []
        return [f.strip() for f in self.key_features.split(',') if f.strip()]

    @property
    def achievement_list(self):
        if not self.achievements:
            return []
        return [a.strip() for a in self.achievements.split(',') if a.strip()]

    @property
    def technology_badges(self):
        badges = []
        for tech in self.technology_list:
            t = tech.lower()
            if 'python' in t or 'django' in t or 'flask' in t:
                cls = 'sp-badge-violet'
            elif 'js' in t or 'javascript' in t or 'react' in t or 'vue' in t:
                cls = 'sp-badge-sky'
            elif 'html' in t or 'css' in t or 'tailwind' in t or 'bootstrap' in t:
                cls = 'sp-badge-indigo'
            elif 'mysql' in t or 'postgres' in t or 'sql' in t or 'db' in t or 'database' in t:
                cls = 'sp-badge-amber'
            elif 'mongodb' in t or 'node' in t:
                cls = 'sp-badge-green'
            elif 'docker' in t or 'aws' in t or 'cloud' in t or 'azure' in t or 'firebase' in t:
                cls = 'sp-badge-sky'
            else:
                cls = 'sp-badge-gray'
            badges.append({'name': tech, 'class': cls})
        return badges

    @property
    def portfolio_score(self):
        score = 0
        if self.github_url:
            score += 10
        if self.live_url:
            score += 10
        if self.documentation_url:
            score += 5
        if self.detailed_description and len(self.detailed_description.strip()) > 0:
            score += 5
        if len(self.technology_list) >= 5:
            score += 5
        if self.youtube_url:
            score += 5
        if self.is_featured:
            score += 5
        return score


from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# ─────────────────────────────────────────────────────────────────────────────
# TechnicalLinks
# ─────────────────────────────────────────────────────────────────────────────

class TechnicalLinks(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='technical_links')
    github = models.URLField(blank=True, verbose_name="GitHub URL")
    leetcode = models.URLField(blank=True, verbose_name="LeetCode URL")
    codechef = models.URLField(blank=True, verbose_name="CodeChef URL")
    codeforces = models.URLField(blank=True, verbose_name="CodeForces URL")
    hackerrank = models.URLField(blank=True, verbose_name="HackerRank URL")
    geeksforgeeks = models.URLField(blank=True, verbose_name="GeeksforGeeks URL")
    kaggle = models.URLField(blank=True, verbose_name="Kaggle URL")
    portfolio = models.URLField(blank=True, verbose_name="Portfolio URL")
    linkedin = models.URLField(blank=True, verbose_name="LinkedIn URL")

    def __str__(self):
        return f"Technical Links — {self.student.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Activity — Unified Developer Journey Timeline Event
# ─────────────────────────────────────────────────────────────────────────────

class Activity(models.Model):
    class Category(models.TextChoices):
        LEARNING = 'LEARNING', 'Learning'
        PROJECT = 'PROJECT', 'Project'
        CODING_PRACTICE = 'CODING_PRACTICE', 'Coding Practice'
        HACKATHON = 'HACKATHON', 'Hackathon'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        WORKSHOP = 'WORKSHOP', 'Workshop'
        RESEARCH = 'RESEARCH', 'Research'
        CERTIFICATE = 'CERTIFICATE', 'Certificate'
        COMPETITION = 'COMPETITION', 'Competition'
        OTHER = 'OTHER', 'Other'

    class ActivityType(models.TextChoices):
        DAILY_LOG = 'DAILY_LOG', 'Daily Log'
        WEEKLY_SUMMARY = 'WEEKLY_SUMMARY', 'Weekly Summary'
        MONTHLY_SUMMARY = 'MONTHLY_SUMMARY', 'Monthly Summary'
        CODING_PRACTICE = 'CODING_PRACTICE', 'Coding Practice'
        PROJECT_MILESTONE = 'PROJECT_MILESTONE', 'Project Milestone'
        HACKATHON = 'HACKATHON', 'Hackathon Journal'
        CERTIFICATE = 'CERTIFICATE', 'Certificate'
        LEARNING_JOURNAL = 'LEARNING_JOURNAL', 'Learning Journal'
        OPEN_SOURCE = 'OPEN_SOURCE', 'Open Source'
        ACHIEVEMENT = 'ACHIEVEMENT', 'Achievement'

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='journey_activities')
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices, default=ActivityType.DAILY_LOG)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.LEARNING)
    date = models.DateField()
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    technology_tags = models.TextField(blank=True, help_text="Comma-separated technologies")
    related_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_activities')
    attachment = models.FileField(upload_to='journey_attachments/', blank=True, null=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Generic relation link back to the specific source record
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.title} — {self.student.name}"

    @property
    def tech_list(self):
        if not self.technology_tags:
            return []
        return [t.strip() for t in self.technology_tags.split(',') if t.strip()]

    @property
    def technology_badges(self):
        badges = []
        for tech in self.tech_list:
            t = tech.lower()
            if 'python' in t or 'django' in t or 'flask' in t:
                cls = 'sp-badge-violet'
            elif 'js' in t or 'javascript' in t or 'react' in t or 'vue' in t:
                cls = 'sp-badge-sky'
            elif 'html' in t or 'css' in t or 'tailwind' in t or 'bootstrap' in t:
                cls = 'sp-badge-indigo'
            elif 'mysql' in t or 'postgres' in t or 'sql' in t or 'db' in t or 'database' in t:
                cls = 'sp-badge-amber'
            elif 'mongodb' in t or 'node' in t:
                cls = 'sp-badge-green'
            elif 'docker' in t or 'aws' in t or 'cloud' in t or 'azure' in t or 'firebase' in t:
                cls = 'sp-badge-sky'
            else:
                cls = 'sp-badge-gray'
            badges.append({'name': tech, 'class': cls})
        return badges


# ─────────────────────────────────────────────────────────────────────────────
# WeeklySummary
# ─────────────────────────────────────────────────────────────────────────────

class WeeklySummary(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='weekly_summaries')
    week_number = models.PositiveIntegerField(verbose_name="Week Number")
    summary = models.TextField(verbose_name="Weekly Summary Details")
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Hours Worked")
    problems_solved = models.PositiveIntegerField(default=0, verbose_name="Problems Solved")
    projects_worked = models.TextField(blank=True, verbose_name="Projects Worked On")
    skills_learned = models.TextField(blank=True, verbose_name="Skills Learned")
    challenges = models.TextField(blank=True, verbose_name="Challenges Faced")
    date = models.DateField(help_text="Usually the Sunday/ending date of the week")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Week {self.week_number} Summary — {self.student.name}"

    def get_activity_title(self):
        return f"Weekly Summary: Week {self.week_number}"

    def get_activity_description(self):
        desc = f"Spent {self.hours} hours. Solved {self.problems_solved} problems.\n"
        if self.skills_learned:
            desc += f"Learned: {self.skills_learned}\n"
        desc += self.summary
        return desc

    def get_activity_category(self):
        return Activity.Category.LEARNING

    def get_activity_type(self):
        return Activity.ActivityType.WEEKLY_SUMMARY

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.hours_spent = self.hours
        activity.technology_tags = self.skills_learned
        activity.status = Activity.Status.COMPLETED
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# MonthlySummary
# ─────────────────────────────────────────────────────────────────────────────

class MonthlySummary(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='monthly_summaries')
    month = models.CharField(max_length=100, verbose_name="Month")
    achievements = models.TextField(blank=True, verbose_name="Key Achievements")
    projects_completed = models.TextField(blank=True, verbose_name="Projects Completed")
    technologies_learned = models.TextField(blank=True, verbose_name="Technologies Learned")
    certificates = models.TextField(blank=True, verbose_name="Certificates Acquired")
    goals = models.TextField(blank=True, verbose_name="Goals Set / Completed")
    date = models.DateField(help_text="Starting date or ending date of the month")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Monthly Summary: {self.month} — {self.student.name}"

    def get_activity_title(self):
        return f"Monthly Summary: {self.month}"

    def get_activity_description(self):
        desc = ""
        if self.achievements:
            desc += f"Achievements: {self.achievements}\n"
        if self.projects_completed:
            desc += f"Completed Projects: {self.projects_completed}\n"
        if self.certificates:
            desc += f"Certificates: {self.certificates}\n"
        if self.goals:
            desc += f"Goals achieved: {self.goals}"
        return desc or f"Monthly summary for {self.month}"

    def get_activity_category(self):
        return Activity.Category.LEARNING

    def get_activity_type(self):
        return Activity.ActivityType.MONTHLY_SUMMARY

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.technology_tags = self.technologies_learned
        activity.status = Activity.Status.COMPLETED
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# ProjectMilestone
# ─────────────────────────────────────────────────────────────────────────────

class ProjectMilestone(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='project_milestones')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    milestone = models.CharField(max_length=255, verbose_name="Milestone Name")
    progress_pct = models.PositiveIntegerField(default=0, help_text="Progress from 0 to 100", verbose_name="Progress %")
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Hours Contributed")
    technologies = models.TextField(blank=True, help_text="Comma-separated technologies", verbose_name="Technologies Used")
    status = models.CharField(max_length=50, choices=Activity.Status.choices, default=Activity.Status.IN_PROGRESS, verbose_name="Status")
    date = models.DateField(verbose_name="Milestone Date")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.project.title} — {self.milestone} ({self.progress_pct}%)"

    def get_activity_title(self):
        return f"Milestone: {self.milestone} on {self.project.title}"

    def get_activity_description(self):
        return f"Achieved {self.progress_pct}% progress on project '{self.project.title}'. Status is {self.get_status_display()}.\nSpent {self.hours} hours implementing project features."

    def get_activity_category(self):
        return Activity.Category.PROJECT

    def get_activity_type(self):
        return Activity.ActivityType.PROJECT_MILESTONE

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.hours_spent = self.hours
        activity.technology_tags = self.technologies
        activity.related_project = self.project
        activity.status = self.status
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# HackathonJournal
# ─────────────────────────────────────────────────────────────────────────────

class HackathonJournal(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='hackathons')
    hackathon_name = models.CharField(max_length=255, verbose_name="Hackathon Name")
    organizer = models.CharField(max_length=255, verbose_name="Organizer")
    date = models.DateField(verbose_name="Hackathon Date")
    theme = models.CharField(max_length=255, verbose_name="Theme")
    team = models.TextField(blank=True, verbose_name="Team Details")
    role = models.CharField(max_length=100, blank=True, verbose_name="Your Role")
    project = models.CharField(max_length=255, blank=True, verbose_name="Project Built")
    technologies = models.TextField(blank=True, help_text="Comma-separated technologies", verbose_name="Technologies Used")
    challenges = models.TextField(blank=True, verbose_name="Challenges Faced")
    learning = models.TextField(blank=True, verbose_name="Key Learning Outcomes")
    achievement = models.CharField(max_length=255, blank=True, verbose_name="Achievement/Prize")
    certificate = models.FileField(upload_to='hackathon_certs/', blank=True, null=True, verbose_name="Certificate")
    repository = models.URLField(blank=True, verbose_name="Repository Link")
    presentation = models.URLField(blank=True, verbose_name="Presentation / Demo Link")
    photo = models.ImageField(upload_to='hackathon_photos/', blank=True, null=True, verbose_name="Photos / Team Banner")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.hackathon_name} — {self.student.name}"

    def get_activity_title(self):
        ach = f" ({self.achievement})" if self.achievement else ""
        return f"Hackathon: Participated in {self.hackathon_name}{ach}"

    def get_activity_description(self):
        desc = f"Organized by {self.organizer}. Theme was '{self.theme}'.\n"
        if self.project:
            desc += f"Built project '{self.project}' as {self.role}.\n"
        if self.challenges:
            desc += f"Challenges: {self.challenges}\n"
        if self.learning:
            desc += f"Learning: {self.learning}\n"
        return desc

    def get_activity_category(self):
        return Activity.Category.HACKATHON

    def get_activity_type(self):
        return Activity.ActivityType.HACKATHON

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.technology_tags = self.technologies
        activity.status = Activity.Status.COMPLETED
        if self.certificate:
            activity.attachment = self.certificate
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# CodingPractice
# ─────────────────────────────────────────────────────────────────────────────

class CodingPractice(models.Model):
    class Platform(models.TextChoices):
        LEETCODE = 'LeetCode', 'LeetCode'
        CODECHEF = 'CodeChef', 'CodeChef'
        CODEFORCES = 'Codeforces', 'Codeforces'
        HACKERRANK = 'HackerRank', 'HackerRank'
        GEEKSFORGEEKS = 'GeeksforGeeks', 'GeeksforGeeks'
        OTHER = 'Other', 'Other'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='coding_practices')
    platform = models.CharField(max_length=50, choices=Platform.choices, default=Platform.LEETCODE, verbose_name="Platform")
    problems_solved = models.PositiveIntegerField(default=0, verbose_name="Problems Solved")
    difficulty = models.CharField(max_length=100, blank=True, help_text="e.g. 3 Easy, 2 Medium", verbose_name="Difficulty")
    topics = models.TextField(blank=True, help_text="Comma-separated topics e.g. DP, Graphs, HashTables", verbose_name="Topics covered")
    notes = models.TextField(blank=True, verbose_name="Notes/Optimal Solutions Learned")
    date = models.DateField(verbose_name="Practice Date")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.platform} Practice on {self.date} — {self.student.name}"

    def get_activity_title(self):
        return f"Coding Practice: Solved {self.problems_solved} problems on {self.platform}"

    def get_activity_description(self):
        desc = f"Difficulty: {self.difficulty or 'Not specified'}.\n"
        if self.topics:
            desc += f"Topics: {self.topics}\n"
        if self.notes:
            desc += f"Notes: {self.notes}"
        return desc

    def get_activity_category(self):
        return Activity.Category.CODING_PRACTICE

    def get_activity_type(self):
        return Activity.ActivityType.CODING_PRACTICE

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.technology_tags = self.topics
        activity.status = Activity.Status.COMPLETED
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# LearningJournal
# ─────────────────────────────────────────────────────────────────────────────

class LearningJournal(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='learning_logs')
    course = models.CharField(max_length=255, verbose_name="Course Name / Topic")
    platform = models.CharField(max_length=100, verbose_name="Platform / Provider")
    duration = models.CharField(max_length=100, blank=True, help_text="e.g. 10 hours, 2 weeks", verbose_name="Duration")
    progress = models.PositiveIntegerField(default=100, help_text="Progress % (e.g. 100 for completed)", verbose_name="Progress %")
    topics = models.TextField(blank=True, help_text="Comma-separated topics learned", verbose_name="Topics Covered")
    certificate = models.FileField(upload_to='learning_certs/', blank=True, null=True, verbose_name="Certificate File")
    notes = models.TextField(blank=True, verbose_name="Learning Notes")
    date = models.DateField(verbose_name="Logging Date")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.course} ({self.progress}%) — {self.student.name}"

    def get_activity_title(self):
        prog = "Completed" if self.progress == 100 else f"Progressed {self.progress}% in"
        return f"Learning Log: {prog} course '{self.course}'"

    def get_activity_description(self):
        desc = f"Provider: {self.platform}. Duration: {self.duration or 'Not specified'}.\n"
        if self.topics:
            desc += f"Topics: {self.topics}\n"
        if self.notes:
            desc += f"Notes: {self.notes}"
        return desc

    def get_activity_category(self):
        return Activity.Category.LEARNING

    def get_activity_type(self):
        return Activity.ActivityType.LEARNING_JOURNAL

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.technology_tags = self.topics
        activity.status = Activity.Status.COMPLETED if self.progress == 100 else Activity.Status.IN_PROGRESS
        if self.certificate:
            activity.attachment = self.certificate
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# OpenSourceContribution
# ─────────────────────────────────────────────────────────────────────────────

class OpenSourceContribution(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='open_source_contributions')
    repository = models.CharField(max_length=255, verbose_name="GitHub Repository Name")
    contribution = models.TextField(verbose_name="Contribution details")
    pull_request = models.URLField(blank=True, verbose_name="Pull Request URL")
    issue = models.URLField(blank=True, verbose_name="Issue URL")
    date = models.DateField(verbose_name="Contribution Date")
    learning = models.TextField(blank=True, verbose_name="Learning gained")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"OS Contribution to {self.repository} — {self.student.name}"

    def get_activity_title(self):
        return f"Open Source: Contributed to {self.repository}"

    def get_activity_description(self):
        desc = f"Repository: {self.repository}.\nDetails: {self.contribution}\n"
        if self.pull_request:
            desc += f"PR: {self.pull_request}\n"
        if self.issue:
            desc += f"Issue: {self.issue}\n"
        if self.learning:
            desc += f"Learning: {self.learning}"
        return desc

    def get_activity_category(self):
        return Activity.Category.PROJECT

    def get_activity_type(self):
        return Activity.ActivityType.OPEN_SOURCE

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.status = Activity.Status.COMPLETED
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# LearningGoal
# ─────────────────────────────────────────────────────────────────────────────

class LearningGoal(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='learning_goals')
    title = models.CharField(max_length=255, verbose_name="Goal Description")
    priority = models.CharField(max_length=50, choices=Priority.choices, default=Priority.MEDIUM, verbose_name="Priority")
    target_date = models.DateField(verbose_name="Target Completion Date")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING, verbose_name="Goal Status")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-target_date']

    def __str__(self):
        return f"Goal: {self.title} — {self.student.name}"


# ─────────────────────────────────────────────────────────────────────────────
# DeveloperAchievement
# ─────────────────────────────────────────────────────────────────────────────

class DeveloperAchievement(models.Model):
    class Category(models.TextChoices):
        HACKATHON = 'HACKATHON', 'Hackathon'
        RESEARCH_PAPER = 'RESEARCH_PAPER', 'Research Paper'
        AWARD = 'AWARD', 'Award'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        COMPETITION = 'COMPETITION', 'Competition'
        VOLUNTEER = 'VOLUNTEER', 'Volunteer Work'
        TECH_CLUB = 'TECH_CLUB', 'Technical Club'
        OTHER = 'OTHER', 'Other Achievement'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='journey_achievements')
    title = models.CharField(max_length=255, verbose_name="Achievement Title")
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.AWARD, verbose_name="Category")
    date = models.DateField(verbose_name="Date Achieved")
    description = models.TextField(verbose_name="Description / Details")
    certificate = models.FileField(upload_to='achievement_certs/', blank=True, null=True, verbose_name="Certificate File")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()}) — {self.student.name}"

    def get_activity_title(self):
        return f"Achievement: Earned '{self.title}'"

    def get_activity_description(self):
        return f"Category: {self.get_category_display()}.\n{self.description}"

    def get_activity_category(self):
        return Activity.Category.COMPETITION

    def get_activity_type(self):
        return Activity.ActivityType.ACHIEVEMENT

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ct = ContentType.objects.get_for_model(self)
        activity, created = Activity.objects.get_or_create(
            content_type=ct,
            object_id=self.pk,
            defaults={'student': self.student, 'date': self.date}
        )
        activity.title = self.get_activity_title()
        activity.description = self.get_activity_description()
        activity.date = self.date
        activity.category = self.get_activity_category()
        activity.activity_type = self.get_activity_type()
        activity.status = Activity.Status.COMPLETED
        if self.certificate:
            activity.attachment = self.certificate
        activity.save()

    def delete(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self)
        Activity.objects.filter(content_type=ct, object_id=self.pk).delete()
        super().delete(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Certificate Model
# ─────────────────────────────────────────────────────────────────────────────

class Certificate(models.Model):
    class Purpose(models.TextChoices):
        COURSE_COMPLETION = 'COURSE_COMPLETION', 'Course Completion'
        HACKATHON = 'HACKATHON', 'Hackathon'
        WORKSHOP = 'WORKSHOP', 'Workshop'
        SEMINAR = 'SEMINAR', 'Seminar'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        COMPETITION = 'COMPETITION', 'Competition'
        RESEARCH = 'RESEARCH', 'Research'
        BOOTCAMP = 'BOOTCAMP', 'Bootcamp'
        TRAINING_PROGRAM = 'TRAINING_PROGRAM', 'Training Program'
        CERTIFICATION_EXAM = 'CERTIFICATION_EXAM', 'Certification Exam'
        VOLUNTEER_PROGRAM = 'VOLUNTEER_PROGRAM', 'Volunteer Program'
        LEADERSHIP_PROGRAM = 'LEADERSHIP_PROGRAM', 'Leadership Program'
        COLLEGE_EVENT = 'COLLEGE_EVENT', 'College Event'
        OTHER = 'OTHER', 'Other'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255)
    purpose = models.CharField(max_length=50, choices=Purpose.choices, default=Purpose.COURSE_COMPLETION)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. Web Development, Cloud, AI/ML")
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    certificate_url = models.URLField(blank=True, null=True, verbose_name="Credential URL")
    certificate_file = models.FileField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"{self.title} — {self.student.name}"


# ─────────────────────────────────────────────────────────────────────────────
# SemesterPerformance Model
# ─────────────────────────────────────────────────────────────────────────────

class SemesterPerformance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_performances')
    semester = models.PositiveSmallIntegerField(help_text="e.g. 1 to 8")
    spi = models.DecimalField(max_digits=4, decimal_places=2, help_text="Semester Performance Index (SPI/SGPA)")
    status = models.CharField(max_length=20, default="Completed", choices=[
        ("Completed", "Completed"),
        ("Current", "Current"),
        ("Upcoming", "Upcoming")
    ])

    class Meta:
        ordering = ['semester']
        constraints = [
            models.UniqueConstraint(fields=['student', 'semester'], name='unique_student_semester_performance')
        ]

    def __str__(self):
        return f"Sem {self.semester}: {self.spi} ({self.status}) — {self.student.name}"


