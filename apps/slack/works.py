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
from apps.visualizer.warehouse_sql_views import SQLViewGeneratorForContact


time_slugs = ['today', 'yesterday', 'week', 'month', 'quarter']
time_slug_default = 'week'
commands = ['city', 'seniority', 'segment', 'opportunity', 'email', 'call']
command_default = 'seniority'
by_reps = ['rep']


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

    response_json = {
        "text": result.get('title', 'Not Specified'),
        "replace_original": True,
        "delete_original": True,
        "attachments": [
            {
                "text": "Change Question",
                "color": "#FF3333",
                "attachment_type": "default",
                "callback_id": "question_selection",
                "actions": [
                    {
                        "name": "question_list",
                        "text": "Select Question...",
                        "type": "select",
                        "options": [
                            {
                                "text": "Meetings by City",
                                "value": "city"
                            },
                            {
                                "text": "Meetings by Seniority",
                                "value": "seniority"
                            },
                            {
                                "text": "Meetings by Segment",
                                "value": "segment"
                            },
                            {
                                "text": "Meetings by Opportunity",
                                "value": "oppty"
                            },
                            {
                                "text": "Meetings by Region",
                                "value": "region"
                            }
                        ],
                        # "selected_options": [
                        #     {
                        #         "text": stringcase.capitalcase(time_slug),
                        #         "value": time_slug
                        #     }
                        # ]
                    }
                ]
            },
            {
                "text": "Choose time interval",
                "color": "#FFAAAA",
                "attachment_type": "default",
                "callback_id": "time_interval_selection",
                "actions": [
                    {
                        "name": "time_interval_list",
                        "text": "Select Time Interval...",
                        "type": "select",
                        "options": [
                            {
                                "text": "Today",
                                "value": "today"
                            },
                            {
                                "text": "Yesterday",
                                "value": "yesterday"
                            },
                            {
                                "text": "Week",
                                "value": "week"
                            },
                            {
                                "text": "Month",
                                "value": "month"
                            },
                            {
                                "text": "Quarter",
                                "value": "quarter"
                            }
                        ],
                        "selected_options": [
                            {
                                "text": stringcase.capitalcase(time_slug),
                                "value": time_slug
                            }
                        ]
                    }
                ]
            },
            {
                "color": "8888FF",
                "fallback": "Here Comes a Fallback!",
                "callback_id": "blue-ish callback ID",
                "fields": result.get('fields', [])
            },
        ]
    }

    requests.post(response_url, json=response_json)

# request.POST
# {'token': ['KHj2Wr8dLI7OHnLGWdKGVUmy'],
#  'team_id': ['T2MH8D152'],
#  'team_domain': ['attent-team'],
#  'channel_id': ['C5S03KG10'],
#  'channel_name': ['statsbots_test'],
#  'user_id': ['U6MH3117U'],
# 'user_name': ['cun3yt'],
# 'command': ['/attent'],
# 'text': ['week'],
# 'response_url': ['https://hooks.slack.com/commands/T2MH8D152/264407892822/r99HE4yBWBPp23gC1atLox1r'],
# 'trigger_id': ['263447371859.89586443172.30bc6b844847899b3d6b80c57b6d04d5']
# }


def answer_parsed_question(client: Client, time_slug, command, by_rep):
    time_beginning, time_ending = time_slug_to_interval(time_slug)

    if command == 'seniority':
        warehouse_model = client.get_warehouse_view_model_for_contact()
        q_set = warehouse_model.objects.filter(meeting_date__range=[time_beginning, time_ending])
        return slack_seniority_groups(q_set, by_rep, time_slug)

    warehouse_model = client.get_warehouse_view_model_for_oppty()
    q_set = warehouse_model.objects.filter(meeting_date__range=[time_beginning, time_ending])

    if command == 'city':
        return slack_top_cities(q_set)
    elif command == 'segment':
        return slack_segments(q_set, by_rep)

    return slack_all_time_titles(warehouse_model)


def slack_top_cities(q_set):
    result_set = q_set.values('billing_city').annotate(count=Count('meeting_id', distinct=True)).order_by("-count").\
                     using('warehouse')[:5]
    return "\n".join("{}: {}".format(result.get('billing_city', ''), result.get('count', ''))
                     for result in result_set)


def slack_seniority_groups(q_set, by_rep, time_slug):
    if by_rep:
        raise Exception('Not Implemented')

    q_set_limited = q_set.filter(contact_seniority__isnull=False).values('contact_seniority'). \
        annotate(count=Count('meeting_id', distinct=True), distinct_contacts=Count('email', distinct=True)). \
        order_by("-count").using('warehouse')

    print(str(q_set_limited.query))

    result_set = q_set_limited[:20]

    order = SQLViewGeneratorForContact.seniority_to_order()

    ordered_set = sorted(result_set, key=lambda item: order.get(item['contact_seniority'], 100))

    fields = [
        {
            "title": "{index}. {title}".format(index=index, title=result.get('contact_seniority', '')),
            "value": "{num_meetings} Meeting(s) with {num_contacts} contact(s)".format(
                num_meetings=result.get('count', ''),
                num_contacts=result.get('distinct_contacts', '')),
            "short": True
        } for index, result in enumerate(ordered_set, start=1)
    ]

    return {
        "title": "How many meetings by seniority (C-Level, VP, Director, etc) "
                 "this {time_int}?".format(time_int=time_slug),
        "fields": fields
    }


def slack_segments(q_set, by_rep):
    # 51, 200, 500, 1000
    if by_rep:
        raise Exception('Not Implemented')


def slack_all_time_titles(WarehouseModel):
    result_set = WarehouseModel.objects.filter(contact_title__isnull=False).values('contact_title').\
                     annotate(count=Count('meeting_id')).order_by("-count").using('warehouse')[:5]

    result = "\n".join("{}: {}".format(result.get('contact_title', ''), result.get('count', ''))
                       for result in result_set)
    return result


# Acct Name, Num of Employees, Contact name, contact title, Agenda: Yes/No
# {
#   rep name => {
#       total_oppty,
#       seniority => {level => number},
#       segment => {level => number}
#   }
# }


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


# Apply date Series  - today, yesterday, this week, this month, this quarter

# >>> * What are the top 5 cities for meetings this XXXX?
# * How many Call Connects by person this XXXX?

# >>> * How many Meetings by Seniority (C-Level, VP, Director, etc) this XXXX?
# * How many Meetings by Segment this XXXX?
# * What is the average Opportunity Amount for meetings this XXXX?
# * How many Email Replies by Seniority (C-Level, VP, Director, etc) this XXXX?

# * How many Meetings by Seniority (C-Level, VP, Director, etc) this XXXX by Rep?
# * What is the average Opportunity Amount for meetings this XXXX by Rep?
# * How many Meetings by Segment this XXXX by Rep?
# * How many Email Replies by Seniority (C-Level, VP, Director, etc) this XXXX by Rep?
