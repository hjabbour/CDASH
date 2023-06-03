# Create your views here.
# views.py
from pymongo import MongoClient
from admin_datta.forms import RegistrationForm, LoginForm, UserPasswordChangeForm, UserPasswordResetForm, UserSetPasswordForm
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.views.generic import CreateView
from django.contrib.auth import logout

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from .forms import ForecastedOpportunityForm, FunnelOpportunityForm, BEEngagementActivityForm, CXEngagementActivityForm, TACCaseForm

client = MongoClient('mongodb://root:rootpassword@192.168.2.190:27017')
db = client['CDASH']

def forecasted_opportunity_view(request):
    form = ForecastedOpportunityForm()
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'forecasted_opportunity'})

def funnel_opportunity_view(request):
    form = FunnelOpportunityForm()
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'funnel_opportunity'})

def be_engagement_activity_view(request):
    form = BEEngagementActivityForm()
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'be_engagement_activity'})

def cx_engagement_activity_view(request):
    form = CXEngagementActivityForm()
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'cx_engagement_activity'})

def tac_case_view(request):
    form = TACCaseForm()
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'tac_case'})


def process_forecasted_opportunity_form(data):
    collection = db['forecasted_opportunity']
    # Process and save the forecasted opportunity form data
    # ...
    collection.insert_one(data)

def process_funnel_opportunity_form(data):
    collection = db['funnel_opportunity']
    # Process and save the funnel opportunity form data
    # ...
    collection.insert_one(data)

def process_be_engagement_activity_form(data):
    collection = db['be_engagement_activity']
    # Process and save the BE engagement activity form data
    # ...
    collection.insert_one(data)

def process_cx_engagement_activity_form(data):
    collection = db['cx_engagement_activity']
    # Process and save the CX engagement activity form data
    # ...
    collection.insert_one(data)

def process_tac_case_form(data):
    collection = db['tac_case']
    # Process and save the TAC case form data
    # ...
    collection.insert_one(data)

@login_required
def process_form_view(request, form_name):
    if request.method == 'POST':
        user_id = request.user.id  # Retrieve the logged-in user ID
        
        if form_name == 'forecasted_opportunity':
            form = ForecastedOpportunityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'progress': form.cleaned_data['progress'],
                    'approx_value': form.cleaned_data['approx_value']
                }
                process_forecasted_opportunity_form(data)
                return redirect('success_page')

        elif form_name == 'funnel_opportunity':
            form = FunnelOpportunityForm(request.POST)
            if form.is_valid():
                data = {
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'progress': form.cleaned_data['progress'],
                    'approx_value': form.cleaned_data['approx_value']
                }
                process_funnel_opportunity_form(data, user_id)
                return redirect('success_page')

        elif form_name == 'be_engagement_activity':
            form = BEEngagementActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'client_name': form.cleaned_data['client_name'],
                    'be_name': form.cleaned_data['be_name'],
                    'progress': form.cleaned_data['progress']
                }
                process_be_engagement_activity_form(data, user_id)
                return redirect('success_page')

        elif form_name == 'cx_engagement_activity':
            form = CXEngagementActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'client_name': form.cleaned_data['client_name'],
                    'cx_name': form.cleaned_data['cx_name'],
                    'progress': form.cleaned_data['progress']
                }
                process_cx_engagement_activity_form(data, user_id)
                return redirect('success_page')

        elif form_name == 'tac_case':
            form = TACCaseForm(request.POST)
            if form.is_valid():
                data = {
                    'client_name': form.cleaned_data['client_name'],
                    'case_name': form.cleaned_data['case_name'],
                    'selected_options': form.cleaned_data['selected_options']
                }
                process_tac_case_form(data, user_id)
                return redirect('success_page')

    else:
        # Invalid request method, redirect to an error page or handle as needed
        return redirect('error_page')

