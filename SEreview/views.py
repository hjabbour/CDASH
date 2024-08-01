# Create your views here.
# views.py
# 2023 Haytham Jabbour hjabbour
from pymongo import MongoClient
from datetime import datetime,timedelta
from bson import ObjectId
from dateutil.relativedelta import relativedelta
from django.utils import timezone



from admin_datta.forms import RegistrationForm, LoginForm, UserPasswordChangeForm, UserPasswordResetForm, UserSetPasswordForm 
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User 
from django.http import HttpResponse ,HttpResponseNotFound


from django.views.generic import CreateView
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth.decorators import login_required
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404 

from .forms import ForecastedOpportunityForm, FunnelOpportunityForm,ActivityForm, BEEngagementActivityForm, CXEngagementActivityForm, TACCaseForm, IssuesForm,WeeklyMeetingForm,EngineerSelectionForm,ClientForm,DateRangeForm,SwotForm,ClientStrategyForm,BEStatusForm,BEInitiativeForm,BEActivityForm
from .forms import UForecastedOpportunityForm, UFunnelOpportunityForm,UActivityForm, UBEEngagementActivityForm, UCXEngagementActivityForm, UTACCaseForm, UIssuesForm,UWeeklyMeetingForm,UClientForm,USwotForm,UClientStrategyForm
from .conn import get_mongodb_connection

from collections import defaultdict
import pandas as pd

## remove status list from collection_user and put toupdatelist
statuslist = ['Planned','Active','Delayed']
toupdatelist = ['Planned','Active','Delayed','Monitoring','Engaged','Initial','Followup','Funnel','Completed']
fields_to_display = {
        'forecasted_opportunity': ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'funnel_opportunity': ['Client/Status', 'Creatiion Date','Update', 'Pending','Action'],
        'activity': ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'be_engagement_activity': ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'meetings': ['Client/Status', 'Creation Date','Update','Pending','Action'],
        'cx_engagement_activity' : ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'tac_case' : ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'issues' : ['Issue title', 'Creation Date','Update', 'Pending','Action'],
        'clients' : ['Client'],
        'swot': ['Strength', 'Weakness', 'Opportunity', 'Threat'],
        'client_strategy': ['Security Strategy', 'AI Strategy', 'Cloud Strategy', 'Observability Strategy'],
        'bestatus': ['Client','BE'],
        'beinitiative' : ['Client', 'BE', 'Initiative Name', 'Initiative desc', 'Expected Outcome', 'Expected Date', 'Owners', 'desc_update'],
        'beactivity':['Activity Name','Client', 'BE','Activity', 'Initiative', 'Pending', 'Status', 'Update']
        
        
        # Add more collections and their corresponding fields here
    }

client = get_mongodb_connection()
db = client['CDASH']


## function to wrap logins
def group_required(allowed_groups=None):
    """
    Decorator to check user group membership and access control.

    Args:
        allowed_groups (list, optional): A list of allowed group names for this view (e.g., ['SE', 'BE']).
            If None, only superusers can access the view. Defaults to None.

    Returns:
        function: A decorator function.
    """

    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            if user.is_superuser:  # Superusers have full access
                return func(request, *args, **kwargs)

            # Check for allowed groups if provided (otherwise only superuser is allowed)
            if allowed_groups is not None:
                if user.groups.filter(name__in=allowed_groups).exists():
                    return func(request, *args, **kwargs)
                else:
                    # Handle unauthorized access for non-superusers in non-allowed groups
                    #return render(request, 'unauthorized.html')  # Or redirect/display error
                    error_message = "Unauthorized Access"
                    return redirect('SEreview:error_page_with_message', message=error_message)

            # If no allowed_groups are specified, only superuser can access
            error_message = "Unauthorized Access"
            return redirect('SEreview:error_page_with_message', message=error_message)

        return wrapper
    return decorator  # Correct return of the decorator function


# def get_existing_clients(user_id):
#     # Access your MongoDB collection
#     collection = db['clients']
#     # Fetch the client names based on user_id
#     existing_clients = collection.find({'user_id': user_id})
#     client_list = [(client['client_name'], client['client_name']) for client in existing_clients]
#     #client.close()  # Close the MongoDB connection
#     return client_list

def get_existing_clients(user_id):
    collection = db['clients']
    if is_user_superuser(user_id):
        existing_clients = collection.find()
    else:
        existing_clients = collection.find({'user_id': user_id})
    client_list = [(client['client_name'], client['client_name']) for client in existing_clients]
    return client_list

def get_existing_beinitiative(client_name, be_name,user_id):
    collection = db['beinitiative']
    if is_user_superuser(user_id):
        existing_beinitiative = collection.find()
    else:
        existing_beinitiative = collection.find({'client_name': client_name, 'be_name': be_name})
    
    beinitiatives_list = [('None', 'None')] + [
        (initiative.get('initiative_short', 'None'), initiative.get('initiative_short', 'None')) 
        for initiative in existing_beinitiative
    ]
    
    return beinitiatives_list

## this function is to retreive all clients with their id as opposed to just a list of names
def get_all_clients(user_id):
    collection = db['clients']
    if is_user_superuser(user_id):
        existing_clients = collection.find()
    else:
        existing_clients = collection.find({'user_id': user_id})

    return existing_clients

def is_user_in_group(user_id, group_name):
    user = User.objects.get(id=user_id)
    return user.groups.filter(name=group_name).exists()

def get_all_clients_for_user(user_id):
    collection = db['clients']
    if is_user_superuser(user_id):
        existing_clients = collection.find()
    elif is_user_in_group(user_id, 'BE'):
        # If the user is in the BE group, return all clients
        existing_clients = collection.find()
    elif is_user_in_group(user_id, 'SE'):
        # If the user is in the SE group, return clients where the user_id matches
        existing_clients = collection.find({'user_id': user_id})
    else:
        # If the user is not in either group, return an empty cursor
        existing_clients = collection.find({'_id': None})  # No client will match this

    return existing_clients

