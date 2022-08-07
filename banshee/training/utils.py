from calendar import HTMLCalendar


class TrainingCalendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(TrainingCalendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events, today):
        events_per_day = events.filter(date__day=day)
        d = ""
        for event in events_per_day:
            d += f"<li> {event} </li>"

        if day != 0:
            if today == None:
                class_ = ""
            else:
                class_ = ' class="istoday"' if day == today.day else ""
            return f"<td{class_}><span class='date'>{day}</span><ul> {d} </ul></td>"
        return "<td></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events, today):
        week = ""
        for d, weekday in theweek:
            week += self.formatday(d, events, today)
        return f"<tr> {week} </tr>"

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, nights, today, withyear=True):
        events = nights

        if not self.year == today.year or not self.month == today.month:
            today = None

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
        cal += f"{self.formatweekheader()}\n"
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events, today)}\n"
        return cal


class DashboardCalendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(DashboardCalendar, self).__init__()

    def formatday(self, day, events, today):
        event_today = events.filter(date__day=day).exists()
        d = ""
        if event_today:
            d += ' small-day-green-highlight' # space nesscary to keep classes seperated 
        if day == today.day:
            d += ' small-day-yellow-circle'
        if d:
            return f"""<td><div class='w-full h-full'>
                    <div class='small-day-highlight-wrapper'>
                        <a role="link" tabindex="0"
                            class="small-day-highlight-base{d}">{day}</a>
                    </div>
                </div></td>"""

        if day != 0:
            return f"<td><div class='small-day-wrapper'><p class='small-day-number'>{day}</p></div></td>"
        return "<td><div class='small-day-wrapper'></div></td>"

    def formatweek(self, theweek, events, today):
        week = ""
        for d, weekday in theweek:
            week += self.formatday(d, events, today)
        return f"<tr> {week} </tr>"

    def formatmonth(self, nights, today, withyear=True):
        events = nights

        if not self.year == today.year or not self.month == today.month:
            today = None

        cal = ""
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events, today)}\n"
        return cal
