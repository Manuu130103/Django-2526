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
    logger = logging.getLogger(__name__)

    def form_valid(self, form):
        # 1. Save in DB
        response = super().form_valid(form)
        info = form.instance

        # 2. Sender (always your Gmail SMTP user)
        sender = settings.EMAIL_HOST_USER
        from_email = f"ReleCloud <{sender}>"

        # 3. Fixed admin email that receives every request
        admin_recipient = "grupob7is2@gmail.com"

        # 4. Build admin message
        admin_subject = f"New info request for {info.cruise} from {info.name}"
        admin_message = (
            "A new information request has been submitted:\n\n"
            f"Name: {info.name}\n"
            f"Email: {info.email}\n"
            f"Cruise: {info.cruise}\n\n"
            "Notes:\n"
            f"{info.notes}\n"
        )

        # 5. Build confirmation message
        confirm_subject = f"We received your info request for {info.cruise}"
        confirm_message = (
            f"Hi {info.name},\n\n"
            "Thanks for your request! We received the following information:\n\n"
            f"Name: {info.name}\n"
            f"Email: {info.email}\n"
            f"Cruise: {info.cruise}\n\n"
            "Notes:\n"
            f"{info.notes}\n\n"
            "We will contact you soon.\n"
        )

        # 6. Try to use the configured SMTP backend
        try:
            connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
            )
        except Exception:
            logger.exception(
                " Could not get email connection for InfoRequest id=%s. No emails sent.",
                info.pk,
            )
            return response

        # 7. Send admin email
        try:
            EmailMessage(
                subject=admin_subject,
                body=admin_message,
                from_email=from_email,
                to=[admin_recipient],
                reply_to=[info.email] if info.email else None,
                connection=connection,
            ).send()
            logger.info("📬 Admin email sent for InfoRequest id=%s", info.pk)
        except Exception:
            logger.exception(
                " Failed to send admin email for InfoRequest id=%s", info.pk
            )

        # 8. Send confirmation email to user
        if info.email:
            try:
                EmailMessage(
                    subject=confirm_subject,
                    body=confirm_message,
                    from_email=from_email,
                    to=[info.email],
                    connection=connection,
                ).send()
                logger.info("📨 Confirmation sent to %s", info.email)
            except Exception:
                logger.exception(
                    " Failed sending confirmation email for InfoRequest id=%s to %s",
                    info.pk,
                    info.email,
                )

        return response
