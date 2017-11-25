from apps.visualizer.models import Client
import requests
import pytz
from datetime import datetime
from datetime import timedelta
from delorean import Delorean
import calendar
import math
from django.db.models import Count
import stringcase
from apps.visualizer.warehouse_sql_views import SQLViewGeneratorForContact, SQLViewGeneratorForAccount
from collections import defaultdict


time_slugs = ['today', 'yesterday', 'week', 'month', 'quarter']
time_slug_default = 'week'
commands = ['city', 'seniority', 'segment', 'region',]  # 'opportunity', 'email', 'call']
command_default = 'seniority'
by_reps = ['rep']


def get_option(slug):
    return {"text": stringcase.capitalcase(slug), "value": slug}


def get_options(slug_list):
    return [get_option(slug) for slug in slug_list]


def question_time_formatting(question, time_slug):
    time = time_slug
    if time_slug not in ('today', 'yesterday'):
        time = "this {}".format(time_slug)
    return "{question} {time}?".format(question=question, time=time)


def parse_args(arguments):
    time_slug = None
    command = None
    by_rep = None

    for argument in arguments:
        if argument in time_slugs:
            time_slug = argument
        elif argument in commands:
            command = argument
        elif argument in by_reps:
            by_rep = argument

    return (time_slug if time_slug else time_slug_default), (command if command else command_default), by_rep


def answer_slack_question(params):
    team_id = params.get('team_id')
    response_url = params.get('response_url')

    client_qset = Client.objects.filter(slack_team_id=team_id)

    result = None

    if client_qset.count() < 1:
        result = "Your team is not associated with an Attent client. Please reach out to the Attent team."
    elif client_qset.count() > 1:
        result = "Your team is associated with more than one Attent client. Please reach out to the Attent team."

    client = client_qset[0]

    if not client.is_active():
        result = "Your company's Attent account is not active. Please reach out to the Attent team."

    if result:
        response_json = {
            "text": result,
            "replace_original": True
        }
        requests.post(response_url, json=response_json)
        return

    time_slug, command, by_rep = parse_args(params.get('text').lower().split(' '))
    result = answer_parsed_question(client, time_slug, command, by_rep)
    callback_id_shared_part = "{time_slug} {cmd}".format(time_slug=time_slug, cmd=command)

    attachments = [
        {
            "text": "Meetings By...",
            "color": "#FF3333",
            "attachment_type": "default",
            "callback_id": "command {shared_part}".format(shared_part=callback_id_shared_part),
            "actions": [
                {
                    "name": "question_list",
                    "text": "Select Question...",
                    "type": "select",
                    "options": get_options(commands),
                    "selected_options": [get_option(command)],
                }
            ]
        },
        {
            "text": "Time Interval",
            "color": "#FFAAAA",
            "attachment_type": "default",
            "callback_id": "time {callback_id_shared_part}".format(callback_id_shared_part=callback_id_shared_part),
            "actions": [
                {
                    "name": "time_interval_list",
                    "text": "Select Time Interval...",
                    "type": "select",
                    "options": get_options(time_slugs),
                    "selected_options": [get_option(time_slug)],
                }
            ]
        },
        {
            "color": "8888FF",
            "fallback": "Here Comes a Fallback!",
            "callback_id": "blue-ish callback ID",
            "fields": result.get('fields', []),
        },
    ]

    if result.get('chart_url'):
        attachments[-1]["image_url"] = result.get('chart_url')

    response_json = {
        "text": result.get('title', 'Not Specified'),
        "replace_original": True,
        "delete_original": True,
        "attachments": attachments
    }

    requests.post(response_url, json=response_json)


