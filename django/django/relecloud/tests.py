from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Destination, Cruise, InfoRequest
from django.core import mail


class InfoRequestEmailTests(TestCase):
	def setUp(self):
		self.destination = Destination.objects.create(name='Test Dest', description='Desc')
		self.cruise = Cruise.objects.create(name='Test Cruise', description='Cruise desc', destination=self.destination)
		self.url = reverse('info_request')

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
					   DEFAULT_FROM_EMAIL='no-reply@example.com',
					   CONTACT_EMAIL='admin@example.com')
	def test_sends_admin_and_confirmation_emails(self):
		data = {
			'name': 'Alice Example',
			'email': 'alice@example.com',
			'cruise': self.cruise.pk,
			'notes': 'I would like more info.'
		}
		response = self.client.post(self.url, data)
		# Should redirect to index on success
		self.assertEqual(response.status_code, 302)

		# InfoRequest saved
		self.assertEqual(InfoRequest.objects.count(), 1)
		info = InfoRequest.objects.first()
		self.assertEqual(info.name, 'Alice Example')

		# Two emails: one to admin, one confirmation to requester
		self.assertEqual(len(mail.outbox), 2)
		recipients = [to for m in mail.outbox for to in m.to]
		self.assertIn('admin@example.com', recipients)
		self.assertIn('alice@example.com', recipients)

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
					   DEFAULT_FROM_EMAIL='no-reply@example.com',
					   CONTACT_EMAIL='')
	def test_sends_only_confirmation_when_no_contact_email(self):
		data = {
			'name': 'Bob Example',
			'email': 'bob@example.com',
			'cruise': self.cruise.pk,
			'notes': 'Please send details.'
		}
		response = self.client.post(self.url, data)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(InfoRequest.objects.count(), 1)

		# Only confirmation email should be sent
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, ['bob@example.com'])

