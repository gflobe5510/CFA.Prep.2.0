library(shiny)
library(shinythemes)
library(ggplot2)
library(jsonlite)
library(dplyr)
library(purrr)
library(DT)
library(plotly)

# ===== CFA CONFIGURATION =====
QUIZ_TITLE <- "CFA Exam Preparation Pro"
CFA_REGISTRATION_URL <- "https://www.cfainstitute.org/"
STUDY_GUIDE_PATH <- "Data/CFA_Study_Guide.pdf"
REGISTRATION_TIPS <- HTML("• Early registration discounts available<br>• Prepare payment method in advance<br>• Have identification documents ready<br>• Check exam schedule carefully")

# Topic mapping
TOPIC_TO_CATEGORY <- list(
  "Ethical & Professional Standards" = "Ethical and Professional Standards",
  "Quantitative Methods" = "Quantitative Methods",
  "Economics" = "Economics",
  "Financial Reporting & Analysis" = "Financial Statement Analysis",
  "Corporate Issuers" = "Corporate Issuers",
  "Equity Investments" = "Equity Investments",
  "Fixed Income" = "Fixed Income",
  "Derivatives" = "Derivatives",
  "Alternative Investments" = "Alternative Investments",
  "Portfolio Management" = "Portfolio Management"
)

# Categories data
CATEGORIES <- list(
  "Ethical and Professional Standards" = list(
    description = "Focuses on ethical principles and professional standards",
    weight = 0.15
  ),
  "Quantitative Methods" = list(
    description = "Covers statistical tools for financial analysis",
    weight = 0.10
  ),
  "Economics" = list(
    description = "Examines macroeconomic and microeconomic concepts",
    weight = 0.10
  ),
  "Financial Statement Analysis" = list(
    description = "Analysis of financial statements",
    weight = 0.15
  ),
  "Corporate Issuers" = list(
    description = "Characteristics of corporate issuers",
    weight = 0.10
  ),
  "Equity Investments" = list(
    description = "Valuation of equity securities",
    weight = 0.11
  ),
  "Fixed Income" = list(
    description = "Analysis of fixed-income securities",
    weight = 0.11
  ),
  "Derivatives" = list(
    description = "Valuation of derivative securities",
    weight = 0.06
  ),
  "Alternative Investments" = list(
    description = "Hedge funds, private equity, real estate",
    weight = 0.06
  ),
  "Portfolio Management" = list(
    description = "Portfolio construction and risk management",
    weight = 0.06
  )
)

# ===== HELPER FUNCTIONS =====
format_time <- function(seconds) {
  sprintf("%02d:%02d", seconds %/% 60, round(seconds %% 60))
}

# ===== LOAD QUESTIONS =====
load_questions <- function() {
  tryCatch({
    questions_data <- fromJSON('Data/updated_questions_with_5_options_final.json')
    
    questions_by_category <- map(names(CATEGORIES), ~list(easy = list(), medium = list(), hard = list())) %>%
      set_names(names(CATEGORIES))
    
    if ("questions" %in% names(questions_data)) {
      for (question in questions_data$questions) {
        topic <- ifelse(is.null(question$topic), "", trimws(question$topic))
        category <- ifelse(topic %in% names(TOPIC_TO_CATEGORY), 
                          TOPIC_TO_CATEGORY[[topic]], topic)
        difficulty <- ifelse(is.null(question$difficulty), "medium", tolower(question$difficulty))
        
        if (category %in% names(questions_by_category) && difficulty %in% c('easy', 'medium', 'hard')) {
          questions_by_category[[category]][[difficulty]] <- c(questions_by_category[[category]][[difficulty]], list(question))
        }
      }
    }
    
    return(questions_by_category)
  }, error = function(e) {
    showNotification(paste("Error loading questions:", e$message), type = "error")
    return(map(names(CATEGORIES), ~list(easy = list(), medium = list(), hard = list())) %>% set_names(names(CATEGORIES)))
  })
}