def answer_parsed_question(client: Client, time_slug, command, by_rep):
    time_beginning, time_ending = time_slug_to_interval(time_slug)

    if command == 'seniority':
        warehouse_model = client.get_warehouse_view_model_for_contact()
        q_set = warehouse_model.objects.filter(meeting_date__range=[time_beginning, time_ending])
        return slack_seniority_groups(q_set, by_rep, time_slug)

    if command == 'city':
        warehouse_model = client.get_warehouse_view_model_for_account()
        q_set = warehouse_model.objects.filter(meeting_date__range=[time_beginning, time_ending])
        return slack_top_cities(q_set, time_slug)

    if command == 'segment':
        warehouse_model = client.get_warehouse_view_model_for_account()
        q_set = warehouse_model.objects.filter(meeting_date__range=[time_beginning, time_ending])
        return slack_segments(q_set, time_slug, by_rep)

    if command == 'region':
        warehouse_model = client.get_warehouse_view_model_for_account()
        q_set = warehouse_model.objects.filter(meeting_date__range=[time_beginning, time_ending])
        return slack_regions(q_set, time_slug, by_rep)

    warehouse_model = client.get_warehouse_view_model_for_oppty()
    return slack_all_time_titles(warehouse_model)


def slack_seniority_groups_by_rep(q_set, time_slug):
    q_set_limited = q_set.filter(contact_seniority__isnull=False).values('first_name', 'contact_seniority'). \
        annotate(count=Count('meeting_id', distinct=True), distinct_contacts=Count('email', distinct=True)). \
        order_by('first_name').using('warehouse')
    # "Group by" can include Role. Also output can include email in case there is no "first_name" & "role"

    res = defaultdict(SQLViewGeneratorForContact.default_dict({'count': 0, 'distinct_contacts': 0}))

    for row in q_set_limited:
        rep_id = row.get('first_name') if row.get('first_name', None) else 'Unknown'
        seniority = row.get('contact_seniority')
        res[rep_id][seniority] = {'count': row.get('count'), 'distinct_contacts': row.get('distinct_contacts')}

    line = "{level}: {count} meeting(s) with {contacts} contact(s)"
    line_zero_state = "{level}: no meetings"

    fields = [
        {
            "title": "{index}. {name}".format(index=index, name=rep_id),
            "value": "\n".join([(line if counts['count'] > 0 else line_zero_state).format(level=level,
                                                                                          count=counts['count'],
                                                                                          contacts=counts['distinct_contacts'])
                                for level, counts in result.items()]),
            "short": True
        } for index, (rep_id, result) in enumerate(res.items(), start=1)
    ]

    question = question_time_formatting("How many meetings by seniority (C-Level, VP, Director, etc) by rep", time_slug)

    if len(fields) < 1:
        return {"title": "{q}\nThere is no meeting data for this time interval.".format(q=question)}

    return {
        "title": question,
        "fields": fields
    }


def slack_seniority_groups(q_set, by_rep, time_slug):
    if by_rep:
        return slack_seniority_groups_by_rep(q_set, time_slug)

    result_set = q_set.filter(contact_seniority__isnull=False).values('contact_seniority'). \
        annotate(count=Count('meeting_id', distinct=True), distinct_contacts=Count('email', distinct=True)). \
        using('warehouse')[:20]

    ordered_set = SQLViewGeneratorForContact.order_list_by_seniority_level(result_set, 'contact_seniority')

    line = "{num_meetings} Meeting(s) with {num_contacts} contact(s)"
    line_zero_state = "No Meetings"

    fields = [
        {
            "title": "{index}. {title}".format(index=index, title=result.get('contact_seniority', '')),
            "value": (line if result.get('count', 0) > 0 else line_zero_state).format(
                num_meetings=result.get('count', ''),
                num_contacts=result.get('distinct_contacts', '')),
            "short": True
        } for index, result in enumerate(ordered_set, start=1)
    ]

    question = question_time_formatting("How many meetings by seniority (C-Level, VP, Director, etc)", time_slug)

    if len(fields) < 1:
        return {"title": "{q}\nThere is no meeting data for this time interval.".format(q=question)}

    graph_values = {
        "meetings_series": ",".join([str(result.get('count', 0)) for result in ordered_set]),
        "contacts_series": ",".join([str(result.get('distinct_contacts', 0)) for result in ordered_set]),
        "seniority": "|".join([result.get('contact_seniority', '') for result in ordered_set])
    }

    series = "{}|{}".format(graph_values["meetings_series"], graph_values["contacts_series"])
    titles = "|{}".format(graph_values["seniority"])

    return {
        "title": question,
        "fields": fields,
        "chart_url": "https://image-charts.com/chart?cht=bvg&chs=990x400&chd=t:{series}&chf=b0,lg,0,4ECDC4,0,556270,"
                     "1&chxt=y,x&chxl=1:{titles}&chdl=Meetings|Contacts&chma=20,0,20,20".format(series=series,
                                                                                                titles=titles),
    }


