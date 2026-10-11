from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from .models import Department
from .forms import DepartmentForm

class DepartmentListView(LoginRequiredMixin, View):
    template_name = 'departments/department_list.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")
        
        departments = college.departments.all().order_by('name')
        
        # Search query logic
        q = request.GET.get('q', '').strip()
        if q:
            departments = departments.filter(
                Q(name__icontains=q) | Q(code__icontains=q) | Q(department_head__icontains=q)
            )
            
        departments_data = []
        for dept in departments:
            total_students = dept.students.count()
            total_batches = dept.batches.count()
            placed_students = dept.students.filter(
                placement_status__in=['PLACED', 'PLACED_AND_INTERN']
            ).count()
            pct = round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0
            departments_data.append({
                'dept': dept,
                'total_students': total_students,
                'total_batches': total_batches,
                'placement_pct': pct
            })

        return render(request, self.template_name, {
            'departments_data': departments_data,
            'q': q
        })


class DepartmentCreateView(LoginRequiredMixin, View):
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(college=request.user.college)
        return render(request, self.template_name, {'form': form, 'action': 'Add'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, college=request.user.college)
        if form.is_valid():
            dept = form.save(commit=False)
            dept.college = request.user.college
            dept.save()
            messages.success(request, f"Department '{dept.name}' has been added successfully.")
            return redirect('departments:list')
        return render(request, self.template_name, {'form': form, 'action': 'Add'})


class DepartmentUpdateView(LoginRequiredMixin, View):
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'

    def get(self, request, pk, *args, **kwargs):
        dept = get_object_or_404(Department, pk=pk, college=request.user.college)
        form = self.form_class(instance=dept, college=request.user.college)
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'department': dept})

    def post(self, request, pk, *args, **kwargs):
        dept = get_object_or_404(Department, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, instance=dept, college=request.user.college)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{dept.name}' details updated successfully.")
            return redirect('departments:list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'department': dept})


class DepartmentDeleteView(LoginRequiredMixin, View):
    template_name = 'departments/department_confirm_delete.html'

    def get(self, request, pk, *args, **kwargs):
        dept = get_object_or_404(Department, pk=pk, college=request.user.college)
        return render(request, self.template_name, {'department': dept})

    def post(self, request, pk, *args, **kwargs):
        dept = get_object_or_404(Department, pk=pk, college=request.user.college)
        name = dept.name
        dept.delete()
        messages.success(request, f"Department '{name}' has been deleted successfully.")
        return redirect('departments:list')
