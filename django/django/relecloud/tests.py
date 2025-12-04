from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Destination, Cruise, InfoRequest, Review
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile


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


    def test_destination_image_display(self):
        # Crear una imagen GIF pequeña en memoria
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        )
        image = SimpleUploadedFile("test_image.gif", small_gif, content_type="image/gif")

        dest = Destination.objects.create(name="Marte", image=image)

        # Ajusta esta URL si la tuya es distinta (usa reverse si existe)
        response = self.client.get('/destinations/')

        # Verifica que la imagen aparece en la respuesta
        self.assertContains(response, 'test_image.gif')

class ReviewModelTests(TestCase):
    def setUp(self):
        # Crear un destino de prueba
        self.dest = Destination.objects.create(
            name="Test Planet", 
            description="A test description"
        )

    def test_create_review(self):
        """Probar que se puede crear una review correctamente"""
        review = Review.objects.create(
            destination=self.dest,
            author="Tester",
            rating=5,
            comment="Great place!"
        )
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(review.rating, 5)

    def test_rating_average_logic(self):
        """Probar manualmente que la media tendría sentido"""
        Review.objects.create(destination=self.dest, rating=5, comment="A")
        Review.objects.create(destination=self.dest, rating=1, comment="B")

        # 5 + 1 = 6. Media = 3.
        reviews = self.dest.reviews.all()
        total = sum([r.rating for r in reviews])
        avg = total / len(reviews)
        self.assertEqual(avg, 3.0)

class DestinationDetailViewTests(TestCase):
    def setUp(self):
        self.dest = Destination.objects.create(name="Mars", description="Red planet")
        self.url = reverse('destination_detail', args=[self.dest.id])

    def test_view_context_contains_form(self):
        """La vista debe enviar el formulario al HTML"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('avg_rating', response.context)