def slack_top_cities(q_set, time_slug):
    result_set = q_set.filter(billing_city__isnull=False).values('billing_city'). \
        annotate(count=Count('meeting_id', distinct=True), distinct_contacts=Count('email', distinct=True)). \
        order_by('-count', '-distinct_contacts').using('warehouse')[:5]

    line = "{num_meetings} Meeting(s) with {num_contacts} contact(s)"
    line_zero_state = "No Meetings"

    fields = [
        {
            "title": "{index}. {title}".format(index=index, title=result.get('billing_city', '')),
            "value": (line if result.get('count', 0) > 0 else line_zero_state).format(
                num_meetings=result.get('count', ''),
                num_contacts=result.get('distinct_contacts', '')),
            "short": True,
        } for index, result in enumerate(result_set, start=1)
    ]

    question = question_time_formatting("What are the top 5 cities for meetings", time_slug)

    if len(fields) < 1:
        return {"title": "{q}\nThere is no meeting data for this time interval.".format(q=question)}

    from urllib.parse import quote

    graph_values = {
        "meetings_series": ",".join([str(result.get('count', 0)) for result in result_set]),
        "contacts_series": ",".join([str(result.get('distinct_contacts', 0)) for result in result_set]),
        "city": "|".join([str(quote(result.get('billing_city', ''))) for result in result_set])
    }

    series = "{}|{}".format(graph_values["meetings_series"], graph_values["contacts_series"])
    titles = "|{}".format(graph_values["city"])

    return {
        "title": question,
        "fields": fields,
        "chart_url": "https://image-charts.com/chart?cht=bvg&chs=990x400&chd=t:{series}&chf=b0,lg,0,4ECDC4,0,556270,"
                     "1&chxt=y,x&chxl=1:{titles}&chdl=Meetings|Contacts&chma=20,0,20,20".format(series=series,
                                                                                                titles=titles),
    }


def slack_segments(q_set, time_slug, by_rep):
    if by_rep:
        raise Exception('Not Implemented')

    result_set = q_set.values('account_target'). \
        annotate(count=Count('meeting_id', distinct=True), distinct_contacts=Count('email', distinct=True)). \
        using('warehouse')

    ordered_set = SQLViewGeneratorForAccount.order_list_by_targets(result_set, 'account_target')

    line = "{num_meetings} Meeting(s) with {num_contacts} contact(s)"
    line_zero_state = "No Meetings"

    fields = [
        {
            "title": "{index}. {title}".format(index=index, title=result.get('account_target', '')),
            "value": (line if result.get('count', 0) > 0 else line_zero_state).format(
                num_meetings=result.get('count', ''),
                num_contacts=result.get('distinct_contacts', '')),
            "short": True
        } for index, result in enumerate(ordered_set, start=1)
    ]

    question = question_time_formatting("How many meetings by segment", time_slug)

    if len(fields) < 1:
        return {"title": "{q}\nThere is no meeting data for this time interval.".format(q=question)}

    return {
        "title": question,
        "fields": fields
    }


