# Create your views here.
# views.py
from pymongo import MongoClient
from datetime import datetime,timedelta
from bson import ObjectId
from dateutil.relativedelta import relativedelta


from admin_datta.forms import RegistrationForm, LoginForm, UserPasswordChangeForm, UserPasswordResetForm, UserSetPasswordForm
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.contrib.auth import get_user_model
from django.views.generic import CreateView
from django.contrib.auth import logout

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from .forms import ForecastedOpportunityForm, FunnelOpportunityForm, BEEngagementActivityForm, CXEngagementActivityForm, TACCaseForm
from .forms import UForecastedOpportunityForm, UFunnelOpportunityForm, UBEEngagementActivityForm, UCXEngagementActivityForm, UTACCaseForm


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
                process_forecasted_opportunity_form(data)
                return redirect('success_page')

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
                process_funnel_opportunity_form(data)
                return redirect('success_page')

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
                process_be_engagement_activity_form(data)
                return redirect('success_page')

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
                process_cx_engagement_activity_form(data)
                return redirect('success_page')

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
                process_tac_case_form(data)
                return redirect('success_page')

    else:
        # Invalid request method, redirect to an error page or handle as needed
        return redirect('error_page')

def collection_list(request, collection_name):
    user_id = request.user.id  # Retrieve the logged-in user ID
    collection = db[collection_name]
    data = collection.find()
    context = {
        'collection_name': collection_name,
        'data': data
        # Other context variables
    }
    
    return render(request, 'SEreview/collection_list.html', context)

def update_item(request, collection_name, item_id):
    user_id = request.user.id  # Retrieve the logged-in user ID
    collection = db[collection_name]
    item = collection.find_one({'_id': ObjectId(item_id)})

    # Determine the update form class based on the collection name
    if collection_name == 'forecasted_opportunity':
        UpdateForm = UForecastedOpportunityForm
    elif collection_name == 'funnel_opportunity':
        UpdateForm = UFunnelOpportunityForm
    elif collection_name == 'be_engagement_activity':
        UpdateForm = UBEEngagementActivityForm
    elif collection_name == 'cx_engagement_activity':
        UpdateForm = UCXEngagementActivityForm
    elif collection_name == 'tac_case':
        UpdateForm = UTACCaseForm
    else:
        # Handle the case when the collection name is not recognized
        return HttpResponse('Invalid collection name')

    if request.method == 'POST':
        form = UpdateForm(request.POST)
        if form.is_valid():
            pending = form.cleaned_data['pending']
            status = form.cleaned_data['status']
            approx_value = form.cleaned_data['approx_value']
            desc_update_text = form.cleaned_data['desc_update']
            
            # Update pending, status, and desc_update fields
            if(approx_value):
                collection.update_one({'_id': ObjectId(item_id)}, {'$set': {'pending': pending, 'status': status,'approx_value':approx_value}})
            else:
                collection.update_one({'_id': ObjectId(item_id)}, {'$set': {'pending': pending, 'status': status}})
            
            # Add to desc_update array
            update = {
                'text': desc_update_text,
                'timestamp': datetime.now()
            }
            collection.update_one({'_id': ObjectId(item_id)}, {'$push': {'desc_update': update}})
            
            return redirect('SEreview:collection_list', collection_name=collection_name)
    else:
        form = UpdateForm()

    return render(request, 'SEreview/update_item.html', {'form': form, 'item': item, 'collection_name': collection_name, 'item_id': item_id})

## Queries sections maybe moved to seperate file 
def count_active_forecasted_opportunities(user_id=None):
    # Establish connection to MongoDB
    client = MongoClient('mongodb://root:rootpassword@192.168.2.190:27017')
    db = client['CDASH']

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
    client = MongoClient('mongodb://root:rootpassword@192.168.2.190:27017')
    db = client['CDASH']

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
    client = MongoClient('mongodb://root:rootpassword@192.168.2.190:27017')
    db = client['CDASH']
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


def stats_view(request, user_id=None):
    user_id = request.user.id
    # Retrieve the forecasted opportunities based on the user_id parameter
    if user_id:
        forecast_count,forecast_value = count_active_forecasted_opportunities(user_id)
        funnel_count,funnel_value = count_active_funnel_opportunities(user_id)
        user_first_name = get_user_first_name(user_id)
    else:
        forecast_count,forecast_value =count_active_forecasted_opportunities()
        funnel_count,funnel_value = count_active_funnel_opportunities(user_id)
        
    total_funnel = forecast_value+funnel_value
    total_count = funnel_count+forecast_count
    
    week_updates = weekly_updates()
    # Create the context dictionary
    context = {
        'forecast_count': forecast_count,
        'forecast_value':forecast_value,
        'funnel_count':funnel_count,
        'funnel_value':funnel_value,
        'total_funnel':total_funnel,
        'total_count':total_count,
        'week_updates':week_updates,
        'first_name': user_first_name
    }

    # Render the stats.html template with the context
    #return render(request, 'SEreview/stats.html', context)
    return render(request, 'pages/index.html', context)