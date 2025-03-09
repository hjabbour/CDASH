# Create your views here.
from django.shortcuts import render,redirect, get_object_or_404 
from django.contrib import messages
from .forms import sWebexMessageForm ,WebexSpaceForm,WebexMessageForm,BEActivityReportForm
# from .utils import send_message_to_user, send_message_to_space
from SEreview.conn import get_mongodb_connection  # Correct import for another app
from django.contrib.auth.decorators import user_passes_test
# from .utils import send_message, send_table_message, send_adaptive_card, send_markdown_message, generate_beactivity_report, send_to_webex
from .utils import  send_to_webex ,be_activity_report,be_activity_report_detailed,be_metrics_report,send_table_to_webex,combined_be_report,combined_be_initiative_report

import json  # For parsing JSON data
import pandas as pd  # For working with Pandas DataFrames



# Establish MongoDB connection
client = get_mongodb_connection()
db = client["CDASH"]
collection = db["webex_spaces"]  # Collection for storing spaces


# Function to check if user is a superuser
def superuser_required(user):
    return user.is_superuser

@user_passes_test(superuser_required)
def send_webex_message(request):
    if request.method == "POST":
        form = sWebexMessageForm(request.POST)
        if form.is_valid():
            recipient_email = form.cleaned_data["recipient_email"]
            space_id = form.cleaned_data["space_id"]
            message_text = form.cleaned_data["message"]

            try:
                if recipient_email:
                    send_message_to_user(recipient_email, message_text)
                elif space_id:
                    send_message_to_space(space_id, message_text)

                messages.success(request, "Message sent successfully!")
            except Exception as e:
                messages.error(request, f"Failed to send message: {str(e)}")
    else:
        form = sWebexMessageForm()

    return render(request, "messaging/send_message.html", {"form": form})

@user_passes_test(superuser_required)
def add_webex_space(request):
    if request.method == "POST":
        form = WebexSpaceForm(request.POST)
        if form.is_valid():
            space_data = {
                "space_name": form.cleaned_data["space_name"],
                "space_id": form.cleaned_data["space_id"],
                "group": form.cleaned_data["group"],
            }
            collection.insert_one(space_data)  # Insert into MongoDB
    else:
        form = WebexSpaceForm()

    # 🔍 DEBUG: Print MongoDB contents to confirm data retrieval
    existing_spaces = list(collection.find({}, {"_id": 0, "space_name": 1, "space_id": 1, "group": 1}))
    print("Existing Spaces:", existing_spaces)  # Check if data is being fetched

    return render(request, "messaging/add_webex_space.html", {"form": form, "existing_spaces": existing_spaces})




@user_passes_test(superuser_required)
def send_mwebex_message(request):
    """
    View to send a Webex message via a form.
    Supports:
    - Plain text messages
    - MongoDB query results (formatted as tables)
    - Pandas DataFrame tables
    - Adaptive Cards (for structured data)
    - Markdown-formatted messages
    """
    if request.method == "POST":
        form = WebexMessageForm(request.POST)
        if form.is_valid():
            recipient_email = form.cleaned_data["recipient_email"]
            space_id = form.cleaned_data["space_id"]
            message_text = form.cleaned_data["message"]
            message_type = form.cleaned_data["message_type"]

            try:
                # Handle message type
                if message_type == "text":
                    response = send_message(recipient_email, space_id, message_text)

                elif message_type == "mongodb":
                    # Assuming the MongoDB data is submitted as a JSON string, parse it
                    try:
                        query_results = json.loads(message_text)  # Convert string to list of dicts
                        response = send_table_message(query_results=query_results, recipient_email=recipient_email, space_id=space_id)
                    except json.JSONDecodeError:
                        raise Exception("Invalid MongoDB JSON format.")

                elif message_type == "pandas":
                    # If the message is in CSV format (as a string), create a DataFrame
                    try:
                        data = [line.split(",") for line in message_text.split("\n")]
                        df = pd.DataFrame(data[1:], columns=data[0])
                        response = send_table_message(df=df, recipient_email=recipient_email, space_id=space_id)
                    except Exception as e:
                        raise Exception(f"Failed to process Pandas DataFrame: {str(e)}")

                elif message_type == "adaptive_card":
                    # Assuming the message is in JSON format for Adaptive Card
                    try:
                        adaptive_card = json.loads(message_text)  # Convert string to dict
                        response = send_adaptive_card(query_results=adaptive_card, recipient_email=recipient_email, space_id=space_id)
                    except json.JSONDecodeError:
                        raise Exception("Invalid Adaptive Card JSON format.")

                elif message_type == "markdown":
                    response = send_markdown_message(markdown_text=message_text, recipient_email=recipient_email, space_id=space_id)

                messages.success(request, response)

            except Exception as e:
                messages.error(request, f"Failed to send message: {str(e)}")
    else:
        form = WebexMessageForm()

    return render(request, "messaging/send_message.html", {"form": form})




