from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout
import json
from urllib.parse import urlencode
import binascii

import hmac
import hashlib


def index(request):
    # api_key = b'd595f160-b550-4986-b2fb-261a82bb'
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

    data = {}
    data['dashboard'] = selected_dashboard.periscope_dashboard_id
    data['embed'] = 'v2'
    data['filters'] = []

    api_key = client.extra_info['periscope_api_key']

    path = '/api/embedded_dashboard?%s' % urlencode({'data': json.dumps(data)})
    sign = binascii.hexlify(hmac.new(bytes(api_key, encoding='utf8'), msg=path.encode('utf-8'), digestmod=hashlib.sha256).digest()).decode("utf-8")
    url = 'https://www.periscopedata.com%s&signature=%s' % (path, sign)

    context['dashboards'] = client.periscopedashboard_set.filter(is_visible=True)

    context['selected_dashboard'] = {
        'url': url,
        'id': selected_dashboard.id
    }

    return render(request, template, context=context)


def social_complete_google(request):
    return HttpResponse('Some kinda social connect..')


@csrf_exempt
def sign_out(request):
    if request.method == 'GET':
        logout(request)

    return redirect('/')
