from webexteamssdk import WebexTeamsAPI
from django.conf import settings
import os
from dotenv import load_dotenv
from SEreview.conn import get_mongodb_connection  # Correct import for another app
from datetime import datetime,timedelta
import requests




client = get_mongodb_connection()
db = client["CDASH"]

# Try to get the Webex Access Token
WEBEX_ACCESS_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")

# If not found, load .env.webex (one level up from the current file)
if not WEBEX_ACCESS_TOKEN:
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "env.webex"))
    WEBEX_ACCESS_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")  # Retry fetching the variable

# Manually set it here for testing
if not WEBEX_ACCESS_TOKEN:
    WEBEX_ACCESS_TOKEN = "ZDA2OGIyMTktODc4Mi00NGEyLWFkZDYtNjYwOGYwY2VmZTA5ZmE5YzViOWUtOGM0_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"  # Replace with your manual test value



api = WebexTeamsAPI(access_token=WEBEX_ACCESS_TOKEN)

def send_message_to_user(email, message):
    """Sends a message to a Webex user via email."""
    api.messages.create(toPersonEmail=email, text=message)

def send_message_to_space(space_id, message):
    """Sends a message to a Webex space (room)."""
    api.messages.create(roomId=space_id, text=message)


def send_message(email=None, space_id=None, message=""):
    """Sends a plain text message to a Webex user or space."""
    if email:
        return api.messages.create(toPersonEmail=email, text=message)
    elif space_id:
        return api.messages.create(roomId=space_id, text=message)


def send_table_message(query_results=None, df=None, recipient_email=None, space_id=None):
    """Sends a table-based message (MongoDB results or Pandas DataFrame)."""
    if df is not None:
        table_data = df.to_markdown(index=False)
    elif query_results:
        table_data = "| " + " | ".join(query_results[0].keys()) + " |\n"
        table_data += "| " + " | ".join(["---"] * len(query_results[0])) + " |\n"
        for row in query_results:
            table_data += "| " + " | ".join(str(value) for value in row.values()) + " |\n"
    else:
        return "No data provided."

    return send_markdown_message(markdown_text=table_data, recipient_email=recipient_email, space_id=space_id)


def send_markdown_message(markdown_text, recipient_email=None, space_id=None):
    """Sends a markdown-formatted message to a Webex user or space."""
    if recipient_email:
        return api.messages.create(toPersonEmail=recipient_email, markdown=markdown_text)
    elif space_id:
        return api.messages.create(roomId=space_id, markdown=markdown_text)

## very bad formatting 
def send_adaptive_card(query_results, recipient_email=None, space_id=None):
    """Sends an adaptive card message (structured JSON format)."""
    
    # Prepare a list of rows for the adaptive card (ensure the structure is correct)
    card_rows = []
    for result in query_results:
        # Dynamically build columns based on the result's data
        card_rows.append(
            {"type": "ColumnSet", "columns": [
                {"type": "Column", "items": [{"type": "TextBlock", "text": f"Activity Name: {result['activity_name']}", "wrap": True}]},
                {"type": "Column", "items": [{"type": "TextBlock", "text": f"Client: {result['client_name']}", "wrap": True}]},
                {"type": "Column", "items": [{"type": "TextBlock", "text": f"Status: {result['status']}", "wrap": True}]},
                {"type": "Column", "items": [{"type": "TextBlock", "text": f"Pending: {result['pending']}", "wrap": True}]},
                {"type": "Column", "items": [{"type": "TextBlock", "text": f"Created: {result['created']}", "wrap": True}]},
                {"type": "Column", "items": [{"type": "TextBlock", "text": f"Last Updated: {result['last_updated']}", "wrap": True}]}
            ]}
        )

    card_content = {
        "type": "AdaptiveCard",
        "version": "1.0",  # Use version 1.0 for better compatibility
        "body": [
            {"type": "TextBlock", "text": "Report Data", "weight": "Bolder", "size": "Medium"},
            {"type": "TextBlock", "text": "Here is the detailed report based on your query:", "wrap": True},
            *card_rows  # Add each dynamically created row to the body
        ]
    }

    # Send the message with both the adaptive card and a brief text message
    return api.messages.create(
        toPersonEmail=recipient_email,
        roomId=space_id,
        markdown="Please find the detailed report below.",  # Optional Markdown text
        attachments=[{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card_content
        }]
    )






