# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.contrib import messages
from django.template import RequestContext
from django.core.urlresolvers import reverse

from models import TestProject
from othermodels import Flavour

def _check_for_local_changes(request, project):
    if project.check_for_local_changes():
        messages.add_message(request, messages.INFO, "You have local changes")
        return True
    return False

def update_project(project):
    project.update_svn()

def home(request):

    projects = TestProject.objects.all()
    
    return render_to_response('home.html', locals(), context_instance = RequestContext(request))


def projects(request, project = None):
    
    # this should be the 404 shortcut thing
    project = TestProject.objects.get(name = project)
    
    if request.method == 'POST':
        
        if request.POST.get('commit', None):
            # commit it
            project.commit(request.POST['commit_message'])
        
        else:
            try:
                update_project(project)
                messages.add_message(request, messages.INFO, "Updated project")
            except Exception, ex:
                messages.add_message(request, messages.INFO, "Failure to update project: " + str(ex))
    
    return render_to_response('project.html', locals(), context_instance = RequestContext(request))


def flavour_view(request, project, flavour):
    
    # this should be the 404 shortcut thing
    project = TestProject.objects.get(name = project)
    flavour = project.get_flavour(flavour)
    
    if request.method == 'POST':
        
        if request.POST.get('CSV', None):
            # download the csv
            csv, filename = flavour.make_csv()
            response =  HttpResponse(csv.read(), mimetype = 'application/csv')
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            return response
    
    return render_to_response('flavour.html', locals(), context_instance = RequestContext(request))

def tests_view(request, project, flavour, mbox):
    
    # this should be the 404 shortcut thing
    project = TestProject.objects.get(name = project)
    flavour = project.get_flavour(flavour)
    mbox = flavour.get_specific_mbox(mbox)
    
    if _check_for_local_changes(request, project):
        local_changes = True
    
    return render_to_response('tests.html', locals(), context_instance = RequestContext(request))

def test_edit(request, project, flavour, mbox, test):
    
    # this should be the 404 shortcut thing
    project = TestProject.objects.get(name = project)
    flavour = project.get_flavour(flavour)
    mbox = flavour.get_specific_mbox(mbox)
    test = mbox.get_specific_test(test)
    
    if request.method == 'POST':
        test.story_id = request.POST['story_id']
        test.summary = request.POST['summary']
        test.steps = request.POST['steps']
        test.expected_result = request.POST['expected_result']
        test.priority = request.POST['priority']
        test.automated_test_id = request.POST['automated_test_id']
        test.save()
        return redirect(reverse('tests', kwargs = {'project':project.name, 'flavour':flavour.name, 'mbox':mbox.name}))
        
    
    return render_to_response('test_edit.html', locals(), context_instance = RequestContext(request))