# 🌍 Multi-Agent Travel Planner

An intelligent travel planning system that demonstrates **multi-agent orchestration** using Anthropic's Claude AI. Specialized agents collaborate to create comprehensive, personalized travel itineraries.

## 🎯 Demo Concept

This project showcases how specialized AI agents can work together to solve complex tasks:

- **🌍 Host/Coordinator Agent**: Orchestrates the entire planning process
- **✈️ Flight Specialist Agent**: Finds and recommends optimal flights
- **🏨 Hotel Specialist Agent**: Searches for accommodations matching your preferences
- **📅 Activity Specialist Agent**: Creates detailed day-by-day itineraries

## ✨ Features

- **Natural Language Input**: Just describe your dream trip in plain English
- **Intelligent Parsing**: AI extracts destinations, dates, budget, and preferences automatically
- **Multi-Agent Collaboration**: Specialized agents work in parallel for comprehensive planning
- **Beautiful UI**: Clean Streamlit interface with real-time progress updates
- **Complete Itineraries**: Get flights, hotels, and day-by-day activities in one plan
- **Export Options**: Download your plan as Markdown or JSON

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API Key ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone or navigate to the travel planner directory:**
   ```bash
   cd travel_planner
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   ```bash
   # Create .env file from example
   cp .env.example .env

   # Edit .env and add your Anthropic API key
   # ANTHROPIC_API_KEY=your-actual-api-key-here
   ```

   Or export directly:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

4. **Run the Streamlit app:**
   ```bash
   cd ui
   streamlit run streamlit_app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 📖 Usage Examples

Try these example requests:

1. **Budget Art Trip:**
   ```
   Plan me a 3-day budget trip to Paris focused on art and museums
   ```

2. **Luxury Food & Culture:**
   ```
   I want a 5-day luxury vacation in Tokyo with great food and culture
   ```

3. **Family Adventure:**
   ```
   Create a 4-day family trip to Orlando with theme parks
   ```

4. **Romantic Getaway:**
   ```
   Plan a romantic 3-day getaway to Santorini with beach and sunset views
   ```

5. **Nature Adventure:**
   ```
   I need a 7-day adventure trip to Iceland with hiking and nature
   ```

## 🏗️ Architecture

### Agent Hierarchy

```
CoordinatorAgent (Host)
    ├── FlightAgent (Specialist)
    ├── HotelAgent (Specialist)
    └── ActivityAgent (Specialist)
```

### Data Flow

1. **User Input** → Coordinator parses natural language request
2. **Parallel Agent Tasks**:
   - Flight Agent searches for flights
   - Hotel Agent searches for accommodations
   - Activity Agent creates itinerary
3. **Coordination** → Coordinator combines all results
4. **Output** → Beautiful markdown travel plan

### Project Structure

```
travel_planner/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class
│   ├── coordinator_agent.py   # Host/orchestrator
│   ├── flight_agent.py        # Flight specialist
│   ├── hotel_agent.py         # Hotel specialist
│   └── activity_agent.py      # Activity/itinerary specialist
├── ui/
│   └── streamlit_app.py       # Streamlit web interface
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 How It Works

### 1. Request Parsing
The Coordinator Agent uses Claude to parse natural language into structured data:
```python
"3-day budget trip to Paris for art"
→ {destination: "Paris", duration: 3, budget: "budget", interests: ["art", "museums"]}
```

### 2. Specialist Agents
Each agent has:
- **Specialized system prompt** defining their role
- **Domain-specific tools** (mock APIs for demo, easily replaced with real APIs)
- **JSON response format** for structured communication

### 3. Agent Communication
Agents communicate via JSON:
```json
{
  "task": {...},
  "results": {...},
  "success": true
}
```

### 4. Final Assembly
The Coordinator combines all agent outputs into a cohesive travel plan.

## 🛠️ Customization

### Adding Real APIs

The current implementation uses mock data for demonstration. To integrate real APIs:

1. **Flights** - Use [Amadeus API](https://developers.amadeus.com/):
   ```python
   # In flight_agent.py
   from amadeus import Client
   amadeus = Client(client_id='...', client_secret='...')
   ```

2. **Hotels** - Use [Booking.com API](https://www.booking.com/affiliate-program) or Amadeus

3. **Activities** - Use [Google Places API](https://developers.google.com/maps/documentation/places/web-service/overview)

### Customizing Agents

Modify agent behavior by editing their `create_system_prompt()` method:

```python
def create_system_prompt(self) -> str:
    return """Your custom instructions here..."""
```

## 💰 Cost Considerations

- Uses Claude 3.5 Sonnet model
- Approximate cost: $0.10-0.30 per complete travel plan
- Costs depend on:
  - Trip complexity (number of days)
  - Number of options requested
  - Detail level in itinerary

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile
- **Example Prompts**: Click to try pre-built examples
- **Real-time Progress**: See which agent is working
- **Multiple Views**: Formatted markdown and raw JSON
- **Export Options**: Download as .md or .json files

## 🚦 API Requirements

### Anthropic API
- **Required**: Yes
- **Cost**: Pay-as-you-go (see [pricing](https://www.anthropic.com/pricing))
- **Free Tier**: No, but very affordable for testing

### Optional APIs (Future)
- Amadeus (Free tier available)
- Google Places (Free tier with limits)
- OpenWeather (Free tier available)

## 🧪 Testing

Run the test script to verify your setup:

```bash
python test_planner.py
```

This will:
1. Test agent initialization
2. Create a sample travel plan
3. Verify JSON structure
4. Display results

## 📝 Example Output

The system generates comprehensive plans including:

✅ **Trip Summary** (destination, dates, budget)
✅ **Total Cost Breakdown** (flights, hotels, activities)
✅ **Recommended Flight** (with alternatives)
✅ **Recommended Hotel** (with alternatives)
✅ **Day-by-Day Itinerary** (with timing, costs, descriptions)
✅ **Local Tips & Packing Suggestions**

## 🎓 Learning Objectives

This demo illustrates:

1. **Agent Orchestration**: How a host agent coordinates specialists
2. **Task Decomposition**: Breaking complex requests into subtasks
3. **Structured Communication**: Agents communicating via JSON
4. **LLM Specialization**: Different prompts for different expertise
5. **Error Handling**: Graceful degradation when agents fail
6. **UI Integration**: Connecting agents to user-friendly interfaces

## 🤝 Contributing

Want to enhance this demo? Consider:

- Adding real API integrations
- Implementing caching for repeated searches
- Adding more specialist agents (car rental, travel insurance)
- Improving error handling and validation
- Adding user authentication and saved plans

## 📄 License

This project is open-source and available for educational purposes.

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/)
- UI powered by [Streamlit](https://streamlit.io/)
- Inspired by multi-agent system architectures

## 📞 Support

For issues or questions:
1. Check the troubleshooting section below
2. Review the example prompts
3. Ensure your API key is correctly set

## 🔍 Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Make sure you've set the environment variable
- Check `.env` file exists and is loaded
- Try exporting directly: `export ANTHROPIC_API_KEY='...'`

### "Agent failed to respond"
- Check your internet connection
- Verify API key is valid
- Check Anthropic API status

### "JSON parsing error"
- This is usually temporary
- The system has fallbacks for invalid JSON
- Try running the request again

---

**Ready to plan your next adventure?** 🌟

```bash
cd ui && streamlit run streamlit_app.py
```
