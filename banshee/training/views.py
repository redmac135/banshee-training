import calendar
from datetime import date, datetime, timedelta

from django.views.generic import TemplateView, FormView
from django.views import View
from django.urls import reverse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.contrib import messages

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MapSeniorNight, MapSeniorTeach, TrainingNight, Level, Teach, Senior
from .forms import (
    AssignTeachFormset,
    AssignNightFormset,
    LessonTeachForm,
    ActivityTeachForm,
    TeachPlanForm,
)
from .utils import (
    DashboardCalendar,
    DueTrainingDaySchedule,
    EditTrainingDaySchedule,
    TrainingDaySchedule,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.


class HomeView(TemplateView, LoginRequiredMixin):
    template_name = "training/home.html"

    def get(self, request, *args, **kwargs):
        return redirect("dashboard", view="view")


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

    def get(self, request, view: str = "view", *args, **kwargs):
        context = self.get_context_data(request, view, **kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, request, view: str = "view", **kwargs):
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
    schedule_class = TrainingDaySchedule
    template_name = "training/night.html"

    def get(self, request, night_id, *args, **kwargs):
        night: TrainingNight = TrainingNight.objects.get(pk=night_id)

        level_objects = Level.get_juniors()
        levels = [level_object.name for level_object in level_objects]

        schedule_obj = self.schedule_class()
        schedule = schedule_obj.formatschedule(night, levels)
        mark_safe(schedule)

        roles = MapSeniorNight.get_instructors(night)

        date = night.date
        title = {}
        title["month"] = date.strftime("%B")
        title["day"] = date.day

        context = {
            "schedule": mark_safe(schedule),
            "nightid": night.pk,
            "roles": roles,
            "title": title,
        }
        context.update(self.get_context_data())

        return render(
            request,
            self.template_name,
            context,
        )

    def get_context_data(self, **kwargs):
        context = {}
        context["view"] = "view"
        return context


class EditTrainingNightView(TrainingNightView):
    schedule_class = EditTrainingDaySchedule

    def get_context_data(self, **kwargs):
        context = {}
        context["view"] = "edit"
        return context


class DueTrainingNightView(TrainingNightView):
    schedule_class = DueTrainingDaySchedule

    def get_context_data(self, **kwargs):
        context = {}
        context["view"] = "due"
        return context


class TeachFormView(LoginRequiredMixin, UserPassesTestMixin, View):
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

    def get(self, request, night_id, form_id, teach_id=None, *args, **kwargs):
        levels = Level.get_juniors()
        content_initial = {}
        if teach_id == None:
            slot_initial = None
        else:
            teach_instance = Teach.get_by_teach_id(teach_id)
            content_initial.update(teach_instance.get_form_content_initial())
            slot_initial = teach_instance.get_form_slot_initial()

        # As get_form_content_initial will override with blank string
        if content_initial["location"] == "":
            content_initial["location"] = Teach.DEFAULT_LOCATION

        form = self.init_form(levels, night_id, form_id, initial=content_initial)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "levels": levels,
                "nightid": night_id,
                "formid": form_id,
                "slot_initial": slot_initial,
                "teach_id": teach_id,
            },
        )

    def post(self, request, night_id, form_id, teach_id=None, *args, **kwargs):
        levels = Level.get_juniors()
        if teach_id == None:
            form = self.init_form(levels, night_id, form_id, data=request.POST)
            slot_initial = None
        else:
            teach_instance = Teach.get_by_teach_id(teach_id)
            initial = teach_instance.get_form_content_initial()
            slot_initial = teach_instance.get_form_slot_initial()
            form = self.init_form(
                levels, night_id, form_id, initial=initial, data=request.POST
            )
        if form.is_valid():
            if form.has_changed():
                form.save()
                teach_id = form.teach_id  # Created in form.save() Method
                messages.success(request, "Teach Created Successfully.")
            if "saveteach" in request.POST:
                return redirect("edit-trainingnight", night_id=night_id)
            if "assignteach" in request.POST:
                return redirect("teach-assign", teach_id=teach_id)
            return redirect("teach-assign", teach_id=teach_id)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "levels": levels,
                "nightid": night_id,
                "formid": form_id,
                "slot_initial": slot_initial,
            },
        )