# ===== SHINY APP =====
ui <- fluidPage(
  theme = shinytheme("flatly"),
  tags$head(
    tags$style(HTML("
      /* Global background image */
      body {
        background-image: url('Data/background.jpg');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
      }
      
      /* Overlay to improve text visibility */
      .container-fluid {
        background-color: rgba(255, 255, 255, 0.85) !important;
        padding: 2rem;
        border-radius: 10px;
      }
      
      /* Button styling */
      .btn {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
      }
      
      .btn:hover {
        background-color: #2980b9 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
      }
      
      .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
      }
      
      .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
      }
    "))
  ),
  
  # Main app UI
  uiOutput("main_ui")
)

server <- function(input, output, session) {
  # Initialize reactive values
  rv <- reactiveValues(
    quiz = list(
      all_questions = load_questions(),
      current_questions = list(),
      score = 0,
      current_index = 1,
      user_answer = NULL,
      submitted = FALSE,
      start_time = Sys.time(),
      question_start = Sys.time(),
      time_spent = numeric(0),
      mode = "main_menu",
      selected_category = NULL,
      test_type = NULL,
      exam_number = NULL
    ),
    progress = list(
      attempts = numeric(0),
      scores = numeric(0),
      time_spent = numeric(0),
      dates = character(0),
      registration_clicks = 0,
      last_registration_click = NULL
    )
  )
  
  # Load progress data
  observe({
    tryCatch({
      if (file.exists("Data/progress_data.json")) {
        rv$progress <- fromJSON("Data/progress_data.json")
      }
    }, error = function(e) {
      showNotification(paste("Error loading progress data:", e$message), type = "error")
    })
  })
  
  # Save progress data
  save_progress <- function(score, total_questions, total_time) {
    rv$progress$attempts <- c(rv$progress$attempts, length(rv$progress$attempts) + 1
    rv$progress$scores <- c(rv$progress$scores, score/total_questions)
    rv$progress$time_spent <- c(rv$progress$time_spent, total_time)
    rv$progress$dates <- c(rv$progress$dates, format(Sys.time(), "%Y-%m-%d"))
    
    tryCatch({
      write_json(rv$progress, "Data/progress_data.json", auto_unbox = TRUE)
    }, error = function(e) {
      showNotification("Could not save progress data", type = "error")
    })
  }
  
  # Track registration click
  track_registration_click <- function() {
    rv$progress$registration_clicks <- rv$progress$registration_clicks + 1
    rv$progress$last_registration_click <- Sys.time()
    save_progress(0, 1, 0)
  }
  
  # ===== QUIZ FUNCTIONS =====
  start_random_mix <- function() {
    questions <- list()
    for (category in names(CATEGORIES)) {
      for (difficulty in c('easy', 'medium', 'hard')) {
        category_questions <- rv$quiz$all_questions[[category]][[difficulty]]
        if (length(category_questions) > 0) {
          questions <- c(questions, category_questions)
        }
      }
    }
    
    if (length(questions) == 0) {
      showNotification("No questions available", type = "error")
      return()
    }
    
    questions <- sample(questions, min(20, length(questions)))
    
    rv$quiz$current_questions <- questions
    rv$quiz$current_index <- 1
    rv$quiz$mode <- "question"
    rv$quiz$selected_category <- "Random Mix"
    rv$quiz$question_start <- Sys.time()
    rv$quiz$submitted <- FALSE
    rv$quiz$score <- 0
    rv$quiz$time_spent <- numeric(0)
    rv$quiz$test_type <- "random_mix"
  }
  
  start_quick_quiz <- function() {
    questions <- list()
    for (category in names(CATEGORIES)) {
      for (difficulty in c('easy', 'medium', 'hard')) {
        category_questions <- rv$quiz$all_questions[[category]][[difficulty]]
        if (length(category_questions) > 0) {
          questions <- c(questions, category_questions)
        }
      }
    }
    
    if (length(questions) < 5) {
      showNotification("Not enough questions available", type = "error")
      return()
    }
    
    questions <- sample(questions, 5)
    
    rv$quiz$current_questions <- questions
    rv$quiz$current_index <- 1
    rv$quiz$mode <- "question"
    rv$quiz$selected_category <- "Quick Quiz"
    rv$quiz$question_start <- Sys.time()
    rv$quiz$submitted <- FALSE
    rv$quiz$score <- 0
    rv$quiz$time_spent <- numeric(0)
    rv$quiz$test_type <- "quick_quiz"
  }
  
  start_super_hard_exam <- function() {
    questions <- list()
    for (category in names(CATEGORIES)) {
      category_questions <- rv$quiz$all_questions[[category]]$hard
      if (length(category_questions) > 0) {
        questions <- c(questions, sample(category_questions, min(3, length(category_questions))))
      }
    }
    
    if (length(questions) == 0) {
      showNotification("No hard questions available", type = "error")
      return()
    }
    
    questions <- sample(questions)
    
    rv$quiz$current_questions <- questions
    rv$quiz$current_index <- 1
    rv$quiz$mode <- "question"
    rv$quiz$selected_category <- "Super Hard Exam"
    rv$quiz$question_start <- Sys.time()
    rv$quiz$submitted <- FALSE
    rv$quiz$score <- 0
    rv$quiz$time_spent <- numeric(0)
    rv$quiz$test_type <- "super_hard"
  }
  
  start_balanced_exam <- function(exam_number) {
    questions <- list()
    target_per_difficulty <- 10
    
    for (difficulty in c('easy', 'medium', 'hard')) {
      difficulty_questions <- list()
      for (category in names(CATEGORIES)) {
        cat_questions <- rv$quiz$all_questions[[category]][[difficulty]]
        if (length(cat_questions) > 0) {
          difficulty_questions <- c(difficulty_questions, sample(cat_questions, min(2, length(cat_questions))))
        }
      }
      
      if (length(difficulty_questions) > 0) {
        questions <- c(questions, sample(difficulty_questions, min(target_per_difficulty, length(difficulty_questions))))
      }
    }
    
    if (length(questions) < 15) {
      showNotification("Not enough questions available for a balanced exam", type = "error")
      return()
    }
    
    questions <- sample(questions)
    
    rv$quiz$current_questions <- questions
    rv$quiz$current_index <- 1
    rv$quiz$mode <- "question"
    rv$quiz$selected_category <- paste("Balanced Exam", exam_number)
    rv$quiz$question_start <- Sys.time()
    rv$quiz$submitted <- FALSE
    rv$quiz$score <- 0
    rv$quiz$time_spent <- numeric(0)
    rv$quiz$test_type <- "balanced_exam"
    rv$quiz$exam_number <- exam_number
  }
  
  start_practice_test <- function(difficulty) {
    questions <- list()
    for (category in names(CATEGORIES)) {
      category_questions <- rv$quiz$all_questions[[category]][[difficulty]]
      if (length(category_questions) > 0) {
        questions <- c(questions, sample(category_questions, min(2, length(category_questions))))
      }
    }
    
    if (length(questions) == 0) {
      showNotification(paste("No", difficulty, "questions available for practice test"), type = "error")
      return()
    }
    
    questions <- sample(questions)
    
    rv$quiz$current_questions <- questions
    rv$quiz$current_index <- 1
    rv$quiz$mode <- "question"
    rv$quiz$selected_category <- paste(toupper(substring(difficulty, 1, 1), substring(difficulty, 2), "Exam")
    rv$quiz$question_start <- Sys.time()
    rv$quiz$submitted <- FALSE
    rv$quiz$score <- 0
    rv$quiz$time_spent <- numeric(0)
    rv$quiz$test_type <- "practice_test"
  }
  
  process_answer <- function(question, user_answer) {
    time_spent <- as.numeric(difftime(Sys.time(), rv$quiz$question_start, units = "secs"))
    rv$quiz$time_spent <- c(rv$quiz$time_spent, time_spent)
    rv$quiz$submitted <- TRUE
    
    if (user_answer == question$correct_answer) {
      rv$quiz$score <- rv$quiz$score + 1
      showNotification("✅ Correct!", type = "message")
    } else {
      showNotification(paste("❌ Incorrect. The correct answer is:", question$correct_answer), type = "error")
    }
  }
  
  # ===== UI RENDER FUNCTIONS =====
  output$main_ui <- renderUI({
    switch(
      rv$quiz$mode,
      "main_menu" = main_menu_ui(),
      "progress_tracking" = progress_tracking_ui(),
      "difficulty_selection" = difficulty_selection_ui(),
      "category_selection" = category_selection_ui(),
      "question" = question_ui()
    )
  })
  
  main_menu_ui <- function() {
    tagList(
      div(
        style = "display: flex; align-items: center; margin-bottom: 30px;",
        h1(QUIZ_TITLE, style = "margin: 0;")
      ),
      
      # Stats summary card
      div(
        class = "card",
        h3("CFA Level I Exam Preparation Pro", style = "color: #2c3e50; margin-top: 0;"),
        if (length(rv$progress$attempts) {
          tagList(
            p(paste("Total attempts:", length(rv$progress$attempts))),
            p(paste("Average score:", sprintf("%.1f%%", mean(rv$progress$scores) * 100))
          )
        } else {
          p("Complete your first quiz to see stats")
        }
      ),
      
      # Resources section
      div(
        class = "card",
        h3("📚 Study Resources", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      fluidRow(
        column(4,
               if (file.exists(STUDY_GUIDE_PATH)) {
                 downloadButton("download_guide", "📘 Download Study Guide", class = "btn", style = "width: 100%;")
               } else {
                 div(class = "alert alert-warning", "Study guide not found")
               }
        ),
        column(4,
               actionButton("register_btn", "🌐 Register for CFA Exam", 
                           class = "btn", style = "width: 100%;",
                           title = REGISTRATION_TIPS)
        ),
        column(4,
               actionButton("progress_btn", "📈 View Progress Dashboard", 
                           class = "btn", style = "width: 100%;")
        )
      ),
      
      # Practice options
      div(
        class = "card",
        h3("🎯 Practice Options", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      fluidRow(
        column(6,
               actionButton("custom_exam_btn", "📝 Custom Practice Exam",
                            class = "btn", style = "width: 100%;",
                            title = "Tailored exams by difficulty and topic")
        ),
        column(6,
               actionButton("topic_practice_btn", "📚 Focused Topic Practice",
                            class = "btn", style = "width: 100%;",
                            title = "Drill specific CFA topics")
        )
      )
    )
  }
  
  progress_tracking_ui <- function() {
    tagList(
      div(
        class = "card",
        h2("Your Study Progress", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      if (length(rv$progress$attempts) == 0) {
        div(
          class = "card",
          p("No progress data yet. Complete some quizzes to track your progress!"),
          actionButton("back_to_menu_from_progress", "← Back to Main Menu", 
                       class = "btn", style = "width: 100%;")
        )
      } else {
        tagList(
          # Progress Metrics
          div(
            class = "card",
            h3("Progress Overview", style = "color: #2c3e50; margin-top: 0;")
          ),
          
          fluidRow(
            column(4,
                   div(
                     class = "metric-card",
                     div("Total Attempts", style = "font-size: 16px; color: #7f8c8d;"),
                     div(length(rv$progress$attempts), style = "font-size: 24px; font-weight: bold; color: #2c3e50;")
                   )
            ),
            column(4,
                   div(
                     class = "metric-card",
                     div("Average Score", style = "font-size: 16px; color: #7f8c8d;"),
                     div(sprintf("%.1f%%", mean(rv$progress$scores) * 100), 
                         style = "font-size: 24px; font-weight: bold; color: #2c3e50;")
                   )
            ),
            column(4,
                   div(
                     class = "metric-card",
                     div("Total Study Time", style = "font-size: 16px; color: #7f8c8d;"),
                     div(paste(round(sum(rv$progress$time_spent)/60, "min"), 
                         style = "font-size: 24px; font-weight: bold; color: #2c3e50;")
                   )
            )
          ),
          
          # Registration Stats
          div(
            class = "card",
            h3("Registration Interest", style = "color: #2c3e50; margin-top: 0;")
          ),
          
          fluidRow(
            column(6,
                   div(
                     class = "metric-card",
                     div("Total Registration Clicks", style = "font-size: 16px; color: #7f8c8d;"),
                     div(rv$progress$registration_clicks, 
                         style = "font-size: 24px; font-weight: bold; color: #2c3e50;")
                   )
            ),
            column(6,
                   div(
                     class = "metric-card",
                     div("Last Registration Click", style = "font-size: 16px; color: #7f8c8d;"),
                     div(ifelse(is.null(rv$progress$last_registration_click), "Never",
                                format(as.POSIXct(rv$progress$last_registration_click), "%Y-%m-%d %H:%M")), 
                         style = "font-size: 24px; font-weight: bold; color: #2c3e50;")
                   )
            )
          ),
          
          # Progress Charts
          div(
            class = "card",
            h3("Progress Charts", style = "color: #2c3e50; margin-top: 0;")
          ),
          
          plotOutput("progress_plot"),
          
          # Detailed Progress Table
          div(
            class = "card",
            h3("Detailed Progress History", style = "color: #2c3e50; margin-top: 0;")
          ),
          
          DTOutput("progress_table"),
          
          actionButton("back_to_menu_from_progress", "← Back to Main Menu", 
                       class = "btn", style = "width: 100%; margin-top: 20px;")
        )
      }
    )
  }
  
  difficulty_selection_ui <- function() {
    tagList(
      div(
        class = "card",
        h2("Select Practice Exam Type", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      div(
        class = "card",
        h3("Balanced Exams (Mixed Difficulty)", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      fluidRow(
        lapply(1:5, function(i) {
          column(2,
                 actionButton(paste0("balanced_exam_", i), 
                              paste("Balanced Exam", i),
                              class = "btn", style = "width: 100%; margin-bottom: 10px;",
                              title = "1/3 Easy, 1/3 Medium, 1/3 Hard questions")
          )
        })
      ),
      
      div(
        class = "card",
        h3("Specialized Exams", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      fluidRow(
        column(3,
               actionButton("easy_exam_btn", "📗 Easy Exam",
                            class = "btn", style = "width: 100%;")
        ),
        column(3,
               actionButton("medium_exam_btn", "📘 Medium Exam",
                            class = "btn", style = "width: 100%;")
        ),
        column(3,
               actionButton("hard_exam_btn", "📕 Hard Exam",
                            class = "btn", style = "width: 100%;")
        ),
        column(3,
               actionButton("super_hard_btn", "💀 Super Hard",
                            class = "btn", style = "width: 100%;",
                            title = "Only the most challenging questions")
        )
      ),
      
      div(
        class = "card",
        h3("Quick Practice", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      fluidRow(
        column(6,
               actionButton("quick_quiz_btn", "🎯 Quick Quiz",
                            class = "btn", style = "width: 100%;",
                            title = "5 random questions from all categories")
        ),
        column(6,
               actionButton("random_mix_btn", "🔀 Random Mix",
                            class = "btn", style = "width: 100%;",
                            title = "Completely random question selection")
        )
      ),
      
      actionButton("back_to_menu_from_difficulty", "← Back to Main Menu", 
                   class = "btn", style = "width: 100%; margin-top: 20px;")
    )
  }
  
  category_selection_ui <- function() {
    tagList(
      div(
        class = "card",
        h2("Select a CFA Topic Area", style = "color: #2c3e50; margin-top: 0;")
      ),
      
      fluidRow(
        lapply(seq_along(names(CATEGORIES)), function(i) {
          category <- names(CATEGORIES)[i]
          total_questions <- sum(map_int(rv$quiz$all_questions[[category]], length))
          
          column(6,
                 actionButton(paste0("category_", gsub(" ", "_", tolower(category))),
                              paste(category, "(", total_questions, "questions)"),
                              class = "btn", style = "width: 100%; margin-bottom: 10px;",
                              disabled = total_questions == 0,
                              title = CATEGORIES[[category]]$description)
          )
        })
      ),
      
      actionButton("back_to_menu_from_category", "← Back to Main Menu", 
                   class = "btn", style = "width: 100%; margin-top: 20px;")
    )
  }
  
  question_ui <- function() {
    if (length(rv$quiz$current_questions) == 0) {
      showNotification("No questions available", type = "error")
      rv$quiz$mode <- "main_menu"
      return(main_menu_ui())
    }
    
    if (rv$quiz$current_index > length(rv$quiz$current_questions)) {
      return(show_results_ui())
    }
    
    question <- rv$quiz$current_questions[[rv$quiz$current_index]]
    
    tagList(
      progressBar(
        id = "quiz_progress",
        value = rv$quiz$current_index / length(rv$quiz$current_questions) * 100,
        display_pct = TRUE
      ),
      
      h3(switch(
        rv$quiz$test_type,
        "balanced_exam" = paste("Balanced Exam", rv$quiz$exam_number),
        "practice_test" = rv$quiz$selected_category,
        "super_hard" = "Super Hard Exam",
        "quick_quiz" = "Quick Quiz",
        "random_mix" = "Random Mix",
        rv$quiz$selected_category
      )),
      
      h4(paste("Question", rv$quiz$current_index, "of", length(rv$quiz$current_questions))),
      
      if (!is.null(question$difficulty)) {
        p(em(paste("Difficulty:", tools::toTitleCase(question$difficulty))))
      },
      
      p(em(question$question)),
      
      radioButtons(
        "user_answer", 
        "Select your answer:",
        choices = question$options,
        selected = character(0)
      ),
      
      if (!rv$quiz$submitted) {
        actionButton("submit_answer", "Submit Answer", class = "btn", style = "width: 100%;")
      } else {
        tagList(
          if ("explanation" %in% names(question)) {
            div(
              class = "alert alert-info",
              strong("Explanation:"), question$explanation
            )
          },
          actionButton("next_question", "Next Question", class = "btn", style = "width: 100%;")
        )
      }
    )
  }
  
  show_results_ui <- function() {
    total_time <- as.numeric(difftime(Sys.time(), rv$quiz$start_time, units = "secs"))
    avg_time <- ifelse(length(rv$quiz$time_spent) > 0, 
                      mean(rv$quiz$time_spent), 0)
    
    save_progress(rv$quiz$score, length(rv$quiz$current_questions), total_time)
    
    tagList(
      div(
        class = "card",
        h2("Quiz Completed!", style = "color: #2c3e50; margin-top: 0;"),
        div(
          style = "display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0;",
          div(
            class = "metric-card",
            div("Score", style = "font-size: 16px; color: #7f8c8d;"),
            div(paste(rv$quiz$score, "/", length(rv$quiz$current_questions)), 
                style = "font-size: 32px; font-weight: bold; color: #2c3e50;")
          ),
          div(
            class = "metric-card",
            div("Total Time", style = "font-size: 16px; color: #7f8c8d;"),
            div(format_time(total_time), 
                style = "font-size: 32px; font-weight: bold; color: #2c3e50;")
          ),
          div(
            class = "metric-card",
            div("Avg/Question", style = "font-size: 16px; color: #7f8c8d;"),
            div(format_time(avg_time), 
                style = "font-size: 32px; font-weight: bold; color: #2c3e50;")
          )
        )
      ),
      
      plotOutput("result_chart"),
      
      fluidRow(
        column(6,
               actionButton("return_to_menu", "Return to Main Menu", 
                           class = "btn", style = "width: 100%;")
        ),
        column(6,
               actionButton("view_progress", "View Progress Dashboard", 
                           class = "btn", style = "width: 100%;")
        )
      )
    )
  }
  
  # ===== OUTPUT RENDER FUNCTIONS =====
  output$result_chart <- renderPlot({
    score <- rv$quiz$score / length(rv$quiz$current_questions)
    df <- data.frame(
      Metric = c("Your Score", "Benchmark"),
      Value = c(score, 0.75)
    )
    
    ggplot(df, aes(x = Metric, y = Value, fill = Metric)) +
      geom_col() +
      scale_fill_manual(values = c("#3498db", "#95a5a6")) +
      ylim(0, 1) +
      theme_minimal() +
      theme(legend.position = "none")
  })
  
  output$progress_plot <- renderPlot({
    req(length(rv$progress$attempts) > 0)
    
    df <- data.frame(
      Attempt = rv$progress$attempts,
      Score = rv$progress$scores,
      Time = rv$progress$time_spent
    )
    
    p1 <- ggplot(df, aes(x = Attempt, y = Score)) +
      geom_line(color = "#3498db") +
      geom_point(color = "#3498db") +
      ggtitle("Score Improvement Over Time") +
      ylab("Score (%)") +
      ylim(0, 1) +
      theme_minimal()
    
    p2 <- ggplot(df, aes(x = Attempt, y = Time)) +
      geom_col(fill = "#3498db") +
      ggtitle("Time Spent per Attempt") +
      ylab("Time (seconds)") +
      theme_minimal()
    
    gridExtra::grid.arrange(p1, p2, ncol = 2)
  })
  
  output$progress_table <- renderDT({
    req(length(rv$progress$attempts) > 0)
    
    df <- data.frame(
      Attempt = rv$progress$attempts,
      Date = rv$progress$dates,
      Score = sprintf("%.1f%%", rv$progress$scores * 100),
      Time_Spent = paste(floor(rv$progress$time_spent / 60), "m", 
                         round(rv$progress$time_spent %% 60), "s")
    )
    
    datatable(df, options = list(pageLength = 5))
  })
  
  output$download_guide <- downloadHandler(
    filename = function() {
      "CFA_Study_Guide.pdf"
    },
    content = function(file) {
      file.copy(STUDY_GUIDE_PATH, file)
    }
  )
  
  # ===== EVENT HANDLERS =====
  observeEvent(input$register_btn, {
    track_registration_click()
    js <- paste0("window.open('", CFA_REGISTRATION_URL, "', '_blank')")
    runjs(js)
  })
  
  observeEvent(input$progress_btn, {
    rv$quiz$mode <- "progress_tracking"
  })
  
  observeEvent(input$custom_exam_btn, {
    rv$quiz$mode <- "difficulty_selection"
  })
  
  observeEvent(input$topic_practice_btn, {
    rv$quiz$mode <- "category_selection"
  })
  
  observeEvent(input$back_to_menu_from_progress, {
    rv$quiz$mode <- "main_menu"
  })
  
  observeEvent(input$back_to_menu_from_difficulty, {
    rv$quiz$mode <- "main_menu"
  })
  
  observeEvent(input$back_to_menu_from_category, {
    rv$quiz$mode <- "main_menu"
  })
  
  observeEvent(input$easy_exam_btn, {
    start_practice_test("easy")
  })
  
  observeEvent(input$medium_exam_btn, {
    start_practice_test("medium")
  })
  
  observeEvent(input$hard_exam_btn, {
    start_practice_test("hard")
  })
  
  observeEvent(input$super_hard_btn, {
    start_super_hard_exam()
  })
  
  observeEvent(input$quick_quiz_btn, {
    start_quick_quiz()
  })
  
  observeEvent(input$random_mix_btn, {
    start_random_mix()
  })
  
  lapply(1:5, function(i) {
    observeEvent(input[[paste0("balanced_exam_", i)]], {
      start_balanced_exam(i)
    })
  })
  
  lapply(seq_along(names(CATEGORIES)), function(i) {
    category <- names(CATEGORIES)[i]
    observeEvent(input[[paste0("category_", gsub(" ", "_", tolower(category))]], {
      questions <- list()
      for (difficulty in c('easy', 'medium', 'hard')) {
        questions <- c(questions, rv$quiz$all_questions[[category]][[difficulty]])
      }
      
      rv$quiz$current_questions <- questions
      rv$quiz$current_index <- 1
      rv$quiz$mode <- "question"
      rv$quiz$selected_category <- category
      rv$quiz$question_start <- Sys.time()
      rv$quiz$submitted <- FALSE
      rv$quiz$score <- 0
      rv$quiz$time_spent <- numeric(0)
      rv$quiz$test_type <- "category"
    })
  })
  
  observeEvent(input$submit_answer, {
    req(input$user_answer)
    question <- rv$quiz$current_questions[[rv$quiz$current_index]]
    process_answer(question, input$user_answer)
  })
  
  observeEvent(input$next_question, {
    rv$quiz$current_index <- rv$quiz$current_index + 1
    rv$quiz$submitted <- FALSE
    rv$quiz$question_start <- Sys.time()
  })
  
  observeEvent(input$return_to_menu, {
    rv$quiz$mode <- "main_menu"
  })
  
  observeEvent(input$view_progress, {
    rv$quiz$mode <- "progress_tracking"
  })
}

shinyApp(ui, server)
