# 🌍 Multi-Agent Travel Planner - Demo Guide

## Overview

This is a complete implementation of a **multi-agent travel planning system** that demonstrates how specialized AI agents can collaborate to solve complex tasks. Built with Anthropic's Claude AI, this system showcases:

- **Agent Orchestration**: A coordinator agent manages specialist agents
- **Task Decomposition**: Complex travel planning broken into subtasks
- **Parallel Execution**: Agents work simultaneously for efficiency
- **Structured Communication**: JSON-based inter-agent messaging
- **Beautiful UI**: Streamlit interface for user interaction

## 🏗️ System Architecture

### Agent Roles

```
┌─────────────────────────────────────────────────────┐
│         CoordinatorAgent (Host)                     │
│  - Parses user requests                            │
│  - Orchestrates specialist agents                  │
│  - Combines results into final plan                │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│FlightAgent   │ │HotelAgent    │ │ActivityAgent │
│              │ │              │ │              │
│Searches for  │ │Finds hotels  │ │Creates       │
│flights,      │ │near attrac-  │ │detailed      │
│compares      │ │tions, matches│ │itineraries   │
│prices        │ │to budget     │ │with timing   │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Workflow

1. **User Input**: "Plan a 3-day budget trip to Paris focused on art"

2. **Coordinator Parses**:
   ```json
   {
     "destination": "Paris",
     "duration_days": 3,
     "budget": "budget",
     "interests": ["art", "museums"]
   }
   ```

3. **Parallel Agent Execution**:
   - FlightAgent → Searches flights, returns top 3 options
   - HotelAgent → Finds hotels near art museums
   - ActivityAgent → Creates 3-day art-focused itinerary

4. **Result Combination**:
   - Coordinator assembles complete travel plan
   - Calculates total costs
   - Formats as beautiful markdown

5. **User Output**: Complete travel plan with flights, hotel, and day-by-day itinerary

## 🎯 Key Features Demonstrated

### 1. Multi-Agent Collaboration
Each agent has specialized knowledge and tools:
- **Flight Agent**: Mock flight API (easily replaceable with Amadeus, Skyscanner)
- **Hotel Agent**: Mock hotel search (replaceable with Booking.com, Hotels.com)
- **Activity Agent**: Uses Claude's world knowledge to create itineraries

### 2. Natural Language Understanding
Claude parses free-form requests into structured data:
```
"5-day luxury Tokyo trip with amazing food"
→ {destination: "Tokyo", days: 5, budget: "luxury", interests: ["food"]}
```

### 3. Intelligent Recommendations
Each agent uses Claude to:
- Analyze options
- Make recommendations based on context
- Explain choices to users

### 4. Structured Inter-Agent Communication
Agents communicate via JSON:
```json
{
  "task": {
    "destination": "Paris",
    "budget": "budget"
  },
  "results": {
    "recommended_hotel": {...},
    "alternatives": [...]
  }
}
```

## 🚀 Running the Demo

### Option 1: Web UI (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export ANTHROPIC_API_KEY='your-key-here'

# 3. Run Streamlit app
cd ui
streamlit run streamlit_app.py

# 4. Open browser to http://localhost:8501
```

**Try these example requests:**
- "Plan a 3-day budget trip to Paris focused on art"
- "5-day luxury vacation in Tokyo with great food"
- "Family trip to Orlando, 4 days, theme parks"

### Option 2: Command Line Test

```bash
# Run the test script
python test_planner.py
```

This will:
- Verify your API key
- Initialize all agents
- Create a sample travel plan
- Save as JSON and Markdown

### Option 3: Architecture Demo (No API Key)

```bash
# See the system architecture without API calls
python demo.py
```

Shows:
- Agent hierarchy
- Workflow steps
- Sample output structure
- Technology stack

## 📊 Sample Output

### Trip Summary
```markdown
# 🌍 Your Complete Travel Plan

## 📋 Trip Summary
- Destination: Paris, France
- Duration: 3 days
- Dates: 2024-04-15 to 2024-04-18
- Budget Level: Budget

## 💰 Estimated Total Cost
### $1,450.00 USD
- Flights: $650.00
- Accommodation: $450.00
- Activities: $350.00
```

### Day-by-Day Itinerary
```markdown
### Day 1: Classic Parisian Art

**09:00** - Louvre Museum
  📍 Rue de Rivoli
  - Explore world's largest art museum
  - See Mona Lisa, Venus de Milo
  💵 ~$20

**12:30** - Lunch at Le Comptoir
  - Traditional French bistro
  💵 ~$25

**14:30** - Musée d'Orsay
  - Impressionist masterpieces
  💵 ~$16
```

## 🔧 Customization Guide

### Adding Real APIs

#### Flights (Amadeus API)
```python
# In flight_agent.py
from amadeus import Client

class FlightAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_API_KEY'),
            client_secret=os.getenv('AMADEUS_API_SECRET')
        )

    def search_flights(self, origin, destination, date):
        response = self.amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1
        )
        return response.data
```

