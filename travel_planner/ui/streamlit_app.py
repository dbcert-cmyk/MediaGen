"""
Streamlit UI for Multi-Agent Travel Planner
Beautiful, user-friendly interface for the travel planning system
"""
import streamlit as st
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents import CoordinatorAgent


# Page configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-size: 1.1rem;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
    }
    .example-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'travel_plan' not in st.session_state:
        st.session_state.travel_plan = None
    if 'planning_started' not in st.session_state:
        st.session_state.planning_started = False


def display_header():
    """Display the main header"""
    st.markdown('<div class="main-header">✈️ AI Travel Planner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Your Personal Multi-Agent Travel Planning Assistant</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")


def display_example_requests():
    """Display example travel requests"""
    st.sidebar.markdown("### 💡 Example Requests")

    examples = [
        "Plan me a 3-day budget trip to Paris focused on art and museums",
        "I want a 5-day luxury vacation in Tokyo with great food and culture",
        "Create a 4-day family trip to Orlando with theme parks",
        "Plan a romantic 3-day getaway to Santorini with beach and sunset views",
        "I need a 7-day adventure trip to Iceland with hiking and nature"
    ]

    for example in examples:
        if st.sidebar.button(example, key=f"example_{example[:20]}"):
            st.session_state.user_request = example


def display_agent_info():
    """Display information about the agent system"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 How It Works")
    st.sidebar.markdown("""
    Our AI team consists of:

    **✈️ Flight Specialist**
    - Searches for best flight options
    - Compares prices and routes
    - Recommends optimal flights

    **🏨 Hotel Specialist**
    - Finds perfect accommodations
    - Matches hotels to your interests
    - Ensures great location and value

    **📅 Activity Specialist**
    - Creates detailed itineraries
    - Recommends attractions & experiences
    - Balances popular spots with hidden gems

    **🌍 Travel Coordinator**
    - Orchestrates all agents
    - Combines everything into one plan
    - Ensures seamless experience
    """)


def create_travel_plan(user_request: str):
    """
    Create travel plan using the coordinator agent

    Args:
        user_request: User's natural language travel request
    """
    try:
        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("⚠️ ANTHROPIC_API_KEY not found in environment variables!")
            st.info("Please set your Anthropic API key to use this application.")
            st.code("export ANTHROPIC_API_KEY='your-api-key-here'")
            return None

        # Initialize coordinator
        coordinator = CoordinatorAgent()

        # Create travel plan with progress updates
        with st.spinner("🤖 Our AI agents are working on your perfect trip..."):
            # Create columns for progress tracking
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.info("📋 Analyzing request...")

            travel_plan = coordinator.create_travel_plan(user_request)

            with col2:
                st.success("✈️ Flights found!")

            with col3:
                st.success("🏨 Hotels found!")

            with col4:
                st.success("📅 Itinerary created!")

        return travel_plan

    except Exception as e:
        st.error(f"❌ Error creating travel plan: {str(e)}")
        st.exception(e)
        return None


def display_travel_plan(plan: dict):
    """
    Display the complete travel plan in a beautiful format

    Args:
        plan: Travel plan dictionary
    """
    if not plan or not plan.get("success"):
        st.error(f"❌ Failed to create travel plan: {plan.get('error', 'Unknown error')}")
        return

    # Create coordinator instance for markdown formatting
    coordinator = CoordinatorAgent()
    markdown_plan = coordinator.format_travel_plan_markdown(plan)

    # Display in two tabs: Formatted View and JSON View
    tab1, tab2 = st.tabs(["📋 Your Travel Plan", "🔧 JSON Data"])

    with tab1:
        st.markdown(markdown_plan)

        # Download button for the plan
        st.download_button(
            label="📥 Download Travel Plan (Markdown)",
            data=markdown_plan,
            file_name=f"travel_plan_{plan['trip_summary']['destination']}.md",
            mime="text/markdown"
        )

    with tab2:
        st.json(plan)

        # Download button for JSON
        st.download_button(
            label="📥 Download Travel Plan (JSON)",
            data=json.dumps(plan, indent=2),
            file_name=f"travel_plan_{plan['trip_summary']['destination']}.json",
            mime="application/json"
        )


def main():
    """Main application"""
    initialize_session_state()

    # Display header
    display_header()

    # Sidebar with examples and info
    display_example_requests()
    display_agent_info()

    # Main content area
    st.markdown("### 🌟 Describe Your Dream Trip")

    # Text area for user request
    user_request = st.text_area(
        "Tell us about your ideal trip...",
        value=st.session_state.get('user_request', ''),
        height=150,
        placeholder="Example: Plan me a 5-day trip to Barcelona focused on architecture, food, and beaches. Budget is mid-range.",
        help="Be as specific or general as you like! Our AI will understand your needs."
    )

    # Advanced options (collapsible)
    with st.expander("⚙️ Advanced Options (Optional)"):
        col1, col2 = st.columns(2)

        with col1:
            origin_city = st.text_input("Departure City", value="", placeholder="Auto-detected")
            travelers = st.number_input("Number of Travelers", min_value=1, max_value=10, value=1)

        with col2:
            budget_override = st.selectbox(
                "Budget Override",
                ["Auto-detect", "Budget", "Economy", "Premium", "Luxury"]
            )
            duration_override = st.number_input(
                "Duration Override (days)",
                min_value=0,
                max_value=30,
                value=0,
                help="0 = auto-detect from request"
            )

    # Plan button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Create My Travel Plan", type="primary"):
            if not user_request:
                st.warning("⚠️ Please describe your trip first!")
            else:
                st.session_state.planning_started = True
                travel_plan = create_travel_plan(user_request)
                if travel_plan:
                    st.session_state.travel_plan = travel_plan

    # Display travel plan if available
    if st.session_state.travel_plan:
        st.markdown("---")
        st.markdown("## ✨ Your Personalized Travel Plan")
        display_travel_plan(st.session_state.travel_plan)

        # New plan button
        if st.button("🔄 Plan Another Trip"):
            st.session_state.travel_plan = None
            st.session_state.planning_started = False
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Powered by Claude AI & Multi-Agent Architecture | "
        "Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
