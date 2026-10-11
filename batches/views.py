from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Avg
from django.http import Http404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import pandas as pd
import re

from .models import Batch
from .forms import BatchForm
from students.models import Student

User = get_user_model()

class BatchListView(LoginRequiredMixin, View):
    template_name = 'batches/batch_list.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        # Scoped to college departments
        batches = Batch.objects.filter(department__college=college).order_by('-graduation_year', 'name')

        # Search query logic
        q = request.GET.get('q', '').strip()
        if q:
            batches = batches.filter(
                Q(name__icontains=q) | 
                Q(department__name__icontains=q) | 
                Q(department__code__icontains=q)
            )

        return render(request, self.template_name, {
            'batches': batches,
            'q': q
        })


class BatchCreateView(LoginRequiredMixin, View):
    form_class = BatchForm
    template_name = 'batches/batch_form.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(college=request.user.college)
        return render(request, self.template_name, {'form': form, 'action': 'Add'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, college=request.user.college)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Batch '{batch.name}' has been created successfully.")
            return redirect('batches:list')
        return render(request, self.template_name, {'form': form, 'action': 'Add'})


class BatchUpdateView(LoginRequiredMixin, View):
    form_class = BatchForm
    template_name = 'batches/batch_form.html'

    def get(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        form = self.form_class(instance=batch, college=request.user.college)
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'batch': batch})

    def post(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        form = self.form_class(request.POST, instance=batch, college=request.user.college)
        if form.is_valid():
            form.save()
            messages.success(request, f"Batch '{batch.name}' details have been updated.")
            return redirect('batches:list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'batch': batch})


class BatchDeleteView(LoginRequiredMixin, View):
    template_name = 'batches/batch_confirm_delete.html'

    def get(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        return render(request, self.template_name, {'batch': batch})

    def post(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        name = batch.name
        batch.delete()
        messages.success(request, f"Batch '{name}' has been deleted successfully.")
        return redirect('batches:list')


class BatchDashboardView(LoginRequiredMixin, View):
    template_name = 'batches/batch_dashboard.html'

    def get(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        
        # All students in this batch
        all_students = batch.students.all()
        
        # Calculate statistics
        total_students = all_students.count()
        
        # Placed status includes PLACED and PLACED_AND_INTERN
        placed_students = all_students.filter(
            placement_status__in=['PLACED', 'PLACED_AND_INTERN']
        ).count()
        
        # Internship status includes INTERN and PLACED_AND_INTERN
        internship_students = all_students.filter(
            placement_status__in=['INTERN', 'PLACED_AND_INTERN']
        ).count()
        
        placement_pct = (placed_students / total_students * 100) if total_students > 0 else 0.0
        
        # package & stipend aggregation calculations
        placed_qs = all_students.filter(placement_status__in=['PLACED', 'PLACED_AND_INTERN'])
        highest_pkg = placed_qs.aggregate(Max('package_amount'))['package_amount__max'] or 0.0
        avg_pkg = placed_qs.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.0
        
        intern_qs = all_students.filter(placement_status__in=['INTERN', 'PLACED_AND_INTERN'])
        highest_stipend = intern_qs.aggregate(Max('stipend_amount'))['stipend_amount__max'] or 0.0
        avg_stipend = intern_qs.aggregate(Avg('stipend_amount'))['stipend_amount__avg'] or 0.0

        stats = {
            'total_students': total_students,
            'placed_students': placed_students,
            'internship_students': internship_students,
            'placement_percentage': round(placement_pct, 1),
            'highest_package': round(highest_pkg, 2),
            'average_package': round(avg_pkg, 2),
            'highest_stipend': round(highest_stipend, 2),
            'average_stipend': round(avg_stipend, 2),
        }

        # Handle student search filtering inside list
        students = all_students
        q = request.GET.get('q', '').strip()
        if q:
            students = students.filter(
                Q(name__icontains=q) | 
                Q(roll_number__icontains=q) | 
                Q(placement_status__icontains=q)
            )

        context = {
            'batch': batch,
            'stats': stats,
            'students': students,
            'q': q
        }
        return render(request, self.template_name, context)


class BatchStudentImportView(LoginRequiredMixin, View):
    template_name = 'batches/student_import.html'

    def get(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        return render(request, self.template_name, {'batch': batch})

    def post(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        default_password = request.POST.get('default_password', '').strip()
        csv_file = request.FILES.get('csv_file')

        errors = []

        if not default_password:
            errors.append("Default password is required.")
        if len(default_password) < 6:
            errors.append("Default password must be at least 6 characters long.")
        if not csv_file:
            errors.append("Please upload a CSV file.")

        if errors:
            return render(request, self.template_name, {'batch': batch, 'errors': errors})

        try:
            # Parse using Pandas
            df = pd.read_csv(csv_file, dtype=str)
            
            # Clean headers: lowercase and stripped
            df.columns = [str(c).strip() for c in df.columns]
            
            # Map canonical column names to CSV columns dynamically
            header_map = {}
            for col in df.columns:
                c = str(col).strip().lower().replace(' ', '_').replace('current_', '').replace('graduation_', 'passing_')
                if c in ['enrollment_number', 'roll_number', 'enrollmentno', 'username']:
                    header_map['roll_number'] = col
                elif c in ['student_name', 'name', 'fullname']:
                    header_map['name'] = col
                elif c in ['email', 'email_address']:
                    header_map['email'] = col
                elif c in ['phone', 'phone_number', 'contact']:
                    header_map['phone'] = col
                elif c in ['department', 'dept']:
                    header_map['department'] = col
                elif c in ['semester', 'sem']:
                    header_map['semester'] = col
                elif c in ['division', 'div']:
                    header_map['division'] = col
                elif c in ['spi']:
                    header_map['spi'] = col
                elif c in ['cpi']:
                    header_map['cpi'] = col
                elif c in ['cgpa']:
                    header_map['cgpa'] = col
                elif c in ['backlogs', 'backlog', 'active_backlogs']:
                    header_map['backlogs'] = col
                elif c in ['passing_year', 'year']:
                    header_map['passing_year'] = col

            # Check required columns
            missing_cols = []
            if 'roll_number' not in header_map:
                missing_cols.append("Enrollment Number")
            if 'name' not in header_map:
                missing_cols.append("Student Name")
            if 'email' not in header_map:
                missing_cols.append("Email")

            if missing_cols:
                errors.append(f"CSV is missing required columns: {', '.join(missing_cols)}.")
                return render(request, self.template_name, {'batch': batch, 'errors': errors})

            # Clean dataframe: fill nan with empty and convert all to string
            df = df.fillna('').astype(str)
            for c in df.columns:
                df[c] = df[c].str.strip()

            valid_students = []
            failed_students = []
            duplicate_students = []

            rolls_seen = set()
            emails_seen = set()

            for idx, row in df.iterrows():
                row_num = idx + 2 # 1-based index + header row = idx + 2
                
                # Fetch row fields dynamically based on header mapping
                roll = row[header_map['roll_number']].strip()
                name = row[header_map['name']].strip()
                email = row[header_map['email']].strip()
                
                phone = row[header_map['phone']].strip() if 'phone' in header_map else ''
                dept_val = row[header_map['department']].strip() if 'department' in header_map else ''
                sem_val = row[header_map['semester']].strip() if 'semester' in header_map else ''
                div_val = row[header_map['division']].strip() if 'division' in header_map else ''
                spi_val = row[header_map['spi']].strip() if 'spi' in header_map else ''
                cpi_val = row[header_map['cpi']].strip() if 'cpi' in header_map else ''
                cgpa_val = row[header_map['cgpa']].strip() if 'cgpa' in header_map else ''
                backlog_val = row[header_map['backlogs']].strip() if 'backlogs' in header_map else ''
                passing_val = row[header_map['passing_year']].strip() if 'passing_year' in header_map else ''

                # Skip completely empty rows
                if not any([roll, name, email]):
                    continue

                row_errors = []
                if not roll:
                    row_errors.append("Roll Number is empty.")
                if not name:
                    row_errors.append("Student Name is empty.")
                if not email:
                    row_errors.append("Email Address is empty.")
                else:
                    try:
                        validate_email(email)
                    except ValidationError:
                        row_errors.append(f"Email '{email}' is invalid.")

                # Parse and validate numbers / decimals
                def parse_decimal(val, name_label):
                    if not val:
                        return None, None
                    try:
                        return float(val), None
                    except ValueError:
                        return None, f"Invalid {name_label} value '{val}'"

                def parse_int(val, name_label):
                    if not val:
                        return None, None
                    try:
                        return int(val), None
                    except ValueError:
                        return None, f"Invalid {name_label} value '{val}'"

                spi_num, err = parse_decimal(spi_val, "SPI")
                if err: row_errors.append(err)
                
                cpi_num, err = parse_decimal(cpi_val, "CPI")
                if err: row_errors.append(err)

                cgpa_num, err = parse_decimal(cgpa_val, "CGPA")
                if err: row_errors.append(err)

                backlog_num, err = parse_int(backlog_val, "Backlogs")
                if err: row_errors.append(err)

                sem_num, err = parse_int(sem_val, "Semester")
                if err: row_errors.append(err)

                passing_num, err = parse_int(passing_val, "Passing Year")
                if err: row_errors.append(err)

                # Validation failure?
                if row_errors:
                    failed_students.append({
                        'row_num': row_num,
                        'roll_number': roll or '—',
                        'name': name or '—',
                        'email': email or '—',
                        'errors': ', '.join(row_errors)
                    })
                    continue

                # Check duplicates in CSV itself
                roll_lower = roll.lower() if roll else ''
                email_lower = email.lower() if email else ''
                is_duplicate = False

                if roll_lower:
                    if roll_lower in rolls_seen:
                        duplicate_students.append({
                            'row_num': row_num,
                            'roll_number': roll,
                            'name': name,
                            'email': email,
                            'reason': f"Duplicate Roll Number '{roll}' within CSV."
                        })
                        is_duplicate = True
                    else:
                        rolls_seen.add(roll_lower)

                if email_lower:
                    if email_lower in emails_seen:
                        if not is_duplicate:
                            duplicate_students.append({
                                'row_num': row_num,
                                'roll_number': roll,
                                'name': name,
                                'email': email,
                                'reason': f"Duplicate Email '{email}' within CSV."
                            })
                            is_duplicate = True
                    else:
                        emails_seen.add(email_lower)

                if is_duplicate:
                    continue

                # Check database existence check
                db_dup_reason = []
                if roll:
                    if Student.objects.filter(college=request.user.college, roll_number__iexact=roll).exists():
                        db_dup_reason.append(f"Roll Number '{roll}' is already registered in your college.")
                    if User.objects.filter(username__iexact=roll).exists():
                        db_dup_reason.append(f"Roll Number (Username) '{roll}' is already registered in the system.")
                if email:
                    if User.objects.filter(email__iexact=email).exists():
                        db_dup_reason.append(f"Email '{email}' is already registered in the system.")

                if db_dup_reason:
                    duplicate_students.append({
                        'row_num': row_num,
                        'roll_number': roll,
                        'name': name,
                        'email': email,
                        'reason': ', '.join(db_dup_reason)
                    })
                    continue

                # Clean parsed records
                valid_students.append({
                    'roll_number': roll,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'semester': sem_num or batch.semester or 1,
                    'division': div_val or '',
                    'spi': spi_num,
                    'cpi': cpi_num,
                    'cgpa': cgpa_num,
                    'backlogs': backlog_num or 0,
                    'passing_year': passing_num or batch.graduation_year or 2027
                })

            # If any validation errors or duplicate conflicts exist, block import at this stage
            if failed_students or duplicate_students:
                errors = []
                for f in failed_students:
                    errors.append(f"Row {f['row_num']}: {f['errors']}")
                for d in duplicate_students:
                    errors.append(f"Row {d.get('row_num', '—')}: {d['reason']}")
                return render(request, self.template_name, {'batch': batch, 'errors': errors[:50]})

            # Save arrays to session (using canonical keys for test compatibility)
            request.session['import_preview_data'] = valid_students
            request.session['import_failed_data'] = failed_students
            request.session['import_duplicate_data'] = duplicate_students
            request.session['import_default_password'] = default_password

            return redirect('batches:import_preview', pk=batch.pk)

        except Exception as e:
            errors.append(f"Failed to parse CSV file: {str(e)}")
            return render(request, self.template_name, {'batch': batch, 'errors': errors})


class BatchStudentImportPreviewView(LoginRequiredMixin, View):
    template_name = 'batches/student_import_preview.html'

    def get(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        valid_records = request.session.get('import_preview_data', [])
        failed_records = request.session.get('import_failed_data', [])
        duplicate_records = request.session.get('import_duplicate_data', [])
        default_password = request.session.get('import_default_password')

        if default_password is None:
            messages.error(request, "No import session found. Please upload CSV first.")
            return redirect('batches:import_students', pk=batch.pk)

        return render(request, self.template_name, {
            'batch': batch,
            'valid_records': valid_records,
            'failed_records': failed_records,
            'duplicate_records': duplicate_records,
            'default_password': default_password
        })

    def post(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        records = request.session.get('import_preview_data', [])
        default_password = request.session.get('import_default_password')

        if default_password is None:
            messages.error(request, "Import session expired or invalid. Please re-upload.")
            return redirect('batches:import_students', pk=batch.pk)

        college = request.user.college
        imported_list = []

        try:
            with transaction.atomic():
                for row in records:
                    roll = row['roll_number'].strip()
                    name = row['name'].strip()
                    email = row['email'].strip()
                    phone = row.get('phone', '').strip()

                    # 1. Create custom User account
                    user = User.objects.create_user(
                        username=roll, # Enrollment Number as username
                        email=email,
                        password=default_password,
                        role=User.Role.STUDENT,
                        college=college
                    )
                    user.must_change_password = True
                    user.save()

                    # 2. Create Student Profile
                    Student.objects.create(
                        user=user,
                        college=college,
                        department=batch.department,
                        batch=batch,
                        roll_number=roll,
                        name=name,
                        email=email,
                        phone=phone,
                        semester=row.get('semester', 1),
                        division=row.get('division', ''),
                        spi=row.get('spi'),
                        cpi=row.get('cpi'),
                        cgpa=row.get('cgpa'),
                        backlogs=row.get('backlogs', 0)
                    )
                    
                    imported_list.append({
                        'roll_number': roll,
                        'name': name,
                        'email': email,
                        'phone': phone
                    })

            # Retrieve fails/dups from session and clear temp data
            failed_students = request.session.pop('import_failed_data', [])
            duplicate_students = request.session.pop('import_duplicate_data', [])
            request.session.pop('import_preview_data', None)
            request.session.pop('import_default_password', None)
            
            request.session['import_report'] = {
                'batch_name': batch.name,
                'total_imported': len(imported_list),
                'default_password': default_password,
                'students': imported_list, # For test suite compatibility
                'imported': imported_list,
                'failed': failed_students,
                'duplicates': duplicate_students
            }

            messages.success(request, f"Imported {len(imported_list)} student accounts successfully.")
            return redirect('batches:import_report', pk=batch.pk)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f"Database transaction failed: {str(e)}")
            return redirect('batches:import_preview', pk=batch.pk)


class BatchStudentImportReportView(LoginRequiredMixin, View):
    template_name = 'batches/student_import_report.html'

    def get(self, request, pk, *args, **kwargs):
        batch = get_object_or_404(Batch, pk=pk, department__college=request.user.college)
        report = request.session.pop('import_report', None) # Read once and clear

        if not report:
            messages.error(request, "No import report found or it has already expired.")
            return redirect('batches:dashboard', pk=batch.pk)

        return render(request, self.template_name, {
            'batch': batch,
            'report': report
        })

