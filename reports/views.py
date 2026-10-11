from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, FileResponse
from django.db.models import Avg, Max, Min, Count

from students.models import Student
from companies.models import Company
from batches.models import Batch
from placements.models import PlacementDrive, Application
from departments.models import Department

from decimal import Decimal

def compile_report_data(college, report_type):
    """
    Helper function to aggregate data for the 6 report types.
    Returns: dict with title, headers, data rows, and metrics list.
    """
    if report_type == 'placement':
        # Placement summary stats
        students = Student.objects.filter(college=college)
        total_students = students.count()
        placed_students = students.filter(placement_status__in=['PLACED', 'PLACED_AND_INTERN']).count()
        placement_ratio = (placed_students / total_students * 100) if total_students > 0 else 0
        
        job_drives = PlacementDrive.objects.filter(college=college, drive_type='JOB')
        avg_package = job_drives.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.00
        highest_package = job_drives.aggregate(Max('package_amount'))['package_amount__max'] or 0.00

        metrics = [
            {'label': 'Total Registered Students', 'value': str(total_students)},
            {'label': 'Placed Students', 'value': str(placed_students)},
            {'label': 'Placement Ratio', 'value': f"{placement_ratio:.1f}%"},
            {'label': 'Average Package', 'value': f"{avg_package:.2f} LPA"},
            {'label': 'Highest Package', 'value': f"{highest_package:.2f} LPA"}
        ]
        headers = ['Company Name', 'Role Title', 'Package', 'Job Mode', 'Deadline', 'Applicants', 'Selections']
        
        drives = PlacementDrive.objects.filter(college=college).select_related('company').order_by('-created_at')
        data = []
        for d in drives:
            app_count = d.applications.count()
            sel_count = d.applications.filter(status='SELECTED').count()
            data.append([
                d.company.name,
                d.role,
                f"{d.package_amount} LPA" if d.package_amount else '-',
                d.get_job_mode_display(),
                str(d.deadline) if d.deadline else '-',
                str(app_count),
                str(sel_count)
            ])
            
        return {
            'title': 'Overall Placement Report',
            'metrics': metrics,
            'headers': headers,
            'data': data
        }
        
    elif report_type == 'student':
        students = Student.objects.filter(college=college).select_related('department', 'batch').order_by('roll_number')
        total_count = students.count()
        placed_count = students.filter(placement_status__in=['PLACED', 'PLACED_AND_INTERN']).count()
        avg_cgpa = students.aggregate(Avg('cgpa'))['cgpa__avg'] or 0.00
        total_backlogs = students.aggregate(Min('backlogs'))['backlogs__min'] or 0

        metrics = [
            {'label': 'Total Students', 'value': str(total_count)},
            {'label': 'Placed Students', 'value': str(placed_count)},
            {'label': 'Average CGPA', 'value': f"{avg_cgpa:.2f}"}
        ]
        headers = ['Roll Number', 'Student Name', 'Branch', 'Batch Name', 'CGPA', 'Backlogs', 'Placement Status', 'Package']
        
        data = []
        for s in students:
            data.append([
                s.roll_number,
                s.name,
                s.department.code,
                s.batch.name,
                str(s.cgpa) if s.cgpa else '-',
                str(s.backlogs),
                s.get_placement_status_display(),
                f"{s.package_amount} LPA" if s.package_amount else '-'
            ])
            
        return {
            'title': 'Student Directory Placement Report',
            'metrics': metrics,
            'headers': headers,
            'data': data
        }
        
    elif report_type == 'batch':
        batches = Batch.objects.filter(department__college=college).select_related('department').order_by('-graduation_year', 'name')
        total_batches = batches.count()
        students = Student.objects.filter(college=college)
        total_students = students.count()
        placed_students = students.filter(placement_status__in=['PLACED', 'PLACED_AND_INTERN']).count()
        overall_ratio = (placed_students / total_students * 100) if total_students > 0 else 0

        metrics = [
            {'label': 'Total Batches', 'value': str(total_batches)},
            {'label': 'Total Students', 'value': str(total_students)},
            {'label': 'Overall Placement Ratio', 'value': f"{overall_ratio:.1f}%"}
        ]
        headers = ['Batch Name', 'Department', 'Graduation Year', 'Total Students', 'Placed Count', 'Placement Ratio', 'Avg CGPA']
        
        data = []
        for b in batches:
            b_students = b.students.all()
            b_total = b_students.count()
            b_placed = b_students.filter(placement_status__in=['PLACED', 'PLACED_AND_INTERN']).count()
            b_ratio = (b_placed / b_total * 100) if b_total > 0 else 0
            b_cgpa = b_students.aggregate(Avg('cgpa'))['cgpa__avg'] or 0.00
            
            data.append([
                b.name,
                b.department.code,
                str(b.graduation_year),
                str(b_total),
                str(b_placed),
                f"{b_ratio:.1f}%",
                f"{b_cgpa:.2f}"
            ])
            
        return {
            'title': 'Batch-wise Statistics Report',
            'metrics': metrics,
            'headers': headers,
            'data': data
        }
        
    elif report_type == 'company':
        companies = Company.objects.filter(college=college).order_by('name')
        total_companies = companies.count()
        verified_count = companies.filter(verification_status='VERIFIED').count()
        
        drives = PlacementDrive.objects.filter(college=college)
        total_drives = drives.count()

        metrics = [
            {'label': 'Partner Companies', 'value': str(total_companies)},
            {'label': 'Verified Partners', 'value': str(verified_count)},
            {'label': 'Total Drives Conducted', 'value': str(total_drives)}
        ]
        headers = ['Company Name', 'Industry', 'Location', 'Trust Score', 'Status', 'Drives Conducted', 'Selections']
        
        data = []
        for c in companies:
            c_drives = c.placement_drives.all()
            c_drives_count = c_drives.count()
            selections_count = Application.objects.filter(drive__company=c, status='SELECTED').count()
            data.append([
                c.name,
                c.industry or '-',
                c.location or '-',
                f"{c.trust_score}%",
                c.get_verification_status_display(),
                str(c_drives_count),
                str(selections_count)
            ])
            
        return {
            'title': 'Corporate Recruiter Performance Report',
            'metrics': metrics,
            'headers': headers,
            'data': data
        }
        
    elif report_type == 'salary':
        # Salary stats grouped by department
        departments = Department.objects.filter(college=college)
        placed_students_qs = Student.objects.filter(
            college=college, 
            placement_status__in=['PLACED', 'PLACED_AND_INTERN'], 
            package_amount__isnull=False
        )
        
        avg_overall = placed_students_qs.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.00
        max_overall = placed_students_qs.aggregate(Max('package_amount'))['package_amount__max'] or 0.00

        metrics = [
            {'label': 'Overall Avg CTC Package', 'value': f"{avg_overall:.2f} LPA"},
            {'label': 'Highest CTC Offered', 'value': f"{max_overall:.2f} LPA"}
        ]
        headers = ['Department Name', 'Branch Code', 'Hires Count', 'Average CTC (LPA)', 'Highest CTC', 'Lowest CTC']
        
        data = []
        for dept in departments:
            dept_students = placed_students_qs.filter(department=dept)
            d_count = dept_students.count()
            d_avg = dept_students.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.00
            d_max = dept_students.aggregate(Max('package_amount'))['package_amount__max'] or 0.00
            d_min = dept_students.aggregate(Min('package_amount'))['package_amount__min'] or 0.00
            
            data.append([
                dept.name,
                dept.code,
                str(d_count),
                f"{d_avg:.2f}" if d_count > 0 else '0.00',
                f"{d_max:.2f}" if d_count > 0 else '0.00',
                f"{d_min:.2f}" if d_count > 0 else '0.00'
            ])
            
        return {
            'title': 'Departmental Salary Statistics Report',
            'metrics': metrics,
            'headers': headers,
            'data': data
        }
        
    elif report_type == 'internship':
        students = Student.objects.filter(college=college)
        total_students = students.count()
        intern_students = students.filter(placement_status__in=['INTERN', 'PLACED_AND_INTERN']).count()
        internship_ratio = (intern_students / total_students * 100) if total_students > 0 else 0
        
        internship_drives = PlacementDrive.objects.filter(college=college, drive_type='INTERNSHIP')
        total_internships = internship_drives.count()

        metrics = [
            {'label': 'Registered Students', 'value': str(total_students)},
            {'label': 'Internship Hires', 'value': str(intern_students)},
            {'label': 'Internship Ratio', 'value': f"{internship_ratio:.1f}%"},
            {'label': 'Internship Drives', 'value': str(total_internships)}
        ]
        headers = ['Company Name', 'Role Title', 'Stipend Amount', 'Job Mode', 'Applicants', 'Selections']
        
        data = []
        for d in internship_drives.select_related('company').order_by('-created_at'):
            app_count = d.applications.count()
            sel_count = d.applications.filter(status='SELECTED').count()
            data.append([
                d.company.name,
                d.role,
                f"{d.package_amount}/mo" if d.package_amount else '-',
                d.get_job_mode_display(),
                str(app_count),
                str(sel_count)
            ])
            
        return {
            'title': 'Internship Drive Statistics Report',
            'metrics': metrics,
            'headers': headers,
            'data': data
        }
        
    return None