@login_required
def render_dynamic_form(request, form_name):
    form_classes = {
        'meetings': WeeklyMeetingForm,
        'forecasted_opportunity': ForecastedOpportunityForm,
        'funnel_opportunity': FunnelOpportunityForm,
        'activity': ActivityForm,
        'be_engagement_activity': BEEngagementActivityForm,
        'cx_engagement_activity': CXEngagementActivityForm,
        'tac_case': TACCaseForm,
        'issues': IssuesForm,
        'clients': ClientForm,
        # Add more form classes and form names as needed
    }

    form_class = form_classes.get(form_name)

    if form_class:
        form = form_class()
        user_id = request.user.id
        existing_clients = get_existing_clients(user_id)  # Use get_existing_clients for all forms
        data = collection_user(user_id, form_name)
        fields = fields_to_display.get(form_name, [])
        return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': form_name, 'data': data, 'fields_to_display': fields, 'existing_clients': existing_clients})
    else:
        # Handle cases where form_name is not found (e.g., return an error page)
        return HttpResponseNotFound("Form not found")


def process_form_data(form_name, data):
    # Define a mapping of form names to collection names
    form_to_collection = {
        'forecasted_opportunity': 'forecasted_opportunity',
        'funnel_opportunity': 'funnel_opportunity',
        'activity': 'activity',
        'be_engagement_activity': 'be_engagement_activity',
        'cx_engagement_activity': 'cx_engagement_activity',
        'tac_case': 'tac_case',
        'issues': 'issues',
        'meetings': 'meetings',
        'clients': 'clients',
        'swot':'swot',
        'client_strategy':'client_strategy',
        'bestatus': 'bestatus',
        'beinitiative': 'beinitiative',
        'beactivity': 'beactivity'
        
    }

    # Get the collection name based on the form name
    collection_name = form_to_collection.get(form_name)

    if collection_name:
        collection = db[collection_name]

        if form_name == 'clients':
            data['client_name'] = data['client_name'].capitalize()
           

        # Process and save the form data
        # ...
        collection.insert_one(data)
    else:
        # Handle cases where the form name is not found (e.g., log an error)
        print(f"Collection not found for form name: {form_name}")


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
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'create_date' : datetime.now(),
                    'approx_value': form.cleaned_data['approx_value'],
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_forecasted_opportunity_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)

        elif form_name == 'funnel_opportunity':
            form = FunnelOpportunityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'approx_value': form.cleaned_data['approx_value'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_funnel_opportunity_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)
            
        elif form_name == 'activity':
            form = ActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'activity_name': form.cleaned_data['activity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_activity_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)
        
        elif form_name == 'be_engagement_activity':
            form = BEEngagementActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'be_name':form.cleaned_data['be_name'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_be_engagement_activity_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)

        elif form_name == 'cx_engagement_activity':
            form = CXEngagementActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'cx_name': form.cleaned_data['cx_name'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'be_name':form.cleaned_data['be_name'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_cx_engagement_activity_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)

        elif form_name == 'tac_case':
            form = TACCaseForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'case_name': form.cleaned_data['case_name'],
                    'status': form.cleaned_data['status'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_tac_case_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)
            
        elif form_name == 'issues':
            form = IssuesForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id':user_id,
                    'issue_title': form.cleaned_data['issue_title'],
                    'status': form.cleaned_data['status'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_issues_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)
            
        elif form_name == 'meetings':
            form =  WeeklyMeetingForm(request.POST)
            if form.is_valid():
                meeting_date = datetime(year=form.cleaned_data['meeting_date'].year,month=form.cleaned_data['meeting_date'].month,day=form.cleaned_data['meeting_date'].day,)
                data = {
                    'user_id':user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'status': 'Active',
                    'meeting_date' :meeting_date,
                    'meeting_outcome' :form.cleaned_data['meeting_outcome'],
                    'create_date' :datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                                    ]
                }
                #process_meetings_form(data)
                process_form_data(form_name, data)
                return redirect('SEreview:'+form_name)
            
        elif form_name == 'clients':
            form =  ClientForm(request.POST)
            if form.is_valid():
                client_name = form.cleaned_data['client_name'].capitalize()
                if not check_client_exists(client_name, user_id): 
                
                    data = {
                            'user_id':user_id,
                            'status': 'Active',
                            'client_name': form.cleaned_data['client_name'],
                            
                        }
                    #process_client_form(data)
                    process_form_data(form_name, data)
                    return redirect('SEreview:'+form_name)  
                else:
                # The client already exists, handle this case as needed
                # You can pass an error message as a URL parameter
                    error_message = "Client already exists."
                    return redirect('SEreview:error_page_with_message', message=error_message)  

    else:
        # Invalid request method, redirect to an error page or handle as needed
        return redirect('SEreview:error_page')

def collection_list(request, collection_name):
    user_id = request.user.id  # Retrieve the logged-in user ID
    collection = db[collection_name]
    if is_user_superuser(user_id):
        data = collection.find()
    else:
        data = collection.find({'user_id': user_id,'status': {'$in': toupdatelist}})
    fields = fields_to_display.get(collection_name, [])
    # Preprocess the data to create a list of dictionaries
    
    context = {
        'collection_name': collection_name,
        'data': data,
        'fields_to_display': fields,
        
         }
    
    return render(request, 'SEreview/collection_list.html', context)

## use the toupdatelist to get what is needed 
# def collection_user(user_id, collection_name,superuser=False):
    
#     #statuslist = ['Planned','Active','Delayed']
#     collection = db[collection_name]
#     if is_user_superuser(user_id):
#         data = collection.find({'status': {'$in': toupdatelist}})
#     else:
#         data = collection.find({'user_id': user_id,'status': {'$in': toupdatelist}})
#     return data

def collection_user(user_id, collection_name, client_name=None, superuser=False):
    collection = db[collection_name]
    query = {'status': {'$in': toupdatelist}}
    
    if not is_user_superuser(user_id):
        query['user_id'] = user_id

    if client_name:
        query['client_name'] = client_name

    data = collection.find(query)
    return data


def collection_client(collection_name, client_name=None, superuser=False):
    collection = db[collection_name]
    query = {'status': {'$in': toupdatelist}}
    
    if client_name:
        query['client_name'] = client_name

    data = collection.find(query)
    return data

def collection_client_be(collection_name, client_name=None, be_name=None, superuser=False):
    collection = db[collection_name]
    query = {'status': {'$in': toupdatelist}}
    
    if client_name:
        query['client_name'] = client_name
    
    if be_name:
        query['be_name'] = be_name  # Add be_name to the query if it is provided

    data = collection.find(query)
    return data



def delete_item(request, collection_name, item_id):
    # Retrieve the logged-in user ID
    user_id = request.user.id

    # Retrieve the collection based on the collection_name
    collection = db[collection_name]

    # Find the item to be "deleted"
    item = collection.find_one({'_id': ObjectId(item_id)})

    if item:
        # Check if the user has permission to delete the item
        if item['user_id'] == user_id:
            # Update the status of the item to "deleted"
            collection.update_one({'_id': ObjectId(item_id)}, {'$set': {'status': 'deleted'}})
            #return HttpResponse('Item marked as deleted.')
            return redirect('SEreview:collection_list', collection_name=collection_name)
        else:
            #return HttpResponse('You do not have permission to delete this item.')
            return redirect('SEreview:collection_list', collection_name=collection_name)
    else:
        return redirect('SEreview:collection_list', collection_name=collection_name)

## Queries sections maybe moved to seperate file 
def count_active_forecasted_opportunities(user_id=None):
    # Establish connection to MongoDB

    # Prepare the query based on the user_id parameter
    query = {'status': 'Active'}
    if user_id is not None:
        query['user_id'] = user_id

    # Retrieve the forecasted_opportunity collection
    collection = db['forecasted_opportunity']

    # Count the number of active opportunities and calculate their sum
    count = collection.count_documents(query)
    sum_value = collection.aggregate([
        {'$match': query},
        {'$group': {'_id': 'None', 'sum_value': {'$sum': '$approx_value'}}}
    ])
    #sump_op=sum_value['sum_value']
    sum_value = sum_value.next()['sum_value'] if sum_value.alive else 0

    return count, sum_value

def count_active_funnel_opportunities(user_id=None):
    # Establish connection to MongoDB

    # Prepare the query based on the user_id parameter
    query = {'status': 'Active'}
    if user_id is not None:
        query['user_id'] = user_id

    # Retrieve the forecasted_opportunity collection
    collection = db['funnel_opportunity']

    # Count the number of active opportunities and calculate their sum
    count = collection.count_documents(query)
    sum_value = collection.aggregate([
        {'$match': query},
        {'$group': {'_id': 'None', 'sum_value': {'$sum': '$approx_value'}}}
    ])
    #sump_op=sum_value['sum_value']
    sum_value = sum_value.next()['sum_value'] if sum_value.alive else 0

    return count, sum_value

def weekly_updates():
    collection_names = db.list_collection_names()

    past_week_timestamp = datetime.now() - timedelta(days=7)

    total_updates = 0
    for collection_name in collection_names:
        collection = db[collection_name]
        updates = collection.count_documents({
            'desc_update': {
                '$elemMatch': {
                    'timestamp': {
                        '$gte': past_week_timestamp
                    }
                }
            }
        })
        total_updates += updates

    return total_updates

def get_user_first_name(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        first_name = user.first_name
        return first_name
    except User.DoesNotExist:
        return "notfound"


def get_recent_updates():
    collection_names = db.list_collection_names()

    recent_updates = []

    for collection_name in collection_names:
        if collection_name == 'issues':
            continue  # Skip the 'issues' collection
        collection = db[collection_name]
        updates = collection.aggregate([
            {'$unwind': '$desc_update'},
            {'$sort': {'desc_update.timestamp': -1}},
            {'$limit': 10}
        ])

        for update in updates:
            update_text = update['desc_update']['text'][:50]
            timestamp = update['desc_update']['timestamp']
            user_id = update['user_id']
            client_name = update['client_name']

            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                user_first_name = user.first_name
            except User.DoesNotExist:
                user_first_name = None

            recent_updates.append({
                'update_text': update_text,
                'timestamp': timestamp,
                'user_id': user_id,
                'user_first_name': user_first_name,
                'client_name': client_name
            })

            # Break the loop if the total number of updates reaches 10
            if len(recent_updates) >= 10:
                break

        # Break the loop if the total number of updates reaches 10
        if len(recent_updates) >= 10:
            break

    return recent_updates[:10]  # Ensure only 10 updates are returned


def stats_view(request, user_id=None):
    user_id = request.user.id
    user_first_name = "no firstname"
    # Retrieve the forecasted opportunities based on the user_id parameter
    if user_id:
        forecast_count,forecast_value = count_active_forecasted_opportunities(user_id)
        funnel_count,funnel_value = count_active_funnel_opportunities(user_id)
        user_first_name = get_user_first_name(user_id)
    else:
        forecast_count,forecast_value =count_active_forecasted_opportunities()
        funnel_count,funnel_value = count_active_funnel_opportunities()
        
    total_funnel = forecast_value+funnel_value
    total_count = funnel_count+forecast_count
    
    week_updates = weekly_updates()
    recent_updates = get_recent_updates()
    # Create the context dictionary
    context = {
        'forecast_count': forecast_count,
        'forecast_value':forecast_value,
        'funnel_count':funnel_count,
        'funnel_value':funnel_value,
        'total_funnel':total_funnel,
        'total_count':total_count,
        'week_updates':week_updates,
        'first_name': user_first_name,
        'recent_updates':recent_updates
    }

    # Render the stats.html template with the context
    #return render(request, 'SEreview/stats.html', context)
    return render(request, 'pages/index.html', context)


def error_page(request, message=None):
    context = {'message': message}
    return render(request, 'SEreview/error_page.html', context)

def is_user_superuser(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        return user.is_superuser
    except User.DoesNotExist:
        return False

def weeklyreview(request,engineer_id=None):
    
    if engineer_id is not None:
        user_id = get_object_or_404(User, id=engineer_id, is_superuser=False)
    else:
        user_id = request.user.id  # Default to the logged-in user
    
    # Calculate the date range for the past month
    today = datetime.now()
    period_filter = today - timedelta(days=14)
    
    # Get meetings from the past month
    all_meetings = list(collection_user(user_id, 'meetings'))
    meetings = [meeting for meeting in all_meetings if meeting['meeting_date'] >= period_filter]


    forecasted_opportunities = list(collection_user(user_id, 'forecasted_opportunity'))
    funnel_opportunities = list(collection_user(user_id, 'funnel_opportunity'))
    be_engagements = list(collection_user(user_id, 'be_engagement_activity'))
    cx_engagements = list(collection_user(user_id, 'cx_engagement_activity'))
    issues = list(collection_user(user_id, 'issues'))
    tac_cases = list(collection_user(user_id, 'tac_case'))
    activities = list(collection_user(user_id, 'activity'))
    
    
    ## group data by month 
    forecasted_opportunities = group_data_by_month(forecasted_opportunities)
    funnel_opportunities = group_data_by_month(funnel_opportunities)
    be_engagements = group_data_by_month(be_engagements)
    cx_engagements = group_data_by_month(cx_engagements)
    meetings = group_data_by_month(all_meetings)
    activities = group_data_by_month(activities)
    # Calculate the count and value of active forecasted opportunities
    forecast_count, forecast_value = count_active_forecasted_opportunities(user_id)
    
    # Calculate the count and value of active funnel opportunities
    funnel_count, funnel_value = count_active_funnel_opportunities(user_id)

    return render(request, 'SEreview/weeklyreview.html', {
        'forecasted_opportunities': forecasted_opportunities,
        'funnel_opportunities': funnel_opportunities,
        'meetings': meetings,
        'be_engagements': be_engagements,
        'cx_engagements': cx_engagements,
        'issues': issues,
        'tac_cases': tac_cases,
        'forecast_count':forecast_count,
        'forecast_value':forecast_value,
        'funnel_count': funnel_count,
        'funnel_value' :funnel_value,
        'activities' : activities,
    })
def is_superuser(user):
    return user.is_superuser

## unused function can use it later to filter any form or view with parametrized form
@user_passes_test(is_superuser)
def select_engineer(request):
    if request.method == 'POST':
        form = EngineerSelectionForm(request.POST)
        if form.is_valid():
            selected_engineer = form.cleaned_data['engineer']
            return redirect('SEreview:mweeklyreview', engineer_id=selected_engineer.id)
    else:
        form = EngineerSelectionForm()

    return render(request, 'SEreview/select_engineer.html', {'form': form})

@user_passes_test(is_superuser)
def mweeklyreview(request,engineer_id=None):
    if request.method == 'POST':
        # If it's a POST request, process the form submission.
        form = EngineerSelectionForm(request.POST)
        if form.is_valid():
            selected_engineer = form.cleaned_data['engineer']
            return redirect('SEreview:mweeklyreview', engineer_id=selected_engineer.id)
    else:
        # For GET requests and initial load, handle the engineer_id parameter if provided.
        if engineer_id is not None:
            form = EngineerSelectionForm(initial={'engineer': engineer_id})
            user_id = engineer_id
        else:
            form = EngineerSelectionForm()
            user_id = request.user.id  # Default to the logged-in user
    
    # Calculate the date range for the past month
    today = datetime.now()
    period_filter = today - timedelta(days=14)
    
    # Get meetings from the past month
    all_meetings = list(collection_user(user_id, 'meetings'))
    meetings = [meeting for meeting in all_meetings if meeting['meeting_date'] >= period_filter]


    forecasted_opportunities = list(collection_user(user_id, 'forecasted_opportunity'))
    funnel_opportunities = list(collection_user(user_id, 'funnel_opportunity'))
    be_engagements = list(collection_user(user_id, 'be_engagement_activity'))
    cx_engagements = list(collection_user(user_id, 'cx_engagement_activity'))
    issues = list(collection_user(user_id, 'issues'))
    tac_cases = list(collection_user(user_id, 'tac_case'))
    activities = list(collection_user(user_id, 'activity'))
    
    
    # Calculate the count and value of active forecasted opportunities
    forecast_count, forecast_value = count_active_forecasted_opportunities(user_id)
    
    # Calculate the count and value of active funnel opportunities
    funnel_count, funnel_value = count_active_funnel_opportunities(user_id)
    form = EngineerSelectionForm(request.POST)

    return render(request, 'SEreview/manager_weeklyreview.html', {
        'forecasted_opportunities': forecasted_opportunities,
        'funnel_opportunities': funnel_opportunities,
        'meetings': meetings,
        'be_engagements': be_engagements,
        'cx_engagements': cx_engagements,
        'issues': issues,
        'tac_cases': tac_cases,
        'forecast_count':forecast_count,
        'forecast_value':forecast_value,
        'funnel_count': funnel_count,
        'funnel_value' :funnel_value,
        'activities' : activities,
        'form': form,
    })
def detail_item(request, collection_name, item_id):
    user_id = request.user.id  # Retrieve the logged-in user ID
    collection = db[collection_name]
    item = collection.find_one({'_id': ObjectId(item_id)})
    fields = fields_to_display.get(collection_name, [])
    
    return render(request, 'SEreview/detail_item.html', { 'item': item, 'collection_name': collection_name, 'item_id': item_id,'fields_to_display':fields})

def check_client_exists(client_name, user_id):
# Query the MongoDB collection to check if the client with the given name and user_id exists
# You can adjust the query conditions as needed
    collection = db['clients']
    query = {
        'user_id': user_id,
        'client_name': client_name
    }
    existing_client = collection.find_one(query)

    # If an existing client is found, return True; otherwise, return False
    return existing_client is not None

def update_item(request, collection_name, item_id):
    user_id = request.user.id  # Retrieve the logged-in user ID
    collection = db[collection_name]
    item = collection.find_one({'_id': ObjectId(item_id)})

    # Determine the update form class based on the collection name
    update_form_classes = {
        'forecasted_opportunity': UForecastedOpportunityForm,
        'funnel_opportunity': UFunnelOpportunityForm,
        'activity': UActivityForm,
        'meetings': UWeeklyMeetingForm,
        'be_engagement_activity': UBEEngagementActivityForm,
        'cx_engagement_activity': UCXEngagementActivityForm,
        'tac_case': UTACCaseForm,
        'issues': UIssuesForm,
        'clients': UClientForm,
    }

    UpdateForm = update_form_classes.get(collection_name)

    if not UpdateForm:
        return HttpResponse('Invalid collection name')

    if request.method == 'POST':
        form = UpdateForm(request.POST)
        if form.is_valid():
            # Create an update_data dictionary from the form's cleaned data
            update_data = form.cleaned_data
            move_to_forecasted = form.cleaned_data.get('move_to_forecasted', False)  # Default to False if not provided
            
                # Check if 'meeting_date' exists in the form's cleaned data
            if 'meeting_date' in form.cleaned_data and form.cleaned_data['meeting_date']:
                update_data['meeting_date'] = datetime(
                    year=form.cleaned_data['meeting_date'].year,
                    month=form.cleaned_data['meeting_date'].month,
                    day=form.cleaned_data['meeting_date'].day,
                )            




            # Push a new entry to the desc_update array
            desc_update_text = update_data.pop('desc_update', None)
            if desc_update_text:
                update_entry = {
                    'text': desc_update_text,
                    'timestamp': datetime.now()
                }
                collection.update_one({'_id': ObjectId(item_id)}, {'$push': {'desc_update': update_entry}})
                
            
            
            # Update all fields in the MongoDB document with the update_data dictionary
            collection.update_one({'_id': ObjectId(item_id)}, {'$set': update_data})
            
            if move_to_forecasted:

                # Retrieve the data from the original record
                record_data = item.copy()

                # Delete the record from the current collection
                collection.delete_one({'_id': ObjectId(item_id)})

                # Insert the record into the forecasted_opportunity collection
                forecasted_collection = db['forecasted_opportunity']
                forecasted_collection.insert_one(record_data)
            
            return redirect('SEreview:collection_list', collection_name=collection_name)
    else:
        # Fill the form with data from the record to be updated
            # Fill the form with data from the record to be updated, except for desc_update
        initial_data = {k: v for k, v in item.items() if k != 'desc_update'}
        form = UpdateForm(initial=initial_data)

    return render(request, 'SEreview/update_item.html', {'form': form, 'item': item, 'collection_name': collection_name, 'item_id': item_id})

def group_data_by_month_timestamp(data):
    grouped_data = {}
    for entry in data:
        month_key = datetime.utcfromtimestamp(entry['create_date']).strftime('%B %Y')
        if month_key not in grouped_data:
            grouped_data[month_key] = []
        grouped_data[month_key].append(entry)
    return grouped_data

def group_data_by_month(data):
    grouped_data = defaultdict(list)

    for entry in data:
        # Use strftime directly on datetime object
        month_key = entry['create_date'].strftime('%B %Y')
        grouped_data[month_key].append(entry)

    return dict(grouped_data)



def countsum_collection(collection_name, user_id=None, value=True):
    query = {}
    if user_id:
        query['user_id'] = user_id

    collection = db[collection_name]

    if value:
        # Count the number of records and calculate their sum
        result = collection.aggregate([
            {'$match': query},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'sum_value': {'$sum': '$approx_value'}}}
        ])
    else:
        # Count only the number of records
        result = collection.aggregate([
            {'$match': query},
            {'$group': {'_id': None, 'count': {'$sum': 1}}}
        ])

    # Extract the count and sum_value from the result
    try:
        result_dict = next(result)
        count = result_dict.get('count', 0)
        sum_value = result_dict.get('sum_value', None) if value else None
    except StopIteration:
        count = 0
        sum_value = None

    return {'count': count, 'sum_value': sum_value}


def count_updates(collection_name, user_id=None):
    query = {}
    if user_id:
        query['user_id'] = user_id

    collection = db[collection_name]
    total_updates = collection.aggregate([
        {'$match': query},
        {'$project': {'update_count': {'$size': '$desc_update'}}},
        {'$group': {'_id': None, 'total_updates': {'$sum': '$update_count'}}}
    ])

    total_updates = total_updates.next()['total_updates'] if total_updates.alive else 0

    return total_updates


def engineer_stats(request):
    engineer_id = request.user.id  # Use the request user ID as engineer_id

    # Forecasted Opportunities
    forecasted_opportunity_result = countsum_collection('forecasted_opportunity', engineer_id, value=True)
    user_forecast_total_count = forecasted_opportunity_result['count']
    user_forecast_total_value = forecasted_opportunity_result['sum_value']

    all_users_forecasted_opportunity_result = countsum_collection('forecasted_opportunity', None, value=True)
    all_users_forecasted_total_count = all_users_forecasted_opportunity_result['count']
    all_users_forecasted_total_value = all_users_forecasted_opportunity_result['sum_value']

    user_forecasted_updates = count_updates('forecasted_opportunity', engineer_id)
    all_users_forecasted_updates = count_updates('forecasted_opportunity', None)

    # Funnel Opportunities
    funnel_opportunity_result = countsum_collection('funnel_opportunity', None, value=True)
    funnel_total_count = funnel_opportunity_result['count']
    funnel_total_value = funnel_opportunity_result['sum_value']

    funnel_user_opportunity_result = countsum_collection('funnel_opportunity', engineer_id, value=True)
    funnel_user_count = funnel_user_opportunity_result['count']
    funnel_user_value = funnel_user_opportunity_result['sum_value']

    funnel_updates = count_updates('funnel_opportunity', engineer_id)
    all_users_funnel_updates = count_updates('funnel_opportunity', None)

    # Meetings
    meetings_result = countsum_collection('meetings', None, value=False)
    meetings_total_count = meetings_result['count']
    
    meetings_user_result = countsum_collection('meetings', engineer_id, value=False)
    meetings_user_count = meetings_user_result['count']

    meetings_updates = count_updates('meetings', engineer_id)
    all_users_meetings_updates = count_updates('meetings', None)

    # BE Engagements
    be_result = countsum_collection('be_engagement_activity', None, value=False)
    be_total_count = be_result['count']

    be_user_result = countsum_collection('be_engagement_activity', engineer_id, value=False)
    be_user_count = be_user_result['count']

    be_updates = count_updates('be_engagement_activity', engineer_id)
    all_users_be_updates = count_updates('be_engagement_activity', None)

    # CX Engagements
    cx_result = countsum_collection('cx_engagement_activity', None, value=False)
    cx_total_count = cx_result['count']

    cx_user_result = countsum_collection('cx_engagement_activity', engineer_id, value=False)
    cx_user_count = cx_user_result['count']

    cx_updates = count_updates('cx_engagement_activity', engineer_id)
    all_users_cx_updates = count_updates('cx_engagement_activity', None)

    # Issues
    issues_result = countsum_collection('issues', None, value=False)
    issues_total_count = issues_result['count']

    issues_user_result = countsum_collection('issues', engineer_id, value=False)
    issues_user_count = issues_user_result['count']

    issues_updates = count_updates('issues', engineer_id)
    all_users_issues_updates = count_updates('issues', None)

    # TAC Cases
    tac_result = countsum_collection('tac_case', None, value=False)
    tac_total_count = tac_result['count']

    tac_user_result = countsum_collection('tac_case', engineer_id, value=False)
    tac_user_count = tac_user_result['count']

    tac_updates = count_updates('tac_case', engineer_id)
    all_users_tac_updates = count_updates('tac_case', None)

    # Activities
    activities_result = countsum_collection('activity', None, value=False)
    activities_total_count = activities_result['count']

    activities_user_result = countsum_collection('activity', engineer_id, value=False)
    activities_user_count = activities_user_result['count']

    activities_updates = count_updates('activity', engineer_id)
    all_users_activities_updates = count_updates('activity', None)

    context = {
        'user_forecast_total_count': user_forecast_total_count,
        'user_forecast_total_value': user_forecast_total_value,
        'all_users_forecasted_total_count': all_users_forecasted_total_count,
        'all_users_forecasted_total_value': all_users_forecasted_total_value,
        'user_forecasted_updates': user_forecasted_updates,
        'all_users_forecasted_updates': all_users_forecasted_updates,

        'funnel_total_count': funnel_total_count,
        'funnel_total_value': funnel_total_value,
        'funnel_user_count': funnel_user_count,
        'funnel_user_value': funnel_user_value,
        'funnel_updates': funnel_updates,
        'all_users_funnel_updates': all_users_funnel_updates,

        'meetings_total_count': meetings_total_count,
        'meetings_user_count': meetings_user_count,
        'meetings_updates': meetings_updates,
        'all_users_meetings_updates': all_users_meetings_updates,

        'be_total_count': be_total_count,
        'be_user_count': be_user_count,
        'be_updates': be_updates,
        'all_users_be_updates': all_users_be_updates,

        'cx_total_count': cx_total_count,
        'cx_user_count': cx_user_count,
        'cx_updates': cx_updates,
        'all_users_cx_updates': all_users_cx_updates,

        'issues_total_count': issues_total_count,
        'issues_user_count': issues_user_count,
        'issues_updates': issues_updates,
        'all_users_issues_updates': all_users_issues_updates,

        'tac_total_count': tac_total_count,
        'tac_user_count': tac_user_count,
        'tac_updates': tac_updates,
        'all_users_tac_updates': all_users_tac_updates,

        'activities_total_count': activities_total_count,
        'activities_user_count': activities_user_count,
        'activities_updates': activities_updates,
        'all_users_activities_updates': all_users_activities_updates,
    }

    return render(request, 'SEreview/mystats.html', context)



def all_stats(request):
    # Get all unique user IDs and first names
    users = User.objects.values_list('id', 'first_name')

    # List of collections to process
    collections = [
        'forecasted_opportunity',
        'funnel_opportunity',
        'meetings',
        'be_engagement_activity',
        'cx_engagement_activity',
        'issues',
        'tac_case',
        'activity',
    ]

    # Initialize an empty list to store the data
    data = []

    # Initialize an empty dictionary to store DataFrames for each section
    dfs = {}

    for collection_name in collections:
        for user_id, user_firstname in users:
            # Construct the query based on whether 'approx_value' field exists in the collection
            query = {"user_id": user_id}

            # Check if 'approx_value' field exists in the collection
            if db[collection_name].find_one({"approx_value": {"$exists": True}}):
                pipeline = [
                    {"$match": query},
                    {"$group": {
                        "_id": {
                            "user_id": "$user_id",
                        },
                        "count": {"$sum": 1},
                        "sum_value": {"$sum": "$approx_value"},
                        "user_updates": {"$sum": {"$size": "$desc_update"}}
                    }}
                ]
            else:
                pipeline = [
                    {"$match": query},
                    {"$group": {
                        "_id": {
                            "user_id": "$user_id",
                        },
                        "count": {"$sum": 1},
                        "user_updates": {"$sum": {"$size": "$desc_update"}}
                    }}
                ]

            # Aggregate the data
            result = list(db[collection_name].aggregate(pipeline))

            # Combine data into a dictionary
            for item in result:
                data.append({
                    'user_id': user_id,
                    'user_firstname': user_firstname,
                    'section': collection_name,
                    'count': item['count'],
                    'sum_value': item.get('sum_value', 0),  # Replace None with 0
                    'user_updates': item['user_updates'],
                })

        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(data)

        # Pivot the DataFrame to create the desired matrix
        df_pivot = df.pivot_table(index=['user_id', 'user_firstname'], columns=['section'], values=['count', 'sum_value', 'user_updates'], aggfunc='sum', fill_value=0)

        # Reset index to flatten the pivot
        df_pivot = df_pivot.reset_index()

        # Order the DataFrame by the count
        #df_pivot = df_pivot.sort_values(by=[('count', ''), ('user_id', '')], ascending=False)
        #df_pivot = df_pivot.sort_values(by=('user_updates',), ascending=False)








        # Add the DataFrame to the dictionary
        dfs[collection_name] = df_pivot

        # Clear the data list for the next collection
        data = []

    # Flatten the keys for each record in the context
    flattened_context = {}
    for section, section_data in dfs.items():
        flattened_data = []
        for record in section_data.to_dict(orient='records'):
            flattened_record = {}
            for key_tuple, value in record.items():
                flattened_record[key_tuple[0]] = value
            flattened_data.append(flattened_record)
        flattened_context[section] = flattened_data

    return render(request, 'SEreview/allstats.html', {'context': flattened_context})

## same as the all stats but with date range  /monthly_stats/?start_date=01-2023&end_date=02-2023 
def monthly_stats(request):
    form = DateRangeForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())

            users = User.objects.values_list('id', 'first_name')
            collections = [
                'forecasted_opportunity',
                'funnel_opportunity',
                'meetings',
                'be_engagement_activity',
                'cx_engagement_activity',
                'issues',
                'tac_case',
                'activity',
            ]

            data = []
            dfs = {}

            for collection_name in collections:
                for user_id, user_firstname in users:
                    query = {"user_id": user_id}
                    query["create_date"] = {"$gte": start_date, "$lt": end_date}
                    query["desc_update.timestamp"] = {"$gte": start_date, "$lt": end_date}

                    if db[collection_name].find_one({"approx_value": {"$exists": True}}):
                        pipeline = [
                            {"$match": query},
                            {"$group": {
                                "_id": {
                                    "user_id": "$user_id",
                                },
                                "count": {"$sum": 1},
                                "sum_value": {"$sum": "$approx_value"},
                                "user_updates": {"$sum": {"$size": "$desc_update"}}
                            }}
                        ]
                    else:
                        pipeline = [
                            {"$match": query},
                            {"$group": {
                                "_id": {
                                    "user_id": "$user_id",
                                },
                                "count": {"$sum": 1},
                                "user_updates": {"$sum": {"$size": "$desc_update"}}
                            }}
                        ]

                    result = list(db[collection_name].aggregate(pipeline))

                    for item in result:
                        data.append({
                            'user_id': user_id,
                            'user_firstname': user_firstname,
                            'section': collection_name,
                            'count': item['count'],
                            'sum_value': item.get('sum_value', 0),
                            'user_updates': item['user_updates'],
                        })

                df = pd.DataFrame(data)

                if not df.empty:
                    df_pivot = df.pivot_table(index=['user_id', 'user_firstname'], columns=['section'], values=['count', 'sum_value', 'user_updates'], aggfunc='sum', fill_value=0)
                    df_pivot = df_pivot.reset_index()
                    dfs[collection_name] = df_pivot

                data = []

            flattened_context = {}
            for section, section_data in dfs.items():
                flattened_data = []
                for record in section_data.to_dict(orient='records'):
                    flattened_record = {}
                    for key_tuple, value in record.items():
                        flattened_record[key_tuple[0]] = value
                    flattened_data.append(flattened_record)
                flattened_context[section] = flattened_data

            return render(request, 'SEreview/monthly_stats.html', {'context': flattened_context, 'form': form})

    return render(request, 'SEreview/monthly_stats.html', {'form': form})



