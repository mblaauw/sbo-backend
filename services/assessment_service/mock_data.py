def generate_mock_assessments():
    """Generate mock assessment data for the assessment service"""
    
    assessments = [
        {
            "title": "Communication Fundamentals",
            "description": "Assessment to evaluate basic communication skills",
            "skill_id": 1,  # Speaking skill ID
            "difficulty_level": "easy",
            "questions": [
                {
                    "question_text": "What is the most effective way to communicate technical information to a non-technical audience?",
                    "options": [
                        "Use technical jargon to sound professional",
                        "Use simple language and analogies",
                        "Provide detailed technical specifications",
                        "Speak quickly to maintain interest"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "When communicating with a non-technical audience, using simple language and analogies helps them understand complex concepts without requiring specialized knowledge."
                },
                {
                    "question_text": "Which of these is an example of active listening?",
                    "options": [
                        "Planning what you'll say next while the other person is speaking",
                        "Looking at your phone occasionally during a conversation",
                        "Interrupting to correct inaccuracies",
                        "Paraphrasing what the speaker said to confirm understanding"
                    ],
                    "correct_answer_index": 3,
                    "explanation": "Active listening involves fully engaging with the speaker and demonstrating understanding, such as by paraphrasing their points."
                },
                {
                    "question_text": "What communication approach is most appropriate when delivering negative feedback?",
                    "options": [
                        "Be direct and critical to ensure the message is clear",
                        "Use a sandwich approach: positive-negative-positive",
                        "Send feedback via email to avoid confrontation",
                        "Focus only on what went wrong"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "The sandwich approach helps deliver constructive criticism in a way that's easier to receive and act upon."
                }
            ]
        },
        {
            "title": "Data Analysis Skills",
            "description": "Assessment to evaluate data analysis capabilities",
            "skill_id": 6,  # Numeracy skill ID
            "difficulty_level": "medium",
            "questions": [
                {
                    "question_text": "What type of chart is best for showing the distribution of a single variable?",
                    "options": [
                        "Pie chart",
                        "Scatter plot",
                        "Histogram",
                        "Line chart"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "Histograms are designed to show the distribution of a single variable, displaying the frequency of data points across different ranges or bins."
                },
                {
                    "question_text": "When analyzing skewed data, which measure of central tendency is most appropriate?",
                    "options": [
                        "Mean",
                        "Median",
                        "Mode",
                        "Range"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "The median is less affected by outliers and skewed distributions than the mean, making it more representative of the center for skewed data."
                },
                {
                    "question_text": "What is the key difference between correlation and causation?",
                    "options": [
                        "Correlation is weaker than causation",
                        "Correlation is always positive, causation can be negative",
                        "Correlation means two variables are related, causation means one variable causes the other",
                        "They are different terms for the same concept"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "Correlation indicates a relationship or association between variables, while causation specifically means that changes in one variable directly cause changes in another."
                }
            ]
        }
    ]
    
    return assessments