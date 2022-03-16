from django.http import HttpResponse
from models import Notification
import utils
import json
from django.core.exceptions import SuspiciousOperation

def add_comment(request):
    alert_id = int(request.POST.get('alert_id'))
    text = request.POST.get('text')
    user = request.user
    if not user.is_authenticated():
        raise SuspiciousOperation('attempt to add comment w/o authenticated user')

    comment = utils.add_user_comment(Notification.objects.get(id=alert_id), user, text)
    return HttpResponse(json.dumps(comment.json()), 'text/json')

def alert_action(request):
    alert_id = int(request.POST.get('alert_id'))
    action = request.POST.get('action')
    action_comment = request.POST.get('comment')
    user = request.user
    if not user.is_authenticated():
        raise SuspiciousOperation('attempt to take action on alert w/o authenticated user')
    alert = Notification.objects.get(id=alert_id)

    utils.alert_action(alert, action, user, action_comment)

    #simulated delay
    #import time
    #time.sleep(1.)

    return HttpResponse(json.dumps(alert.json(user)), 'text/json')

