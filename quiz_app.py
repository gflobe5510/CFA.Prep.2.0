from shiny import App, reactive, render, ui
import os
import time
import json
import matplotlib.pyplot as plt
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

# Topic and category mappings (same as original)
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
        with open('Data/updated_questions_with_5_options_final.json', 'r') as f:
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

# ===== SHINY APP =====
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            /* Global styles */
            body {
                background-image: url('Data/background.jpg');
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
            }
            
            /* Content container */
            .container-fluid {
                background-color: rgba(255, 255, 255, 0.85) !important;
                padding: 2rem;
                border-radius: 10px;
                margin-top: 1rem;
            }
            
            /* Button styling */
            .btn {
                background-color: #3498db !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: bold !important;
                padding: 0.5rem 1rem !important;
                margin: 0.2rem !important;
            }
            
            .btn:hover {
                background-color: #2980b9 !important;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            
            /* Cards */
            .card {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 15px;
            }
            
            /* Progress bars */
            .progress {
                height: 10px;
                margin: 10px 0;
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

def server(input, output, session):
    # Reactive values to replace session_state
    quiz = reactive.Value({
        "all_questions": load_questions(),
        "current_questions": [],
        "score": 0,
        "current_index": 0,
        "start_time": time.time(),
        "question_start": time.time(),
        "time_spent": [],
        "mode": "main_menu",
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
            with open('Data/progress_data.json', 'r') as f:
                progress.set(json.load(f))
        except:
            pass
    
    # Save progress data
    def save_progress():
        try:
            with open('Data/progress_data.json', 'w') as f:
                json.dump(progress(), f)
        except Exception as e:
            print(f"Could not save progress data: {e}")
    
    # Main menu
    @output
    @render.ui
    def main_menu():
        return ui.div(
            ui.h1(QUIZ_TITLE),
            ui.div(
                ui.h3("CFA Level I Exam Preparation Pro"),
                ui.p("Complete your first quiz to see stats"),
                class_="card"
            ),
            
            # Resources section
            ui.div(
                ui.h3("📚 Study Resources"),
                ui.layout_columns(
                    ui.download_button(
                        "download_guide",
                        "📘 Download Study Guide",
                        class_="btn"
                    ) if Path(STUDY_GUIDE_PATH).exists() else ui.div("Study guide not found"),
                    ui.input_action_button(
                        "register",
                        "🌐 Register for CFA Exam",
                        class_="btn"
                    ),
                    ui.input_action_button(
                        "view_progress",
                        "📈 View Progress Dashboard",
                        class_="btn"
                    ),
                    col_widths=(4, 4, 4)
                ),
                class_="card"
            ),
            
            # Practice options
            ui.div(
                ui.h3("🎯 Practice Options"),
                ui.layout_columns(
                    ui.input_action_button(
                        "custom_practice",
                        "📝 Custom Practice Exam",
                        class_="btn"
                    ),
                    ui.input_action_button(
                        "topic_practice",
                        "📚 Focused Topic Practice",
                        class_="btn"
                    ),
                    col_widths=(6, 6)
                ),
                class_="card"
            )
        )
    
    # Category selection
    @output
    @render.ui
    def category_selection():
        buttons = []
        for i, category in enumerate(CATEGORIES):
            total_questions = sum(len(quiz()["all_questions"][category][d]) 
                              for d in ['easy', 'medium', 'hard'])
            
            disabled = total_questions == 0
            
            buttons.append(
                ui.input_action_button(
                    f"category_{i}",
                    f"{category} ({total_questions} questions)",
                    disabled=disabled,
                    class_="btn"
                )
            )
        
        return ui.div(
            ui.div(
                ui.h2("Select a CFA Topic Area"),
                class_="card"
            ),
            ui.layout_columns(
                *buttons,
                col_widths=6
            ),
            ui.input_action_button(
                "back_to_main_from_category",
                "← Back to Main Menu",
                class_="btn"
            )
        )
    
    # Difficulty selection
    @output
    @render.ui
    def difficulty_selection():
        return ui.div(
            ui.div(
                ui.h2("Select Practice Exam Type"),
                class_="card"
            ),
            
            # Balanced exams
            ui.div(
                ui.h3("Balanced Exams (Mixed Difficulty)"),
                ui.layout_columns(
                    *[
                        ui.input_action_button(
                            f"balanced_{i}",
                            f"Balanced Exam {i}",
                            class_="btn"
                        ) for i in range(1, 6)
                    ],
                    col_widths=[2, 2, 2, 2, 2]
                ),
                class_="card"
            ),
            
            # Specialized exams
            ui.div(
                ui.h3("Specialized Exams"),
                ui.layout_columns(
                    ui.input_action_button("easy_exam", "📗 Easy Exam", class_="btn"),
                    ui.input_action_button("medium_exam", "📘 Medium Exam", class_="btn"),
                    ui.input_action_button("hard_exam", "📕 Hard Exam", class_="btn"),
                    ui.input_action_button("super_hard", "💀 Super Hard", class_="btn"),
                    col_widths=3
                ),
                class_="card"
            ),
            
            # Quick practice
            ui.div(
                ui.h3("Quick Practice"),
                ui.layout_columns(
                    ui.input_action_button("quick_quiz", "🎯 Quick Quiz", class_="btn"),
                    ui.input_action_button("random_mix", "🔀 Random Mix", class_="btn"),
                    col_widths=6
                ),
                class_="card"
            ),
            
            ui.input_action_button(
                "back_to_main_from_difficulty",
                "← Back to Main Menu",
                class_="btn"
            )
        )
    
    # Quiz interface
    @output
    @render.ui
    def quiz_interface():
        current_quiz = quiz()
        questions = current_quiz["current_questions"]
        idx = current_quiz["current_index"]
        
        if not questions:
            return ui.div("No questions available")
        
        if idx >= len(questions):
            return show_results()
        
        question = questions[idx]
        progress = (idx + 1) / len(questions)
        
        # Determine exam title
        exam_type = current_quiz.get("test_type")
        if exam_type == 'balanced_exam':
            title = f"Balanced Exam {current_quiz.get('exam_number', '')}"
        elif exam_type == 'practice_test':
            title = current_quiz['selected_category']
        elif exam_type == 'super_hard':
            title = "Super Hard Exam"
        elif exam_type == 'quick_quiz':
            title = "Quick Quiz"
        elif exam_type == 'random_mix':
            title = "Random Mix"
        else:
            title = current_quiz['selected_category']
        
        return ui.div(
            ui.div(
                ui.h3(title),
                ui.p(f"Question {idx + 1} of {len(questions)}"),
                ui.div(
                    ui.div(style=f"width: {progress*100}%", class_="progress-bar"),
                    class_="progress"
                ),
                ui.p(f"Difficulty: {question.get('difficulty', 'medium').capitalize()}"),
                ui.p(ui.strong(question["question"])),
                ui.input_radio_buttons(
                    f"answer_{idx}",
                    "Select your answer:",
                    choices=question["options"]
                ),
                ui.input_action_button(
                    "submit_answer",
                    "Submit Answer",
                    class_="btn"
                ),
                class_="card"
            )
        )
    
    # Results page
    def show_results():
        current_quiz = quiz()
        questions = current_quiz["current_questions"]
        total_time = time.time() - current_quiz["start_time"]
        avg_time = sum(current_quiz["time_spent"])/len(current_quiz["time_spent"]) if current_quiz["time_spent"] else 0
        score = current_quiz["score"] / len(questions)
        
        # Update progress
        new_progress = progress()
        new_progress["attempts"].append(len(new_progress["attempts"]) + 1)
        new_progress["scores"].append(score)
        new_progress["time_spent"].append(total_time)
        new_progress["dates"].append(datetime.now().strftime("%Y-%m-%d"))
        progress.set(new_progress)
        save_progress()
        
        # Create plot
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Your Score", "Benchmark"],
            y=[score, 0.75],
            marker_color=['#3498db', '#95a5a6']
        ))
        fig.update_layout(yaxis_range=[0, 1])
        
        return ui.div(
            ui.div(
                ui.h2("Quiz Completed!"),
                ui.layout_columns(
                    ui.div(
                        ui.div("Score", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(f"{current_quiz['score']}/{len(questions)}", style="font-size: 32px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    ui.div(
                        ui.div("Total Time", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(format_time(total_time), style="font-size: 32px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    ui.div(
                        ui.div("Avg/Question", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(format_time(avg_time), style="font-size: 32px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    col_widths=4
                ),
                output_widget("results_plot"),
                ui.layout_columns(
                    ui.input_action_button(
                        "return_to_main",
                        "Return to Main Menu",
                        class_="btn"
                    ),
                    ui.input_action_button(
                        "view_progress_results",
                        "View Progress Dashboard",
                        class_="btn"
                    ),
                    col_widths=6
                ),
                class_="card"
            )
        )
    
    @output
    @render_plotly
    def results_plot():
        current_quiz = quiz()
        questions = current_quiz["current_questions"]
        score = current_quiz["score"] / len(questions)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Your Score", "Benchmark"],
            y=[score, 0.75],
            marker_color=['#3498db', '#95a5a6']
        ))
        fig.update_layout(yaxis_range=[0, 1])
        return fig
    
    # Progress tracking
    @output
    @render.ui
    def progress_tracking():
        prog = progress()
        
        if not prog.get("attempts"):
            return ui.div(
                ui.div(
                    ui.p("No progress data yet. Complete some quizzes to track your progress!"),
                    ui.input_action_button(
                        "back_to_main_progress",
                        "← Back to Main Menu",
                        class_="btn"
                    ),
                    class_="card"
                )
            )
        
        # Create progress plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=prog["attempts"],
            y=prog["scores"],
            mode='lines+markers',
            name='Score'
        ))
        fig.update_layout(
            title="Score Improvement Over Time",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1]
        )
        
        return ui.div(
            ui.div(
                ui.h2("Your Study Progress"),
                class_="card"
            ),
            
            # Metrics
            ui.div(
                ui.h3("Progress Overview"),
                ui.layout_columns(
                    ui.div(
                        ui.div("Total Attempts", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(f"{len(prog['attempts'])}", style="font-size: 24px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    ui.div(
                        ui.div("Average Score", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(f"{sum(prog['scores'])/len(prog['scores']):.1%}", style="font-size: 24px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    ui.div(
                        ui.div("Total Study Time", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(f"{sum(prog['time_spent'])/60:.1f} min", style="font-size: 24px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    col_widths=4
                ),
                class_="card"
            ),
            
            # Registration stats
            ui.div(
                ui.h3("Registration Interest"),
                ui.layout_columns(
                    ui.div(
                        ui.div("Total Registration Clicks", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(f"{prog.get('registration_clicks', 0)}", style="font-size: 24px; font-weight: bold; color: #2c3e50;"),
                        class_="card"
                    ),
                    ui.div(
                        ui.div("Last Registration Click", style="font-size: 16px; color: #7f8c8d;"),
                        ui.div(
                            datetime.fromisoformat(prog["last_registration_click"]).strftime("%Y-%m-%d %H:%M") 
                            if prog.get("last_registration_click") 
                            else "Never",
                            style="font-size: 24px; font-weight: bold; color: #2c3e50;"
                        ),
                        class_="card"
                    ),
                    col_widths=6
                ),
                class_="card"
            ),
            
            # Plots
            ui.div(
                ui.h3("Progress Charts"),
                output_widget("progress_plot"),
                class_="card"
            ),
            
            # Table
            ui.div(
                ui.h3("Detailed Progress History"),
                ui.output_table("progress_table"),
                class_="card"
            ),
            
            ui.input_action_button(
                "back_to_main_progress",
                "← Back to Main Menu",
                class_="btn"
            )
        )
    
    @output
    @render_plotly
    def progress_plot():
        prog = progress()
        fig = go.Figure()
        
        # Score progression
        fig.add_trace(go.Scatter(
            x=prog["attempts"],
            y=prog["scores"],
            mode='lines+markers',
            name='Score',
            yaxis='y1'
        ))
        
        # Time spent
        fig.add_trace(go.Bar(
            x=prog["attempts"],
            y=prog["time_spent"],
            name='Time Spent',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Progress Over Time",
            yaxis=dict(
                title="Score",
                tickformat=".0%",
                range=[0, 1]
            ),
            yaxis2=dict(
                title="Time (seconds)",
                overlaying="y",
                side="right"
            )
        )
        
        return fig
    
    @output
    @render.table
    def progress_table():
        prog = progress()
        return {
            "Attempt": prog["attempts"],
            "Date": prog["dates"],
            "Score": [f"{s:.1%}" for s in prog["scores"]],
            "Time Spent": [f"{t//60}m {t%60}s" for t in prog["time_spent"]]
        }
    
    # ===== EVENT HANDLERS =====
    
    # Navigation
    @reactive.Effect
    @reactive.event(input.custom_practice)
    def _():
        ui.update_navs("nav", selected="Difficulty Selection")
    
    @reactive.Effect
    @reactive.event(input.topic_practice)
    def _():
        ui.update_navs("nav", selected="Category Selection")
    
    @reactive.Effect
    @reactive.event(input.view_progress, input.view_progress_results)
    def _():
        ui.update_navs("nav", selected="Progress Tracking")
    
    @reactive.Effect
    @reactive.event(input.back_to_main_from_category, input.back_to_main_from_difficulty, 
                   input.back_to_main_progress, input.return_to_main)
    def _():
        ui.update_navs("nav", selected="Main Menu")
    
    # Category selection
    @reactive.Effect
    def handle_category_selection():
        for i, category in enumerate(CATEGORIES):
            if input[f"category_{i}"]() > 0:
                questions = []
                for difficulty in ['easy', 'medium', 'hard']:
                    questions.extend(quiz()["all_questions"][category][difficulty])
                
                new_quiz = quiz()
                new_quiz.update({
                    "current_questions": questions,
                    "current_index": 0,
                    "selected_category": category,
                    "question_start": time.time(),
                    "score": 0,
                    "time_spent": [],
                    "test_type": "category",
                    "mode": "question"
                })
                quiz.set(new_quiz)
                ui.update_navs("nav", selected="Quiz")
    
    # Difficulty selection
    @reactive.Effect
    def handle_difficulty_selection():
        # Balanced exams
        for i in range(1, 6):
            if input[f"balanced_{i}"]() > 0:
                start_balanced_exam(i)
                return
        
        # Other exam types
        if input.easy_exam() > 0:
            start_practice_test('easy')
        elif input.medium_exam() > 0:
            start_practice_test('medium')
        elif input.hard_exam() > 0:
            start_practice_test('hard')
        elif input.super_hard() > 0:
            start_super_hard_exam()
        elif input.quick_quiz() > 0:
            start_quick_quiz()
        elif input.random_mix() > 0:
            start_random_mix()
    
    def start_balanced_exam(exam_number):
        questions = []
        target_per_difficulty = 10
        
        for difficulty in ['easy', 'medium', 'hard']:
            difficulty_questions = []
            for category in CATEGORIES:
                cat_questions = quiz()["all_questions"][category].get(difficulty, [])
                if cat_questions:
                    difficulty_questions.extend(random.sample(cat_questions, min(2, len(cat_questions)))
            
            if difficulty_questions:
                questions.extend(random.sample(difficulty_questions, min(target_per_difficulty, len(difficulty_questions)))
        
        if len(questions) < 15:
            print("Not enough questions for balanced exam")
            return
        
        random.shuffle(questions)
        
        new_quiz = quiz()
        new_quiz.update({
            "current_questions": questions,
            "current_index": 0,
            "selected_category": f"Balanced Exam {exam_number}",
            "question_start": time.time(),
            "score": 0,
            "time_spent": [],
            "test_type": "balanced_exam",
            "exam_number": exam_number,
            "mode": "question"
        })
        quiz.set(new_quiz)
        ui.update_navs("nav", selected="Quiz")
    
    def start_practice_test(difficulty):
        questions = []
        for category in CATEGORIES:
            category_questions = quiz()["all_questions"][category].get(difficulty, [])
            if category_questions:
                questions.extend(random.sample(category_questions, min(2, len(category_questions))))
        
        if not questions:
            print(f"No {difficulty} questions available")
            return
        
        random.shuffle(questions)
        
        new_quiz = quiz()
        new_quiz.update({
            "current_questions": questions,
            "current_index": 0,
            "selected_category": f"{difficulty.capitalize()} Exam",
            "question_start": time.time(),
            "score": 0,
            "time_spent": [],
            "test_type": "practice_test",
            "mode": "question"
        })
        quiz.set(new_quiz)
        ui.update_navs("nav", selected="Quiz")
    
    def start_super_hard_exam():
        questions = []
        for category in CATEGORIES:
            category_questions = quiz()["all_questions"][category].get('hard', [])
            if category_questions:
                questions.extend(random.sample(category_questions, min(3, len(category_questions))))
        
        if not questions:
            print("No hard questions available")
            return
        
        random.shuffle(questions)
        
        new_quiz = quiz()
        new_quiz.update({
            "current_questions": questions,
            "current_index": 0,
            "selected_category": "Super Hard Exam",
            "question_start": time.time(),
            "score": 0,
            "time_spent": [],
            "test_type": "super_hard",
            "mode": "question"
        })
        quiz.set(new_quiz)
        ui.update_navs("nav", selected="Quiz")
    
    def start_quick_quiz():
        questions = []
        for category in CATEGORIES:
            for difficulty in ['easy', 'medium', 'hard']:
                category_questions = quiz()["all_questions"][category].get(difficulty, [])
                if category_questions:
                    questions.extend(category_questions)
        
        if len(questions) < 5:
            print("Not enough questions for quick quiz")
            return
        
        questions = random.sample(questions, 5)
        
        new_quiz = quiz()
        new_quiz.update({
            "current_questions": questions,
            "current_index": 0,
            "selected_category": "Quick Quiz",
            "question_start": time.time(),
            "score": 0,
            "time_spent": [],
            "test_type": "quick_quiz",
            "mode": "question"
        })
        quiz.set(new_quiz)
        ui.update_navs("nav", selected="Quiz")
    
    def start_random_mix():
        questions = []
        for category in CATEGORIES:
            for difficulty in ['easy', 'medium', 'hard']:
                category_questions = quiz()["all_questions"][category].get(difficulty, [])
                if category_questions:
                    questions.extend(category_questions)
        
        if not questions:
            print("No questions available")
            return
        
        random.shuffle(questions)
        questions = questions[:20]
        
        new_quiz = quiz()
        new_quiz.update({
            "current_questions": questions,
            "current_index": 0,
            "selected_category": "Random Mix",
            "question_start": time.time(),
            "score": 0,
            "time_spent": [],
            "test_type": "random_mix",
            "mode": "question"
        })
        quiz.set(new_quiz)
        ui.update_navs("nav", selected="Quiz")
    
    # Quiz submission
    @reactive.Effect
    @reactive.event(input.submit_answer)
    def handle_answer_submission():
        current_quiz = quiz()
        idx = current_quiz["current_index"]
        question = current_quiz["current_questions"][idx]
        user_answer = input[f"answer_{idx}"]()
        
        time_spent = time.time() - current_quiz["question_start"]
        
        new_quiz = current_quiz.copy()
        new_quiz["time_spent"].append(time_spent)
        
        if user_answer == question["correct_answer"]:
            new_quiz["score"] += 1
        
        new_quiz["current_index"] += 1
        new_quiz["question_start"] = time.time()
        
        quiz.set(new_quiz)
        
        if new_quiz["current_index"] >= len(new_quiz["current_questions"]):
            ui.update_navs("nav", selected="Results")
    
    # Registration click
    @reactive.Effect
    @reactive.event(input.register)
    def handle_registration():
        new_progress = progress()
        new_progress["registration_clicks"] += 1
        new_progress["last_registration_click"] = datetime.now().isoformat()
        progress.set(new_progress)
        save_progress()
        
        # Open in new tab (not directly possible in Shiny, show link instead)
        ui.notification_show("Registration link opened in new tab", duration=3)
        ui.insert_ui(
            ui.tags.script(f"window.open('{CFA_REGISTRATION_URL}')"),
            selector="body",
            immediate=True
        )
    
    # Download study guide
    @session.download(filename="CFA_Study_Guide.pdf")
    def download_guide():
        path = Path(STUDY_GUIDE_PATH)
        if path.exists():
            return str(path)
        else:
            ui.notification_show("Study guide not found", duration=3, type="error")
            return None

app = App(app_ui, server)
