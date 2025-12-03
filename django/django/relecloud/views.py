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
        """
        After saving the InfoRequest, send:
        - A notification email to the admin (grupob7is2@gmail.com) with all fields.
        - A confirmation email to the requester (info.email).
        """
        # Save the InfoRequest first
        response = super().form_valid(form)
        info = form.instance

        # Prefer the authenticated SMTP user as sender, else DEFAULT_FROM_EMAIL
        base_from_email = (
            getattr(settings, 'EMAIL_HOST_USER', None)
            or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        )

        if not base_from_email:
            logger.info(
                'InfoRequest id=%s saved, but email not sent: EMAIL_HOST_USER/DEFAULT_FROM_EMAIL not configured.',
                info.pk,
            )
            return response

        # Human-readable From header, e.g. "ReleCloud <grupob7is2@gmail.com>"
        from_email = f"ReleCloud <{base_from_email}>"

        # Fixed admin recipient
        admin_recipient = 'grupob7is2@gmail.com'

        # Build email bodies including all form fields
        admin_subject = f"New info request for {info.cruise} from {info.name}"
        admin_message = (
            "A new information request has been submitted:\n\n"
            f"Name: {info.name}\n"
            f"Email: {info.email}\n"
            f"Cruise: {info.cruise}\n\n"
            "Notes:\n"
            f"{info.notes}\n"
        )

        confirm_subject = f"We received your info request for {info.cruise}"
        confirm_message = (
            f"Hi {info.name},\n\n"
            "Thanks for your information request. We received the following information:\n\n"
            f"Name: {info.name}\n"
            f"Email: {info.email}\n"
            f"Cruise: {info.cruise}\n\n"
            "Notes:\n"
            f"{info.notes}\n\n"
            "We will contact you at this address when we have more details.\n"
        )

        try:
            # Use the configured EMAIL_BACKEND (SMTP in prod, console/locmem in dev/tests)
            connection = get_connection()
        except Exception:
            logger.exception(
                'Failed to obtain email connection for InfoRequest id=%s. No emails sent.',
                info.pk,
            )
            return response

        # 1) Admin notification (with reply_to set to the requester email)
        try:
            admin_email = EmailMessage(
                subject=admin_subject,
                body=admin_message,
                from_email=from_email,
                to=[admin_recipient],
                reply_to=[info.email] if info.email else None,
                connection=connection,
            )
            admin_email.send(fail_silently=False)
            logger.info(
                'Sent admin notification for InfoRequest id=%s to %s.',
                info.pk,
                admin_recipient,
            )
        except Exception:
            logger.exception(
                'Failed sending admin notification for InfoRequest id=%s to %s.',
                info.pk,
                admin_recipient,
            )

        # 2) Confirmation to requester (only if they gave a valid email)
        if info.email:
            try:
                confirm_email = EmailMessage(
                    subject=confirm_subject,
                    body=confirm_message,
                    from_email=from_email,
                    to=[info.email],
                    connection=connection,
                )
                confirm_email.send(fail_silently=False)
                logger.info(
                    'Sent confirmation email for InfoRequest id=%s to %s.',
                    info.pk,
                    info.email,
                )
            except Exception:
                logger.exception(
                    'Failed sending confirmation email for InfoRequest id=%s to %s.',
                    info.pk,
                    info.email,
                )
        else:
            logger.info(
                'No confirmation email sent for InfoRequest id=%s: requester email is empty.',
                info.pk,
            )

        return response
