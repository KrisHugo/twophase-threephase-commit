from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
from threephase.models import ThreePhaseParticipant, ThreePhaseValue

def get_context():
    context = {'participants': [], 'values': []}
    for p in ThreePhaseParticipant.objects.all():
        p.values=[]
        for v in ThreePhaseValue.objects.filter(participant=p):
            p.values.append(v)
        context['participants'].append(p)
    if len(context['participants']) != 0:
        context['values'] = context['participants'][0].values
    return context

def app_page(request):
    return render(request, 'index1.html', get_context())

def index(request):
    return app_page(request)

def add_participant(request, participant_name):
    response = HttpResponse()
    participants = ThreePhaseParticipant.objects.all()
    for p in participants:
        if p.state != 0:
            response.status_code = 500
            return response
        elif p.name == participant_name:
            response.status_code = 400
            return response

    p = ThreePhaseParticipant(name=participant_name, state=0)
    p.save()
    added_keys = []
    # add existed values
    for v in ThreePhaseValue.objects.all():
        if v.key not in added_keys:
            added_keys.append(v.key)
            new_value = ThreePhaseValue(participant=p, key=v.key, value=v.value, prepared_value=v.value)
            new_value.save()

    return app_page(request)

def add_value(request, key, value):
    response = HttpResponse()
    participants = ThreePhaseParticipant.objects.all()
    values = ThreePhaseValue.objects.all()
    for v in values:
        if v.key == key:
            response.status_code = 400
            return response

    for p in participants:
        new_value = ThreePhaseValue(participant=p, key=key, value=value, prepared_value=value)
        new_value.save()
    return app_page(request)

def prepare(request, key):
    response = HttpResponse()
    value = request.GET[key]
    participants = ThreePhaseParticipant.objects.all()
    values = ThreePhaseValue.objects.filter(key=key)
    if len(values) == 0:
        response.status_code = 400
        return response
    for p in participants:
        p.state = 1
        p.save()
    for v in values:
        v.prepared_value = value
        v.save()
    return app_page(request)

def prepared(request, name):
    response = HttpResponse()
    flag = False
    for p in ThreePhaseParticipant.objects.filter(name=name):
        flag = True
        p.state = 2
        p.save()
    if flag is None:
        response.status_code = 400
        return response
    return app_page(request)

def pre_commit(request):
    context = get_context()
    flag = True
    for p in context['participants']:
        if p.state != 2:
            flag = False
    for p in context['participants']:
        if flag:
            p.state = 3
        else:
            p.state = 0
            for v in p.values:
                v.prepared_value = v.value
                v.save()
        p.save()
    return app_page(request)

def pre_committed(request, name):
    context = get_context()
    for p in context['participants']:
        if p.name == name:
            p.state = 4
            p.save()
    return app_page(request)

def commit(request):
    context = get_context()
    flag = False
    for p in context['participants']:
        if p.state == 4:
            flag = True
    if flag:
        for p in context['participants']:
            p.state = 0
            p.save()
            for v in p.values:
                v.value = v.prepared_value
                v.save()
    else:
        for p in context['participants']:
            p.state = 0
            p.save()
            for v in p.values:
                v.prepared_value = v.value
                v.save()

    return app_page(request)