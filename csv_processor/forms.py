from django import forms

class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV File')