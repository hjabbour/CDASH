from django import forms
# 2023 Haytham Jabbour hjabbour
class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV File')