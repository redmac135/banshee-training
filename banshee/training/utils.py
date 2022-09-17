from calendar import HTMLCalendar
from .models import *
from django.urls import reverse


class TrainingDaySchedule:
    def formatlesson(self, lesson: Teach):
        return f"<td><a href='{lesson.get_absolute_url()}' class='block p-2 m-2 w-auto min-h-24 bg-clr-1 hover:bg-green-900 rounded-lg shadow-md'>{lesson.format_html_block()}</a></td>"

    def formatperiod(self, periodnum: int, period: TrainingPeriod):
        period_html = f"<th>P{str(periodnum)}</th>"

        for lesson in period.get_teach_instances():
            period_html += self.formatlesson(lesson)

        return f"<tr>{period_html}</tr>"

    def formatheader(self, levels: list):
        header = "<th></th>"

        for level in levels:
            header += f"<th>{str(level)}</th>"

        return f"<tr>{header}</tr>"

    def formatschedule(self, night: TrainingNight, levels: list):
        schedule = self.formatheader(levels)
        for number, period in enumerate(night.get_periods(), 1):
            schedule += self.formatperiod(number, period)

        return schedule


class EditTrainingDaySchedule(TrainingDaySchedule):
    def formatlesson(self, lesson: Teach):
        return f"<td><a href='{lesson.get_absolute_edit_url()}' class='block p-2 m-2 w-auto min-h-24 bg-blue-700 hover:bg-blue-900 rounded-lg shadow-md'>{lesson.format_html_block()}</a></td>"

class DueTrainingDaySchedule(TrainingDaySchedule):
    def formatlesson(self, lesson: Teach):
        status = lesson.get_status()
        print(status)
        if status == "Submitted":
            return f"<td><a href='{lesson.get_absolute_url()}' class='block p-2 m-2 w-auto min-h-24 bg-banshee-green-800 hover:bg-green-900 rounded-lg shadow-md text-black'>{lesson.format_html_block()}</a></td>"
        if status == "Not Submitted":
            return f"<td><a href='{lesson.get_absolute_url()}' class='block p-2 m-2 w-auto min-h-24 bg-gray-400 hover:bg-green-900 rounded-lg shadow-md text-black'>{lesson.format_html_block()}</a></td>"
        if status == "Missing":
            return f"<td><a href='{lesson.get_absolute_url()}' class='block p-2 m-2 w-auto min-h-24 bg-red-600 hover:bg-green-900 rounded-lg shadow-md'>{lesson.format_html_block()}</a></td>"
        return f"<td><a href='{lesson.get_absolute_url()}' class='block p-2 m-2 w-auto min-h-24 bg-clr-1 hover:bg-green-900 rounded-lg shadow-md'>{lesson.format_html_block()}</a></td>"


class ViewDashboardCalendar(HTMLCalendar):
    def formatday(self, day, events, today):
        event_today = events.filter(date__day=day).exists()
        href = "#"
        d = ""
        if event_today:
            d += (
                " small-day-green-highlight"  # space nesscary to keep classes seperated
            )
            event_instance = events.get(date__day=day)
            href = reverse("trainingnight", args=[event_instance.pk])
        if day != 0 and today != None:
            if day == today.day:
                d += " small-day-yellow-circle"
        if d:
            return f"""<td><div class='w-full h-full'>
                    <div class='small-day-highlight-wrapper'>
                        <a role="link" tabindex="0" href="{href}"
                            class="small-day-highlight-base{d}">{day}</a>
                    </div>
                </div></td>"""

        if day != 0:
            return f"<td><div class='small-day-wrapper'><p class='small-day-number'>{day}</p></div></td>"
        return "<td><div class='small-day-wrapper'></div></td>"


class CreateDashboardCalendar(HTMLCalendar):
    def formatday(self, day, events, today):
        event_today = events.filter(date__day=day).exists()
        href = reverse("api-trainingnight", args=[self.year, self.month, day])

        if event_today:
            return f"""<td><div class='w-full h-full'>
                <div class='small-day-highlight-wrapper'>
                    <a role="link" tabindex="0" href="#"
                        class="small-day-highlight-base small-day-blue-highlight">{day}</a>
                </div>
            </div></td>"""

        if day != 0:
            return f"""<td><div class='small-day-wrapper'><button onclick='createnight("{href}")'><p class='small-day-blue-number'>{day}</p></button></div></td>"""
        return "<td><div class='small-day-wrapper'></div></td>"


class DeleteDashboardCalendar(HTMLCalendar):
    def formatday(self, day, events, today):
        event_today = events.filter(date__day=day).exists()
        href = reverse("api-trainingnight", args=[self.year, self.month, day])

        if event_today:
            return f"""<td><div class='small-day-highlight-wrapper'><button onclick='deletenight("{href}")'><p class='small-day-highlight-base small-day-red-highlight'>{day}</p></button></div></td>"""

        if day != 0:
            return f"""<td><div class='small-day-wrapper'><p class='small-day-red-number'>{day}</p></div></td>"""
        return "<td><div class='small-day-wrapper'></div></td>"


class DashboardCalendar(HTMLCalendar):
    view: ViewDashboardCalendar

    def __init__(self, view, year=None, month=None):
        if view == "view":
            self.view = ViewDashboardCalendar
        elif view == "create":
            self.view = CreateDashboardCalendar
        elif view == "delete":
            self.view = DeleteDashboardCalendar

        self.year = year
        self.month = month
        super(DashboardCalendar, self).__init__()

    def formatweek(self, theweek, events, today):
        week = ""
        for d, weekday in theweek:
            week += self.view.formatday(
                self, d, events, today
            )  # Call function based on view
        return f"<tr> {week} </tr>"

    def formatmonth(self, nights, today, withyear=True):
        events = nights

        if not self.year == today.year or not self.month == today.month:
            today = None

        cal = ""
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events, today)}\n"
        return cal