## woking with select and options

# def be_activity_report_view(request):
#     # Retrieve Webex spaces from MongoDB
#     collection = db["webex_spaces"]
#     existing_spaces = list(collection.find({}, {"_id": 0, "space_name": 1, "space_id": 1}))
#     space_choices = [(space["space_id"], space["space_name"]) for space in existing_spaces]

#     if request.method == "POST":
#         form = BEActivityReportForm(request.POST)
#         form.fields["space_id"].choices = space_choices  # Set choices dynamically

#         if form.is_valid():
#             be_name = form.cleaned_data["be_name"]
#             space_id = form.cleaned_data["space_id"]
#             status_filter = form.cleaned_data["status_filter"]
#             exclude_status = form.cleaned_data["exclude_status"]
#             pending_filter = form.cleaned_data["pending_filter"]
#             months = form.cleaned_data["months"]

#             # Generate all 4 reports
#             activity_report = be_activity_report(be_name, status_filter, exclude_status, pending_filter, months)
#             detailed_report = be_activity_report_detailed(be_name, status_filter, exclude_status, pending_filter, months)
#             initiative_report = combined_be_initiative_report(be_name, months)
#             combined_report = combined_be_report(be_name, months)

#             # Collect all non-empty reports
#             reports_to_send = {
#                 "Activity Report": activity_report,
#                 "Detailed Activity Report": detailed_report,
#                 "Initiative Report": initiative_report,
#                 "Metric Detail Report": combined_report,
#             }
#             reports_to_send = {name: report for name, report in reports_to_send.items() if report}

#             if reports_to_send:
#                 for report_name, report_text in reports_to_send.items():
#                     send_to_webex(space_id, f"**{report_name} for {be_name}**\n{report_text}")

#                 messages.success(request, "All reports sent successfully to Webex!")
#             else:
#                 messages.warning(request, "No data found for the selected filters.")

#             return redirect("messaging:be_activity_report")

#     else:
#         form = BEActivityReportForm()
#         form.fields["space_id"].choices = space_choices  # Set choices dynamically

#     return render(request, "messaging/be_activity_report.html", {"form": form, "existing_spaces": existing_spaces})

@user_passes_test(superuser_required)
def be_activity_report_view(request):
    # Retrieve Webex spaces from MongoDB
    collection = db["webex_spaces"]
    existing_spaces = list(collection.find({}, {"_id": 0, "space_name": 1, "space_id": 1}))
    space_choices = [(space["space_id"], space["space_name"]) for space in existing_spaces]

    if request.method == "POST":
        form = BEActivityReportForm(request.POST)
        form.fields["space_id"].choices = space_choices  # Set choices dynamically

        if form.is_valid():
            be_name = form.cleaned_data["be_name"]
            space_id = form.cleaned_data["space_id"]
            status_filter = form.cleaned_data["status_filter"]
            exclude_status = form.cleaned_data["exclude_status"]
            pending_filter = form.cleaned_data["pending_filter"]
            months = form.cleaned_data["months"]

            # Check which reports to generate based on user selection
            reports_to_send = {}

            if form.cleaned_data["send_activity_report"]:
                activity_report = be_activity_report(be_name, status_filter, exclude_status, pending_filter, months)
                if activity_report:
                    reports_to_send["Activity Report"] = activity_report

            if form.cleaned_data["send_detailed_report"]:
                detailed_report = be_activity_report_detailed(be_name, status_filter, exclude_status, pending_filter, months)
                if detailed_report:
                    reports_to_send["Detailed Activity Report"] = detailed_report

            if form.cleaned_data["send_initiative_report"]:
                initiative_report = combined_be_initiative_report(be_name, months)
                if initiative_report:
                    reports_to_send["Initiative Report"] = initiative_report

            if form.cleaned_data["send_combined_report"]:
                combined_report = combined_be_report(be_name, months)
                if combined_report:
                    reports_to_send["Combined Report"] = combined_report

            # Send only the selected and non-empty reports
            if reports_to_send:
                for report_name, report_text in reports_to_send.items():
                    #send_to_webex(space_id, f"**{report_name} for {be_name}**\n{report_text}")
                    send_to_webex(space_id, f"{report_text}")

                messages.success(request, "Selected reports sent successfully to Webex!")
            else:
                messages.warning(request, "No data found for the selected reports.")

            return redirect("messaging:be_activity_report")

    else:
        form = BEActivityReportForm()
        form.fields["space_id"].choices = space_choices  # Set choices dynamically

    return render(request, "messaging/be_activity_report.html", {"form": form, "existing_spaces": existing_spaces})
