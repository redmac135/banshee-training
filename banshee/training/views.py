import calendar
from datetime import date, datetime, timedelta

from django.views.generic import TemplateView, ListView
from django.views import View
from django.shortcuts import render
from django.utils.safestring import mark_safe

from .models import TrainingNight, Teach, Level

from .utils import TrainingCalendar, DashboardCalendar, TrainingDaySchedule

# Create your views here.


class HomeView(TemplateView):
    template_name = "training/home.html"

# Testing View
class ExampleView(TemplateView):
    template_name = "training/example.html"

# Main Views
class DashboardView(ListView):
    model = TrainingNight
    template_name = "training/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        d = get_date(self.request.GET.get("month", None))
        context["prev_month"] = prev_month(d)
        context["next_month"] = next_month(d)
        cal = DashboardCalendar(d.year, d.month)

        nights = self.model.get_nights(date__year=d.year, date__month=d.month)

        html_cal = cal.formatmonth(nights=nights, today=date.today(), withyear=True)
        context["calendar"] = mark_safe(html_cal)
        context["monthname"] = str(calendar.month_name[d.month]) + " " + str(d.year)
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


# Function for all Calendars
def get_date(req_day):
    if req_day:
        year, month = map(int, req_day.split("-"))
        return date(year, month, day=1)
    return datetime.now()


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


# View for specific training night
class TrainingNightView(View):
    model = TrainingNight
    template_name = "training/trainingnight.html"

    def get(self, request, *args, **kwargs):
        night = TrainingNight.create(datetime.today())
        schedule_obj = TrainingDaySchedule()
        level_objects = levels = Level.get_juniors()
        levels = [level.name for level in levels]
        schedule = schedule_obj.formatschedule(night, levels)
        mark_safe(schedule)
        return render(request, self.template_name, {"schedule": mark_safe(schedule)})