def slack_regions(q_set, time_slug, by_rep):
    if by_rep:
        raise Exception('Not Implemented')

    result_set = q_set.values('account_region'). \
        annotate(count=Count('meeting_id', distinct=True), distinct_contacts=Count('email', distinct=True)). \
        using('warehouse')

    ordered_set = SQLViewGeneratorForAccount.order_list_by_regions(result_set, 'account_region')

    fields = [
        {
            "title": "{index}. {title}".format(index=index, title=result.get('account_region', '')),
            "value": "{num_meetings} Meeting(s) with {num_contacts} contact(s)".format(
                num_meetings=result.get('count', ''),
                num_contacts=result.get('distinct_contacts', '')),
            "short": True
        } for index, result in enumerate(ordered_set, start=1)
    ]

    question = question_time_formatting("How many meetings by region", time_slug)

    if len(fields) < 1:
        return {"title": "{q}\nThere is no meeting data for this time interval.".format(q=question)}

    return {
        "title": question,
        "fields": fields
    }


def slack_all_time_titles(warehouse_model):
    result_set = warehouse_model.objects.filter(contact_title__isnull=False).values('contact_title').\
                     annotate(count=Count('meeting_id')).order_by("-count").using('warehouse')[:5]

    result = "\n".join("{}: {}".format(result.get('contact_title', ''), result.get('count', ''))
                       for result in result_set)
    return result


def time_slug_to_interval(slug='week'):
    timezone_name = 'US/Pacific'
    dt_format = 'YYYY-MM-dd HH:mm:ssZ'

    tz = pytz.timezone(timezone_name)

    now = datetime.now(tz)
    today = now.date()

    today_start_dt = datetime(now.year, now.month, now.day, 0, 0, 0)
    today_start = Delorean(datetime=today_start_dt, timezone=timezone_name)

    today_end_dt = datetime(now.year, now.month, now.day, 23, 59, 59)
    today_end = Delorean(datetime=today_end_dt, timezone=timezone_name)

    if slug == 'today':
        return today_start.format_datetime(dt_format), today_end.format_datetime(dt_format)

    elif slug == 'yesterday':
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_end - timedelta(days=1)
        return yesterday_start.format_datetime(dt_format), yesterday_end.format_datetime(dt_format)

    elif slug == 'week':
        week_day = today.weekday()
        week_start = today_start - timedelta(days=week_day)
        week_end = today_end + timedelta(days=(6 - week_day))
        return week_start.format_datetime(dt_format), week_end.format_datetime(dt_format)

    elif slug == 'month':
        _, num_days = calendar.monthrange(today_start_dt.year, today_start_dt.month)
        month_start = Delorean(datetime=datetime(today_start_dt.year, today_start_dt.month, 1, 0, 0, 0),
                               timezone=timezone_name)
        month_end = Delorean(datetime=datetime(today_start_dt.year, today_start_dt.month, num_days, 23, 59, 59),
                             timezone=timezone_name)
        return month_start.format_datetime(dt_format), month_end.format_datetime(dt_format)

    elif slug == 'quarter':
        beginning_month = int(math.ceil(today.month/3)*3-2)
        beginning_dt = datetime(today_start_dt.year, beginning_month, 1, 0, 0, 0)
        quarter_start = Delorean(datetime=beginning_dt, timezone=timezone_name)

        ending_month = int(math.ceil(today.month/3)*3)
        _, ending_month_num_days = calendar.monthrange(today.year, ending_month)

        quarter_end = Delorean(datetime=datetime(today_start_dt.year, ending_month, ending_month_num_days, 23, 59, 59),
                               timezone=timezone_name)

        return quarter_start.format_datetime(dt_format), quarter_end.format_datetime(dt_format)


# >>> * What are the top 5 cities for meetings this XXXX?
# >>> * How many Meetings by Seniority (C-Level, VP, Director, etc) this XXXX?
# >>> * How many Meetings by Segment this XXXX?

# * How many Call Connects by person this XXXX?
# * What is the average Opportunity Amount for meetings this XXXX?
# * How many Email Replies by Seniority (C-Level, VP, Director, etc) this XXXX?

# ============================================================

# * How many Meetings by Seniority (C-Level, VP, Director, etc) this XXXX by Rep?
# * How many Meetings by Segment this XXXX by Rep?

# * What is the average Opportunity Amount for meetings this XXXX by Rep?
# * How many Email Replies by Seniority (C-Level, VP, Director, etc) this XXXX by Rep?
