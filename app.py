from shiny import App, reactive, render, ui
import os
import time
import json
import random
from datetime import datetime
from shinywidgets import output_widget, render_plotly
import plotly.graph_objects as go
from pathlib import Path

# ===== CFA CONFIGURATION =====
QUIZ_TITLE = "CFA Exam Preparation Pro"
CFA_REGISTRATION_URL = "https://www.cfainstitute.org/"
STUDY_GUIDE_PATH = "Data/CFA_Study_Guide.pdf"
REGISTRATION_TIPS = """
• Early registration discounts available
• Prepare payment method in advance  
• Have identification documents ready
• Check exam schedule carefully
"""

# Topic and category mappings
TOPIC_TO_CATEGORY = {
    "Ethical & Professional Standards": "Ethical and Professional Standards",
    "Quantitative Methods": "Quantitative Methods", 
    "Economics": "Economics",
    "Financial Reporting & Analysis": "Financial Statement Analysis",
    "Corporate Issuers": "Corporate Issuers",
    "Equity Investments": "Equity Investments",
    "Fixed Income": "Fixed Income",
    "Derivatives": "Derivatives",
    "Alternative Investments": "Alternative Investments",
    "Portfolio Management": "Portfolio Management"
}

CATEGORIES = {
    "Ethical and Professional Standards": {
        "description": "Focuses on ethical principles and professional standards",
        "weight": 0.15
    },
    "Quantitative Methods": {
        "description": "Covers statistical tools for financial analysis",
        "weight": 0.10
    },
    "Economics": {
        "description": "Examines macroeconomic and microeconomic concepts",
        "weight": 0.10
    },
    "Financial Statement Analysis": {
        "description": "Analysis of financial statements", 
        "weight": 0.15
    },
    "Corporate Issuers": {
        "description": "Characteristics of corporate issuers",
        "weight": 0.10
    },
    "Equity Investments": {
        "description": "Valuation of equity securities",
        "weight": 0.11
    },
    "Fixed Income": {
        "description": "Analysis of fixed-income securities",
        "weight": 0.11
    },
    "Derivatives": {
        "description": "Valuation of derivative securities",
        "weight": 0.06
    },
    "Alternative Investments": {
        "description": "Hedge funds, private equity, real estate",
        "weight": 0.06
    },
    "Portfolio Management": {
        "description": "Portfolio construction and risk management",
        "weight": 0.06
    }
}

# ===== HELPER FUNCTIONS =====
def load_questions():
    try:
        json_path = Path(__file__).parent / 'Data' / 'updated_questions_with_5_options_final.json'
        with open(json_path, 'r') as f:
            questions_data = json.load(f)
        
        questions_by_category = {cat: {'easy': [], 'medium': [], 'hard': []} for cat in CATEGORIES}
        
        for question in questions_data.get("questions", []):
            topic = question.get("topic", "").strip()
            category = TOPIC_TO_CATEGORY.get(topic, topic)
            difficulty = question.get("difficulty", "medium").lower()
            
            if category in questions_by_category and difficulty in ['easy', 'medium', 'hard']:
                questions_by_category[category][difficulty].append(question)
        
        return questions_by_category
        
    except Exception as e:
        print(f"Error loading questions: {str(e)}")
        return {cat: {'easy': [], 'medium': [], 'hard': []} for cat in CATEGORIES}

def format_time(seconds):
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

# ===== SHINY APP UI =====
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            body {
                background-image: url('Data/background.jpg');
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
                margin: 0;
                padding: 0;
            }
            
            .container-fluid {
                background-color: rgba(255, 255, 255, 0.85) !important;
                padding: 2rem;
                border-radius: 10px;
                margin-top: 1rem;
            }
            
            .btn {
                background-color: #3498db !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: bold !important;
                padding: 0.5rem 1rem !important;
                margin: 0.2rem !important;
                transition: all 0.3s ease;
            }
            
            .btn:hover {
                background-color: #2980b9 !important;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            
            .card {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .progress {
                height: 10px;
                margin: 10px 0;
                background-color: #e9ecef;
                border-radius: 5px;
            }
            
            .progress-bar {
                height: 100%;
                border-radius: 5px;
                background-color: #3498db;
                transition: width 0.3s ease;
            }
        """)
    ),
    ui.navset_tab(
        ui.nav("Main Menu", ui.output_ui("main_menu")),
        ui.nav("Category Selection", ui.output_ui("category_selection")),
        ui.nav("Difficulty Selection", ui.output_ui("difficulty_selection")),
        ui.nav("Quiz", ui.output_ui("quiz_interface")),
        ui.nav("Results", ui.output_ui("results_page")),
        ui.nav("Progress Tracking", ui.output_ui("progress_tracking")),
        id="nav"
    )
)

# ===== SHINY APP SERVER =====
def server(input, output, session):
    # Reactive state management
    quiz = reactive.Value({
        "all_questions": load_questions(),
        "current_questions": [],
        "score": 0,
        "current_index": 0,
        "start_time": time.time(),
        "question_start": time.time(),
        "time_spent": [],
        "selected_category": None,
        "test_type": None,
        "exam_number": None
    })
    
    progress = reactive.Value({
        "attempts": [],
        "scores": [],
        "time_spent": [],
        "dates": [],
        "registration_clicks": 0,
        "last_registration_click": None
    })
    
    # Load progress data
    @reactive.Effect
    def load_progress_data():
        try:
            progress_path = Path(__file__).parent / 'Data' / 'progress_data.json'
            with open(progress_path, 'r') as f:
                progress.set(json.load(f))
        except:
            pass
    
    # Save progress data
    def save_progress():
        try:
            progress_path = Path(__file__).parent / 'Data' / 'progress_data.json'
            with open(progress_path, 'w') as f:
                json.dump(progress(), f)
        except Exception as e:
            print(f"Could not save progress data: {e}")
    
    # [Rest of the server functions...]
    # Include all your other server functions here following the same pattern
    
    # Quiz submission handler
    @reactive.Effect
    @reactive.event(input.submit_answer)
    def handle_answer_submission():
        current_quiz = dict(quiz())
        idx = current_quiz["current_index"]
        question = current_quiz["current_questions"][idx]
        user_answer = input[f"answer_{idx}"]()
        
        time_spent = time.time() - current_quiz["question_start"]
        current_quiz["time_spent"].append(time_spent)
        
        if user_answer == question["correct_answer"]:
            current_quiz["score"] += 1
        
        current_quiz["current_index"] += 1
        current_quiz["question_start"] = time.time()
        
        quiz.set(current_quiz)
        
        if current_quiz["current_index"] >= len(current_quiz["current_questions"]):
            ui.update_navs("nav", selected="Results")
            save_progress()

app = App(app_ui, server)
