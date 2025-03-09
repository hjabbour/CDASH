from django import forms

# Updated list of Groups
GROUPS = [
    ("Sec", "Security"),
    ("EN", "Enterprise Networking"),
    ("DC", "Data Center"),
    ("Collab", "Collaboration"),
    ("IOT", "Internet of Things"),
    ("SPRouting", "Service Provider Routing"),
    ("FSO", "Full-Stack Observability"),
    ("SES", "Solution Engineers"),
    ("SalesPS", "Sales - Public Sector"),
    ("BES", "Business Entities"),
    ("SalesPvt", "Sales - Private Sector"),
]


STATUS_CHOICES = [
    ("Planned", "Planned"),
    ("Initial", "Initial"),
    ("Followup", "Followup"),
    ("Funnel", "Funnel"),
    ("Completed", "Completed"),
]

PENDING_CHOICES = [
    ("AM", "AM"),
    ("Client", "Client"),
    ("SE", "SE"),
    ("BE", "BE"),
    ("Partner", "Partner"),
    ("Leadership", "Leadership"),
    ("TAC", "TAC"),
    ("CX", "CX"),
    ("BU", "BU"),
]

BE_CHOICES = [
    ("Sec", "Security"),
    ("EN", "Enterprise Networking"),
    ("DC", "Data Center"),
    ("Collab", "Collaboration"),
    ("IOT", "Internet of Things"),
    ("SPRouting", "SP Routing"),
    ("FSO", "Full Stack Observability"),
]

class sWebexMessageForm(forms.Form):
    recipient_email = forms.EmailField(required=False, label="User Email")
    space_id = forms.CharField(required=False, label="Space ID")
    message = forms.CharField(widget=forms.Textarea, label="Message")

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("recipient_email") and not cleaned_data.get("space_id"):
            raise forms.ValidationError("Provide either a recipient email or a space ID.")
        return cleaned_data

class WebexSpaceForm(forms.Form):
    space_name = forms.CharField(label="Space Name", max_length=255, required=True)
    space_id = forms.CharField(label="Space ID", max_length=255, required=True)
    group = forms.ChoiceField(label="Group", choices=GROUPS, required=True)  # Dropdown
    


## template form used to test format not fully functional
class WebexMessageForm(forms.Form):
    MESSAGE_TYPE_CHOICES = [
        ("text", "Plain Text"),
        ("mongodb", "MongoDB Query Results"),
        ("pandas", "Pandas DataFrame"),
        ("adaptive_card", "Webex Adaptive Card"),
        ("markdown", "Formatted Markdown Message")
    ]

    recipient_email = forms.EmailField(required=False, label="Recipient Email")
    space_id = forms.CharField(required=False, label="Webex Space ID")
    message = forms.CharField(widget=forms.Textarea, required=True, label="Message / Data")
    message_type = forms.ChoiceField(choices=MESSAGE_TYPE_CHOICES, label="Message Type", initial="text")

    def clean(self):
        cleaned_data = super().clean()
        recipient_email = cleaned_data.get("recipient_email")
        space_id = cleaned_data.get("space_id")

        if not recipient_email and not space_id:
            raise forms.ValidationError("You must provide either a recipient email or a Webex Space ID.")

        return cleaned_data



class BEActivityReportForm(forms.Form):
    be_name = forms.ChoiceField(
        choices=BE_CHOICES,
        label="Business Entity",
        required=True,
    )
    #space_id = forms.CharField(label="Webex Space ID", max_length=255)
    

    status_filter = forms.MultipleChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Filter by Status",
    )
    exclude_status = forms.MultipleChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Exclude Status",
    )
    pending_filter = forms.MultipleChoiceField(
        choices=PENDING_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Filter by Pending",
    )
    months = forms.IntegerField(
        label="Time Frame (Months)",
        required=False,
        min_value=1,
        help_text="Leave blank for all-time report",
    )
    space_id = forms.ChoiceField(label="Webex Space", choices=[])  # No static choices
    # Checkboxes for optional reports
    send_activity_report = forms.BooleanField(required=False, label="Send Activity Report")
    send_detailed_report = forms.BooleanField(required=False, label="Send Detailed Report")
    send_initiative_report = forms.BooleanField(required=False, label="Send Initiative Report")
    send_combined_report = forms.BooleanField(required=False, label="Send Combined Report")
