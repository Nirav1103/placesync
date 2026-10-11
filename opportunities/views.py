from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.db.models import Q
from django.urls import reverse

from .models import ScrapedOpportunity
from .forms import ScrapedOpportunityForm, ScrapeUrlForm
from .scraper import scrape_career_opportunities

from companies.models import Company
from placements.models import PlacementDrive
from placements.forms import PlacementDriveForm

import re

class OpportunityListView(LoginRequiredMixin, View):
    template_name = 'opportunities/opportunity_list.html'

    def get(self, request, *args, **kwargs):
        college = request.user.college
        if not college:
            raise Http404("No college associated with your account.")

        opportunities = ScrapedOpportunity.objects.filter(college=college)

        # Apply search and filters
        q = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip()

        if q:
            opportunities = opportunities.filter(
                Q(company_name__icontains=q) |
                Q(role__icontains=q) |
                Q(location__icontains=q)
            )
        if status_filter:
            opportunities = opportunities.filter(verification_status=status_filter)
        else:
            # By default show PENDING and VERIFIED, hide IGNORED unless explicitly filtered
            opportunities = opportunities.exclude(verification_status=ScrapedOpportunity.VerificationStatus.IGNORED)

        opportunities = opportunities.order_by('-trust_score', '-created_at')

        # Prefill mock URL helper for easier local testing
        absolute_mock_url = request.build_absolute_uri(reverse('opportunities:mock_career_page'))
        scrape_form = ScrapeUrlForm(initial={'url': absolute_mock_url})

        context = {
            'opportunities': opportunities,
            'scrape_form': scrape_form,
            'statuses': ScrapedOpportunity.VerificationStatus.choices,
            'selected_status': status_filter,
            'q': q,
            'absolute_mock_url': absolute_mock_url
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        college = request.user.college
        scrape_form = ScrapeUrlForm(request.POST)
        
        if scrape_form.is_valid():
            url = scrape_form.cleaned_data['url']
            
            # Scrape openings
            postings = scrape_career_opportunities(url)
            
            if not postings:
                messages.error(request, f"No opportunities discovered from URL. Please check layout or accessibility.")
                return redirect('opportunities:list')
                
            new_count = 0
            for item in postings:
                # Check duplicate case-insensitively within college by company and role
                exists = ScrapedOpportunity.objects.filter(
                    college=college,
                    company_name__iexact=item['company_name'],
                    role__iexact=item['role']
                ).exists()
                
                if not exists:
                    ScrapedOpportunity.objects.create(
                        college=college,
                        company_name=item['company_name'],
                        role=item['role'],
                        package=item['package'],
                        location=item['location'],
                        deadline=item['deadline'],
                        source=item['source']
                    )
                    new_count += 1
                    
            messages.success(request, f"Scraping run completed successfully! Discovered {len(postings)} jobs ({new_count} new).")
        else:
            messages.error(request, "Invalid career page URL format.")
            
        return redirect('opportunities:list')

class OpportunityVerifyView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        opp.verification_status = ScrapedOpportunity.VerificationStatus.VERIFIED
        opp.save()
        messages.success(request, f"Opportunity '{opp.role}' at {opp.company_name} has been verified.")
        return redirect('opportunities:list')

class OpportunityIgnoreView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        opp.verification_status = ScrapedOpportunity.VerificationStatus.IGNORED
        opp.save()
        messages.info(request, f"Opportunity '{opp.role}' at {opp.company_name} is ignored.")
        return redirect('opportunities:list')

class OpportunityEditView(LoginRequiredMixin, View):
    template_name = 'opportunities/opportunity_form.html'
    form_class = ScrapedOpportunityForm

    def get(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        form = self.form_class(instance=opp)
        return render(request, self.template_name, {'form': form, 'opportunity': opp})

    def post(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, instance=opp)
        if form.is_valid():
            opp = form.save()
            messages.success(request, f"Opportunity details saved. Calculated Trust Score: {opp.trust_score}%")
            return redirect('opportunities:list')
        return render(request, self.template_name, {'form': form, 'opportunity': opp})

class OpportunityImportCompanyView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        
        # Import to Company directory
        company, created = Company.objects.get_or_create(
            college=request.user.college,
            name=opp.company_name,
            defaults={
                'location': opp.location,
                'website': opp.source if opp.source.startswith('http') else ''
            }
        )
        
        # Try updating package amount if empty
        if opp.package and not company.package_amount:
            matches = re.findall(r'\d+\.?\d*', opp.package)
            if matches:
                try:
                    company.package_amount = float(matches[0])
                    company.save()
                except ValueError:
                    pass

        if created:
            messages.success(request, f"Company '{company.name}' successfully imported to your directory.")
        else:
            messages.info(request, f"Company '{company.name}' is already in your directory.")
            
        return redirect('opportunities:list')

class OpportunityCreateDriveView(LoginRequiredMixin, View):
    template_name = 'opportunities/drive_form.html'
    form_class = PlacementDriveForm

    def get(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        
        # Ensure company is imported first
        company, _ = Company.objects.get_or_create(
            college=request.user.college,
            name=opp.company_name,
            defaults={
                'location': opp.location,
                'website': opp.source if opp.source.startswith('http') else ''
            }
        )
        
        # Parse package details
        package_val = None
        if opp.package:
            matches = re.findall(r'\d+\.?\d*', opp.package)
            if matches:
                try:
                    package_val = float(matches[0])
                except ValueError:
                    pass
                    
        # Parse deadline details if format is YYYY-MM-DD
        deadline_date = None
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', opp.deadline)
        if date_match:
            deadline_date = date_match.group(0)

        form = self.form_class(
            college=request.user.college,
            initial={
                'company': company,
                'role': opp.role,
                'package_amount': package_val,
                'deadline': deadline_date
            }
        )
        return render(request, self.template_name, {'form': form, 'opportunity': opp})

    def post(self, request, pk, *args, **kwargs):
        opp = get_object_or_404(ScrapedOpportunity, pk=pk, college=request.user.college)
        form = self.form_class(request.POST, college=request.user.college)
        if form.is_valid():
            drive = form.save(commit=False)
            drive.college = request.user.college
            drive.save()
            
            # Auto verify the opportunity once a drive is generated
            opp.verification_status = ScrapedOpportunity.VerificationStatus.VERIFIED
            opp.save()
            
            messages.success(request, f"Placement Drive for '{drive.role}' at {drive.company.name} created successfully!")
            return redirect('placements:list')
            
        return render(request, self.template_name, {'form': form, 'opportunity': opp})

class MockCareerPageView(View):
    """
    Returns a static HTML mockup representing a career board.
    This enables 100% reliable local scraping.
    """
    def get(self, request, *args, **kwargs):
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Mock Career Openings</title>
            <style>
                body { font-family: sans-serif; padding: 2rem; background: #fafafa; }
                .job-container { max-width: 800px; margin: 0 auto; }
                .job-card { background: #fff; border: 1px solid #ddd; padding: 1.5rem; margin-bottom: 1rem; border-radius: 6px; }
                .job-title { margin-top: 0; color: #1e3a8a; }
                .job-meta { display: flex; gap: 1rem; font-size: 0.9rem; color: #555; }
            </style>
        </head>
        <body>
            <div class="job-container">
                <h1>Public Careers Board</h1>
                <p>Latest active job opportunities:</p>
                
                <div class="job-card">
                    <h2 class="job-title"><a href="https://careers.google.com/jobs/1">Backend Developer (Python/Go)</a></h2>
                    <div class="job-meta">
                        <span class="job-company">Google</span>
                        <span class="job-location">Bangalore, India</span>
                        <span class="job-salary">24.5 LPA</span>
                        <span class="job-deadline">Apply by: 2026-12-31</span>
                    </div>
                </div>
                
                <div class="job-card">
                    <h2 class="job-title"><a href="https://careers.microsoft.com/jobs/2">Cloud consultant Specialist</a></h2>
                    <div class="job-meta">
                        <span class="job-company">Microsoft</span>
                        <span class="job-location">Hyderabad, India</span>
                        <span class="job-salary">18.0 LPA</span>
                        <span class="job-deadline">Apply by: 2026-10-15</span>
                    </div>
                </div>
                
                <div class="job-card">
                    <h2 class="job-title"><a href="https://careers.amazon.com/jobs/3">Operations Analyst Associate</a></h2>
                    <div class="job-meta">
                        <span class="job-company">Amazon</span>
                        <span class="job-location">Pune, India</span>
                        <span class="job-salary">14.0 LPA</span>
                        <span class="job-deadline">Apply by: 2026-09-30</span>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content, content_type='text/html')
