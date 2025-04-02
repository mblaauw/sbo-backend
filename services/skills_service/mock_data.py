
# skills_service/mock_data.py
def generate_mock_skills_taxonomy():
    """Generate mock skills data based on the document's taxonomy"""
    
    skills = [
        # Communicative Skills
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
        
        # Cognitive and Analytical Skills
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
        {
            "name": "Active Learning",
            "description": "Ability to acquire work-relevant knowledge",
            "statement": "I can acquire knowledge important for my work through thinking, discussing, researching, and creating.",
            "category_id": 2
        },
        {
            "name": "Comparative Analysis",
            "description": "Ability to compare advantages and disadvantages",
            "statement": "I can compare the pros and cons of different options.",
            "category_id": 2
        },
        {
            "name": "Decision Making",
            "description": "Ability to determine the best option",
            "statement": "I can determine what the best option is.",
            "category_id": 2
        },
        {
            "name": "Ethical Reasoning",
            "description": "Ability to integrate ethical considerations in decision-making",
            "statement": "I can integrate ethical considerations in my decision-making process.",
            "category_id": 2
        },
    ]
    
    return skills