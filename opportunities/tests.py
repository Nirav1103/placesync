from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from colleges.models import College
from companies.models import Company
from placements.models import PlacementDrive
from opportunities.models import ScrapedOpportunity

User = get_user_model()

class OpportunityDiscoveryTestCase(TestCase):
    def setUp(self):
        # Create college
        self.college = College.objects.create(
            name="Test Institute of Technology",
            code="TIT",
            website="https://tit.edu"
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username="tit_admin",
            email="admin@tit.edu",
            password="adminpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college
        )
        
        # Log in admin client
        self.client = Client()
        self.client.login(username="tit_admin", password="adminpassword123")

        self.list_url = reverse('opportunities:list')

    @patch('requests.get')
    def test_scraping_trigger_and_discovery(self, mock_get):
        # Mock requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="job-card">
            <h2 class="job-title"><a href="https://careers.google.com/jobs/1">Software Developer</a></h2>
            <span class="job-company">Google</span>
            <span class="job-location">Bangalore</span>
            <span class="job-salary">24.5 LPA</span>
            <span class="job-deadline">2026-12-31</span>
        </div>
        <div class="job-card">
            <h2 class="job-title"><a href="https://careers.microsoft.com/jobs/2">Cloud Engineer</a></h2>
            <span class="job-company">Microsoft</span>
            <span class="job-location">Hyderabad</span>
            <span class="job-salary">18.0 LPA</span>
            <span class="job-deadline">2026-10-15</span>
        </div>
        """
        mock_get.return_value = mock_response

        # POST to list URL to trigger scraping
        response = self.client.post(self.list_url, {
            'url': 'https://careers.mock.com'
        })
        self.assertRedirects(response, self.list_url)
        
        # Check opportunities created
        self.assertEqual(ScrapedOpportunity.objects.filter(college=self.college).count(), 2)
        
        opp1 = ScrapedOpportunity.objects.get(company_name='Google')
        self.assertEqual(opp1.role, 'Software Developer')
        self.assertEqual(opp1.package, '24.5 LPA')
        self.assertEqual(opp1.location, 'Bangalore')
        self.assertEqual(opp1.deadline, '2026-12-31')
        self.assertEqual(opp1.verification_status, ScrapedOpportunity.VerificationStatus.PENDING)
        # Trust score check: company(20), role(20), location(20), package(15), deadline(15), source(10) = 100
        self.assertEqual(opp1.trust_score, 100)

        # Render list page and check items shown
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Software Developer")
        self.assertContains(list_response, "Cloud Engineer")

    def test_actions_verify_and_ignore(self):
        # Setup one pending opportunity
        opp = ScrapedOpportunity.objects.create(
            college=self.college,
            company_name="Google",
            role="Software Engineer"
        )
        
        verify_url = reverse('opportunities:verify', kwargs={'pk': opp.pk})
        ignore_url = reverse('opportunities:ignore', kwargs={'pk': opp.pk})

        # 1. Verify action
        response = self.client.post(verify_url)
        self.assertRedirects(response, self.list_url)
        opp.refresh_from_db()
        self.assertEqual(opp.verification_status, ScrapedOpportunity.VerificationStatus.VERIFIED)

        # 2. Ignore action
        response = self.client.post(ignore_url)
        self.assertRedirects(response, self.list_url)
        opp.refresh_from_db()
        self.assertEqual(opp.verification_status, ScrapedOpportunity.VerificationStatus.IGNORED)

    def test_opportunity_edit(self):
        opp = ScrapedOpportunity.objects.create(
            college=self.college,
            company_name="Google",
            role="Software Engineer"
        )
        edit_url = reverse('opportunities:edit', kwargs={'pk': opp.pk})
        
        # Load form
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        
        # Post edit details
        response = self.client.post(edit_url, {
            'company_name': 'Alphabet Google',
            'role': 'SWE II',
            'package': '30.0 LPA',
            'location': 'Mountain View',
            'deadline': '2027-01-01',
            'source': 'https://google.com/careers'
        })
        self.assertRedirects(response, self.list_url)
        
        opp.refresh_from_db()
        self.assertEqual(opp.company_name, 'Alphabet Google')
        self.assertEqual(opp.role, 'SWE II')
        self.assertEqual(opp.package, '30.0 LPA')
        self.assertEqual(opp.trust_score, 100)

    def test_import_company(self):
        opp = ScrapedOpportunity.objects.create(
            college=self.college,
            company_name="Amazon Cloud",
            role="SDE",
            location="Seattle, WA",
            package="16.5 LPA",
            source="https://amazon.jobs"
        )
        import_url = reverse('opportunities:import_company', kwargs={'pk': opp.pk})

        # Post import
        response = self.client.post(import_url)
        self.assertRedirects(response, self.list_url)
        
        # Check company created in companies app
        self.assertTrue(Company.objects.filter(college=self.college, name="Amazon Cloud").exists())
        company = Company.objects.get(college=self.college, name="Amazon Cloud")
        self.assertEqual(company.location, "Seattle, WA")
        self.assertEqual(company.package_amount, 16.5)

    def test_create_placement_drive(self):
        opp = ScrapedOpportunity.objects.create(
            college=self.college,
            company_name="Meta Platforms",
            role="Production Engineer",
            package="45.0 LPA",
            deadline="2026-11-20"
        )
        drive_url = reverse('opportunities:create_drive', kwargs={'pk': opp.pk})

        # Load prefilled form
        response = self.client.get(drive_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Meta Platforms")
        
        # Fetch auto-created Company
        company = Company.objects.get(college=self.college, name="Meta Platforms")

        # Submit drive creation form
        response = self.client.post(drive_url, {
            'company': company.pk,
            'drive_type': 'JOB',
            'role': 'Production Engineer',
            'package_amount': '45.0',
            'job_mode': 'HYBRID',
            'min_cgpa': '0.00',
            'max_backlogs': '0',
            'deadline': '2026-11-20',
            'status': 'ACTIVE'
        })
        self.assertRedirects(response, reverse('placements:list'))
        
        # Verify drive created in database
        self.assertTrue(PlacementDrive.objects.filter(college=self.college, company=company, role="Production Engineer").exists())
        
        # Verify opportunity verification status changed to VERIFIED
        opp.refresh_from_db()
        self.assertEqual(opp.verification_status, ScrapedOpportunity.VerificationStatus.VERIFIED)
