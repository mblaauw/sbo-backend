"""
Unified mock data generator for all SBO microservices.
This file contains functions to generate consistent test data across services.
"""
import random
from datetime import datetime, timedelta

def generate_mock_skills_taxonomy():
    """Generate mock skills data with categories"""

    # First create skill categories
    categories = [
        {"id": 1, "name": "Communication", "description": "Skills related to verbal and written communication"},
        {"id": 2, "name": "Cognitive", "description": "Skills related to thinking and problem solving"},
        {"id": 3, "name": "Technical", "description": "Technical and specialized skills"},
        {"id": 4, "name": "Leadership", "description": "Skills related to managing people and projects"},
        {"id": 5, "name": "Project Management", "description": "Skills related to project planning and execution"}
    ]
    
    skills = [
        # Communication Skills (Category 1)
        {
            "name": "Speaking",
            "description": "Ability to verbally communicate information clearly",
            "statement": "I can tell something in a way that people understand me.",
            "category_id": 1
        },
        {
            "name": "Persuasive Speaking",
            "description": "Ability to influence or inform an audience",
            "statement": "I can speak persuasively to influence or inform an audience.",
            "category_id": 1
        },
        {
            "name": "Voice Modulation",
            "description": "Ability to adapt voice and intonation to convey emotions",
            "statement": "I can adapt my voice and intonation to effectively convey emotions and intentions.",
            "category_id": 1
        },
        {
            "name": "Information Documentation",
            "description": "Ability to write information so others can understand it",
            "statement": "I can document data so that other people understand it.",
            "category_id": 1
        },
        {
            "name": "Active Listening",
            "description": "Ability to listen and summarize what was said",
            "statement": "I can listen to a conversation and ask targeted questions to gain more information.",
            "category_id": 1
        },
        
        # Cognitive Skills (Category 2)
        {
            "name": "Numeracy",
            "description": "Ability to work with numbers and solve numerical problems",
            "statement": "I can calculate and solve problems with numbers.",
            "category_id": 2
        },
        {
            "name": "Rule Application",
            "description": "Ability to apply learned rules to solve problems",
            "statement": "I can use rules I've learned to solve problems.",
            "category_id": 2
        },
        {
            "name": "Scientific Method",
            "description": "Ability to design and conduct experiments",
            "statement": "I can design and conduct experiments to investigate questions.",
            "category_id": 2
        },
        {
            "name": "Data Validation",
            "description": "Ability to assess data reliability",
            "statement": "I can evaluate the reliability of data before using it in my analysis.",
            "category_id": 2
        },
        {
            "name": "Reading Comprehension",
            "description": "Ability to read and understand written text",
            "statement": "I can read and understand written text.",
            "category_id": 2
        },
        
        # Technical Skills (Category 3)
        {
            "name": "Python Programming",
            "description": "Ability to develop applications using Python",
            "statement": "I can develop applications in Python.",
            "category_id": 3
        },
        {
            "name": "Data Analysis",
            "description": "Ability to analyze datasets and extract insights",
            "statement": "I can analyze large datasets and extract meaningful insights.",
            "category_id": 3
        },
        {
            "name": "Cloud Infrastructure",
            "description": "Ability to deploy and manage cloud resources",
            "statement": "I can deploy and manage infrastructure in cloud environments.",
            "category_id": 3
        },
        {
            "name": "SQL",
            "description": "Ability to query and manipulate databases using SQL",
            "statement": "I can write SQL queries to retrieve and manipulate data.",
            "category_id": 3
        },
        
        # Leadership Skills (Category 4)
        {
            "name": "Team Leadership",
            "description": "Ability to lead and motivate a team",
            "statement": "I can lead and motivate a team to achieve objectives.",
            "category_id": 4
        },
        {
            "name": "Strategic Thinking",
            "description": "Ability to develop and implement strategies",
            "statement": "I can develop and implement strategic plans.",
            "category_id": 4
        },
        {
            "name": "Conflict Resolution",
            "description": "Ability to resolve conflicts between team members",
            "statement": "I can help resolve conflicts between team members.",
            "category_id": 4
        },
        
        # Project Management Skills (Category 5)
        {
            "name": "Task Planning",
            "description": "Ability to break down projects into tasks",
            "statement": "I can break down projects into manageable tasks.",
            "category_id": 5
        },
        {
            "name": "Resource Allocation",
            "description": "Ability to allocate resources effectively",
            "statement": "I can allocate resources effectively to maximize productivity.",
            "category_id": 5
        },
        {
            "name": "Risk Management",
            "description": "Ability to identify and mitigate project risks",
            "statement": "I can identify and mitigate risks in projects.",
            "category_id": 5
        }
    ]
    
    return {"categories": categories, "skills": skills}

