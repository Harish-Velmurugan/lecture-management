from datetime import datetime, time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.generic import DetailView
from django.views.generic.base import TemplateView

from .models import Event, ExternalUser, Faculty, Student, applications

User = get_user_model()
# now = timezone.now()


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # context['book_list'] = Book.objects.all()
        return context

def get_valid_events(user_pk, exclude_list=[]):
    if ExternalUser.objects.filter(account=user_pk).exists():
        cir_events = Event.objects.filter(allow_ext=True, type=Event.EventType.CIR, status=Event.EventStatus.ON_SCHEDULE, end_date__gt=timezone.now())
        return list(cir_events)

    cir_events = Event.objects.filter(type=Event.EventType.CIR, status=Event.EventStatus.ON_SCHEDULE, end_date__gt=timezone.now())

    user = Student.objects.get(account=user_pk)
    user_dept = user.dept_fk
    
    all_dept_events = Event.objects.filter(type=Event.EventType.DEPT, status=Event.EventStatus.ON_SCHEDULE, end_date__gt=timezone.now())
    dept_events = []

    for dept_event in all_dept_events:
        try:
            faculty_created = Faculty.objects.get(account=dept_event.created_by)
            if faculty_created.dept_fk == user_dept: # and not model_in_operator(dept_event, exclude_list):
                dept_events.append(dept_event)
        except ObjectDoesNotExist:
            continue
        
    return dept_events + list(cir_events)


def applied_events(request, user_pk):
    apps = applications.objects.filter(student=user_pk)
    eventobj_list = []
    for app in apps:
        eventobj = Event.objects.get(id=app.event.id)
        if eventobj.end_date > timezone.now():
            eventobj_list.append(eventobj)
    return render(request, "applied_events.html", {"events": eventobj_list})

# def model_in_operator(model_obj, model_obj_list):
#     for obj in model_obj_list:
#         if model_obj == obj:
#             return True
#     return False


def upcoming_events(request, user_pk):
    apps = applications.objects.filter(student=user_pk)
    applied_events = []
    
    for app in apps:
        eventobj = Event.objects.get(id=app.event.id)
        applied_events.append(eventobj)

    all_events = get_valid_events(user_pk, exclude_list=applied_events)

    for event in applied_events:
        if event in all_events: # and event.end_date < timezone.now():
            all_events.remove(event)
    return render(request, "upcoming_events.html", {"events": all_events})


def past_events(request, user_pk):
    apps = applications.objects.filter(student=user_pk)
    eventobj_list = []
    for app in apps:
        eventobj = Event.objects.get(id=app.event.id)
        if eventobj.end_date < timezone.now():
            eventobj_list.append(eventobj)
    return render(request, "past_events.html", {"events": eventobj_list})


class EventView(DetailView):
    template_name = "event.html"
    model = Event
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['already_applied'] = applications.has_applied(user_pk=self.kwargs["user_pk"], event_pk=context['event'].pk)
        context['current_time'] = timezone.now()
        return context


def event_registration_view(request, user_pk, pk):
    event = Event.objects.get(pk=pk)
    event.register_to_event(user=request.user)
    event.occupied_seats += 1
    event.save()

    user = User.objects.get(pk=user_pk)
    send_confirmation_mail(user, event)

    return redirect(reverse('lecture_app:event', kwargs=dict(user_pk=user_pk,pk=pk)))


def send_confirmation_mail(user, event):
    context = {
        "user": user,
        "event": event
    }

    subject = f"Applied to {event}"
    html_message = render_to_string('mail_template.html', context=context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    
    # email.content_subtype = "html"
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)


# @login_required()
# def home_view(request, username):
#     user = CustomUser.objects.get(username = username)

#     return render(request, 'stud_app/home.html', context={
#         'username': username,
#         'student' : student,
#         'name': student.get_name(),
#         'current_page': 'home',

#     })
