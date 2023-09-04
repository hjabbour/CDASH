from django import forms
from django.forms import formset_factory

# 2023 Haytham Jabbour hjabbour
technologies = ['DC', 'Sec', 'Collab','EN','SDWAN','IOT']
BE = ['Sec', 'EN', 'DC','Collab','IOT']
entities = ['AM', 'Client', 'SE','BE']
status_op = ['Active','Booked','Lost','Closed']
status_be = ['Planned','Finished','Active','Delayed']
status_cx = ['Planned','Finished','Active','Delayed']
status_tac = ['Monitoring','Engaged','Closed']
status_issue = ['Active','Resolved','Improved']

pending= ['AM', 'Client','SE','BE','Partner','Leadership','TAC','CX','BU']

def generate_dropdown_component(options):
    choices = [(option, option) for option in options]
    return forms.ChoiceField(choices=choices)

def generate_multiselect_component(options):
    choices = [(option, option) for option in options]
    return forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple)

def generate_radio_component(options):
    choices = [(option, option) for option in options]
    return forms.ChoiceField(choices=choices, widget=forms.RadioSelect)




class ForecastedOpportunityForm(forms.Form):
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    client_name = forms.CharField(label="Client Name", max_length=100)
    technology=generate_multiselect_component(technologies)
    pending = generate_radio_component(pending)
    status = generate_radio_component(status_op)
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class FunnelOpportunityForm(forms.Form):
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    client_name = forms.CharField(label="Client Name", max_length=100)
    technology=generate_multiselect_component(technologies)
    pending = generate_radio_component(pending)
    status = generate_radio_component(status_op)
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class BEEngagementActivityForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    be_name = generate_radio_component(BE)
    pending = generate_radio_component(pending)
    status = generate_radio_component(status_be)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class CXEngagementActivityForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    cx_name = forms.CharField(label="CX Name", max_length=100)
    be_name = generate_radio_component(BE)
    pending = generate_radio_component(pending)
    status = generate_radio_component(status_cx)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class TACCaseForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    case_name = forms.CharField(label="Case Name", max_length=100)
    status = generate_radio_component(status_tac)
    pending = generate_radio_component(pending)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class IssuesForm(forms.Form):
    issue_title = forms.CharField(label="Issue Title", max_length=100)
    status = generate_radio_component(status_issue)
    pending = generate_radio_component(pending)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class WeeklyMeetingForm(forms.Form):
    client_name = forms.CharField(max_length=100)
    meeting_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    desc_update = forms.CharField(label="Meeting Description",widget=forms.Textarea)
    meeting_outcome = forms.CharField(label="Meeting Outcome",widget=forms.Textarea)

class UForecastedOpportunityForm(forms.Form):
    pending = generate_radio_component(pending)
    status = generate_radio_component(status_op)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class UFunnelOpportunityForm(forms.Form):

    pending = generate_radio_component(pending)
    status = generate_radio_component(status_op)
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class UBEEngagementActivityForm(forms.Form):

    pending = generate_radio_component(pending)
    status = generate_radio_component(status_be)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class UCXEngagementActivityForm(forms.Form):
    pending = generate_radio_component(pending)
    status = generate_radio_component(status_cx)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class UTACCaseForm(forms.Form):
    status = generate_radio_component(status_tac)
    pending = generate_radio_component(pending)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)
    
class UIssuesForm(forms.Form):
    status = generate_radio_component(status_issue)
    pending = generate_radio_component(pending)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)
    