@login_required
@group_required(allowed_groups=['SE'])
def client_centric(request):
    user_id = request.user.id
    clients = get_all_clients(user_id)  # Replace with your logic to retrieve clients
    print(clients)  # Add this line for debugging

    return render(request, 'SEreview/client_centric.html', {'clients': clients})


@login_required
@group_required(allowed_groups=['SE'])
def client_dashboard(request, client_id, form_name='forecasted_opportunity'):
    collection = db['clients']  # Replace with your actual MongoDB collection
    client = collection.find_one({'_id': ObjectId(client_id)})
    #print(client)
    
    context = {
        'client_id': client_id,
        'form_name': form_name,
        # Include other context variables as needed
    }
    if not client:
        return HttpResponseNotFound("Client not found")

    # Dictionary mapping form names to their corresponding form classes
    form_classes = {
        'forecasted_opportunity': ForecastedOpportunityForm,
        'meetings': WeeklyMeetingForm,
        'funnel_opportunity': FunnelOpportunityForm,
        'activity': ActivityForm,
        'be_engagement_activity': BEEngagementActivityForm,
        'cx_engagement_activity': CXEngagementActivityForm,
        'tac_case': TACCaseForm,
        'issues': IssuesForm,
        'clients': ClientForm,
        'swot': SwotForm,
        'client_strategy': ClientStrategyForm,
    }

    # Validate if form_name is in the form_classes dictionary
    if form_name not in form_classes:
        return HttpResponseNotFound("Form not found")

    form_class = form_classes[form_name]
    user_id = request.user.id
    data = collection_client(form_name, client['client_name'])  # Fetch data for the specified form and client
    fields = fields_to_display.get(form_name, [])  # Define this based on your logic
    data = list(data)
    #print(data)

    # Initialize form with client's name selected
    initial_form_data = {'client_name': client['client_name']}
    form = form_class(initial=initial_form_data)

    return render(request, 'SEreview/client_dashboard.html', {
        'client_name': client['client_name'],
        'client_id': client_id,
        'form': form,
        'form_name': form_name,
        'data': data,
        'fields_to_display': fields,
    })
    
