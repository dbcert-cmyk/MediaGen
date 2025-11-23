# Mock Demo Data Setup

This directory contains scripts to populate your Gmail, Calendar, and Drive with realistic demo data for testing the Email & Calendar Assistant agents.

## 📋 What Gets Created

### Gmail (10 emails)
- **Urgent emails**: Budget review, API integration
- **Meeting invites**: Product roadmap planning
- **Team communications**: Sprint planning, quick questions
- **Notifications**: HR reminders, security alerts
- **Customer feedback**: Enterprise demo responses

### Calendar (10 events - adjusted to current week)
- **Daily standup** (recurring)
- **Client demos**
- **1:1 meetings**
- **Sprint planning**
- **Product roadmap planning**
- **Focus time blocks**

### Drive (10 documents)
- **Product Planning**: Q1 Roadmap Draft
- **Vendor Documents**: API Integration Proposal
- **Customer Feedback**: Demo feedback reports
- **Finance**: Infrastructure cost analysis
- **Team Docs**: Meeting notes, sprint retrospectives
- **Sales Materials**: Demo scripts
- **Engineering Docs**: Tech stack architecture

## 🚀 Quick Start

### Prerequisites

1. **Enable APIs:**
```bash
gcloud services enable gmail.googleapis.com
gcloud services enable calendar-json.googleapis.com
gcloud services enable drive.googleapis.com
```

2. **Authenticate:**
```bash
gcloud auth application-default login
```

3. **Grant permissions** when prompted:
   - Gmail: Read, compose, modify
   - Calendar: Manage calendars
   - Drive: Create and edit files

### Option 1: Populate All Data at Once (Recommended)

```bash
cd /home/user/dxb/gemini-enterprise-demos/demo-3-email-calendar-assistant/mock-data
python populate_all.py
```

This runs all three scripts sequentially.

### Option 2: Populate Individual Sources

```bash
# Gmail only
python populate_gmail.py

# Calendar only
python populate_calendar.py

# Drive only
python populate_drive.py
```

## 📊 What Happens After Population

### 1. Data is Created
- **Gmail**: 10 emails appear in your inbox
- **Calendar**: 10 events appear in current week (preserving original times)
- **Drive**: 10 documents in "Demo Data" folder

### 2. Discovery Engine Syncs (1-2 hours)
Your Discovery Engine datastores will automatically sync this data:
- `demo-gmail-datastore`
- `demo-calendar-datastore`
- `demo-drive-datastore`

### 3. Check Sync Status
```bash
cd ../setup/adk-agents
python check_datastores.py
```

### 4. Test Your Agents
Once synced, test queries in Gemini Enterprise Plus:

**Email Agent:**
```
"What urgent emails do I have?"
"Show me emails about the API integration"
```

**Calendar Agent:**
```
"What's on my calendar today?"
"When is my next meeting with Sarah?"
"Do I have any conflicts this week?"
```

**Meeting Prep Agent:**
```
"Prepare me for the Product Roadmap Planning meeting"
"What documents are related to my client demo?"
```

**Multi-Agent (Daily Briefing):**
```
"Give me my daily briefing"
"What meetings and urgent emails do I have today?"
```

## 🛠️ Customization

### Modify Email Content
Edit `gmail_mock_data.json` to change:
- Sender/recipient
- Subject lines
- Email body
- Labels
- Urgency markers

### Modify Calendar Events
Edit `calendar_mock_data.json` to change:
- Event titles
- Attendees
- Descriptions
- Recurring patterns
- Event types

### Modify Drive Documents
Edit `drive_mock_data.json` to change:
- Document names
- Content
- Folder organization
- File types
- Sharing settings

After editing, just re-run the population scripts.

## 🧹 Cleanup (Optional)

### Clear Gmail
```python
# Manual: Delete emails from inbox
# Or use Gmail UI bulk delete
```

### Clear Calendar
```python
# Manual: Delete events from calendar
# The scripts don't include auto-delete to prevent accidents
```

### Clear Drive
```python
# Manual: Delete "Demo Data" folder
# Or keep it for future demos
```

## ⚠️ Important Notes

1. **Data Overwrites**: Running scripts multiple times creates duplicate data (doesn't replace)

2. **Sync Time**: Discovery Engine takes 1-2 hours to index new data

3. **Email Dates**: Gmail emails use recent dates from JSON (some may appear as "older")

4. **Calendar Dates**: Events are automatically adjusted to current week while preserving day-of-week and times

5. **Drive Folder**: All documents go into a "Demo Data" root folder for easy organization

## 🔍 Troubleshooting

### "Authentication failed"
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project ai-testing-458318
```

### "API not enabled"
```bash
gcloud services enable gmail.googleapis.com calendar-json.googleapis.com drive.googleapis.com --project=ai-testing-458318
```

### "Permission denied"
Make sure you granted all permissions during `gcloud auth` flow

### "No data showing in agents"
- Wait 1-2 hours for Discovery Engine sync
- Check datastore status with `check_datastores.py`
- Verify datastores are connected to correct Gmail/Calendar/Drive accounts

## 📚 Related Files

- `gmail_mock_data.json` - Email data definitions
- `calendar_mock_data.json` - Calendar event definitions
- `drive_mock_data.json` - Drive document definitions
- `firestore_schema.py` - User preferences and patterns (already loaded)
- `populate_gmail.py` - Gmail population script
- `populate_calendar.py` - Calendar population script
- `populate_drive.py` - Drive population script
- `populate_all.py` - Master script (runs all three)

## 🎯 Demo Tips

1. **Run population the day before your demo** - Ensures Discovery Engine sync is complete

2. **Test queries beforehand** - Verify all agents return expected results

3. **Keep JSON files updated** - Adjust mock data to match your demo narrative

4. **Use realistic names/companies** - Makes demo more relatable to audience

5. **Highlight multi-agent queries** - "Daily briefing" showcases orchestration power

---

**Ready to populate your demo data?**

```bash
python populate_all.py
```

Then wait 1-2 hours and test your agents! 🚀
