from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.http import HttpResponse
from apps.outreach.syncer import outreach_connect_url, outreach_exchange_for_access_token
from apps.api_connection.models import ApiConnection
from apps.salesforce.authentication import salesforce_connect_url, salesforce_exchange_for_access_token
from ears.settings import SLACK_VERIFICATION_TOKEN

from .models import Client


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

    team_id = request.POST.get('team_id')
    client_qset = Client.objects.filter(slack_team_id=team_id)

    if client_qset.count() < 1:
        return HttpResponse("Your team is not associated with an Attent client. Please reach out to the Attent team.")

    if client_qset.count() > 1:
        return HttpResponse("Your team is associated with more than one Attent client. "
                            "Please reach out to the Attent team.")

    client = client_qset[0]

    if not client.is_active():
        return HttpResponse("Your company's Attent account is not active. Please reach out to the Attent team.")

    if not client.warehouse_view_name:
        return HttpResponse("Attent is working on your data. "
                            "If your saw the same message more than 24 hours ago please reach out to the Attent team.")

    import requests
    requests.post(request.POST.get('response_url'), json={"text": "something is coming!"})

    WarehouseModel = client.get_warehouse_view_model()
    from django.db.models import Count
    set = WarehouseModel.objects.filter(contact_title__isnull=False).values('contact_title').annotate(count=Count('meeting_id')).order_by("-count").using('warehouse')[:5]

    result = "{}: {}\n{}: {}\n{}: {}\n{}: {}".format(
        set[0].get('contact_title', ''), set[0].get('count', ''),
        set[1].get('contact_title', ''), set[1].get('count', ''),
        set[2].get('contact_title', ''), set[2].get('count', ''),
        set[3].get('contact_title', ''), set[3].get('count', ''))

    response_json = {
        "text": result,
        "replace_original": False
    }
    requests.post(request.POST.get('response_url'), json=response_json)

    return HttpResponse("Working on it")
