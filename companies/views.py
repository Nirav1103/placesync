from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.db.models import Q

from .models import Company
from .forms import CompanyForm, CompanyVerificationForm

class CompanyListView(LoginRequiredMixin, View):
    template_name = 'companies/company_list.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        companies = Company.objects.filter(college=college)

        # Filters
        q = request.GET.get('q', '').strip()
        job_mode_filter = request.GET.get('job_mode', '').strip()
        min_pkg_filter = request.GET.get('min_package', '').strip()
        min_stipend_filter = request.GET.get('min_stipend', '').strip()

        if q:
            companies = companies.filter(
                Q(name__icontains=q) |
                Q(industry__icontains=q) |
                Q(location__icontains=q)
            )
        if job_mode_filter:
            companies = companies.filter(job_mode=job_mode_filter)
        if min_pkg_filter:
            try:
                min_pkg = float(min_pkg_filter)
                companies = companies.filter(package_amount__gte=min_pkg)
            except ValueError:
                pass
        if min_stipend_filter:
            try:
                min_stipend = float(min_stipend_filter)
                companies = companies.filter(stipend_amount__gte=min_stipend)
            except ValueError:
                pass

        companies = companies.order_by('name')
        job_modes = Company.JobMode.choices

        context = {
            'companies': companies,
            'job_modes': job_modes,
            'selected_mode': job_mode_filter,
            'selected_pkg': min_pkg_filter,
            'selected_stipend': min_stipend_filter,
            'q': q
        }
        return render(request, self.template_name, context)

class CompanyCreateView(LoginRequiredMixin, View):
    template_name = 'companies/company_form.html'
    form_class = CompanyForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(college=request.user.college)
        return render(request, self.template_name, {'form': form, 'action': 'Add'})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES, college=request.user.college)
        if form.is_valid():
            company = form.save(commit=False)
            company.college = request.user.college
            company.save()
            messages.success(request, f"Company '{company.name}' has been added successfully.")
            return redirect('companies:list')
        return render(request, self.template_name, {'form': form, 'action': 'Add'})

class CompanyUpdateView(LoginRequiredMixin, View):
    template_name = 'companies/company_form.html'
    form_class = CompanyForm

    def get(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        form = self.form_class(instance=company, college=request.user.college)
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'company': company})

    def post(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, request.FILES, instance=company, college=request.user.college)
        if form.is_valid():
            form.save()
            messages.success(request, f"Company '{company.name}' details have been updated.")
            return redirect('companies:list')
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'company': company})

class CompanyDetailView(LoginRequiredMixin, View):
    template_name = 'companies/company_detail.html'

    def get(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        return render(request, self.template_name, {'company': company})

class CompanyDeleteView(LoginRequiredMixin, View):
    template_name = 'companies/company_confirm_delete.html'

    def get(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        return render(request, self.template_name, {'company': company})

    def post(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        name = company.name
        company.delete()
        messages.success(request, f"Company '{name}' has been deleted successfully.")
        return redirect('companies:list')

class CompanyVerificationDashboardView(LoginRequiredMixin, View):
    template_name = 'companies/verification_dashboard.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        companies = Company.objects.filter(college=college)

        # Statistics
        total_count = companies.count()
        verified_count = companies.filter(verification_status='VERIFIED').count()
        pending_count = companies.filter(verification_status='PENDING').count()
        rejected_count = companies.filter(verification_status='REJECTED').count()

        # Status filter
        status_filter = request.GET.get('status', '').strip()
        if status_filter:
            companies = companies.filter(verification_status=status_filter)

        companies = companies.order_by('name')

        context = {
            'companies': companies,
            'total_count': total_count,
            'verified_count': verified_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'selected_status': status_filter
        }
        return render(request, self.template_name, context)

class CompanyVerificationAuditView(LoginRequiredMixin, View):
    template_name = 'companies/verify_audit.html'
    form_class = CompanyVerificationForm

    def get(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        form = self.form_class(instance=company)
        return render(request, self.template_name, {'form': form, 'company': company})

    def post(self, request, pk, *args, **kwargs):
        company = get_object_or_404(Company, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f"Verification audit for '{company.name}' saved. Calculated Trust Score: {company.trust_score}%")
            return redirect('companies:verification_dashboard')
        return render(request, self.template_name, {'form': form, 'company': company})