@login_required    
def process_dash(request, form_name):
    if request.method == 'POST':
        user_id = request.user.id  # Retrieve the logged-in user ID

        client_name = request.POST.get('client_name')  # Retrieve client_name from POST data if available
        client_id = get_client_id_by_name(client_name)
        
        if form_name == 'forecasted_opportunity':
            form = ForecastedOpportunityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'create_date': datetime.now(),
                    'approx_value': form.cleaned_data['approx_value'],
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)
        
        elif form_name == 'funnel_opportunity':
            form = FunnelOpportunityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'approx_value': form.cleaned_data['approx_value'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'activity':
            form = ActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'activity_name': form.cleaned_data['activity_name'],
                    'client_name': form.cleaned_data['client_name'],
                    'technology': form.cleaned_data['technology'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'be_engagement_activity':
            form = BEEngagementActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'opportunity_name': form.cleaned_data['opportunity_name'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'be_name': form.cleaned_data['be_name'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'cx_engagement_activity':
            form = CXEngagementActivityForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'cx_name': form.cleaned_data['cx_name'],
                    'pending': form.cleaned_data['pending'],
                    'status': form.cleaned_data['status'],
                    'be_name': form.cleaned_data['be_name'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'tac_case':
            form = TACCaseForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'case_name': form.cleaned_data['case_name'],
                    'status': form.cleaned_data['status'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'issues':
            form = IssuesForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'issue_title': form.cleaned_data['issue_title'],
                    'status': form.cleaned_data['status'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'meetings':
            form = WeeklyMeetingForm(request.POST)
            if form.is_valid():
                meeting_date = datetime(
                    year=form.cleaned_data['meeting_date'].year,
                    month=form.cleaned_data['meeting_date'].month,
                    day=form.cleaned_data['meeting_date'].day,
                )
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'status': 'Active',
                    'meeting_date': meeting_date,
                    'meeting_outcome': form.cleaned_data['meeting_outcome'],
                    'create_date': datetime.now(),
                    'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'timestamp': datetime.now()
                        }
                    ]
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'clients':
            form = ClientForm(request.POST)
            if form.is_valid():
                client_name = form.cleaned_data['client_name'].capitalize()
                if not check_client_exists(client_name, user_id):
                    data = {
                        'user_id': user_id,
                        'status': 'Active',
                        'client_name': form.cleaned_data['client_name'],
                    }
                    process_form_data(form_name, data)
                    client_id = get_client_id_by_name(client_name)
                    return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)
                else:
                    error_message = "Client already exists."
                    return redirect('SEreview:error_page_with_message', message=error_message)
                
        elif form_name == 'swot':
            form = SwotForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'strength': form.cleaned_data['strength'],
                    'weakness': form.cleaned_data['weakness'],
                    'opportunity': form.cleaned_data['opportunity'],
                    'threat': form.cleaned_data['threat'],
                    'create_date': datetime.now()
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)

        elif form_name == 'client_strategy':
            form = ClientStrategyForm(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'security_strategy': form.cleaned_data['security_strategy'],
                    'ai_strategy': form.cleaned_data['ai_strategy'],
                    'cloud_strategy': form.cleaned_data['cloud_strategy'],
                    'observability_strategy': form.cleaned_data['observability_strategy'],
                    'create_date': datetime.now()
                }
                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_with_form', client_id=client_id, form_name=form_name)
    

    else:
        return redirect('SEreview:error_page')

def get_client_id_by_name(client_name):
    collection = db['clients']
    result = collection.find_one({'client_name': client_name})
    if result:
        return str(result['_id'])
    return None

# Function to get the client name by client_id
def get_client_name_by_id(client_id):
    try:
        collection = db['clients']
        result = collection.find_one({'_id': ObjectId(client_id)})
        if result:
            print (result['client_name'])
            return str(result['client_name'])
    except Exception as e:
        print(f"Error retrieving client name: {e}")
    return None

@group_required(allowed_groups=['SE','BE'])
def client_centric_be(request,be_name=None):
    user_id = request.user.id
    clients = get_all_clients_for_user(user_id) # Replace with your logic to retrieve clients
    #print(clients)  # Add this line for debugging
    if be_name!=None:
        return render(request, 'SEreview/client_centric_be_name.html', {'clients': clients,'be_name':be_name})
    else:
         return render(request, 'SEreview/client_centric_be.html', {'clients': clients})


@group_required(allowed_groups=['SE','BE'])
def client_dashboard_be(request, client_id, form_name=None, be_name=None, source=None):
    # Set default values if parameters are not provided
    if form_name is None:
        form_name = 'bestatus'
    if be_name is None:
        be_name = 'Sec'
    if source is None:
        source = 'SE'
    
    print ("form name "+form_name ,"be_name "+be_name)
    # Define your form classes in a dictionary for easy lookup
    form_classes = {
        'bestatus': BEStatusForm,
        'beinitiative': BEInitiativeForm,
        'beactivity': BEActivityForm,
    }
    
    if request.method == 'GET':
        form_class = form_classes.get(form_name)
        if not form_class:
            error_message = "form ="+form_name+"Source ="+source
            return redirect('SEreview:error_page_with_message', message=error_message)
        
        user_id = request.user.id
        # Fetch client name based on client_id
        client_name = get_client_name_by_id(client_id)
        
        # Fetch data for the specified form and client
        data = collection_client_be(form_name, client_name,be_name)  # Fetch data using client_name directly
        fields = fields_to_display.get(form_name, [])  # Define this based on your logic # Define this based on your logic
        data = list(data)
        
        # Initialize form with client's name and default be_name
        initial_form_data = {
            'client_name': client_name,
            'be_name': be_name
        }
        form = form_class(initial=initial_form_data)
        
        # Fetch existing clients
        existing_clients = get_existing_clients(user_id)
        
        # Initialize context
        context = {
            'form': form,
            'form_name': form_name,
            'client_name': client_name,
            'client_id': client_id,
            'be_name': be_name,
            'existing_clients': existing_clients,
            'fields_to_display': fields,
            'data': data
        }
        
        # Fetch existing initiatives only for 'beactivity' form
        if form_name == 'beactivity':
            existing_beinitiatives = get_existing_beinitiative(client_name, be_name,user_id)
            ## debug print
            #print(existing_beinitiatives)
            context['existing_initiatives'] = existing_beinitiatives
        
        print("Context data:", context['data'])
        if source == 'SE':
            return render(request, 'SEreview/client_dashboard_be.html', context)
        else:
            return render(request, 'SEreview/client_dashboard_be_name.html', context)
    
    return redirect('SEreview:error_page')


def process_dash_be(request, form_name):
    # Define your form classes in a dictionary for easy lookup
    form_classes = {
        'bestatus': BEStatusForm,
        'beinitiative': BEInitiativeForm,
        'beactivity': BEActivityForm,
    }

    if request.method == 'POST':
        user_id = request.user.id  # Retrieve the logged-in user ID
        client_name = request.POST.get('client_name')  # Retrieve client_name from POST data
        client_id = get_client_id_by_name(client_name)
        #source = request.POST.get('source')

        form_class = form_classes.get(form_name)
        if form_class:
            form = form_class(request.POST)
            if form.is_valid():
                data = {
                    'user_id': user_id,
                    'client_name': form.cleaned_data['client_name'],
                    'be_name': form.cleaned_data.get('be_name', ''),  # Default to empty string if not provided
                    'create_date': timezone.now(),
                }

                # Add form-specific fields
                if form_name == 'bestatus':
                    data.update({
                        'worked_last_year': form.cleaned_data.get('worked_last_year', ''),
                        'challenging_last_year': form.cleaned_data.get('challenging_last_year', ''),
                        'status': form.cleaned_data.get('status', ''),
                        'focus_next_year': form.cleaned_data.get('focus_next_year', '')
                    })
                elif form_name == 'beinitiative':
                    data.update({
                        'initiative_short': form.cleaned_data.get('initiative_short', ''),
                        'initiative_desc': form.cleaned_data.get('initiative_desc', ''),
                        'expected_outcome': form.cleaned_data.get('expected_outcome', ''),
                        'expected_execution_date':  datetime.combine(form.cleaned_data.get('expected_execution_date'), datetime.min.time()),
                        'owners': form.cleaned_data.get('owners', []),
                        'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'user_id': request.user.id,
                            'timestamp': datetime.now()
                        }
                                    ],
                        'status': form.cleaned_data.get('status', '')
                    })
                elif form_name == 'beactivity':
                    data.update({
                        'activity_name': form.cleaned_data.get('activity_name', ''),
                        'initiative': form.cleaned_data.get('initiative', ''),
                        'pending': form.cleaned_data.get('pending', ''),
                        'status': form.cleaned_data.get('status', ''),
                        'desc_update': [
                        {
                            'text': form.cleaned_data['desc_update'],
                            'user_id': request.user.id,
                            'timestamp': datetime.now()
                        }
                                    ],
                        'status': form.cleaned_data.get('status', '')
                    })

                process_form_data(form_name, data)
                return redirect('SEreview:client_dashboard_be_with_name', client_id=client_id, form_name=form_name, be_name=form.cleaned_data.get('be_name', ''),source=form.cleaned_data.get('source'))

    return redirect('SEreview:error_page')