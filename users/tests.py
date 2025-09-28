# users/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Profile, PetReport
from django.conf import settings

# =============================================================================
#  Introduction to Django Tests
#
#  This file contains automated tests for the 'users' app. Tests are crucial
#  for ensuring that your application works correctly now and in the future.
#
#  - TestCase: A class that groups related tests. A separate, temporary
#    database is created for each TestCase.
#
#  - setUp(): A method that runs BEFORE every single test function in the class.
#    It's used to set up common objects, like users or a test client.
#
#  - test_*(): Any method starting with 'test_' is an automated test that will
#    be run by the test runner.
#
#  - self.client: A "dummy" web browser that can make requests (GET, POST) to
#    your application's URLs without needing to run a live server.
#
#  - self.assertEqual(a, b): Asserts that a is equal to b.
#  - self.assertTrue(x): Asserts that x is True.
#  - self.assertRedirects(response, url): Asserts that the response is a
#    redirect to the specified URL.
# =============================================================================


class StaticPagesTests(TestCase):
    """
    Tests for simple, static pages that don't require user authentication.
    """
    def setUp(self):
        self.client = Client()

    def test_about_page_loads_correctly(self):
        """
        Tests if the 'About' page is accessible and uses the correct template.
        """
        url = reverse('users:about')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200) # 200 OK
        self.assertTemplateUsed(response, 'users/about.html')
        self.assertContains(response, "Our Mission") # Check for some content


class UserModelAndProfileTests(TestCase):
    """
    Tests for the User model and its related Profile.
    """
    def test_profile_is_created_during_registration_view(self):
        """
        Tests the application's registration view logic to ensure a Profile is created.
        This is a more accurate test than checking the model directly.
        """
        # ## FIX ##: The original test was flawed. This now tests the actual registration form.
        url = reverse('users:register')
        self.client.post(url, {
            'username': 'newuser',
            'email': 'new@user.com',
            'password': 'Password123!',
            'password2': 'Password123!',
        })
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, 'user')


