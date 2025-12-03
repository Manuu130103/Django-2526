from django.shortcuts import render
from django.urls import reverse_lazy
from . import models
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from.models import Destination, Cruise, InfoRequest
from django.core.mail import send_mail
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

        # Destination email for site owner / admin
        recipient = getattr(settings, 'CONTACT_EMAIL', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

        try:
            if recipient and from_email:
                send_mail(subject, message, from_email, [recipient], fail_silently=False)
            else:
                logger.info('Email not sent: CONTACT_EMAIL or DEFAULT_FROM_EMAIL not configured.')

            # Send a confirmation email to requester (fail silently so UX isn't broken)
            if from_email and info.email:
                confirm_subject = f"We received your info request for {info.cruise}"
                confirm_message = (
                    f"Hi {info.name},\n\n"
                    "Thanks for your information request. We received the following message:\n\n"
                    f"""Cruise: {info.cruise}\nNotes:\n{info.notes}\n\nWe will contact you at {info.email} when we have more details.\n"""
                )
                send_mail(confirm_subject, confirm_message, from_email, [info.email], fail_silently=True)

        except Exception as e:
            logger.exception('Error sending info_request emails: %s', e)

        return response