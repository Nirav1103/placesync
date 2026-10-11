from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.db.models import Avg, Max, Min, Count

from students.models import Student
from companies.models import Company
from batches.models import Batch
from departments.models import Department
from placements.models import PlacementDrive, Application

from .chart_generator import (
    generate_status_pie_chart,
    generate_dept_bar_chart,
    generate_batch_line_chart,
    generate_student_scatter_plot,
    generate_company_bar_chart
)

from decimal import Decimal

class AnalyticsDashboardView(LoginRequiredMixin, View):
    template_name = 'analytics/dashboard.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404()

        students = Student.objects.filter(college=college)
        total_students = students.count()
        
        # 1. Core KPIs
        placed_only = students.filter(placement_status=Student.PlacementStatus.PLACED).count()
        intern_only = students.filter(placement_status=Student.PlacementStatus.INTERN).count()
        both_status = students.filter(placement_status=Student.PlacementStatus.PLACED_AND_INTERN).count()
        unplaced = students.filter(placement_status=Student.PlacementStatus.UNPLACED).count()
        
        placed_total = placed_only + both_status
        intern_total = intern_only + both_status
        
        placement_pct = (placed_total / total_students * 100) if total_students > 0 else 0
        internship_pct = (intern_total / total_students * 100) if total_students > 0 else 0

        # Packages (Job drives outcomes)
        job_drives = PlacementDrive.objects.filter(college=college, drive_type='JOB')
        highest_pkg = job_drives.aggregate(Max('package_amount'))['package_amount__max'] or 0.00
        avg_pkg = job_drives.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.00
        
        # Stipends (Internship drives outcomes)
        intern_drives = PlacementDrive.objects.filter(college=college, drive_type='INTERNSHIP')
        highest_stipend = intern_drives.aggregate(Max('package_amount'))['package_amount__max'] or 0.00
        avg_stipend = intern_drives.aggregate(Avg('package_amount'))['package_amount__avg'] or 0.00

        # KPI Metrics list
        kpis = {
            'placement_pct': f"{placement_pct:.1f}%",
            'internship_pct': f"{internship_pct:.1f}%",
            'highest_pkg': f"{highest_pkg:.2f} LPA",
            'avg_pkg': f"{avg_pkg:.2f} LPA",
            'highest_stipend': f"{highest_stipend:,.0f} /mo" if highest_stipend > 0 else "0 /mo",
            'avg_stipend': f"{avg_stipend:,.0f} /mo" if avg_stipend > 0 else "0 /mo"
        }

        # 2. Status Distribution Pie Chart (Base64)
        status_chart = generate_status_pie_chart(placed_only, intern_only, both_status, unplaced)

        # 3. Department Analytics Data & Chart
        departments = Department.objects.filter(college=college)
        dept_names = []
        dept_avg_packages = []
        dept_ratios = []
        
        for dept in departments:
            d_students = dept.students.all()
            d_total = d_students.count()
            d_placed = d_students.filter(placement_status__in=[Student.PlacementStatus.PLACED, Student.PlacementStatus.PLACED_AND_INTERN]).count()
            d_ratio = (d_placed / d_total * 100) if d_total > 0 else 0
            
            d_avg_pkg = dept.students.filter(
                placement_status__in=[Student.PlacementStatus.PLACED, Student.PlacementStatus.PLACED_AND_INTERN]
            ).aggregate(Avg('package_amount'))['package_amount__avg'] or 0.00
            
            dept_names.append(dept.code)
            dept_avg_packages.append(float(d_avg_pkg))
            dept_ratios.append(float(d_ratio))

        dept_chart = generate_dept_bar_chart(dept_names, dept_avg_packages, dept_ratios)

        # 4. Batch Analytics Data & Chart
        batches = Batch.objects.filter(department__college=college).order_by('graduation_year', 'name')
        batch_names = []
        batch_ratios = []
        for batch in batches:
            b_students = batch.students.all()
            b_total = b_students.count()
            b_placed = b_students.filter(placement_status__in=[Student.PlacementStatus.PLACED, Student.PlacementStatus.PLACED_AND_INTERN]).count()
            b_ratio = (b_placed / b_total * 100) if b_total > 0 else 0
            
            batch_names.append(batch.name)
            batch_ratios.append(float(b_ratio))

        batch_chart = generate_batch_line_chart(batch_names, batch_ratios)

        # 5. Student Analytics Data (CGPA vs Package Correlation Scatter)
        placed_students_with_pkg = students.filter(
            placement_status__in=[Student.PlacementStatus.PLACED, Student.PlacementStatus.PLACED_AND_INTERN],
            cgpa__isnull=False,
            package_amount__isnull=False
        )
        cgpas = [float(s.cgpa) for s in placed_students_with_pkg]
        packages = [float(s.package_amount) for s in placed_students_with_pkg]
        student_chart = generate_student_scatter_plot(cgpas, packages)

        # 6. Company Analytics Data (Top hiring companies bar chart)
        companies = Company.objects.filter(college=college)
        company_names = []
        hires_counts = []
        for c in companies:
            selections = Application.objects.filter(drive__company=c, status='SELECTED').count()
            if selections > 0:
                company_names.append(c.name)
                hires_counts.append(selections)

        # Sort companies by hires descending
        company_data = sorted(zip(company_names, hires_counts), key=lambda x: x[1], reverse=True)[:5]
        if company_data:
            c_names, c_hires = zip(*company_data)
        else:
            c_names, c_hires = [], []
            
        company_chart = generate_company_bar_chart(list(c_names), list(c_hires))

        context = {
            'kpis': kpis,
            'status_chart': status_chart,
            'dept_chart': dept_chart,
            'batch_chart': batch_chart,
            'student_chart': student_chart,
            'company_chart': company_chart,
            'dept_data': list(zip(dept_names, dept_avg_packages, dept_ratios)),
            'batch_data': list(zip(batch_names, batch_ratios)),
            'company_data': list(zip(c_names, c_hires))
        }
        return render(request, self.template_name, context)
