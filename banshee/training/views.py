import calendar
from datetime import date, datetime, timedelta

from django.views.generic import TemplateView, ListView, FormView
from django.views import View
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MapSeniorTeach, TrainingNight, Level, Teach
from .forms import LessonTeachForm, ActivityTeachForm
from .utils import (
    TrainingCalendar,
    DashboardCalendar,
    TrainingDaySchedule,
)

# Create your views here.


class HomeView(TemplateView):
    template_name = "training/home.html"


# Testing View
class ExampleView(TemplateView):
    template_name = "training/example.html"


# Functions for Calendar List Views
def get_date(req_day):
    if req_day:
        year, month = map(int, req_day.split("-"))
        return date(year, month, day=1)
    return datetime.now()


def curr_month(d):
    month = "month=" + str(d.year) + "-" + str(d.month)
    return month


def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = "month=" + str(prev_month.year) + "-" + str(prev_month.month)
    return month


def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = "month=" + str(next_month.year) + "-" + str(next_month.month)
    return month


# Main Views
class DashboardView(View):
    model = TrainingNight
    template_name = "training/dashboard.html"

    def get(self, request, view, *args, **kwargs):
        context = self.get_context_data(view, **kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, view, **kwargs):
        context = {}

        d = get_date(self.request.GET.get("month", None))
        context["curr_month"] = curr_month(d)
        context["prev_month"] = prev_month(d)
        context["next_month"] = next_month(d)
        cal = DashboardCalendar(view, d.year, d.month)

        nights = self.model.get_nights(date__year=d.year, date__month=d.month)
        html_cal = cal.formatmonth(nights=nights, today=date.today(), withyear=True)
        context["calendar"] = mark_safe(html_cal)
        context["monthname"] = str(calendar.month_name[d.month]) + " " + str(d.year)

        context["view"] = view

        return context


# Overall view of all training nights
class TrainingCalView(ListView):
    model = TrainingNight
    template_name = "training/trainingcal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # use today's date for the calendar
        d = get_date(self.request.GET.get("month", None))
        context["prev_month"] = prev_month(d)
        context["next_month"] = next_month(d)
        cal = TrainingCalendar(d.year, d.month)

        nights = self.model.get_nights(date__year=d.year, date__month=d.month)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(nights=nights, today=date.today(), withyear=True)
        context["calendar"] = mark_safe(html_cal)
        return context


# View for specific training night
class TrainingNightView(View):
    model = TrainingNight
    template_name = "training/trainingnight.html"

    def get(self, request, night_id, *args, **kwargs):
        night: TrainingNight = TrainingNight.objects.get(pk=night_id)

        level_objects = Level.get_juniors()
        levels = [level_object.name for level_object in level_objects]

        schedule_obj = TrainingDaySchedule()
        schedule = schedule_obj.formatschedule(night, levels)
        mark_safe(schedule)

        roles = MapSeniorTeach.get_instructors(night.masterteach)

        date = night.date
        title = {}
        title["month"] = date.strftime("%B")
        title["day"] = date.day

        return render(
            request,
            self.template_name,
            {
                "schedule": mark_safe(schedule),
                "nightid": night.pk,
                "roles": roles,
                "title": title,
            },
        )


class TeachFormView(FormView):
    template_name = "training/teachform.html"
    form_class = [
        ("Lesson", LessonTeachForm),
        ("Activity", ActivityTeachForm),
    ]

    def init_form(self, levels, night_id, form_id, *args, **kwargs):
        form = self.form_class[form_id][1](levels, night_id, *args, **kwargs)
        return form

    def get(self, request, night_id, form_id, *args, **kwargs):
        levels = Level.get_juniors()
        form = self.init_form(levels, night_id, form_id)
        return render(
            request,
            self.template_name,
            {"form": form, "levels": levels, "nightid": night_id, "formid": form_id},
        )

    def post(self, request, night_id, form_id, *args, **kwargs):
        levels = Level.get_juniors()
        form = self.init_form(levels, night_id, form_id, data=request.POST)
        if form.is_valid():
            form.save()
            print(type(night_id))
            return redirect("trainingnight", night_id=night_id)
        return render(
            request,
            self.template_name,
            {"form": form, "levels": levels, "nightid": night_id, "formid": form_id},
        )


# Teach Specific Views
class TeachView(TemplateView):
    template_name = "training/teach.html"

    def get_context_data(self, teachid, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = Teach.get_by_lessonid(teachid)

        content_details = instance.get_content_attributes()
        content_type = instance.get_content_type()
        context["content"] = {"type": content_type, "attributes": content_details}

        finished = instance.finished
        context["plan"] = {"finished": finished}
        if finished:
            context["plan"]["link"] = instance.plan

        return context


# Utility Views (views that do things but don't actually have a template)
class EditTrainingNightView(APIView):
    http_method_names = ['get', 'delete']
    
    def get(self, request, year, month, day, *args, **kwargs):
        day = date(year, month, day)
        TrainingNight.create(day)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, year, month, day, *args, **kwargs):
        day = date(year, month, day)
        instance = TrainingNight.get_by_date(day)
        instance.delete()
        return Response(status=status.HTTP_200_OK)