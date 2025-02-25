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

# def format_status_with_emoji(status):
#     status = status.lower()
#     if status == "completed": return "✅ Completed"
#     if status == "in progress": return "🔄 In Progress"
#     if status == "blocked": return "🚫 Blocked"
#     if status == "followup": return "⏳ followup"
#     return status

def format_status_with_emoji(status):
    """
    Maps activity status to appropriate emoji indicators
    """
    status_mapping = {
        'planned': '📋 Planned',      # Clipboard for planned activities
        'initial': '🔰 Initial',      # Japanese "beginner" symbol for initial
        'followup': '🔄 Followup',    # Circular arrows for followup (ongoing)
        'funnel': '⏳ Funnel',        # Hourglass for funnel (in process)
        'completed': '✅ Completed',   # Checkmark for completed
    }
    
    # Default fallback for unknown statuses
    if not status:
        return "❓ Unknown"
        
    # Case-insensitive lookup
    return status_mapping.get(status.lower(), status)




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


def send_table_to_webex(space_id, table_data, max_rows_per_chunk=30):
    """
    Sends a markdown table to Webex in chunks, preserving table structure.
    
    Args:
        space_id: Webex space ID to send the message to
        table_data: Complete markdown table as a string
        max_rows_per_chunk: Maximum number of data rows per chunk
    """
    # Parse the table
    lines = table_data.strip().replace("```", "").strip().split("\n")
    if len(lines) < 3:  # Need at least header, separator, and one row
        return send_to_webex(space_id, table_data)
    
    header = lines[0]
    separator = lines[1]
    data_rows = lines[2:]
    
    # Calculate chunks based on rows rather than characters
    chunks = []
    for i in range(0, len(data_rows), max_rows_per_chunk):
        chunk_rows = data_rows[i:i + max_rows_per_chunk]
        # Make sure each chunk has the header row and separator
        chunk_table = f"```\n{header}\n{separator}\n" + "\n".join(chunk_rows) + "\n```"
        chunks.append(chunk_table)
    
    # Add part numbers to each chunk
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        part_info = f"**Table Part {i+1}/{total_chunks}**\n"
        chunks[i] = part_info + chunk
    
    # Send each chunk
    success = True
    for chunk in chunks:
        if len(chunk) > WEBEX_MAX_LENGTH:
            print(f"Warning: A single table chunk exceeds WEBEX_MAX_LENGTH ({len(chunk)} > {WEBEX_MAX_LENGTH})")
            # If this happens, we need to reduce max_rows_per_chunk and try again
            if max_rows_per_chunk > 1:
                print(f"Retrying with smaller chunk size ({max_rows_per_chunk // 2} rows)")
                return send_table_to_webex(space_id, table_data, max_rows_per_chunk // 2)
            else:
                # If we can't reduce further, fall back to character-based chunking
                send_result = send_to_webex(space_id, chunk)
                success = success and send_result
        else:
            send_result = send_to_webex(space_id, chunk)
            success = success and send_result
    
    return success

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
            last_update = f"⚠️ {last_update}"  # Warning emoji for outdated items

        # Apply emoji to status
        status_with_emoji = format_status_with_emoji(activity.get("status", "N/A"))

        # Apply emoji to pending status if needed
        pending = activity.get("pending", "N/A")
        if pending.lower() == "yes":
            pending = "⏱️ Yes"  # Timer for pending items
        
        # Prepare row data
        row = [
            activity.get("activity_name", "Unknown"),
            activity.get("client_name", "N/A"),
            status_with_emoji,
            pending,
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

def format_status_with_emoji(status):
    """Assigns emojis based on status for better readability."""
    status_mapping = {
        "Planned": "📅",
        "Initial": "🚀",
        "Followup": "🔄",
        "Funnel": "📈",
        "Completed": "✅",
        "Cancelled": "❌",
        "Pending": "⏳",
        "Stalled": "⚠️",
        "Active": "🟢"
    }
    return f"{status_mapping.get(status, '🔹')} {status}"



def combined_be_report(be_name, months=None):
    collection = db["beactivity"]
    query = {"be_name": be_name}
    
    if months:
        query["desc_update.timestamp"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

    activities = list(collection.find(query))
    if not activities:
        return "No data available."

    valid_statuses = ['Planned', 'Initial', 'Followup', 'Funnel']  # Valid statuses excluding "Completed"

    # Activity Categorization
    active = sum(1 for a in activities if a.get('status') in valid_statuses and a.get('status') != 'Completed')
    
    # Completed: Count only completed activities, exclude them from active, stalled, and pending
    completed = sum(1 for a in activities if a.get('status') == 'Completed')
    
    # Stalled: Activities that are not 'Completed' or 'Cancelled' and not updated in the last 14 days
    stalled = sum(1 for a in activities if a.get('status') not in ['Completed', 'Cancelled'] and 
                  a.get('desc_update') and 
                  (datetime.utcnow() - max(
                      (entry.get('timestamp', datetime.utcnow()) for entry in a['desc_update']), 
                      default=datetime.utcnow()
                  )).days > 28)

    # Pending: Exclude Completed Activities
    pending = sum(1 for a in activities if a.get('status') != 'Completed' and a.get('pending'))
    
    # Pending Breakdown (by who it is pending with)
    pending_groups = Counter(a.get('pending', 'Unknown') for a in activities if a.get('status') != 'Completed' and a.get('pending'))
    total_pending = sum(pending_groups.values())
    pending_percentage = (total_pending / len(activities)) * 100 if activities else 0
    
    # Average Completion Time: Check the last entry in desc_update array for the completion time
    completion_times = [
        (max((entry.get('timestamp') for entry in a.get('desc_update', [])), default=None) - a.get('create_date')).days
        for a in activities if a.get('status') == 'Completed' and isinstance(a.get('create_date'), datetime)
    ]
    avg_completion = sum(completion_times) / len(completion_times) if completion_times else 0

    # Status Breakdown
    status_counts = Counter(a.get('status', 'Unknown') for a in activities)

    # Outdated Activities: Exclude Completed Activities
    now = datetime.utcnow()
    outdated_1m = sum(1 for a in activities if a.get('status') != 'Completed' and any(
        update.get('timestamp') <= now - timedelta(days=30) for update in a.get('desc_update', [])
    ))
    outdated_2m = sum(1 for a in activities if a.get('status') != 'Completed' and any(
        update.get('timestamp') <= now - timedelta(days=60) for update in a.get('desc_update', [])
    ))
    outdated_3m_plus = sum(1 for a in activities if a.get('status') != 'Completed' and any(
        update.get('timestamp') <= now - timedelta(days=90) for update in a.get('desc_update', [])
    ))

    # # Top Users by Activities & Updates: Check the last entry in desc_update for user_id
    user_activity_counts = Counter(a.get('user_id') for a in activities if a.get('user_id'))
    user_update_counts = Counter(update.get('user_id') for a in activities for update in a.get('desc_update', []) if update.get('user_id'))

    top_activity_user = user_activity_counts.most_common(1)
    top_update_user = user_update_counts.most_common(1)

    top_activity_user_name = User.objects.get(id=top_activity_user[0][0]).username if top_activity_user else 'N/A'
    top_update_user_name = User.objects.get(id=top_update_user[0][0]).username if top_update_user else 'N/A'

    # Report Formatting
    report_lines = [f"📢 **BE Engagement Activity  Metrics Report for {be_name}**"]
    report_lines.append(f"📌 **Total Activities:** {len(activities)}")
    report_lines.append(f"🟢 **Active (Not Completed):** {active}")
    report_lines.append(f"⚠️ **Stalled (Not Updated in 28 Days):** {stalled}")
    report_lines.append(f"✅ **Completed:** {completed}")
    report_lines.append(f"⏳ **Avg Completion Time:** {avg_completion:.1f} days\n")

    # Pending Breakdown Display
    report_lines.append(f"⏳ **Pending Activities:** {total_pending} ({pending_percentage:.1f}%)")
    if pending_groups:  # Display pending activities by assignee/group
        for person, count in pending_groups.items():
            report_lines.append(f"   - Pending with {person}: {count}")
    else:
        report_lines.append("   - No pending activities found.")
    report_lines.append("")

    # Outdated Activities Display
    report_lines.append("📅 **Outdated Activities:**")
    report_lines.append(f"   - 🟡 Not updated for 1+ month: {outdated_1m}")
    report_lines.append(f"   - 🟠 Not updated for 2+ months: {outdated_2m}")
    report_lines.append(f"   - 🔴 Not updated for 3+ months: {outdated_3m_plus}\n")

    # # Top Users Display
    # report_lines.append(f"👥 **Top User by Activities:** {top_activity_user_name} ({top_activity_user[0][1]} activities)" if top_activity_user else "👥 No activity users found")
    # report_lines.append(f"✍️ **Top User by Updates:** {top_update_user_name} ({top_update_user[0][1]} updates)" if top_update_user else "✍️ No update users found")
    # report_lines.append("")

    # Status Breakdown Display
    report_lines.append("📊 **Status Breakdown**")
    total = sum(status_counts.values())
    for status, count in status_counts.items():
        report_lines.append(f"• {format_status_with_emoji(status)}: {count} ({(count/total) * 100:.1f}%)")

    return "\n".join(report_lines)




def combined_be_initiative_report(be_name, months=None):
    collection = db["beinitiative"]
    query = {"be_name": be_name}

    if months:
        query["create_date"] = {"$gte": datetime.utcnow() - timedelta(days=30 * months)}

    initiatives = list(collection.find(query))
    if not initiatives:
        return "No data available."

    valid_statuses = ['Planned', 'Finished', 'Active', 'Delayed']

    # Initiative Categorization
    active = sum(1 for i in initiatives if i.get('status') in ['Planned', 'Active'])
    delayed = sum(1 for i in initiatives if i.get('status') == 'Delayed')
    completed = sum(1 for i in initiatives if i.get('status') == 'Finished')

    # Average Completion Time
    completion_times = [
        (i.get('expected_execution_date') - i.get('create_date')).days
        for i in initiatives if i.get('status') == 'Finished' and isinstance(i.get('expected_execution_date'), datetime)
    ]
    avg_completion = sum(completion_times) / len(completion_times) if completion_times else 0

    # Status Breakdown
    status_counts = Counter(i.get('status', 'Unknown') for i in initiatives)

    # Outdated Initiatives (Not Updated for Periods of Time)
    now = datetime.utcnow()

    outdated_1m = sum(1 for i in initiatives if any(
        isinstance(update, dict) and update.get('timestamp') <= now - timedelta(days=30)
        for update in i.get('desc_update', [])
    ))

    outdated_2m = sum(1 for i in initiatives if any(
        isinstance(update, dict) and update.get('timestamp') <= now - timedelta(days=60)
        for update in i.get('desc_update', [])
    ))

    outdated_3m_plus = sum(1 for i in initiatives if any(
        isinstance(update, dict) and update.get('timestamp') <= now - timedelta(days=90)
        for update in i.get('desc_update', [])
    ))

    # Overdue Initiatives (Based on Expected Execution Date)
    overdue_1m = sum(1 for i in initiatives if i.get('expected_execution_date') and
                     i.get('expected_execution_date') <= now - timedelta(days=30))

    overdue_2m = sum(1 for i in initiatives if i.get('expected_execution_date') and
                     i.get('expected_execution_date') <= now - timedelta(days=60))

    overdue_3m_plus = sum(1 for i in initiatives if i.get('expected_execution_date') and
                          i.get('expected_execution_date') <= now - timedelta(days=90))

    # Top Users by Initiatives
    user_initiative_counts = Counter(i.get('user_id') for i in initiatives if i.get('user_id'))

    top_initiative_user = user_initiative_counts.most_common(1)
    top_initiative_user_name = User.objects.get(id=top_initiative_user[0][0]).username if top_initiative_user else 'N/A'

    # Report Formatting
    report_lines = [f"📢 **BE Initiative Report for {be_name}**"]
    report_lines.append(f"📌 **Total Initiatives:** {len(initiatives)}")
    report_lines.append(f"🟢 **Active (Planned & Active):** {active}")
    report_lines.append(f"⚠️ **Delayed:** {delayed}")
    report_lines.append(f"✅ **Completed:** {completed}")
    report_lines.append(f"⏳ **Avg Completion Time:** {avg_completion:.1f} days\n")

    report_lines.append("📅 **Overdue Initiatives:**")
    report_lines.append(f"   - 🟡 Past due by 1+ month: {overdue_1m}")
    report_lines.append(f"   - 🟠 Past due by 2+ months: {overdue_2m}")
    report_lines.append(f"   - 🔴 Past due by 3+ months: {overdue_3m_plus}\n")

    report_lines.append(f"⏳ **Outdated Initiatives (Not Updated for Periods of Time):**")
    report_lines.append(f"   - 🟡 Past due by 1+ month: {outdated_1m}")
    report_lines.append(f"   - 🟠 Past due by 2+ months: {outdated_2m}")
    report_lines.append(f"   - 🔴 Past due by 3+ months: {outdated_3m_plus}\n")

    report_lines.append(f"👥 **Top User by Initiatives:** {top_initiative_user_name} ({top_initiative_user[0][1]} initiatives)" if top_initiative_user else "👥 No initiative users found")
    report_lines.append("")

    report_lines.append("📊 **Status Breakdown**")
    total = sum(status_counts.values())
    for status, count in status_counts.items():
        report_lines.append(f"• {format_status_with_emoji(status)}: {count} ({(count/total) * 100:.1f}%)")

    return "\n".join(report_lines)
