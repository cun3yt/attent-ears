from django.http import HttpResponse
from apps.visualizer.models import Client
import requests


def answer_slack_question(team_id, response_url):
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

    WarehouseModel = client.get_warehouse_view_model()

    from django.db.models import Count
    result_set = WarehouseModel.objects.filter(contact_title__isnull=False).values('contact_title').annotate(count=Count('meeting_id')).order_by("-count").using('warehouse')[:5]

    result = "{}: {}\n{}: {}\n{}: {}\n{}: {}".format(
        result_set[0].get('contact_title', ''), result_set[0].get('count', ''),
        result_set[1].get('contact_title', ''), result_set[1].get('count', ''),
        result_set[2].get('contact_title', ''), result_set[2].get('count', ''),
        result_set[3].get('contact_title', ''), result_set[3].get('count', ''))

    response_json = {
        "text": result,
        "replace_original": True
    }

    requests.post(response_url, json=response_json)