def generate_mock_users():
    """Generate mock user data with skills"""
    
    users = [
        {
            "username": "johndoe",
            "email": "john.doe@example.com",
            "full_name": "John Doe",
            "department": "Engineering",
            "title": "Software Engineer",
            "bio": "Experienced software engineer with a passion for building scalable applications.",
            "skills": [
                {"skill_id": 11, "proficiency_level": 5, "is_verified": True, "source": "assessment"},  # Python
                {"skill_id": 12, "proficiency_level": 4, "is_verified": True, "source": "manager"},     # Data Analysis
                {"skill_id": 13, "proficiency_level": 3, "is_verified": True, "source": "assessment"},  # Cloud
                {"skill_id": 14, "proficiency_level": 4, "is_verified": False, "source": "self-assessment"}, # SQL
                {"skill_id": 6, "proficiency_level": 4, "is_verified": True, "source": "assessment"}    # Numeracy
            ]
        },
        {
            "username": "janesmith",
            "email": "jane.smith@example.com",
            "full_name": "Jane Smith",
            "department": "Marketing",
            "title": "Marketing Manager",
            "bio": "Creative marketing professional with expertise in digital campaigns.",
            "skills": [
                {"skill_id": 2, "proficiency_level": 5, "is_verified": True, "source": "assessment"},   # Persuasive Speaking
                {"skill_id": 4, "proficiency_level": 4, "is_verified": True, "source": "peer"},         # Info Documentation
                {"skill_id": 15, "proficiency_level": 4, "is_verified": True, "source": "manager"},     # Team Leadership
                {"skill_id": 16, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"} # Strategic Thinking
            ]
        },
        {
            "username": "robertjohnson",
            "email": "robert.johnson@example.com",
            "full_name": "Robert Johnson",
            "department": "Operations",
            "title": "Project Manager",
            "bio": "Certified project manager with experience in agile methodologies.",
            "skills": [
                {"skill_id": 18, "proficiency_level": 5, "is_verified": True, "source": "assessment"},  # Task Planning
                {"skill_id": 19, "proficiency_level": 4, "is_verified": True, "source": "manager"},     # Resource Allocation
                {"skill_id": 20, "proficiency_level": 4, "is_verified": True, "source": "assessment"},  # Risk Management
                {"skill_id": 15, "proficiency_level": 4, "is_verified": True, "source": "assessment"},  # Team Leadership
                {"skill_id": 17, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"} # Conflict Resolution
            ]
        },
        {
            "username": "sarahlee",
            "email": "sarah.lee@example.com",
            "full_name": "Sarah Lee",
            "department": "Data Science",
            "title": "Data Scientist",
            "bio": "Data scientist with expertise in machine learning and statistical analysis.",
            "skills": [
                {"skill_id": 11, "proficiency_level": 4, "is_verified": True, "source": "assessment"},  # Python
                {"skill_id": 12, "proficiency_level": 5, "is_verified": True, "source": "manager"},     # Data Analysis
                {"skill_id": 8, "proficiency_level": 5, "is_verified": True, "source": "assessment"},   # Scientific Method
                {"skill_id": 9, "proficiency_level": 4, "is_verified": True, "source": "assessment"},   # Data Validation
                {"skill_id": 6, "proficiency_level": 5, "is_verified": True, "source": "assessment"}    # Numeracy
            ]
        },
        {
            "username": "michaelbrown",
            "email": "michael.brown@example.com",
            "full_name": "Michael Brown",
            "department": "Sales",
            "title": "Sales Director",
            "bio": "Sales director with a track record of exceeding targets.",
            "skills": [
                {"skill_id": 1, "proficiency_level": 5, "is_verified": True, "source": "assessment"},   # Speaking
                {"skill_id": 2, "proficiency_level": 5, "is_verified": True, "source": "manager"},      # Persuasive Speaking
                {"skill_id": 5, "proficiency_level": 4, "is_verified": True, "source": "assessment"},   # Active Listening
                {"skill_id": 15, "proficiency_level": 4, "is_verified": True, "source": "manager"},     # Team Leadership
                {"skill_id": 16, "proficiency_level": 4, "is_verified": True, "source": "assessment"}   # Strategic Thinking
            ]
        }
    ]
    
    return users

def generate_mock_job_roles():
    """Generate mock job role data with skill requirements"""
    
    roles = [
        {
            "title": "Senior Software Engineer",
            "description": "Design and develop scalable applications using modern software practices.",
            "department": "Engineering",
            "required_skills": [
                {"skill_id": 11, "importance": 0.9, "minimum_proficiency": 4},  # Python Programming
                {"skill_id": 14, "importance": 0.7, "minimum_proficiency": 3},  # SQL
                {"skill_id": 13, "importance": 0.6, "minimum_proficiency": 3},  # Cloud Infrastructure
                {"skill_id": 7, "importance": 0.5, "minimum_proficiency": 3},   # Rule Application
                {"skill_id": 4, "importance": 0.4, "minimum_proficiency": 3}    # Information Documentation
            ]
        },
        {
            "title": "Data Scientist",
            "description": "Analyze data to extract insights and build predictive models.",
            "department": "Data Science",
            "required_skills": [
                {"skill_id": 12, "importance": 0.9, "minimum_proficiency": 4},  # Data Analysis
                {"skill_id": 11, "importance": 0.8, "minimum_proficiency": 4},  # Python Programming
                {"skill_id": 6, "importance": 0.8, "minimum_proficiency": 4},   # Numeracy
                {"skill_id": 8, "importance": 0.7, "minimum_proficiency": 4},   # Scientific Method
                {"skill_id": 9, "importance": 0.7, "minimum_proficiency": 4}    # Data Validation
            ]
        },
        {
            "title": "Product Manager",
            "description": "Oversee product development from conception to launch.",
            "department": "Product",
            "required_skills": [
                {"skill_id": 16, "importance": 0.8, "minimum_proficiency": 4},  # Strategic Thinking
                {"skill_id": 18, "importance": 0.8, "minimum_proficiency": 4},  # Task Planning
                {"skill_id": 1, "importance": 0.7, "minimum_proficiency": 4},   # Speaking
                {"skill_id": 5, "importance": 0.7, "minimum_proficiency": 4},   # Active Listening
                {"skill_id": 4, "importance": 0.6, "minimum_proficiency": 3}    # Information Documentation
            ]
        },
        {
            "title": "Marketing Specialist",
            "description": "Develop and implement marketing campaigns.",
            "department": "Marketing",
            "required_skills": [
                {"skill_id": 2, "importance": 0.9, "minimum_proficiency": 4},   # Persuasive Speaking
                {"skill_id": 4, "importance": 0.8, "minimum_proficiency": 4},   # Information Documentation
                {"skill_id": 16, "importance": 0.6, "minimum_proficiency": 3},  # Strategic Thinking
                {"skill_id": 18, "importance": 0.5, "minimum_proficiency": 3},  # Task Planning
                {"skill_id": 12, "importance": 0.4, "minimum_proficiency": 2}   # Data Analysis
            ]
        },
        {
            "title": "Project Manager",
            "description": "Lead projects from initiation to completion within constraints.",
            "department": "Operations",
            "required_skills": [
                {"skill_id": 18, "importance": 0.9, "minimum_proficiency": 4},  # Task Planning
                {"skill_id": 19, "importance": 0.8, "minimum_proficiency": 4},  # Resource Allocation
                {"skill_id": 20, "importance": 0.8, "minimum_proficiency": 4},  # Risk Management
                {"skill_id": 15, "importance": 0.7, "minimum_proficiency": 3},  # Team Leadership
                {"skill_id": 17, "importance": 0.7, "minimum_proficiency": 4},  # Conflict Resolution
                {"skill_id": 1, "importance": 0.6, "minimum_proficiency": 3}    # Speaking
            ]
        }
    ]
    
    return roles

def generate_mock_assessments():
    """Generate mock assessment data with questions"""
    
    assessments = [
        {
            "title": "Python Programming Assessment",
            "description": "Evaluation of Python programming skills",
            "skill_id": 11,  # Python Programming skill ID
            "difficulty_level": "medium",
            "questions": [
                {
                    "question_text": "What is the output of the following code? 'print([x for x in range(5) if x % 2 == 0])'",
                    "options": [
                        "[0, 2, 4]",
                        "[0, 1, 2, 3, 4]",
                        "[1, 3]",
                        "[2, 4]"
                    ],
                    "correct_answer_index": 0,
                    "explanation": "This list comprehension filters the range by keeping only even numbers, which are those divisible by 2 with no remainder."
                },
                {
                    "question_text": "Which of the following is NOT a built-in data type in Python?",
                    "options": [
                        "List",
                        "Dictionary",
                        "Array",
                        "Tuple"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "Array is not a built-in data type in Python. It requires the 'array' module or NumPy to use arrays. The built-in sequence types are lists, tuples, and strings."
                },
                {
                    "question_text": "What is the purpose of the __init__ method in Python?",
                    "options": [
                        "To initialize a new instance of a class",
                        "To import modules when script starts",
                        "To initialize the Python interpreter",
                        "To define static methods"
                    ],
                    "correct_answer_index": 0,
                    "explanation": "The __init__ method in Python is a special method (constructor) that is automatically called when a new instance of a class is created, used to initialize the object's attributes."
                }
            ]
        },
        {
            "title": "Data Analysis Fundamentals",
            "description": "Assessment to evaluate data analysis capabilities",
            "skill_id": 12,  # Data Analysis skill ID
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
        },
        {
            "title": "Effective Communication",
            "description": "Assessment to evaluate communication skills",
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
            "title": "Project Management Essentials",
            "description": "Assessment of core project management skills",
            "skill_id": 18,  # Task Planning skill ID
            "difficulty_level": "medium",
            "questions": [
                {
                    "question_text": "What is the critical path in project management?",
                    "options": [
                        "The most expensive sequence of tasks",
                        "The sequence of tasks that must be completed on time for the project to finish on schedule",
                        "The tasks assigned to the most critical team members",
                        "The path that has the most risk"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "The critical path is the sequence of dependent tasks that determine the shortest possible duration of a project. Any delay in critical path tasks will delay the entire project."
                },
                {
                    "question_text": "What is the purpose of a project kickoff meeting?",
                    "options": [
                        "To celebrate the start of a new project",
                        "To assign blame for previous project failures",
                        "To introduce team members, clarify roles, and align on project goals and expectations",
                        "To create a detailed project schedule"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "A project kickoff meeting brings together the team to align on the project's purpose, goals, roles, and expectations, setting the foundation for successful collaboration."
                },
                {
                    "question_text": "How should a project manager address scope creep?",
                    "options": [
                        "Automatically reject all change requests",
                        "Accept all changes to keep stakeholders happy",
                        "Evaluate change requests through a formal change control process considering impact on time, cost, and quality",
                        "Refer all changes to senior management"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "A proper change control process ensures that potential changes are evaluated for their impact on the project constraints before being approved or rejected."
                }
            ]
        }
    ]
    
    return assessments

# Function to generate random assessment results for testing
def generate_mock_assessment_results(user_count=5, assessment_count=4):
    """Generate mock assessment results for users"""
    
    results = []
    
    for user_id in range(1, user_count + 1):
        # Each user has taken some assessments
        taken_assessments = random.sample(range(1, assessment_count + 1), 
                                         random.randint(1, assessment_count))
        
        for assessment_id in taken_assessments:
            # Generate random score between 40 and 100
            score = random.randint(40, 100)
            
            # Determine proficiency level based on score
            if score >= 90:
                proficiency_level = 5
            elif score >= 80:
                proficiency_level = 4
            elif score >= 70:
                proficiency_level = 3
            elif score >= 60:
                proficiency_level = 2
            else:
                proficiency_level = 1
                
            # Generate random completion date within the last 30 days
            days_ago = random.randint(0, 30)
            completed_at = datetime.now() - timedelta(days=days_ago)
            
            results.append({
                "user_id": user_id,
                "assessment_id": assessment_id,
                "score": score,
                "proficiency_level": proficiency_level,
                "completed_at": completed_at
            })
    
    return results

# Function to generate assessment questions using LLM (mock version)
def generate_mock_llm_assessment_questions(skill_name, num_questions=3):
    """Generate mock assessment questions as if from an LLM"""
    
    # Template questions for different skills
    question_templates = {
        "Python Programming": [
            {
                "question": "What is the output of: list(filter(lambda x: x % 2 == 0, range(10)))?",
                "options": ["[0, 2, 4, 6, 8]", "[1, 3, 5, 7, 9]", "[2, 4, 6, 8]", "TypeError"],
                "correct_answer_index": 0,
                "explanation": "The filter function with the lambda keeps only even numbers from the range."
            },
            {
                "question": "Which method would you use to remove all whitespace from the beginning and end of a string?",
                "options": [".strip()", ".trim()", ".clean()", ".remove()"],
                "correct_answer_index": 0,
                "explanation": "In Python, the strip() method removes whitespace from the beginning and end of a string."
            },
            {
                "question": "What is the correct way to catch multiple exceptions in Python?",
                "options": [
                    "try: ... except (ValueError, TypeError): ...",
                    "try: ... except ValueError, TypeError: ...",
                    "try: ... catch (ValueError, TypeError): ...",
                    "try: ... except ValueError or TypeError: ..."
                ],
                "correct_answer_index": 0,
                "explanation": "The correct syntax to catch multiple exceptions is to put them in parentheses."
            }
        ],
        "Data Analysis": [
            {
                "question": "When would you use a box plot instead of a histogram?",
                "options": [
                    "When you want to show the distribution and identify outliers",
                    "When you have categorical data",
                    "When you want to show correlation between variables",
                    "When you have time-series data"
                ],
                "correct_answer_index": 0,
                "explanation": "Box plots are especially useful for showing the distribution of data while clearly identifying outliers."
            },
            {
                "question": "What test would you use to compare means between two independent groups?",
                "options": [
                    "t-test", 
                    "Chi-square test", 
                    "ANOVA", 
                    "Pearson correlation"
                ],
                "correct_answer_index": 0,
                "explanation": "A t-test is appropriate for comparing means between two independent groups."
            },
            {
                "question": "What is the purpose of data normalization?",
                "options": [
                    "To scale features to a similar range",
                    "To remove outliers from the dataset",
                    "To fill in missing values",
                    "To convert categorical data to numerical"
                ],
                "correct_answer_index": 0,
                "explanation": "Normalization scales features to a similar range, typically between 0 and 1, to prevent features with larger values from dominating the analysis."
            }
        ]
    }
    
    # Get questions for the requested skill or provide generic ones
    if skill_name in question_templates:
        questions = question_templates[skill_name]
    else:
        # Generic questions for any skill
        questions = [
            {
                "question": f"What is considered a best practice in {skill_name}?",
                "options": [
                    f"Following established {skill_name} frameworks",
                    f"Ignoring industry standards for {skill_name}",
                    f"Working in isolation when practicing {skill_name}",
                    f"Avoiding documentation of {skill_name} processes"
                ],
                "correct_answer_index": 0,
                "explanation": f"Following established frameworks and standards is generally a best practice in {skill_name}."
            },
            {
                "question": f"Which of these is NOT a key component of {skill_name}?",
                "options": [
                    "Continuous learning",
                    "Effective documentation",
                    "Avoiding feedback from others",
                    "Regular practice"
                ],
                "correct_answer_index": 2,
                "explanation": f"Seeking and incorporating feedback is an important part of improving in {skill_name}."
            },
            {
                "question": f"How would you measure success in {skill_name}?",
                "options": [
                    "Through measurable outcomes and objectives",
                    "By the number of hours spent",
                    "By comparing yourself to beginners",
                    "Success in this area cannot be measured"
                ],
                "correct_answer_index": 0,
                "explanation": f"Success in {skill_name}, like most skills, is best measured through specific, measurable outcomes and objectives."
            }
        ]
    
    # Return the requested number of questions
    return {"skill_name": skill_name, "questions": questions[:num_questions]}

# Function to mock analyzing a resume with LLM
def mock_analyze_resume(resume_text):
    """Mock function to analyze a resume and extract skills and experiences"""
    
    # Extract skills based on keywords in the resume
    skills = []
    potential_skills = [
        "Python", "JavaScript", "SQL", "Data Analysis", "Machine Learning",
        "Project Management", "Leadership", "Communication", "Marketing",
        "Sales", "Customer Service", "Problem Solving", "Java", "C++",
        "Cloud Computing", "AWS", "Azure", "Product Management"
    ]
    
    for skill in potential_skills:
        if skill.lower() in resume_text.lower() or random.random() < 0.15:
            confidence = round(random.uniform(0.6, 0.95), 2)
            # Find context by locating a substring around the skill mention
            if skill.lower() in resume_text.lower():
                start_idx = max(0, resume_text.lower().find(skill.lower()) - 30)
                end_idx = min(len(resume_text), resume_text.lower().find(skill.lower()) + len(skill) + 30)
                context = resume_text[start_idx:end_idx]
            else:
                context = ""
                
            skills.append({
                "name": skill,
                "confidence": confidence,
                "evidence": context
            })
    
    # Mock experiences based on common role patterns in resumes
    experiences = []
    
    # Look for potential job titles in the resume
    job_titles = ["Software Engineer", "Data Analyst", "Product Manager", 
                 "Project Manager", "Marketing Specialist", "Sales Representative"]
    
    for title in job_titles:
        if title.lower() in resume_text.lower() or random.random() < 0.1:
            # Create a mock experience entry
            experience = {
                "title": title,
                "company": f"Company {random.choice(['A', 'B', 'C', 'D', 'E'])}",
                "duration": f"{random.randint(1, 5)} years",
                "description": f"Worked as a {title} performing various responsibilities and projects.",
                "skills": random.sample([s["name"] for s in skills], min(3, len(skills)))
            }
            experiences.append(experience)
    
    # Mock education section
    education = [
        {
            "degree": random.choice(["Bachelor's", "Master's", "PhD"]),
            "field": random.choice(["Computer Science", "Business", "Engineering", "Marketing"]),
            "institution": random.choice(["State University", "Tech Institute", "Business School", "College of Arts"]),
            "year": random.randint(2000, 2022)
        }
    ]
    
    # Generate suggested roles based on extracted skills
    suggested_roles = []
    skill_to_role_map = {
        "Python": ["Software Engineer", "Data Scientist", "Backend Developer"],
        "JavaScript": ["Frontend Developer", "Web Developer", "Full Stack Engineer"],
        "SQL": ["Database Administrator", "Data Analyst", "Business Intelligence Analyst"],
        "Data Analysis": ["Data Analyst", "Business Analyst", "Data Scientist"],
        "Machine Learning": ["Machine Learning Engineer", "Data Scientist", "AI Researcher"],
        "Project Management": ["Project Manager", "Program Manager", "Scrum Master"],
        "Leadership": ["Team Lead", "Manager", "Director"],
        "Marketing": ["Marketing Specialist", "Brand Manager", "Digital Marketer"],
        "Sales": ["Sales Representative", "Account Executive", "Business Development Manager"]
    }
    
    # Add suggested roles based on skills
    for skill in skills:
        if skill["name"] in skill_to_role_map and random.random() < 0.7:
            suggested_roles.extend(skill_to_role_map[skill["name"]])
    
    # Remove duplicates and limit to 5 roles
    suggested_roles = list(set(suggested_roles))[:5]
    
    return {
        "skills": skills,
        "experiences": experiences,
        "education": education,
        "summary": f"Professional with skills in {', '.join([s['name'] for s in skills[:3]])}.",
        "suggested_roles": suggested_roles
    }

# Generate mock learning path
def generate_mock_learning_path(user_id, target_skills, current_skills, time_frame=None):
    """Generate a mock personalized learning path"""
    
    # Create a set of current skill names for easy lookup
    current_skill_names = {skill["name"].lower() for skill in current_skills}
    
    # Filter target skills to those not already possessed
    new_target_skills = [skill for skill in target_skills 
                         if skill["name"].lower() not in current_skill_names]
    
    steps = []
    
    # Create steps for each new skill to learn
    for skill in new_target_skills:
        skill_name = skill["name"]
        
        # Learning resources by skill type
        resources = []
        
        # Add course resources
        if random.random() < 0.9:
            resources.append({
                "type": "course",
                "name": f"Introduction to {skill_name}",
                "provider": random.choice(["Coursera", "Udemy", "edX", "LinkedIn Learning"]),
                "duration": f"{random.randint(4, 12)} hours"
            })
        
        # Add book resources
        if random.random() < 0.7:
            resources.append({
                "type": "book",
                "name": f"{skill_name} Fundamentals",
                "author": f"Dr. {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])}",
                "pages": random.randint(200, 500)
            })
        
        # Add practice project
        if random.random() < 0.8:
            resources.append({
                "type": "project",
                "name": f"Hands-on {skill_name} Project",
                "description": f"Apply {skill_name} concepts to solve a real-world problem",
                "estimated_hours": random.randint(10, 40)
            })
        
        # Ensure at least one resource
        if not resources:
            resources.append({
                "type": "course",
                "name": f"Learn {skill_name}",
                "provider": "Online Academy",
                "duration": "8 hours"
            })
        
        # Create learning step
        steps.append({
            "name": f"Learn {skill_name}",
            "description": f"Develop proficiency in {skill_name} through structured learning and practice",
            "duration": f"{random.randint(2, 8)} weeks",
            "resources": resources,
            "skills_addressed": [skill_name]
        })
    
    # If all target skills are already possessed, suggest advanced learning
    if not new_target_skills:
        advanced_resources = [
            {
                "type": "course",
                "name": "Advanced Applications in Your Field",
                "provider": "Professional Academy",
                "duration": "20 hours"
            },
            {
                "type": "mentorship",
                "name": "Expert Mentorship Program",
                "description": "One-on-one guidance from industry experts",
                "duration": "3 months"
            }
        ]
        
        steps = [{
            "name": "Advanced Skill Enhancement",
            "description": "Deepen your existing skills through practical application",
            "duration": "4 weeks",
            "resources": advanced_resources,
            "skills_addressed": [skill["name"] for skill in current_skills[:3]]
        }]
    
    # Calculate total duration
    total_weeks = sum([int(step["duration"].split()[0]) for step in steps])
    
    return {
        "user_id": user_id,
        "title": "Personalized Skill Development Plan",
        "description": f"A customized learning path to help you acquire {len(new_target_skills)} new skills",
        "total_duration": f"{total_weeks} weeks",
        "steps": steps
    }