class ReportsDashboardView(LoginRequiredMixin, View):
    template_name = 'reports/dashboard.html'

    def get(self, request, *args, **kwargs):
        if not request.user.college:
            raise Http404()
        return render(request, self.template_name)

class ViewReportView(LoginRequiredMixin, View):
    template_name = 'reports/report_view.html'

    def get(self, request, report_type, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404()
            
        valid_reports = ['placement', 'student', 'batch', 'company', 'salary', 'internship']
        if report_type not in valid_reports:
            raise Http404("Report type invalid.")
            
        report = compile_report_data(college, report_type)
        context = {
            'report_type': report_type,
            'title': report['title'],
            'headers': report['headers'],
            'data': report['data'],
            'metrics': report['metrics']
        }
        return render(request, self.template_name, context)

class ExportReportView(LoginRequiredMixin, View):
    def get(self, request, report_type, export_format, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404()
            
        valid_reports = ['placement', 'student', 'batch', 'company', 'salary', 'internship']
        if report_type not in valid_reports:
            raise Http404("Report type invalid.")
            
        report = compile_report_data(college, report_type)
        if not report:
            raise Http404()

        if export_format == 'csv':
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
            
            writer = csv.writer(response)
            writer.writerow([f"Report: {report['title']}"])
            for m in report['metrics']:
                writer.writerow([m['label'], m['value']])
            writer.writerow([])
            
            writer.writerow(report['headers'])
            for row in report['data']:
                writer.writerow(row)
            return response
            
        elif export_format == 'pdf':
            from io import BytesIO
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            
            buffer = BytesIO()
            # Set margins to 0.5 inch (36pt)
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=18,
                textColor=colors.HexColor('#1e3a8a'),
                spaceAfter=15
            )
            body_style = styles['BodyText']
            
            elements = []
            elements.append(Paragraph(report['title'], title_style))
            
            # Print metrics
            stats_text = "  |  ".join([f"<b>{m['label']}:</b> {m['value']}" for m in report['metrics']])
            elements.append(Paragraph(stats_text, body_style))
            elements.append(Spacer(1, 15))
            
            # Construct Table
            table_data = []
            table_data.append([Paragraph(f"<b>{h}</b>", body_style) for h in report['headers']])
            for row in report['data']:
                row_cells = []
                for cell in row:
                    row_cells.append(Paragraph(str(cell) if cell is not None else '-', body_style))
                table_data.append(row_cells)
                
            t = Table(table_data, colWidths=None)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('TOPPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                ('TOPPADDING', (0,1), (-1,-1), 5),
            ]))
            elements.append(t)
            
            doc.build(elements)
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename=f"{report_type}_report.pdf")
            
        raise Http404("Invalid format.")
