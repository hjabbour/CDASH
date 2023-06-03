from django import forms
from django.forms import formset_factory


technologies = ['DC', 'Sec', 'Collab','EN','SDWAN','IOT']
BE = ['Sec', 'EN', 'DC','Collab','IOT']
entities = ['AM', 'Client', 'SE','BE']

def generate_dropdown_component(options):
    choices = [(option, option) for option in options]
    return forms.ChoiceField(choices=choices)

def generate_multiselect_component(options):
    choices = [(option, option) for option in options]
    return forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple)

def generate_radio_component(options):
    choices = [(option, option) for option in options]
    return forms.ChoiceField(choices=choices, widget=forms.RadioSelect)



def get_dropdown_options():
    # Define the dropdown options as a list of dictionaries
    dropdown_options = [
        {'value': 'DC', 'label': 'DC'},
        {'value': 'Sec', 'label': 'Sec'},
        {'value': 'Collab', 'label': 'Collab'},
    ]
    return dropdown_options

def get_multiselect_options():
    # Define the multiselect options as a list of dictionaries
    multiselect_options = [
        {'value': 'DC', 'label': 'DC'},
        {'value': 'Sec', 'label': 'Sec'},
        {'value': 'Collab', 'label': 'Collab'},
    ]
    return multiselect_options

class ForecastedOpportunityForm(forms.Form):
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    client_name = forms.CharField(label="Client Name", max_length=100)
    #technology_options = get_dropdown_options()
    #technology = forms.MultipleChoiceField(label="Technology", choices=[(option['value'], option['label']) for option in technology_options], widget=forms.CheckboxSelectMultiple)
    technology=generate_multiselect_component(technologies)
    progress = forms.ChoiceField(label="Progress", choices=[(10, '10%'), (25, '25%'), (50, '50%'), (75, '75%'), (90, '90%'), (100, '100%')], widget=forms.RadioSelect)
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class FunnelOpportunityForm(forms.Form):
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    client_name = forms.CharField(label="Client Name", max_length=100)
    technology_options = get_dropdown_options()
    technology = forms.MultipleChoiceField(label="Technology", choices=[(option['value'], option['label']) for option in technology_options], widget=forms.CheckboxSelectMultiple)
    progress = forms.ChoiceField(label="Progress", choices=[(10, '10%'), (25, '25%'), (50, '50%'), (75, '75%'), (90, '90%'), (100, '100%')], widget=forms.RadioSelect)
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class BEEngagementActivityForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    be_name = generate_radio_component(BE)
    progress = forms.ChoiceField(label="Progress", choices=[(10, '10%'), (25, '25%'), (50, '50%'), (75, '75%'), (90, '90%'), (100, '100%')], widget=forms.RadioSelect)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class CXEngagementActivityForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    cx_name = forms.CharField(label="CX Name", max_length=100)
    progress = forms.ChoiceField(label="Progress", choices=[(10, '10%'), (25, '25%'), (50, '50%'), (75, '75%'), (90, '90%'), (100, '100%')], widget=forms.RadioSelect)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)

class TACCaseForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    case_name = forms.CharField(label="Case Name", max_length=100)
    progress = forms.ChoiceField(label="Progress", choices=[(10, '10%'), (25, '25%'), (50, '50%'), (75, '75%'), (90, '90%'), (100, '100%')], widget=forms.RadioSelect)
    desc_update = forms.CharField(label="Update Description", widget=forms.Textarea)