# Webex sending function
def send_to_webex(space_id, message):
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {WEBEX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"roomId": space_id, "markdown": message}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print(f"Message successfully sent to Webex space {space_id}")
            return True
        else:
            print(f"Failed to send message to Webex. Status code: {response.status_code}, Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending message to Webex: {e}")
        return False




BE Activity Report Generation
def generate_beactivity_report(be_name, status_filter, exclude_status, pending_filter, months):
    collection = db["beactivity"]
    query = {"be_name": be_name}

    if status_filter:
        query["status"] = {"$in": status_filter}

    if exclude_status:
        query["status"] = {"$nin": exclude_status}

    if pending_filter:
        query["pending"] = {"$in": pending_filter}

    if months:
        start_date = datetime.utcnow() - timedelta(days=30 * months)
        query["desc_update.timestamp"] = {"$gte": start_date}

    activities = list(collection.find(query))  # Convert the cursor to a list
    print("Activities found:", activities)  # Print fetched activities

    if not activities:  # Check if the list is empty or None
        return None

    # Build the formatted report
    report_lines = [f"**BE Activity Report for {be_name}**\n"]
    for activity in activities:
        # Get the create_date from the activity, assuming it's in the 'create_date' field
        create_date = activity.get("create_date", "N/A")
        if create_date != "N/A":
            create_date = create_date.strftime("%Y-%m-%d")  # Format the date as YYYY-MM-DD

        # Get the most recent 'desc_update.timestamp' for last_update
        last_update = "N/A"
        if activity.get("desc_update"):
            timestamps = [entry['timestamp'] for entry in activity['desc_update']]
            if timestamps:
                last_update = max(timestamps).strftime("%Y-%m-%d")  # Format the date as YYYY-MM-DD

        report_lines.append(
            f"- **{activity['activity_name']}** (Client: {activity['client_name']}, Status: {activity['status']}, Pending: {activity['pending']}, Created: {create_date}, Last Updated: {last_update})"
        )

    return "\n".join(report_lines)




# # BE Activity Report Generation
def generate_beactivity_reportd(be_name, status_filter, exclude_status, pending_filter, months):
    collection = db["beactivity"]
    query = {"be_name": be_name}

    if status_filter:
        query["status"] = {"$in": status_filter}

    if exclude_status:
        query["status"] = {"$nin": exclude_status}

    if pending_filter:
        query["pending"] = {"$in": pending_filter}

    if months:
        start_date = datetime.utcnow() - timedelta(days=30 * months)
        query["desc_update.timestamp"] = {"$gte": start_date}

    activities = list(collection.find(query))  # Convert cursor to list
    print("Activities found:", activities)  # Debugging log

    if not activities:  # Check if empty
        return f"🚀 **BE Activity Report for {be_name}**\n\n_No activities found._"

    # Start report formatting
    report_lines = [f"🚀 **BE Activity Report for {be_name}**\n"]

    for activity in activities:
        # Handle missing data with default values
        activity_name = activity.get("activity_name", "Unknown")
        client_name = activity.get("client_name", "N/A")
        status = activity.get("status", "N/A")
        pending = activity.get("pending", "N/A")

        # Format dates properly
        create_date = activity.get("create_date")
        create_date = create_date.strftime("%Y-%m-%d") if create_date else "N/A"

        last_update = "N/A"
        if activity.get("desc_update"):
            timestamps = [entry['timestamp'] for entry in activity['desc_update']]
            if timestamps:
                last_update = max(timestamps).strftime("%Y-%m-%d")

        # Append formatted activity details
        report_lines.append(
                f"### 🏢 **{client_name}**\n"  # Makes the client name bigger and bold  
                f"🔹 **{activity_name}**\n"
                f"   - 📌 **Status:** {status}\n"
                f"   - ⏳ **Pending:** {pending}\n"
                f"   - 🗓 **Created:** {create_date}\n"
                f"   - 🔄 **Last Updated:** {last_update}\n"
        )

    return "\n".join(report_lines)

