from django import forms

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
        {'value': 'option1', 'label': 'Option 1'},
        {'value': 'option2', 'label': 'Option 2'},
        {'value': 'option3', 'label': 'Option 3'},
    ]
    return multiselect_options

class ForecastedOpportunityForm(forms.Form):
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    client_name = forms.CharField(label="Client Name", max_length=100)
    technology_options = get_dropdown_options()
    technology = forms.ChoiceField(label="Technology", choices=[(option['value'], option['label']) for option in technology_options])
    progress = forms.IntegerField(label="Progress", min_value=0, max_value=100, widget=forms.NumberInput(attrs={'class': 'progress-bar'}))
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))

class FunnelOpportunityForm(forms.Form):
    opportunity_name = forms.CharField(label="Opportunity Name", max_length=100)
    client_name = forms.CharField(label="Client Name", max_length=100)
    technology_options = get_dropdown_options()
    technology = forms.ChoiceField(label="Technology", choices=[(option['value'], option['label']) for option in technology_options])
    progress = forms.IntegerField(label="Progress", min_value=0, max_value=100, widget=forms.NumberInput(attrs={'class': 'progress-bar'}))
    approx_value = forms.FloatField(label="Approx Value ($)", min_value=0, widget=forms.TextInput(attrs={'pattern': '[0-9]*\.?[0-9]+', 'title': 'Enter a valid numeric value'}))

class BEEngagementActivityForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    be_name = forms.CharField(label="BE Name", max_length=100)
    progress = forms.IntegerField(label="Progress", min_value=0, max_value=100, widget=forms.NumberInput(attrs={'class': 'progress-bar'}))

class CXEngagementActivityForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    cx_name = forms.CharField(label="CX Name", max_length=100)
    progress = forms.IntegerField(label="Progress", min_value=0, max_value=100, widget=forms.NumberInput(attrs={'class': 'progress-bar'}))

class TACCaseForm(forms.Form):
    client_name = forms.CharField(label="Client Name", max_length=100)
    case_name = forms.CharField(label="Case Name", max_length=100)
    multiselect_options = get_multiselect_options()
    selected_options = forms.MultipleChoiceField(label="Select Options", choices=[(option['value'], option['label']) for option in multiselect_options])
