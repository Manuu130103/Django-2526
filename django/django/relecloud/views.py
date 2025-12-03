from django.shortcuts import render
from django.urls import reverse_lazy
from . import models
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from.models import Destination, Cruise, InfoRequest
from django.core.mail import send_mail, EmailMessage, get_connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def destinations(request):
    all_destinations = models.Destination.objects.all()
    return render(request, 'destinations.html', {'destinations': all_destinations})

class DestinationDetailView(generic.DetailView):
    template_name = 'destination_detail.html'
    model = models. Destination
    context_object_name = 'destination'

class DestinationCreateView(generic.CreateView):
    model = models. Destination
    template_name = 'destination_form.html'
    fields = ['name', 'description']

class DestinationUpdateView(generic.UpdateView):
    model = models. Destination
    template_name = 'destination_form.html'
    fields = ['name', 'description']

class DestinationDeleteView(generic.DeleteView):
    model =models. Destination
    template_name = 'destination_confirm_delete.html'
    success_url = reverse_lazy('destinations')

class CruiseDetailView(generic.DetailView):
    template_name = 'cruise_detail.html'
    model = models.Cruise
    context_object_name = 'cruise'

class InfoRequestCreate(SuccessMessageMixin, generic.CreateView):
    template_name = 'info_request_create.html'
    model = models.InfoRequest
    fields = ['name', 'email', 'cruise', 'notes']
    success_url = reverse_lazy('index')
    success_message = 'Thank you, %(name)s! We will email you when we have more information about %(cruise)s!'
    
    def form_valid(self, form):
        # Save the InfoRequest first
        response = super().form_valid(form)
        info = form.instance

        subject = f"New info request for {info.cruise} from {info.name}"
        message = (
            f"Name: {info.name}\n"
            f"Email: {info.email}\n"
            f"Cruise: {info.cruise}\n\n"
            f"Notes:\n{info.notes}\n"
        )

        # Destination email for site owner / admin (fixed)
        recipient = 'grupob7is2@gmail.com'
        # Prefer the authenticated SMTP user as the sender if configured, otherwise use DEFAULT_FROM_EMAIL
        from_email = getattr(settings, 'EMAIL_HOST_USER', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)

        # Send notification to site admin/owner. Also include the requester as a recipient
        # so they receive a copy even if a separate confirmation fails due to provider rules.
        if recipient and from_email:
                try:
                    # Build connection using settings (fallback to default connection when settings absent)
                    conn_kwargs = {}
                    if getattr(settings, 'EMAIL_HOST', None):
                        conn_kwargs = {
                            'host': getattr(settings, 'EMAIL_HOST', None),
                            'port': int(getattr(settings, 'EMAIL_PORT', 0)) or None,
                            'username': getattr(settings, 'EMAIL_HOST_USER', None),
                            'password': getattr(settings, 'EMAIL_HOST_PASSWORD', None),
                            'use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
                        }
                    connection = get_connection(**conn_kwargs) if conn_kwargs else get_connection()

                    admin_msg = EmailMessage(subject, message, from_email, [recipient], connection=connection)
                    admin_msg.send(fail_silently=False)
                    logger.info('Sent admin notification for InfoRequest id=%s to %s via explicit connection', info.pk, recipient)
                except Exception:
                    logger.exception('Failed sending admin notification for InfoRequest id=%s to %s', info.pk, recipient)
        else:
                logger.info('Email not sent: CONTACT_EMAIL or DEFAULT_FROM_EMAIL not configured.')

        # Send a confirmation email to requester and log any issues
        if from_email and info.email:
                confirm_subject = f"We received your info request for {info.cruise}"
                confirm_message = (
                    f"Hi {info.name},\n\n"
                    "Thanks for your information request. We received the following message:\n\n"
                    f"Cruise: {info.cruise}\nNotes:\n{info.notes}\n\nWe will contact you at {info.email} when we have more details.\n"
                )
                try:
                    # Use same explicit connection as above when possible
                    conn_kwargs = {}
                    if getattr(settings, 'EMAIL_HOST', None):
                        conn_kwargs = {
                            'host': getattr(settings, 'EMAIL_HOST', None),
                            'port': int(getattr(settings, 'EMAIL_PORT', 0)) or None,
                            'username': getattr(settings, 'EMAIL_HOST_USER', None),
                            'password': getattr(settings, 'EMAIL_HOST_PASSWORD', None),
                            'use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
                        }
                    connection = get_connection(**conn_kwargs) if conn_kwargs else get_connection()

                    confirm_msg = EmailMessage(confirm_subject, confirm_message, from_email, [info.email], connection=connection)
                    confirm_msg.send(fail_silently=False)
                    logger.info('Sent confirmation email for InfoRequest id=%s to %s via explicit connection', info.pk, info.email)
                except Exception:
                    logger.exception('Failed sending confirmation email to requester for InfoRequest id=%s, email=%s', info.pk, info.email)

        return response