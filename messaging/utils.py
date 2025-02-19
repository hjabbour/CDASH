from webexteamssdk import WebexTeamsAPI
from django.conf import settings
import os
from dotenv import load_dotenv
from SEreview.conn import get_mongodb_connection  # Correct import for another app
from datetime import datetime,timedelta
import requests
from collections import Counter
from django.contrib.auth.models import User
from datetime import datetime, timedelta

WEBEX_MAX_LENGTH = 7400  # Webex's message length limit before encryption
WEBEX_TABLE_ROWS = 40  # Limit table chunks to 40 rows





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
# def send_to_webex(space_id, message):
#     url = "https://webexapis.com/v1/messages"
#     headers = {
#         "Authorization": f"Bearer {WEBEX_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }
#     data = {"roomId": space_id, "markdown": message}
    
#     try:
#         response = requests.post(url, json=data, headers=headers)
#         if response.status_code == 200:
#             print(f"Message successfully sent to Webex space {space_id}")
#             return True
#         else:
#             print(f"Failed to send message to Webex. Status code: {response.status_code}, Error: {response.text}")
#             return False
#     except Exception as e:
#         print(f"Error sending message to Webex: {e}")
#         return False


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

# send to webex with chunks 
def send_to_webex(space_id, message):
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {WEBEX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Split long messages into chunks
    for i in range(0, len(message), WEBEX_MAX_LENGTH):
        chunk = message[i : i + WEBEX_MAX_LENGTH]
        data = {"roomId": space_id, "markdown": chunk}
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                print(f"Chunk sent successfully to Webex space {space_id}")
            else:
                print(f"Failed to send chunk. Status code: {response.status_code}, Error: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending message to Webex: {e}")
            return False

# Send formatted table data to Webex, chunking while keeping headers
def send_to_webex_tables(space_id, table_lines):
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {WEBEX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    header, separator, *rows = table_lines

    for i in range(0, len(rows), WEBEX_TABLE_ROWS):
        chunk = [header, separator] + rows[i : i + WEBEX_TABLE_ROWS]
        message = "```\n" + "\n".join(chunk) + "\n```"

        try:
            response = requests.post(url, json={"roomId": space_id, "markdown": message}, headers=headers)
            if response.status_code == 200:
                print(f"Table chunk sent successfully to Webex space {space_id}")
            else:
                print(f"Failed to send table chunk. Status code: {response.status_code}, Error: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending table chunk to Webex: {e}")
            return False






def be_activity_report(be_name, status_filter=None, exclude_status=None, pending_filter=None, months=None):
    # Query the MongoDB collection for activities related to the Business Entity
    collection = db["beactivity"]
    query = {"be_name": be_name}

    # Apply optional filters to the query
    if status_filter:
        query["status"] = {"$in": status_filter}
    if exclude_status:
        query["status"] = {"$nin": exclude_status}
    if pending_filter:
        query["pending"] = {"$in": pending_filter}
    if months:
        query["desc_update.timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

    # Fetch the activities from the collection
    activities = list(collection.find(query))

    # If no activities found, return a message
    if not activities:
        return "No data available."

    # Define column headers for the Markdown table
    headers = ["Activity", "Client", "Status", "Pending", "Created On", "Last Updated"]

    # Prepare data rows for the table
    rows = []
    for activity in activities:
        # Format create_date and last_update
        create_date = activity.get("create_date", "N/A")
        create_date = create_date.strftime("%Y-%m-%d") if isinstance(create_date, datetime) else create_date

        last_update = max((entry.get('timestamp', "N/A") for entry in activity.get("desc_update", [])), default="N/A")
        last_update = last_update.strftime("%Y-%m-%d") if isinstance(last_update, datetime) else last_update

        # Check if last_update is older than a month and highlight it
        last_update_date = datetime.strptime(last_update, "%Y-%m-%d") if last_update != "N/A" else None
        if last_update_date and (datetime.utcnow() - last_update_date > timedelta(days=45)):
            last_update = f"{last_update}(!)"

        # Prepare row data
        row = [
            activity.get("activity_name", "Unknown"),
            activity.get("client_name", "N/A"),
            activity.get("status", "N/A"),
            activity.get("pending", "N/A"),
            create_date,
            last_update
        ]
        rows.append(row)

    # Dynamically calculate column widths based on the maximum length of data in each column
    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

    # Function to format each row with the appropriate column width
    def format_row(row):
        return " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers)))

    # Generate the Markdown table
    report_lines = []
    report_lines.append(format_row(headers))  # Add headers
    report_lines.append("-+-".join("-" * w for w in col_widths))  # Separator line
    report_lines.extend(format_row(row) for row in rows)  # Add the rows

    # Return the formatted report within a code block
    return "```\n" + "\n".join(report_lines) + "\n```"

# def be_activity_report(be_name, status_filter=None, exclude_status=None, pending_filter=None, months=None):
#     collection = db["beactivity"]
#     query = {"be_name": be_name}

#     if status_filter:
#         query["status"] = {"$in": status_filter}
#     if exclude_status:
#         query["status"] = {"$nin": exclude_status}
#     if pending_filter:
#         query["pending"] = {"$in": pending_filter}
#     if months:
#         query["desc_update.timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

#     activities = list(collection.find(query))

#     if not activities:
#         return "No data available."

#     headers = ["Activity", "Client", "Status", "Pending", "Created On", "Last Updated"]
#     rows = []

#     for activity in activities[:20]:  # Limit to 20 rows to prevent overflow
#         create_date = activity.get("create_date", "N/A")
#         create_date = create_date.strftime("%Y-%m-%d") if isinstance(create_date, datetime) else create_date

#         last_update = max((entry.get('timestamp', "N/A") for entry in activity.get("desc_update", [])), default="N/A")
#         last_update = last_update.strftime("%Y-%m-%d") if isinstance(last_update, datetime) else last_update

#         last_update_date = datetime.strptime(last_update, "%Y-%m-%d") if last_update != "N/A" else None
#         if last_update_date and (datetime.utcnow() - last_update_date > timedelta(days=45)):
#             last_update = f"{last_update}(!)"

#         row = [
#             activity.get("activity_name", "Unknown"),
#             activity.get("client_name", "N/A"),
#             activity.get("status", "N/A"),
#             activity.get("pending", "N/A"),
#             create_date,
#             last_update
#         ]
#         rows.append(row)

#     col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

#     def format_row(row):
#         return "| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))) + " |"

#     report_lines = []
#     report_lines.append(format_row(headers))
#     report_lines.append("|" + "|".join("-" * (col_widths[i] + 2) for i in range(len(headers))) + "|")
#     report_lines.extend(format_row(row) for row in rows)

#     markdown_report = "```\n" + "\n".join(report_lines) + "\n```"

#     return markdown_report







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
