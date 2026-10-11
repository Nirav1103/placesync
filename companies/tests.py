from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from colleges.models import College
from companies.models import Company

User = get_user_model()

class CompanyManagementTestCase(TestCase):
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
        
        # Create companies
        self.company_1 = Company.objects.create(
            college=self.college,
            name="Google",
            website="https://google.com",
            industry="Technology",
            hr_name="Larry Page",
            hr_email="larry@google.com",
            hr_phone="1234567890",
            hr_notes="Co-founder HR contact",
            location="Mountain View, CA",
            package_amount=25.50,
            stipend_amount=100000.00,
            job_mode=Company.JobMode.HYBRID,
            placement_history="Recruited 10 students in 2025."
        )

        self.company_2 = Company.objects.create(
            college=self.college,
            name="Microsoft",
            website="https://microsoft.com",
            industry="Software",
            hr_name="Satya Nadella",
            hr_email="satya@microsoft.com",
            hr_phone="0987654321",
            location="Redmond, WA",
            package_amount=20.00,
            stipend_amount=80000.00,
            job_mode=Company.JobMode.REMOTE
        )

        self.client = Client()
        self.client.login(username="tit_admin", password="adminpassword123")

        self.list_url = reverse('companies:list')
        self.create_url = reverse('companies:create')

    def test_company_listing_search_and_filters(self):
        # 1. Listing shows both companies
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")
        self.assertContains(response, "Microsoft")

        # 2. Search query matches
        response = self.client.get(self.list_url, {'q': 'Google'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")
        self.assertNotContains(response, "Microsoft")

        # 3. Filter by job mode (REMOTE)
        response = self.client.get(self.list_url, {'job_mode': 'REMOTE'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Google")
        self.assertContains(response, "Microsoft")

        # 4. Filter by minimum package (>= 22.0 LPA)
        response = self.client.get(self.list_url, {'min_package': '22.0'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")
        self.assertNotContains(response, "Microsoft")

        # 5. Filter by minimum stipend (>= 90000)
        response = self.client.get(self.list_url, {'min_stipend': '90000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")
        self.assertNotContains(response, "Microsoft")

    def test_company_details_view(self):
        detail_url = reverse('companies:detail', kwargs={'pk': self.company_1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")
        self.assertContains(response, "Mountain View, CA")
        self.assertContains(response, "Larry Page")
        self.assertContains(response, "larry@google.com")
        self.assertContains(response, "1234567890")
        self.assertContains(response, "Co-founder HR contact")
        self.assertContains(response, "Recruited 10 students in 2025.")
        self.assertContains(response, "25.50 LPA")
        self.assertContains(response, "100000.00 /mo")

    def test_company_creation_success_and_failures(self):
        # 1. Load form
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

        # 2. Successful creation
        response = self.client.post(self.create_url, {
            'name': 'Netflix',
            'website': 'https://netflix.com',
            'industry': 'Entertainment',
            'hr_name': 'Ted Sarandos',
            'hr_email': 'ted@netflix.com',
            'hr_phone': '1122334455',
            'location': 'Los Gatos, CA',
            'package_amount': '30.0',
            'stipend_amount': '120000.0',
            'job_mode': 'ON_SITE',
            'placement_history': 'First time recruiting.'
        })
        self.assertRedirects(response, self.list_url)
        self.assertTrue(Company.objects.filter(name='Netflix', college=self.college).exists())
        
        # 3. Duplicate name check case-insensitively within college
        response = self.client.post(self.create_url, {
            'name': 'google', # Case-insensitive collision with Google
            'website': 'https://google.com',
            'placement_status': 'ON_SITE'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'name', "A company with this name is already registered in your college.")

    def test_company_edit(self):
        edit_url = reverse('companies:edit', kwargs={'pk': self.company_2.pk})
        
        # Load form
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Post edit update
        response = self.client.post(edit_url, {
            'name': 'Microsoft Corp',
            'website': 'https://microsoft.com',
            'industry': 'Software & Cloud',
            'hr_name': 'Satya Nadella',
            'hr_email': 'satya@microsoft.com',
            'hr_phone': '9988776655',
            'location': 'Redmond, WA',
            'package_amount': '21.0',
            'stipend_amount': '85000.0',
            'job_mode': 'HYBRID',
            'placement_history': 'Updated recruits details.'
        })
        self.assertRedirects(response, self.list_url)
        
        # Verify database fields updated
        self.company_2.refresh_from_db()
        self.assertEqual(self.company_2.name, 'Microsoft Corp')
        self.assertEqual(self.company_2.industry, 'Software & Cloud')
        self.assertEqual(self.company_2.hr_phone, '9988776655')
        self.assertEqual(self.company_2.package_amount, 21.0)
        self.assertEqual(self.company_2.stipend_amount, 85000.0)
        self.assertEqual(self.company_2.job_mode, Company.JobMode.HYBRID)
        self.assertEqual(self.company_2.placement_history, 'Updated recruits details.')

    def test_company_delete(self):
        delete_url = reverse('companies:delete', kwargs={'pk': self.company_2.pk})
        
        # Load delete warning screen
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Company Profile?")

        # Post delete request
        response = self.client.post(delete_url)
        self.assertRedirects(response, self.list_url)
        
        # Verify record deleted
        self.assertFalse(Company.objects.filter(pk=self.company_2.pk).exists())

    def test_company_verification_dashboard(self):
        verify_dashboard_url = reverse('companies:verification_dashboard')
        
        # 1. Load verification dashboard
        response = self.client.get(verify_dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Company Verification Dashboard")
        
        # Should display both companies under Pending status by default
        self.assertContains(response, "Google")
        self.assertContains(response, "Microsoft")
        
        # Stats checks: pending should be 2
        self.assertEqual(response.context['pending_count'], 2)
        self.assertEqual(response.context['verified_count'], 0)

    def test_company_verification_audit(self):
        audit_url = reverse('companies:verify_audit', kwargs={'pk': self.company_1.pk})
        
        # 1. Load audit page
        response = self.client.get(audit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verify Partner Profile")
        self.assertContains(response, "Google")

        # 2. Post verification checklist (Website & Email checked)
        response = self.client.post(audit_url, {
            'is_website_verified': 'on',
            'is_email_verified': 'on',
            'is_career_page_verified': '', # unchecked
            'is_address_verified': '', # unchecked
            'verification_status': 'VERIFIED',
            'verification_notes': 'Audited website and email details.'
        })
        self.assertRedirects(response, reverse('companies:verification_dashboard'))

        # 3. Verify fields saved and trust score is 50% (2 out of 4 checked)
        self.company_1.refresh_from_db()
        self.assertEqual(self.company_1.verification_status, 'VERIFIED')
        self.assertTrue(self.company_1.is_website_verified)
        self.assertTrue(self.company_1.is_email_verified)
        self.assertFalse(self.company_1.is_career_page_verified)
        self.assertEqual(self.company_1.trust_score, 50)
        self.assertEqual(self.company_1.verification_notes, 'Audited website and email details.')
