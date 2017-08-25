from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.urls import reverse
from apps.outreach.syncer import outreach_connect_url, outreach_exchange_for_access_token
from apps.api_connection.models import ApiConnection
from apps.salesforce.authentication import salesforce_connect_url, salesforce_exchange_for_access_token


def index(request):
    context = {}
    template = 'index.html'

    if not request.user.is_authenticated():
        return render(request, template, context=context)

    client = request.user.client

    all_dashboards = client.periscopedashboard_set.filter(is_visible=True)
    dashboard_id = request.GET.get('dashboard_id', '')

    selected_dashboard_set = all_dashboards.filter(periscope_dashboard_id=dashboard_id)

    context['all_dashboards'] = all_dashboards

    if selected_dashboard_set.count() == 0:
        context['no_dashboard_selected'] = True
        return render(request, template, context=context)

    selected_dashboard = selected_dashboard_set[0]

    api_key = client.extra_info['periscope_api_key']
    url = selected_dashboard.get_embed_url(api_key)

    context['dashboards'] = client.periscopedashboard_set.filter(is_visible=True)

    context['selected_dashboard'] = {
        'url': url,
        'id': selected_dashboard.id
    }

    return render(request, template, context=context)


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
        'detail': current_outreach_connection,
    }

    salesforce_connection = {
        'name': 'salesforce',
        'setting_name': 'SalesForce',
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
            outreach_connection,
            salesforce_connection,
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
                                           defaults={'data': resp.text})
    return redirect(reverse('settings'))


def salesforce_redirect(request):
    if not request.user.is_authenticated():
        redirect('/')

    authorization_code = request.GET.get('code')

    redirect_uri = request.build_absolute_uri(reverse('salesforce-redirect'))
    resp = salesforce_exchange_for_access_token(authorization_code=authorization_code, redirect_uri=redirect_uri)

    ApiConnection.objects.update_or_create(type='salesforce',
                                           user=request.user,
                                           defaults={'data': resp.text})
    return redirect(reverse('settings'))
