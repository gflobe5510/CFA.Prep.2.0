from shiny import App, reactive, render, ui
from shinywidgets import output_widget
import time

# Simplified working version with correct navigation
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .btn {
                background-color: #3498db !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
            }
            .card {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 15px;
            }
        """)
    ),
    ui.navset_pill(
        ui.nav_panel("Main Menu", 
            ui.div(
                ui.h2("CFA Exam Prep Pro"),
                ui.div(
                    ui.h4("Welcome!"),
                    class_="card"
                ),
                ui.input_action_button("btn_practice", "Start Practice", class_="btn"),
                ui.input_action_button("btn_progress", "View Progress", class_="btn")
            )
        ),
        ui.nav_panel("Practice", 
            ui.div(
                ui.h3("Practice Mode"),
                class_="card"
            )
        ),
        ui.nav_panel("Progress",
            ui.div(
                ui.h3("Your Progress"),
                class_="card"
            )
        ),
        id="main_tabs"
    )
)

def server(input, output, session):
    @reactive.Effect
    @reactive.event(input.btn_practice)
    def _():
        ui.update_navs("main_tabs", selected="Practice")
    
    @reactive.Effect
    @reactive.event(input.btn_progress)
    def _():
        ui.update_navs("main_tabs", selected="Progress")

app = App(app_ui, server)
