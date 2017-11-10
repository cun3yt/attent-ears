from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.http import HttpResponse
from apps.outreach.syncer import outreach_connect_url, outreach_exchange_for_access_token
from apps.api_connection.models import ApiConnection
from apps.salesforce.authentication import salesforce_connect_url, salesforce_exchange_for_access_token
from ears.settings import SLACK_VERIFICATION_TOKEN

import django_rq
from apps.slack.works import answer_slack_question


def index(request):
    context = {}

    if request.user.is_authenticated():
        return redirect(reverse('settings'))

    return render(request, 'landing-page.html', context=context)

    # template = 'index.html'
    #
    # if not request.user.is_authenticated():
    #     return render(request, template, context=context)
    #
    # client = request.user.client
    #
    # all_dashboards = client.periscopedashboard_set.filter(is_visible=True)
    # dashboard_id = request.GET.get('dashboard_id', '')
    #
    # selected_dashboard_set = all_dashboards.filter(periscope_dashboard_id=dashboard_id)
    #
    # context['all_dashboards'] = all_dashboards
    #
    # if selected_dashboard_set.count() == 0:
    #     context['no_dashboard_selected'] = True
    #     return render(request, template, context=context)
    #
    # selected_dashboard = selected_dashboard_set[0]
    #
    # api_key = client.extra_info['periscope_api_key']
    # url = selected_dashboard.get_embed_url(api_key)
    #
    # context['dashboards'] = client.periscopedashboard_set.filter(is_visible=True)
    #
    # context['selected_dashboard'] = {
    #     'url': url,
    #     'id': selected_dashboard.id
    # }
    #
    # return render(request, template, context=context)


@csrf_exempt
def sign_out(request):
    if request.method == 'GET':
        logout(request)

    return redirect('/')


def settings(request):
    if not request.user.is_authenticated():
        redirect('/')

    current_outreach_connection = None
    try:
        current_outreach_connection = request.user.api_connections.get(type='outreach')
    except Exception:
        pass

    current_salesforce_connection = None
    try:
        current_salesforce_connection = request.user.api_connections.get(type='salesforce')
    except Exception:
        pass

    outreach_connection = {
        'name': 'outreach',
        'setting_name': 'Outreach',
        'meta': 'Sales Engagement Platform',
        'detail': current_outreach_connection,
    }

    salesforce_connection = {
        'name': 'salesforce',
        'setting_name': 'Salesforce',
        'meta': 'Customer Relationship Management',
        'detail': current_salesforce_connection,
    }

    if not current_outreach_connection:
        redirect_uri = request.build_absolute_uri(reverse('outreach-redirect'))
        outreach_connection['connect_url'] = outreach_connect_url(redirect_uri)

    if not current_salesforce_connection:
        redirect_uri = request.build_absolute_uri(reverse('salesforce-redirect'))
        salesforce_connection['connect_url'] = salesforce_connect_url(redirect_uri)

    api_connections = {
        'data_api': [
            salesforce_connection,
            outreach_connection,
        ],
    }

    context = {
        'api_connections': api_connections,
    }

    return render(request, 'settings.html', context=context)


def outreach_redirect(request):
    if not request.user.is_authenticated():
        redirect('/')

    authorization_code = request.GET.get('code')

    redirect_uri = request.build_absolute_uri(reverse('outreach-redirect'))
    resp = outreach_exchange_for_access_token(authorization_code, redirect_uri)

    ApiConnection.objects.update_or_create(type='outreach',
                                           user=request.user,
                                           defaults={'data': resp.text})    # TODO: must be resp.json()
    return redirect(reverse('settings'))


def salesforce_redirect(request):
    if not request.user.is_authenticated():
        redirect('/')

    authorization_code = request.GET.get('code')

    redirect_uri = request.build_absolute_uri(reverse('salesforce-redirect'))
    resp = salesforce_exchange_for_access_token(authorization_code=authorization_code, redirect_uri=redirect_uri)

    ApiConnection.objects.update_or_create(type='salesforce',
                                           user=request.user,
                                           defaults={'data': resp.json()})
    return redirect(reverse('settings'))


@csrf_exempt
def slack_command(request):
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
    #
    # {'token': ['KHj2Wr8dLI7OHnLGWdKGVUmy'],
    # 'team_id': ['T2MH8D152'],
    # 'team_domain': ['attent-team'],
    # 'channel_id': ['D6NKTJ32B'],
    # 'channel_name': ['directmessage'],
    # 'user_id': ['U6MH3117U'],
    # 'user_name': ['cun3yt'],
    # 'command': ['/attent'],
    # 'text': ["what's up"],
    # 'response_url': ['https://hooks.slack.com/commands/T2MH8D152/262877675392/bwkqc2q2SdKENHBfwSZ4BBuL'],
    # 'trigger_id': ['262877675408.89586443172.cf24e6cf8ab6f08d99fb03abbc4837c6']}

    # TODO: Save all requests & responses

    if request.POST.get('token') != SLACK_VERIFICATION_TOKEN:
        return HttpResponse("Not Allowed", status=406)

    req_method = request.POST

    django_rq.enqueue(answer_slack_question, req_method.get('team_id'), req_method.get('response_url'))
    return HttpResponse("Working on it...")


def slack_individuals_meetings(date_interval=None):
    # Acct Name, Num of Employees, Contact name, contact title, Agenda: Yes/No
    pass


def slack_team_meetings_summary(date_interval=None):
    # {
    #   rep name => {
    #       total_oppty,
    #       seniority => {level => number},
    #       segment => {level => number}
    #   }
    # }
    pass


def slack_redirect_uri(request):
    # TODO What do we need to do here?

    return HttpResponse("redirect uri hit")


# Apply date Series  - today, yesterday, this week, this month, this quarter
#
# * What are the top 5 cities for meetings this XXXX?
# * How many Meetings by Seniority (C-Level, VP, Director, etc) this XXXX?
# * How many Meetings by Segment this XXXX?
# * What is the average Opportunity Amount for meetings this XXXX?
# * How many Email Replies by Seniority (C-Level, VP, Director, etc) this XXXX?
# * How many Call Connects by person this XXXX?
# * How many Meetings by Seniority (C-Level, VP, Director, etc) this XXXX by Rep?
# * How many Email Replies by Seniority (C-Level, VP, Director, etc) this XXXX by Rep?
# * What is the average Opportunity Amount for meetings this XXXX by Rep?
# * How many Meetings by Segment this XXXX by Rep?
