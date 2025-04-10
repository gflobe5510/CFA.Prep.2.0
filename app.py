from shiny import App, reactive, render, ui
import json
import random
from datetime import datetime
import time

# ===== CONSTANTS & CONFIG =====
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
    "Ethical and Professional Standards": {"weight": 0.15},
    "Quantitative Methods": {"weight": 0.10},
    "Economics": {"weight": 0.10},
    "Financial Statement Analysis": {"weight": 0.15},
    "Corporate Issuers": {"weight": 0.10},
    "Equity Investments": {"weight": 0.11},
    "Fixed Income": {"weight": 0.11},
    "Derivatives": {"weight": 0.06},
    "Alternative Investments": {"weight": 0.06},
    "Portfolio Management": {"weight": 0.06}
}

# ===== HELPER FUNCTIONS =====
def load_questions():
    with open('Data/updated_questions_with_5_options_final.json') as f:
        questions = json.load(f)["questions"]
    
    # Organize by category and difficulty
    organized = {cat: {"easy": [], "medium": [], "hard": []} for cat in CATEGORIES}
    
    for q in questions:
        category = TOPIC_TO_CATEGORY.get(q["topic"], q["topic"])
        difficulty = q.get("difficulty", "medium").lower()
        if category in organized and difficulty in organized[category]:
            organized[category][difficulty].append(q)
    
    return organized

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# ===== APP UI =====
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            :root {
                --primary: #3498db;
                --secondary: #f8f9fa;
                --text: #2c3e50;
                --border: #e0e0e0;
            }
            .btn {
                background-color: var(--primary) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                margin: 4px !important;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .card {
                background-color: var(--secondary);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 15px;
                border: 1px solid var(--border);
            }
            .progress-container {
                height: 10px;
                background-color: #e0e0e0;
                border-radius: 5px;
                margin: 10px 0;
            }
            .progress-bar {
                height: 100%;
                border-radius: 5px;
                background-color: var(--primary);
                transition: width 0.3s ease;
            }
            .correct {
                color: #2ecc71;
                font-weight: bold;
            }
            .incorrect {
                color: #e74c3c;
                font-weight: bold;
            }
            .explanation {
                background-color: #f0f8ff;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
                border-left: 4px solid var(--primary);
            }
        """)
    ),
    ui.navset_pill(
        ui.nav_panel(
            "Main Menu",
            ui.div(
                ui.h2("CFA Exam Prep Pro", class_="text-center"),
                ui.div(
                    ui.h4("Welcome!", class_="text-center"),
                    ui.p("Select an option below to begin your practice:", class_="text-center"),
                    class_="card"
                ),
                ui.div(
                    ui.input_action_button("btn_practice", "📝 Practice Exam", class_="btn"),
                    ui.input_action_button("btn_category", "📚 Focused Topic Practice", class_="btn"),
                    ui.input_action_button("btn_progress", "📈 View Progress", class_="btn"),
                    class_="text-center"
                ),
                class_="container"
            )
        ),
        ui.nav_panel(
            "Practice",
            ui.div(
                ui.output_ui("practice_ui"),
                class_="container"
            )
        ),
        ui.nav_panel(
            "Category Practice",
            ui.div(
                ui.output_ui("category_ui"),
                class_="container"
            )
        ),
        ui.nav_panel(
            "Progress",
            ui.div(
                ui.output_ui("progress_ui"),
                class_="container"
            )
        ),
        ui.nav_panel(
            "Quiz",
            ui.div(
                ui.output_ui("quiz_ui"),
                class_="container"
            )
        ),
        id="main_tabs"
    )
)

# ===== SERVER LOGIC =====
def server(input, output, session):
    # Reactive values
    questions = reactive.Value(load_questions())
    current_questions = reactive.Value([])
    current_index = reactive.Value(0)
    score = reactive.Value(0)
    quiz_start_time = reactive.Value(0)
    question_start_time = reactive.Value(0)
    time_spent = reactive.Value([])
    submitted = reactive.Value(False)
    quiz_mode = reactive.Value("")  # "practice", "category", "quick_quiz"
    selected_category = reactive.Value("")
    
    # Progress tracking
    progress_data = reactive.Value({
        "attempts": [],
        "scores": [],
        "time_spent": [],
        "dates": []
    })
    
    # Load progress data
    @reactive.Effect
    def _():
        try:
            with open('Data/progress_data.json') as f:
                progress_data.set(json.load(f))
        except:
            pass
    
    # Navigation handlers
    @reactive.Effect
    @reactive.event(input.btn_practice)
    def _():
        quiz_mode.set("practice")
        ui.update_navs("main_tabs", selected="Practice")
    
    @reactive.Effect
    @reactive.event(input.btn_category)
    def _():
        quiz_mode.set("category")
        ui.update_navs("main_tabs", selected="Category Practice")
    
    @reactive.Effect
    @reactive.event(input.btn_progress)
    def _():
        ui.update_navs("main_tabs", selected="Progress")
    
    # Start quiz
    def start_quiz(questions_list, mode="practice", category=""):
        current_questions.set(questions_list)
        current_index.set(0)
        score.set(0)
        quiz_start_time.set(time.time())
        question_start_time.set(time.time())
        time_spent.set([])
        submitted.set(False)
        quiz_mode.set(mode)
        selected_category.set(category)
        ui.update_navs("main_tabs", selected="Quiz")
    
    # Practice mode UI
    @output
    @render.ui
    def practice_ui():
        return ui.div(
            ui.h3("Practice Exam Options"),
            ui.div(
                ui.input_action_button("btn_easy", "📗 Easy Exam", class_="btn"),
                ui.input_action_button("btn_medium", "📘 Medium Exam", class_="btn"),
                ui.input_action_button("btn_hard", "📕 Hard Exam", class_="btn"),
                ui.input_action_button("btn_mixed", "🔀 Mixed Difficulty", class_="btn"),
                class_="text-center"
            )
        )
    
    # Category selection UI
    @output
    @render.ui
    def category_ui():
        cats = list(CATEGORIES.keys())
        return ui.div(
            ui.h3("Select a Topic Area"),
            *[
                ui.div(
                    ui.input_action_button(
                        f"btn_cat_{i}", 
                        f"{cat} ({sum(len(questions.get()[cat][d]) for d in ['easy','medium','hard'])} questions)",
                        class_="btn"
                    ),
                    class_="text-center"
                )
                for i, cat in enumerate(cats)
            ],
            ui.div(
                ui.input_action_button("btn_back_main", "← Back to Main Menu", class_="btn"),
                class_="text-center"
            )
        )
    
    # Quiz UI
    @output
    @render.ui
    def quiz_ui():
        if not current_questions.get():
            return ui.div("No questions available.")
        
        idx = current_index.get()
        if idx >= len(current_questions.get()):
            return show_results()
        
        q = current_questions.get()[idx]
        
        progress = (idx + 1) / len(current_questions.get())
        
        return ui.div(
            ui.div(
                ui.div(
                    style=f"width: {progress*100}%",
                    class_="progress-bar"
                ),
                class_="progress-container"
            ),
            ui.h4(f"Question {idx + 1} of {len(current_questions.get())}"),
            ui.p(f"Difficulty: {q.get('difficulty', 'medium').capitalize()}"),
            ui.h5(q["question"]),
            ui.input_radio_buttons(
                f"answer_{idx}",
                "Select your answer:",
                choices=q["options"],
                selected=None if not submitted.get() else q["correct_answer"]
            ),
            ui.div(
                ui.input_action_button(
                    "btn_submit" if not submitted.get() else "btn_next",
                    "Submit Answer" if not submitted.get() else "Next Question",
                    class_="btn"
                ),
                class_="text-center"
            ),
            *([
                ui.div(
                    ui.h5("✅ Correct!" if input[f"answer_{idx}"]() == q["correct_answer"] else "❌ Incorrect"),
                    ui.p(f"Correct answer: {q['correct_answer']}"),
                    ui.div(
                        ui.p(f"Explanation: {q['explanation']}"),
                        class_="explanation"
                    ) if "explanation" in q else None,
                )
            ] if submitted.get() else [])
        )
    
    # Progress UI
    @output
    @render.ui
    def progress_ui():
        data = progress_data.get()
        if not data["attempts"]:
            return ui.div(
                ui.h3("Your Progress"),
                ui.p("No progress data yet. Complete some quizzes to track your progress!"),
                ui.div(
                    ui.input_action_button("btn_back_main2", "← Back to Main Menu", class_="btn"),
                    class_="text-center"
                )
            )
        
        avg_score = sum(data["scores"]) / len(data["scores"])
        total_time = sum(data["time_spent"]) / 60  # in minutes
        
        return ui.div(
            ui.h3("Your Progress"),
            ui.div(
                ui.div(
                    ui.h5("Total Attempts"),
                    ui.h4(len(data["attempts"]))
                ),
                ui.div(
                    ui.h5("Average Score"),
                    ui.h4(f"{avg_score:.1%}")
                ),
                ui.div(
                    ui.h5("Total Study Time"),
                    ui.h4(f"{total_time:.1f} minutes")
                ),
                class_="card"
            ),
            ui.div(
                ui.input_action_button("btn_back_main2", "← Back to Main Menu", class_="btn"),
                class_="text-center"
            )
        )
    
    # Show results
    def show_results():
        total_time = time.time() - quiz_start_time.get()
        avg_time = sum(time_spent.get()) / len(time_spent.get()) if time_spent.get() else 0
        
        # Save progress
        new_progress = progress_data.get()
        new_progress["attempts"].append(len(new_progress["attempts"]) + 1)
        new_progress["scores"].append(score.get() / len(current_questions.get()))
        new_progress["time_spent"].append(total_time)
        new_progress["dates"].append(datetime.now().strftime("%Y-%m-%d"))
        
        try:
            with open('Data/progress_data.json', 'w') as f:
                json.dump(new_progress, f)
        except:
            pass
        
        progress_data.set(new_progress)
        
        return ui.div(
            ui.h3("Quiz Completed!"),
            ui.div(
                ui.div(
                    ui.h5("Score"),
                    ui.h4(f"{score.get()}/{len(current_questions.get())}")
                ),
                ui.div(
                    ui.h5("Total Time"),
                    ui.h4(format_time(total_time))
                ),
                ui.div(
                    ui.h5("Average Time per Question"),
                    ui.h4(format_time(avg_time))
                ),
                class_="card"
            ),
            ui.div(
                ui.input_action_button("btn_restart", "🔄 Take Another Quiz", class_="btn"),
                ui.input_action_button("btn_view_progress", "📈 View Progress", class_="btn"),
                ui.input_action_button("btn_return_main", "🏠 Return to Main Menu", class_="btn"),
                class_="text-center"
            )
        )
    
    # Submit answer handler
    @reactive.Effect
    @reactive.event(input.btn_submit)
    def _():
        idx = current_index.get()
        q = current_questions.get()[idx]
        
        # Calculate time spent
        spent = time.time() - question_start_time.get()
        time_spent.set([*time_spent.get(), spent])
        
        # Check answer
        if input[f"answer_{idx}"]() == q["correct_answer"]:
            score.set(score.get() + 1)
        
        submitted.set(True)
    
    # Next question handler
    @reactive.Effect
    @reactive.event(input.btn_next)
    def _():
        idx = current_index.get() + 1
        if idx < len(current_questions.get()):
            current_index.set(idx)
            question_start_time.set(time.time())
            submitted.set(False)
        else:
            # Quiz complete
            pass
    
    # Navigation buttons
    @reactive.Effect
    @reactive.event(input.btn_back_main, input.btn_back_main2, input.btn_return_main)
    def _():
        ui.update_navs("main_tabs", selected="Main Menu")
    
    @reactive.Effect
    @reactive.event(input.btn_view_progress)
    def _():
        ui.update_navs("main_tabs", selected="Progress")
    
    @reactive.Effect
    @reactive.event(input.btn_restart)
    def _():
        if quiz_mode.get() == "practice":
            ui.update_navs("main_tabs", selected="Practice")
        elif quiz_mode.get() == "category":
            ui.update_navs("main_tabs", selected="Category Practice")
    
    # Practice exam buttons
    @reactive.Effect
    @reactive.event(input.btn_easy)
    def _():
        questions_list = []
        for cat in questions.get():
            questions_list.extend(questions.get()[cat]["easy"])
        random.shuffle(questions_list)
        start_quiz(questions_list[:20], "practice", "Easy Exam")
    
    @reactive.Effect
    @reactive.event(input.btn_medium)
    def _():
        questions_list = []
        for cat in questions.get():
            questions_list.extend(questions.get()[cat]["medium"])
        random.shuffle(questions_list)
        start_quiz(questions_list[:20], "practice", "Medium Exam")
    
    @reactive.Effect
    @reactive.event(input.btn_hard)
    def _():
        questions_list = []
        for cat in questions.get():
            questions_list.extend(questions.get()[cat]["hard"])
        random.shuffle(questions_list)
        start_quiz(questions_list[:20], "practice", "Hard Exam")
    
    @reactive.Effect
    @reactive.event(input.btn_mixed)
    def _():
        questions_list = []
        for cat in questions.get():
            for diff in ["easy", "medium", "hard"]:
                questions_list.extend(questions.get()[cat][diff])
        random.shuffle(questions_list)
        start_quiz(questions_list[:20], "practice", "Mixed Exam")
    
    # Category buttons
    @reactive.Effect
    def _():
        for i, cat in enumerate(CATEGORIES.keys()):
            if input[f"btn_cat_{i}"]() > 0:
                questions_list = []
                for diff in ["easy", "medium", "hard"]:
                    questions_list.extend(questions.get()[cat][diff])
                random.shuffle(questions_list)
                start_quiz(questions_list[:20], "category", cat)

app = App(app_ui, server)
