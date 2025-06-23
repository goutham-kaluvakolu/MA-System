# Configuration file for the Multi-Agent System UI

# UI Configuration
UI_CONFIG = {
    "page_title": "🤖 Multi-Agent System",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Task Templates
TASK_TEMPLATES = {
    "📧 Email Management": "Help me manage my emails - check for important messages and draft responses",
    "📅 Calendar Planning": "Schedule a meeting for next week and send calendar invites",
    "🔍 Research Task": "Research the latest developments in AI and provide a summary",
    "📊 Data Analysis": "Analyze my recent email patterns and provide insights",
    "📝 Document Creation": "Create a professional document based on my requirements",
    "🤖 Custom Task": "Enter your own task..."
}

# Agent Configuration
AGENTS = {
    "planner": {
        "name": "Planner",
        "description": "Central planning and coordination agent",
        "icon": "🧠",
        "color": "#667eea"
    },
    "google_apis_agent": {
        "name": "Google APIs",
        "description": "Handles Google services (Gmail, Calendar, etc.)",
        "icon": "🔗",
        "color": "#4285f4"
    },
    "websearch_agent": {
        "name": "Web Search",
        "description": "Performs web searches and information gathering",
        "icon": "🌐",
        "color": "#34a853"
    }
}

# Status Configuration
STATUS_CONFIG = {
    "idle": {"icon": "⚪", "color": "#6c757d"},
    "running": {"icon": "🟡", "color": "#ffc107"},
    "success": {"icon": "🟢", "color": "#28a745"},
    "error": {"icon": "🔴", "color": "#dc3545"}
}

# Theme Configuration
THEME = {
    "primary_color": "#667eea",
    "secondary_color": "#764ba2",
    "success_color": "#28a745",
    "warning_color": "#ffc107",
    "error_color": "#dc3545",
    "background_color": "#f8f9fa",
    "text_color": "#212529"
}

# Export Configuration
EXPORT_CONFIG = {
    "csv_filename_prefix": "task_history",
    "date_format": "%Y%m%d_%H%M%S",
    "max_history_display": 50
} 