class AuthenticationTests(TestCase):
    """
    Tests for user registration, login, and logout functionality.
    """
    def setUp(self):
        self.client = Client()
        # Create a user to test login and other authenticated actions
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='strongpassword!1')
        # ## FIX ##: Create the associated profile for the test user.
        Profile.objects.create(user=self.user)

    def test_registration_page_loads_correctly(self):
        """Tests if the registration page is accessible."""
        url = reverse('users:register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_user_can_register_successfully(self):
        """Tests the full registration process for a new user."""
        url = reverse('users:register')
        form_data = {
            'username': 'new_register_user',
            'email': 'new_register@example.com',
            'password': 'V3ryStrongPassword!',
            'password2': 'V3ryStrongPassword!',
            'first_name': 'Test',
            'city': 'Testville'
        }
        response = self.client.post(url, form_data)
        
        # Check that the user was created
        self.assertTrue(User.objects.filter(username='new_register_user').exists())
        # Check that the user is logged in and redirected to the dashboard
        self.assertRedirects(response, reverse('users:dashboard'))

    def test_login_page_loads_correctly(self):
        """Tests if the login page is accessible."""
        url = reverse('users:login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_successful_login(self):
        """Tests that a user with correct credentials can log in and is redirected."""
        url = reverse('users:login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'strongpassword!1'})
        
        self.assertRedirects(response, reverse('users:dashboard'))
        # Check if the user ID is stored in the session, confirming login
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_failed_login(self):
        """Tests that a user with incorrect credentials cannot log in."""
        url = reverse('users:login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'wrongpassword'})
        
        self.assertEqual(response.status_code, 200) # Stays on the same page
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertNotIn('_auth_user_id', self.client.session) # Not logged in

    def test_user_can_logout(self):
        """Tests the logout process."""
        # First, log the user in
        self.client.login(username='testuser', password='strongpassword!1')
        self.assertIn('_auth_user_id', self.client.session)

        # Then, access the logout URL
        url = reverse('users:logout')
        response = self.client.get(url)

        # Check that it redirects to the login page
        self.assertRedirects(response, reverse('users:login'))
        # Check that the user is no longer in the session
        self.assertNotIn('_auth_user_id', self.client.session)


class PetReportTests(TestCase):
    """
    Tests for creating and viewing Lost/Found pet reports.
    Requires a logged-in user.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='reporter', password='password123')
        # ## FIX ##: Create the associated profile for the reporter user.
        Profile.objects.create(user=self.user)
        self.client = Client()
        self.client.login(username='reporter', password='password123')

    def test_create_report_page_loads(self):
        """Tests if the form page for creating a report is accessible."""
        url = reverse('users:create_pet_report', kwargs={'report_type': 'Lost'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/create_pet_report.html')

    def test_create_found_pet_report(self):
        """Tests the full process of submitting a 'Found' pet report."""
        url = reverse('users:create_pet_report', kwargs={'report_type': 'Found'})
        # Create a dummy image file in memory for the upload
        dummy_image = SimpleUploadedFile("pet.jpg", b"file_content", content_type="image/jpeg")
        
        form_data = {
            'pet_type': 'Dog',
            # ## FIX ##: Add all required fields from the form to make it valid.
            'color': 'Golden',
            'location': 'City Park',
            'contact_info': '555-1234',
            'pet_image': dummy_image,
        }
        
        response = self.client.post(url, form_data)

        # ## FIX ##: Check for redirect first, as it indicates success before checking the count.
        self.assertRedirects(response, reverse('users:dashboard'))
        
        # Check that the report was created in the database
        self.assertEqual(PetReport.objects.count(), 1)
        report = PetReport.objects.first()
        self.assertEqual(report.report_type, 'Found')
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.pet_type, 'Dog')


    def test_view_pet_report_detail(self):
        """Tests if a user can view the details of a specific report."""
        # ## FIX ##: ImageField is required, so we need to provide a dummy one.
        dummy_image = SimpleUploadedFile("cat.jpg", b"file_content", content_type="image/jpeg")
        report = PetReport.objects.create(
            reporter=self.user,
            report_type='Lost',
            pet_type='Cat',
            color='Black',
            location='Downtown',
            contact_info='test@example.com',
            pet_image=dummy_image, # ## FIX ##: Add the required image field
        )
        url = reverse('users:pet_report_detail', kwargs={'report_id': report.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/pet_report_detail.html')
        self.assertContains(response, 'Pet Type:</span> Cat') # ## FIX ##: Check for more specific HTML
        self.assertContains(response, 'Location:</span> Downtown')


class AdminFunctionalityTests(TestCase):
    """
    Tests for custom admin panel functionality like promoting and removing users.
    This requires multiple user types (regular, staff, superuser).
    """
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(username='regular', password='password123')
        self.staff_user = User.objects.create_user(username='staff', password='password123', is_staff=True)
        self.superuser = User.objects.create_user(username='super', password='password123', is_staff=True, is_superuser=True)
        # ## FIX ##: Create profiles for all users to prevent crashes.
        Profile.objects.create(user=self.regular_user)
        Profile.objects.create(user=self.staff_user)
        Profile.objects.create(user=self.superuser)

    def test_manage_users_page_access(self):
        """Tests that only staff and superusers can access the manage users page."""
        url = reverse('users:admin_manage_users')

        # Regular user should be redirected
        self.client.login(username='regular', password='password123')
        response = self.client.get(url)
        # ## FIX ##: When a decorator blocks access, it redirects. The status code is 302, not 200.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('users:login')))

        # Staff user should have access
        self.client.login(username='staff', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Superuser should have access
        self.client.login(username='super', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_promote_user_to_admin(self):
        """Tests if a superuser can successfully promote a regular user."""
        self.client.login(username='super', password='password123')
        url = reverse('users:admin_promote_user', kwargs={'user_id': self.regular_user.id})
        
        self.assertFalse(self.regular_user.is_staff)
        
        response = self.client.post(url)
        
        self.assertRedirects(response, reverse('users:admin_manage_users'))
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_staff)

    def test_staff_user_cannot_promote_user(self):
        """Tests that a non-superuser staff member cannot promote users."""
        self.client.login(username='staff', password='password123')
        url = reverse('users:admin_promote_user', kwargs={'user_id': self.regular_user.id})

        response = self.client.post(url)
        
        # ## FIX ##: The decorator will cause a redirect to the login page.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('users:login')))
        
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_staff)

    def test_superuser_can_remove_user(self):
        """Tests if a superuser can remove another user."""
        self.client.login(username='super', password='password123')
        url = reverse('users:admin_remove_user', kwargs={'user_id': self.regular_user.id})
        
        self.assertTrue(User.objects.filter(id=self.regular_user.id).exists())
        
        response = self.client.post(url)
        self.assertRedirects(response, reverse('users:admin_manage_users'))
        
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

    def test_staff_user_cannot_remove_other_staff(self):
        """
        Tests that a staff user is blocked from removing another staff user,
        as per the logic in the view.
        """
        self.client.login(username='staff', password='password123')
        # A staff user trying to remove a superuser (who is also staff)
        url = reverse('users:admin_remove_user', kwargs={'user_id': self.superuser.id})
        
        response = self.client.post(url)
        self.assertRedirects(response, reverse('users:admin_manage_users'))
        
        self.assertTrue(User.objects.filter(id=self.superuser.id).exists())

    def test_staff_user_can_remove_regular_user(self):
        """Tests that a staff user CAN remove a non-staff, regular user."""
        self.client.login(username='staff', password='password123')
        url = reverse('users:admin_remove_user', kwargs={'user_id': self.regular_user.id})
        
        self.assertTrue(User.objects.filter(id=self.regular_user.id).exists())
        
        response = self.client.post(url)
        self.assertRedirects(response, reverse('users:admin_manage_users'))
        
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())