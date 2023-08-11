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
from .forms import ForecastedOpportunityForm, FunnelOpportunityForm, BEEngagementActivityForm, CXEngagementActivityForm, TACCaseForm, IssuesForm,WeeklyMeetingForm
from .forms import UForecastedOpportunityForm, UFunnelOpportunityForm, UBEEngagementActivityForm, UCXEngagementActivityForm, UTACCaseForm, UIssuesForm

## remove status list from collection_user and put toupdatelist
statuslist = ['Planned','Active','Delayed']
toupdatelist = ['Planned','Active','Delayed','Monitoring','Engaged']
fields_to_display = {
        'forecasted_opportunity': ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'funnel_opportunity': ['Client/Status', 'Creatiion Date','Update', 'Pending','Action'],
        'be_engagement_activity': ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'meetings': ['Client/Status', 'Creation Date','Update','Pending','Action'],
        'cx_engagement_activity' : ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'tac_case' : ['Client/Status', 'Creation Date','Update', 'Pending','Action'],
        'issues' : ['Issue title', 'Creation Date','Update', 'Pending','Action'],
         
        # Add more collections and their corresponding fields here
    }

#client = MongoClient('mongodb://root:password@192.168.2.155:27017')
client = MongoClient('mongodb://root:password@192.168.2.156:27017')
#client = MongoClient('mongodb://root:password@10.229.166.67:27017')
#client = MongoClient('mongodb://root:password@127.0.0.1:27017')
#client = MongoClient('mongodb://root:password@192.168.43.143:27017')




db = client['CDASH']
@login_required
def meetings_view(request):
    form = WeeklyMeetingForm()
    user_id = request.user.id
    data =  collection_user(user_id, 'meetings') 
    fields = fields_to_display.get('meetings', [])
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'meetings','data':data,'fields_to_display':fields})

def forecasted_opportunity_view(request):
    form = ForecastedOpportunityForm()
    user_id = request.user.id
    data =  collection_user(user_id, 'forecasted_opportunity')
    fields = fields_to_display.get('forecasted_opportunity', []) 
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'forecasted_opportunity','data':data,'fields_to_display':fields})

def funnel_opportunity_view(request):
    form = FunnelOpportunityForm()
    user_id = request.user.id
    data =  collection_user(user_id, 'funnel_opportunity') 
    fields = fields_to_display.get('funnel_opportunity', []) 
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'funnel_opportunity','data':data,'fields_to_display':fields})

def be_engagement_activity_view(request):
    form = BEEngagementActivityForm()
    user_id = request.user.id
    fields = fields_to_display.get('be_engagement_activity', []) 
    data =  collection_user(user_id, 'be_engagement_activity')
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'be_engagement_activity','data':data,'fields_to_display':fields})

def cx_engagement_activity_view(request):
    form = CXEngagementActivityForm()
    user_id = request.user.id
    fields = fields_to_display.get('cx_engagement_activity', []) 
    data =  collection_user(user_id, 'cx_engagement_activity')
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'cx_engagement_activity','data':data,'fields_to_display':fields})

def tac_case_view(request):
    form = TACCaseForm()
    user_id = request.user.id
    fields = fields_to_display.get('tac_case', [])
    data =  collection_user(user_id, 'tac_case')
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'tac_case','data':data,'fields_to_display':fields})

def issues_view(request):
    form = IssuesForm()
    user_id = request.user.id
    fields = fields_to_display.get('issues', [])
    data =  collection_user(user_id, 'issues')
    return render(request, 'SEreview/form_template.html', {'form': form, 'form_name': 'issues','data':data,'fields_to_display':fields})


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

def process_issues_form(data):
    collection = db['issues']
    # Process and save the TAC case form data
    # ...
    collection.insert_one(data)
    
def process_meetings_form(data):
    collection = db['meetings']
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
                process_funnel_opportunity_form(data)
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
                process_be_engagement_activity_form(data)
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
                process_cx_engagement_activity_form(data)
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
                process_tac_case_form(data)
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
                process_issues_form(data)
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
                process_meetings_form(data)
                return redirect('SEreview:'+form_name)

    else:
        # Invalid request method, redirect to an error page or handle as needed
        return redirect('error_page')

def collection_list(request, collection_name):
    user_id = request.user.id  # Retrieve the logged-in user ID
    collection = db[collection_name]
    if is_user_superuser(user_id):
        data = collection.find()
    else:
        data = collection.find({'user_id': user_id})
    fields = fields_to_display.get(collection_name, [])
    # Preprocess the data to create a list of dictionaries
    
    context = {
        'collection_name': collection_name,
        'data': data,
        'fields_to_display': fields,
        
         }
    
    return render(request, 'SEreview/collection_list.html', context)

## use the toupdatelist to get what is needed 
def collection_user(user_id, collection_name,superuser=False):
    
    #statuslist = ['Planned','Active','Delayed']
    collection = db[collection_name]
    if is_user_superuser(user_id):
        data = collection.find({'status': {'$in': toupdatelist}})
    else:
        data = collection.find({'user_id': user_id,'status': {'$in': toupdatelist}})
    return data

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
    elif collection_name == 'issues':
        UpdateForm = UIssuesForm
    else:
        # Handle the case when the collection name is not recognized
        return HttpResponse('Invalid collection name')

    if request.method == 'POST':
        form = UpdateForm(request.POST)
        approx_value = None 
        if form.is_valid():
            pending = form.cleaned_data['pending']
            status = form.cleaned_data['status']
            if 'approx_value' in form.cleaned_data:
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
        funnel_count,funnel_value = count_active_funnel_opportunities(user_id)
        
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

def is_user_superuser(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        return user.is_superuser
    except User.DoesNotExist:
        return False

def weeklyreview(request):
    user_id = request.user.id
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
    })