class AssignTeachView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "training/teachassign.html"
    formset_class = AssignTeachFormset

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def init_form(self, teach_id, teach_instance, *args, **kwargs):
        senior_queryset = Senior.get_all_instructors()
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

    def get_context_data(self, formset, teach_instance, **kwargs):
        context = {}
        context["formset"] = formset
        context["teach_attrs"] = teach_instance.get_content_attributes()
        context["teach_url"] = teach_instance.get_absolute_edit_url()
        context["role_suggestions"] = MapSeniorTeach.DATALIST_SUGGESTIONS

        return context

    def get(self, request, teach_id, *args, **kwargs):
        teach_instance = Teach.get_by_teach_id(teach_id)
        formset = self.init_form(teach_id, teach_instance)
        context = self.get_context_data(formset, teach_instance)
        return render(
            request,
            self.template_name,
            context,
        )

    def post(self, request, teach_id, *args, **kwargs):
        self.object = None
        teach_instance = Teach.get_by_teach_id(teach_id)
        formset = self.init_form(teach_id, teach_instance, self.request.POST)
        context = self.get_context_data(formset, teach_instance)
        if formset.is_valid():
            formset.save()
            night_id = teach_instance.get_night_id()
            messages.success(request, "Seniors Assigned Successfully.")
            return redirect("edit-trainingnight", night_id=night_id)
        else:
            return render(
                request,
                self.template_name,
                context,
            )


class AssignNightView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "training/nightassign.html"
    formset_class = AssignNightFormset

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def get_context_data(self, formset, **kwargs):
        context = {}
        context["formset"] = formset
        context["role_suggestions"] = MapSeniorNight.DATALIST_SUGGESTIONS

        return context

    def init_form(self, night_id, night_instance, *args, **kwargs):
        senior_queryset = Senior.get_all_instructors()
        senior_choices = [(senior.id, str(senior)) for senior in senior_queryset]
        formset = self.formset_class(
            *args,
            form_kwargs={
                "night_id": night_id,
                "senior_choices": senior_choices,
                "parent_instance": night_instance,
            },
            instance=night_instance,
            **kwargs
        )
        return formset

    def get(self, request, night_id, *args, **kwargs):
        night_instance = TrainingNight.get(night_id)
        formset = self.init_form(night_id, night_instance)
        context = self.get_context_data(formset)
        return render(
            request,
            self.template_name,
            context,
        )

    def post(self, request, night_id, *args, **kwargs):
        self.object = None
        night_instance = TrainingNight.get(night_id)
        formset = self.init_form(night_id, night_instance, self.request.POST)
        context = self.get_context_data(formset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Seniors Assigned Successfully.")
            return redirect("trainingnight", night_id=night_id)
        else:
            return render(
                request,
                self.template_name,
                context,
            )


# Teach Specific Views
class TeachView(LoginRequiredMixin, View):
    template_name = "training/teach.html"
    form_class = TeachPlanForm

    def get_context_data(self, teach_id, **kwargs):
        context = {}
        instance = Teach.get_by_teach_id(teach_id)

        content_details = instance.get_content_attributes()
        content_type = instance.get_content_type()
        context["content"] = {"type": content_type, "attributes": content_details}

        finished = instance.finished
        context["plan"] = {"finished": finished}
        if finished:
            context["plan"]["link"] = instance.plan

        context["assignments"] = MapSeniorTeach.get_instructors(instance)
        context["can_edit_plan"] = instance.can_edit_plan(self.request.user.senior)

        context["night_id"] = instance.get_night_id()

        return context

    def get(self, request, teach_id, *args, **kwargs):
        form = self.form_class(teach_id)
        context = self.get_context_data(teach_id)
        context.update({"form": form})
        return render(request, self.template_name, context)

    def post(self, request, teach_id, *args, **kwargs):
        teach_instance = Teach.get_by_teach_id(teach_id)
        if teach_instance.can_edit_plan(request.user.senior):
            form = self.form_class(teach_id, request.POST)
            context = self.get_context_data(teach_id)
            context.update({"form": form})
            if form.is_valid():
                if form.has_changed():
                    form.save()
                    messages.success(request, "Plan Uploaded Successfully.")
                return render(request, self.template_name, context)
        return render(request, self.template_name, context)


# Utility Views (views that do things but don't actually have a template)
class TrainingNightDetailView(LoginRequiredMixin, UserPassesTestMixin, APIView):
    http_method_names = ["get", "delete"]

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def get(self, request, year, month, day, *args, **kwargs):
        day = date(year, month, day)
        TrainingNight.create(day)
        messages.success(request, "Training Day Created.")
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, year, month, day, *args, **kwargs):
        day = date(year, month, day)
        instance = TrainingNight.get_by_date(day)
        instance.delete()
        messages.success(request, "Training Day Deleted.")
        return Response(status=status.HTTP_200_OK)
