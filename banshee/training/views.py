import calendar
from datetime import date, datetime, timedelta

from django.views.generic import TemplateView, ListView, FormView
from django.views import View
from django.urls import reverse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MapSeniorNight, MapSeniorTeach, TrainingNight, Level, Teach, Senior
from .forms import (
    AssignTeachFormset,
    AssignNightFormset,
    LessonTeachForm,
    ActivityTeachForm,
)
from .utils import (
    DashboardCalendar,
    TrainingDaySchedule,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.


class HomeView(TemplateView, LoginRequiredMixin):
    template_name = "training/home.html"

    def get(self, request, *args, **kwargs):
        return redirect("dashboard", view="view")


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
class DashboardView(LoginRequiredMixin, View):
    model = TrainingNight
    template_name = "training/dashboard.html"

    def get(self, request, view, *args, **kwargs):
        context = self.get_context_data(view, request, **kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, view, request, **kwargs):
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

        teach_assignments = MapSeniorTeach.get_senior_queryset_after_date(
            request.user.senior, date.today()
        )
        context["teach_assignments"] = teach_assignments
        night_assignments = MapSeniorNight.get_senior_queryset_after_date(
            request.user.senior, date.today()
        )
        context["night_assignments"] = night_assignments

        context["view"] = view

        return context


# View for specific training night
class TrainingNightView(LoginRequiredMixin, View):
    model = TrainingNight
    template_name = "training/trainingnight.html"

    def get(self, request, night_id, *args, **kwargs):
        night: TrainingNight = TrainingNight.objects.get(pk=night_id)

        level_objects = Level.get_juniors()
        levels = [level_object.name for level_object in level_objects]

        schedule_obj = TrainingDaySchedule()
        schedule = schedule_obj.formatschedule(night, levels)
        mark_safe(schedule)

        roles = MapSeniorNight.get_instructors(night)

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


class TeachFormView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "training/teachform.html"
    form_class = [
        ("Lesson", LessonTeachForm),
        ("Activity", ActivityTeachForm),
    ]

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

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
            teach_id = form.teach_id  # Created in form.save() Method
            return redirect("teach-assign", teach_id=teach_id)
        return render(
            request,
            self.template_name,
            {"form": form, "levels": levels, "nightid": night_id, "formid": form_id},
        )


class AssignTeachView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "training/teachassign.html"
    formset_class = AssignTeachFormset

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def init_form(self, teach_id, teach_instance, *args, **kwargs):
        senior_queryset = Senior.get_all()
        senior_choices = [(senior.id, str(senior)) for senior in senior_queryset]
        formset = self.formset_class(
            *args,
            form_kwargs={
                "teach_id": teach_id,
                "senior_choices": senior_choices,
                "parent_instance": teach_instance,
            },
            instance=teach_instance,
            **kwargs
        )
        return formset

    def get(self, request, teach_id, *args, **kwargs):
        teach_instance = Teach.get_by_teach_id(teach_id)
        formset = self.init_form(teach_id, teach_instance)
        teach_attrs = teach_instance.get_content_attributes()
        return render(
            request,
            self.template_name,
            {"formset": formset, "teach": teach_attrs},
        )

    def post(self, request, teach_id, *args, **kwargs):
        self.object = None
        teach_instance: Teach = Teach.get_by_teach_id(teach_id)
        formset = self.init_form(teach_id, teach_instance, self.request.POST)
        if formset.is_valid():
            formset.save()
            night_id = teach_instance.get_night_id()
            return redirect("trainingnight", night_id=night_id)
        else:
            return render(
                request,
                self.template_name,
                {"formset": formset},
            )


class AssignNightView(FormView):
    template_name = "training/nightassign.html"
    formset_class = AssignNightFormset

    def init_form(self, night_id, night_instance, *args, **kwargs):
        senior_queryset = Senior.get_all()
        senior_choices = [(senior.id, str(senior)) for senior in senior_queryset]
        formset = self.formset_class(
            *args,
            form_kwargs={"night_id": night_id, "senior_choices": senior_choices},
            instance=night_instance,
            **kwargs
        )
        return formset

    def get(self, request, night_id, *args, **kwargs):
        night_instance = TrainingNight.get(night_id)
        formset = self.init_form(night_id, night_instance)
        return render(
            request,
            self.template_name,
            {"formset": formset},
        )

    def post(self, request, night_id, *args, **kwargs):
        self.object = None
        night_instance = TrainingNight.get(night_id)
        formset = self.init_form(night_id, night_instance, self.request.POST)
        if formset.is_valid():
            formset.save()
            return redirect("trainingnight", night_id=night_id)
        else:
            return render(
                request,
                self.template_name,
                {"formset": formset},
            )


# Teach Specific Views
class TeachView(LoginRequiredMixin, TemplateView):
    template_name = "training/teach.html"

    def get_context_data(self, teachid, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = Teach.get_by_teach_id(teachid)

        content_details = instance.get_content_attributes()
        content_type = instance.get_content_type()
        context["content"] = {"type": content_type, "attributes": content_details}

        finished = instance.finished
        context["plan"] = {"finished": finished}
        if finished:
            context["plan"]["link"] = instance.plan

        return context


# Utility Views (views that do things but don't actually have a template)
class EditTrainingNightView(LoginRequiredMixin, UserPassesTestMixin, APIView):
    http_method_names = ["get", "delete"]

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def get(self, request, year, month, day, *args, **kwargs):
        day = date(year, month, day)
        TrainingNight.create(day)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, year, month, day, *args, **kwargs):
        day = date(year, month, day)
        instance = TrainingNight.get_by_date(day)
        instance.delete()
        return Response(status=status.HTTP_200_OK)
