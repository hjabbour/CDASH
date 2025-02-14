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


db["beactivity"].create_index([("desc_update.timestamp", 1)])



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


# Fiscal quarter calculation
def get_fiscal_quarter(date):
    month, year = date.month, date.year
    if month in [8, 9, 10]:
        return f"FY{year+1} Q1"
    if month in [11, 12, 1]:
        return f"FY{year+1} Q2"
    if month in [2, 3, 4]:
        return f"FY{year+1} Q3"
    return f"FY{year+1} Q4"


# BE Activity Report (Basic)
def be_activity_report(be_name, status_filter=None, exclude_status=None, pending_filter=None, months=None):
    collection = db["beactivity"]
    query = {"be_name": be_name}

    if status_filter:
        query["status"] = {"$in": status_filter}
    if exclude_status:
        query["status"] = {"$nin": exclude_status}
    if pending_filter:
        query["pending"] = {"$in": pending_filter}
    if months:
        query["desc_update.timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

    activities = list(collection.find(query))
    if not activities:
        return None

    report_lines = [f"**BE Activity Report for {be_name}**\n"]
    for activity in activities:
        create_date = activity.get("create_date", "N/A")
        last_update = max((entry.get('timestamp', "N/A") for entry in activity.get("desc_update", [])), default="N/A")

        report_lines.append(
            f"- **{activity.get('activity_name', 'Unknown')}** (Client: {activity.get('client_name', 'N/A')}, "
            f"Status: {activity.get('status', 'N/A')}, Pending: {activity.get('pending', 'N/A')}, "
            f"Created: {create_date}, Last Updated: {last_update})"
        )

    return "\n".join(report_lines)


# BE Activity Report (Detailed & Styled)
def be_activity_report_detailed(be_name, status_filter=None, exclude_status=None, pending_filter=None, months=None):
    collection = db["beactivity"]
    query = {"be_name": be_name}

    if status_filter:
        query["status"] = {"$in": status_filter}
    if exclude_status:
        query["status"] = {"$nin": exclude_status}
    if pending_filter:
        query["pending"] = {"$in": pending_filter}
    if months:
        query["desc_update.timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

    activities = list(collection.find(query))
    if not activities:
        return f"🚀 **BE Activity Report for {be_name}**\n\n_No activities found._"

    report_lines = [f"🚀 **BE Activity Report for {be_name}**\n"]
    for activity in activities:
        activity_name = activity.get("activity_name", "Unknown")
        client_name = activity.get("client_name", "N/A")
        status = activity.get("status", "N/A")
        pending = activity.get("pending", "N/A")
        create_date = activity.get("create_date", "N/A")
        last_update = max((entry.get('timestamp', "N/A") for entry in activity.get("desc_update", [])), default="N/A")

        report_lines.append(
            f"### 🏢 **{client_name}**\n"
            f"🔹 **{activity_name}**\n"
            f"   - 📌 **Status:** {status}\n"
            f"   - ⏳ **Pending:** {pending}\n"
            f"   - 🗓 **Created:** {create_date}\n"
            f"   - 🔄 **Last Updated:** {last_update}\n"
        )

    return "\n".join(report_lines)


# BE Metrics Report


from collections import Counter
from django.contrib.auth.models import User
from datetime import datetime, timedelta

def be_metrics_report(be_name, months=None):
    collection = db["beactivity"]
    query = {"be_name": be_name}
    if months:
        query["desc_update.timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

    activities = list(collection.find(query))
    if not activities:
        return None

    # Adjust active count to consider only valid statuses: 'Planned', 'Initial', 'Followup', 'Funnel'
    valid_statuses = ['Planned', 'Initial', 'Followup', 'Funnel']
    active = sum(1 for a in activities if a.get('status') in valid_statuses)

    # Refine stalled count: ensure that we check activities that are neither 'Completed' nor 'Cancelled'
    stalled = sum(1 for a in activities if a.get('status') not in ['Completed', 'Cancelled'] and 
                  (datetime.utcnow() - max((entry.get('timestamp', datetime.utcnow()) 
                  for entry in a.get('desc_update', [])), default=datetime.utcnow())).days > 14)
    
    completed = sum(1 for a in activities if a.get('status') == 'Completed')

    # Completion times for activities (ignore activities with 0 days completion)
    completion_times = []
    for a in activities:
        if a.get('status') == 'Completed':
            create_date = a.get('create_date')
            if isinstance(create_date, datetime):
                print(f"Create Date: {create_date}")
            else:
                # Explicitly parse if not a datetime
                create_date = datetime.strptime(str(create_date), '%Y-%m-%dT%H:%M:%S.%fZ')
                print(f"Parsed Create Date: {create_date}")
            
            # Get the latest desc_update.timestamp (most recent update)
            last_update = max(
                (entry.get('timestamp') for entry in a.get('desc_update', [])),
                default=None
            )

            if last_update:
                # Ensure last_update is a datetime object
                if isinstance(last_update, datetime):
                    print(f"Last Update: {last_update}")
                else:
                    # Explicitly parse the timestamp if it's not a datetime object
                    last_update = datetime.strptime(str(last_update), '%Y-%m-%dT%H:%M:%S.%fZ')
                    print(f"Parsed Last Update: {last_update}")

                # Calculate the difference between create_date and last_update
                if last_update > create_date:  # Only consider if last_update is after create_date
                    completion_time = (last_update - create_date).days
                    print(f"Completion Time: {completion_time} days")
                    if completion_time > 0:  # Exclude completion time of 0
                        completion_times.append(completion_time)

    # Calculate average completion time, excluding 0 days
    avg_completion = sum(completion_times) / len(completion_times) if completion_times else 0

    # Status breakdown (include all statuses)
    status_counts = {}
    for activity in activities:
        status = activity.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    # Track users involved in activities and updates
    user_activity_counts = Counter()
    user_update_counts = Counter()

    for activity in activities:
        user_id = activity.get('user_id')
        if user_id:
            user_activity_counts[user_id] += 1
        for update in activity.get('desc_update', []):
            user_id = update.get('user_id')
            if user_id:
                user_update_counts[user_id] += 1

    # Fetch user names instead of user IDs
    top_activity_user = user_activity_counts.most_common(1)
    top_update_user = user_update_counts.most_common(1)

    top_activity_user_name = User.objects.get(id=top_activity_user[0][0]).username if top_activity_user else 'N/A'
    top_update_user_name = User.objects.get(id=top_update_user[0][0]).username if top_update_user else 'N/A'

    # Report construction
    report_lines = [f"**BE Metrics Report for {be_name}**\n"]
    report_lines.append(f"Total Activities: {len(activities)}")
    report_lines.append(f"Active: {active}")
    report_lines.append(f"Stalled: {stalled} ⚠️")
    report_lines.append(f"Completed: {completed} 🎉")
    report_lines.append(f"Average Completion Time: {avg_completion:.1f} days\n")

    # Add top users metrics to the report
    report_lines.append(f"📊 **Top User by Activities**")
    report_lines.append(f"• {top_activity_user_name}: {top_activity_user[0][1]} activities" if top_activity_user else "• No activity users found")

    report_lines.append(f"📊 **Top User by Updates**")
    report_lines.append(f"• {top_update_user_name}: {top_update_user[0][1]} updates" if top_update_user else "• No update users found")

    # Add status breakdown to the report
    report_lines.append(f"📊 **Status Breakdown**")
    total = sum(status_counts.values())
    for status, count in status_counts.items():
        report_lines.append(f"• {status}: {count} ({(count/total) * 100:.1f}%)")

    return "\n".join(report_lines)