#### Hotels (Booking.com API)
```python
# In hotel_agent.py
import requests

def search_hotels(self, destination, checkin, checkout):
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
    params = {
        "locale": "en-us",
        "dest_id": destination,
        "checkin_date": checkin,
        "checkout_date": checkout
    }
    headers = {
        "X-RapidAPI-Key": os.getenv('RAPIDAPI_KEY')
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

### Customizing Agent Behavior

Edit the `create_system_prompt()` method:

```python
def create_system_prompt(self) -> str:
    return """You are a luxury travel specialist.

    Focus on:
    - 5-star hotels and premium airlines
    - Exclusive experiences
    - Fine dining recommendations
    - VIP services and concierge

    Always prioritize quality over price."""
```

### Adding New Specialist Agents

Create `car_rental_agent.py`:
```python
from .base_agent import BaseAgent

class CarRentalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Car Rental Specialist",
            role="expert car rental advisor"
        )

    def create_system_prompt(self) -> str:
        return """You are a car rental specialist..."""

    def process_task(self, task):
        # Search for rental cars
        # Return recommendations
        pass
```

Then add to coordinator:
```python
# In coordinator_agent.py
from .car_rental_agent import CarRentalAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        # ... existing code ...
        self.car_rental_agent = CarRentalAgent()
```

## 💡 Use Cases

This architecture can be adapted for:

1. **E-commerce Product Research**
   - Price comparison agent
   - Review analysis agent
   - Specification matcher agent

2. **Financial Planning**
   - Budget analysis agent
   - Investment recommendation agent
   - Risk assessment agent

3. **Event Planning**
   - Venue finder agent
   - Catering agent
   - Entertainment agent

4. **Research Assistant**
   - Literature review agent
   - Data analysis agent
   - Citation management agent

## 📈 Performance & Costs

### Typical Request Costs (Claude 3.5 Sonnet)
- Simple trip (3 days): ~$0.10-0.15
- Complex trip (7 days): ~$0.20-0.30
- With real-time API calls: +$0.05-0.10

### Response Times
- Request parsing: 1-2 seconds
- Each specialist agent: 2-5 seconds
- Total (parallel execution): 5-8 seconds
- UI rendering: <1 second

### Optimization Tips
1. Cache common destinations
2. Batch similar requests
3. Use cheaper models for simple tasks
4. Implement request deduplication

## 🎓 Learning Points

### 1. Agent Design Patterns
- **Specialist Pattern**: Each agent has specific expertise
- **Coordinator Pattern**: Central agent manages workflow
- **Observer Pattern**: Agents report results back to coordinator

### 2. Prompt Engineering
- System prompts define agent behavior
- Response format specifications ensure structure
- Context management for continuity

### 3. Error Handling
- Fallback responses when AI fails
- Mock data for testing without APIs
- Graceful degradation

### 4. UI/UX Considerations
- Real-time progress feedback
- Multiple output formats (Markdown, JSON)
- Example prompts for user guidance

## 🔒 Security Considerations

### API Key Management
```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use environment variables
export ANTHROPIC_API_KEY='...'

# Or use .env file (included in .gitignore)
cp .env.example .env
# Edit .env with your keys
```

### Input Validation
```python
def validate_request(user_input):
    # Check for reasonable trip duration
    if duration > 30:
        return "Trips longer than 30 days not supported"

    # Validate dates
    if departure_date < today:
        return "Cannot book trips in the past"

    return "valid"
```

### Rate Limiting
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_search(destination, dates):
    # Cache results for 1 hour
    return search_results
```

## 🌟 Next Steps

### Immediate Improvements
1. Add authentication and user sessions
2. Implement plan saving/loading
3. Add plan comparison features
4. Email itinerary to users

### Advanced Features
1. Real-time price tracking
2. Weather forecasts integration
3. Currency conversion
4. Travel visa requirements checker
5. Packing list generator
6. Budget tracking during trip

### Production Readiness
1. Error logging and monitoring
2. Performance metrics
3. A/B testing for prompts
4. User feedback collection
5. Database for storing plans

## 📚 Additional Resources

- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Amadeus Travel APIs](https://developers.amadeus.com/)
- [Multi-Agent System Design](https://en.wikipedia.org/wiki/Multi-agent_system)

## 🤝 Contributing

To extend this demo:

1. Fork the repository
2. Create a feature branch
3. Add your agent or enhancement
4. Test thoroughly
5. Submit a pull request

## 📞 Troubleshooting

### Common Issues

**"ANTHROPIC_API_KEY not found"**
```bash
# Set environment variable
export ANTHROPIC_API_KEY='sk-ant-...'

# Or create .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**"Streamlit command not found"**
```bash
pip install streamlit
```

**Agent returns invalid JSON**
- This is usually temporary
- System has fallback logic
- Try the request again

---

**Built to demonstrate multi-agent orchestration with Claude AI** 🤖

For questions or feedback, see the main README.md file.
