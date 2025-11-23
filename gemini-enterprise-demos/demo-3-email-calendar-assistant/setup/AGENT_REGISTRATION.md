# Agent Registration for Gemini Enterprise Plus

This document contains the correct agent URLs for registering your 4 deployed ADK agents in Gemini Enterprise Plus.

## Important: Use Full URL Format

Gemini Enterprise Plus requires agents to be registered using the **full REST API URL format**, not the short resource path format.

### Correct Format ✅
```
https://us-central1-aiplatform.googleapis.com/v1/projects/805114253837/locations/us-central1/reasoningEngines/AGENT_ID
```

### Incorrect Format ❌
```
projects/805114253837/locations/us-central1/reasoningEngines/AGENT_ID
```

---

## Agent URLs for Registration

Copy and paste these URLs when registering agents in Gemini Enterprise Plus:

### 1. Email Management Agent
**Resource ID:** `6553102495684493312`

**Full URL:**
```
https://us-central1-aiplatform.googleapis.com/v1/projects/805114253837/locations/us-central1/reasoningEngines/6553102495684493312
```

**Description:** AI-powered email management assistant that helps users efficiently manage their inbox through intelligent email summarization, automated prioritization, smart response drafting, and context-aware categorization.

**Suggested Test Queries:**
- "Summarize my emails from today"
- "Show me urgent emails"
- "Search for emails from the CEO"

---

### 2. Calendar Management Agent
**Resource ID:** `8840086681458573312`

**Full URL:**
```
https://us-central1-aiplatform.googleapis.com/v1/projects/805114253837/locations/us-central1/reasoningEngines/8840086681458573312
```

**Description:** Intelligent calendar assistant that helps manage schedules, find meeting times, analyze workload, and optimize time allocation.

**Suggested Test Queries:**
- "What's on my calendar today?"
- "Find time for a 30-minute meeting this week"
- "Show me my busiest days this week"

---

### 3. Meeting Preparation Agent
**Resource ID:** `2472841233286823936`

**Full URL:**
```
https://us-central1-aiplatform.googleapis.com/v1/projects/805114253837/locations/us-central1/reasoningEngines/2472841233286823936
```

**Description:** Meeting preparation assistant that gathers context from emails, calendar, and documents to help prepare for upcoming meetings.

**Suggested Test Queries:**
- "Help me prepare for my next meeting"
- "What do I need to know for the Q1 planning meeting?"
- "Summarize background for my 2pm meeting"

---

### 4. Follow-up & Task Management Agent
**Resource ID:** `3123611379441860608`

**Full URL:**
```
https://us-central1-aiplatform.googleapis.com/v1/projects/805114253837/locations/us-central1/reasoningEngines/3123611379441860608
```

**Description:** Task and follow-up assistant that tracks action items from emails and meetings, manages follow-ups, and ensures nothing falls through the cracks.

**Suggested Test Queries:**
- "What tasks do I need to follow up on?"
- "Show me pending action items"
- "Track follow-ups from this week's meetings"

---

## Registration Steps

### Option 1: Gemini Enterprise Plus UI

1. Go to Gemini Enterprise Plus console
2. Navigate to **Agent Registration** or **Extensions**
3. Click **Add Agent** or **Register New Agent**
4. For each agent:
   - **Name:** Use the agent name (e.g., "Email Management Agent")
   - **Description:** Copy from above
   - **Agent URL/Endpoint:** Paste the full URL from above
   - **Type:** Select "Vertex AI Agent Engine" or "ADK Agent"
5. Save and test each agent

### Option 2: API Registration (if available)

If Gemini Enterprise Plus supports API-based registration, use the REST API with the full URLs above.

---

## Troubleshooting

### If agents still show errors after re-registration:

1. **Verify URL format:** Ensure you're using the full `https://...` URL, not the short path
2. **Check permissions:** Ensure the Gemini Enterprise service account has access to your Agent Engine resources
3. **Session configuration:** Some agents may require session backend (Firestore) to be configured
4. **Test directly:** Verify agents work in Vertex AI Agent Engine console before registering in Gemini Enterprise Plus

### Testing Individual Agents

You can test agents directly in the Vertex AI console:
- Console URL: https://console.cloud.google.com/vertex-ai/agent-engine?project=ai-testing-458318
- Each agent should show as "DEPLOYED" status
- You can test queries directly from the console

---

## Project Information

- **Project ID:** `ai-testing-458318`
- **Project Number:** `805114253837`
- **Location:** `us-central1`
- **Discovery Engine Datastores:**
  - Gmail: `demo-gmail-datastore_1763851937069_google_mail`
  - Calendar: `demo-calendar-datastore_1763851980966_google_calendar`
  - Drive: `demo-drive-datastore_1763851832394_google_drive`

---

## Next Steps After Registration

1. Test each agent individually with simple queries
2. Test multi-agent scenarios (e.g., "Prepare me for today" should use multiple agents)
3. Verify Discovery Engine data is accessible
4. Create demo script for presentation

---

## Support

If you continue to experience issues after re-registration:
1. Check agent logs in Cloud Console
2. Verify Discovery Engine datastores have data
3. Test agents directly in Vertex AI Agent Engine console
4. Check service account permissions for both Agent Engine and Discovery Engine
