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
import json
import os


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
        'slack_client_id': os.environ.get('SLACK_ATTENT_BOT_CLIENT_ID')
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
    req_method = request.POST

    if req_method.get('token') != SLACK_VERIFICATION_TOKEN:
        return HttpResponse("Not Allowed", status=406)

    django_rq.enqueue(answer_slack_question, req_method.dict())

    # TODO: Save all requests & responses
    return HttpResponse("Working on it...")


@csrf_exempt
def slack_selection(request):
    req_method = request.POST

    payload = json.loads(req_method.get('payload'))

    if payload.get('token') != SLACK_VERIFICATION_TOKEN:
        return HttpResponse("Not Allowed", status=406)

    changed_variable, time_slug, command = payload.get('callback_id').split(' ')
    value = payload.get('actions')[0].get('selected_options')[0].get('value')

    if changed_variable == 'time':
        time_slug = value
    elif changed_variable == 'command':
        command = value

    text = '{time_slug} {command}'.format(time_slug=time_slug, command=command)

    params = {
        'team_id': payload.get('team').get('id'),
        'response_url': payload.get('response_url'),
        'text': text
    }

    django_rq.enqueue(answer_slack_question, params)

    # TODO: Save all requests & responses
    return HttpResponse("Working on {}...".format(text))


def sample_chart(request):
    import pygal

    line_chart = pygal.Treemap()
    line_chart.title = 'Browser usage evolution (in %)'
    line_chart.x_labels = map(str, range(2002, 2013))
    line_chart.add('Firefox', [None, None, 0, 16.6,   25,   31, 36.4, 45.5, 46.3, 42.8, 37.1])
    line_chart.add('Chrome',  [None, None, None, None, None, None,    0,  3.9, 10.8, 23.8, 35.3])
    line_chart.add('IE',      [85.8, 84.6, 84.7, 74.5,   66, 58.6, 54.7, 44.8, 36.2, 26.6, 20.1])
    line_chart.add('Others',  [14.2, 15.4, 15.3,  8.9,    9, 10.4,  8.9,  5.8,  6.7,  6.8,  7.5])
    line_chart.value_formatter = lambda x: '%.2f%%' % x if x is not None else '∅'
    png_data = line_chart.render_to_png()

    response = HttpResponse(png_data, content_type='image/png')
    response['Content-Length'] = len(png_data)

    return response


def slack_redirect_uri(request):
    # TODO What do we need to do here?

    return HttpResponse("redirect uri hit")
