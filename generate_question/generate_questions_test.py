import json
import random
from typing import List, Dict, Any

class MockOpenAI:
    """Mock OpenAI client that returns realistic sample responses"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.chat = MockChatCompletions()

class MockChatCompletions:
    def create(self, model: str, messages: List[Dict], temperature: float = 0.3, max_tokens: int = None):
        """Mock the chat completions create method"""
        
        # Get the user's prompt to determine what type of response to generate
        user_message = messages[-1]["content"] if messages else ""
        
        if "TASK 1 - TOPIC ANALYSIS" in user_message:
            # This is a topic analysis request
            return self._mock_topic_analysis_response(user_message)
        elif "You are an expert question designer" in user_message:
            # This is a question generation request
            return self._mock_question_generation_response(user_message)
        else:
            # Default response
            return MockResponse('{"error": "Unknown request type"}')
    
    def _mock_topic_analysis_response(self, prompt: str) -> 'MockResponse':
        """Generate mock topic analysis based on the prompt"""
        
        # Extract topic from prompt (simple heuristic)
        topic = "Sample Topic"
        if 'learning goal:' in prompt:
            start = prompt.find('learning goal: "') + len('learning goal: "')
            end = prompt.find('"', start)
            if end > start:
                topic = prompt[start:end]
        
        # Generate realistic analysis based on topic keywords
        if any(word in topic.lower() for word in ['finnish', 'language', 'grammar']):
            analysis = self._finnish_language_analysis(topic)
        elif any(word in topic.lower() for word in ['python', 'programming', 'coding']):
            analysis = self._python_programming_analysis(topic)
        elif any(word in topic.lower() for word in ['marketing', 'business']):
            analysis = self._marketing_analysis(topic)
        else:
            analysis = self._generic_analysis(topic)
        
        return MockResponse(json.dumps(analysis, indent=2))
    
    def _mock_question_generation_response(self, prompt: str) -> 'MockResponse':
        """Generate mock questions based on the prompt"""
        
        # Extract topic name from prompt
        topic_name = "Sample Topic"
        if 'creating assessment items for:' in prompt:
            start = prompt.find('creating assessment items for: "') + len('creating assessment items for: "')
            end = prompt.find('"', start)
            if end > start:
                topic_name = prompt[start:end]
        
        # Check if it's test mode (fewer questions)
        is_test_mode = "Generate 5 high-quality questions" in prompt
        num_questions = 5 if is_test_mode else random.randint(8, 15)
        
        questions = self._generate_sample_questions(topic_name, num_questions)
        return MockResponse(json.dumps(questions, indent=2))
    
    def _finnish_language_analysis(self, topic: str) -> Dict:
        return {
            "analysis": {
                "subject_area": "Finnish Language Learning",
                "complexity_level": "Intermediate (B1 level)",
                "learning_objectives": [
                    "Master Finnish verb conjugation patterns",
                    "Understand case system usage in context",
                    "Develop conversational fluency",
                    "Recognize and use complex sentence structures"
                ],
                "prerequisites": [
                    "Basic Finnish vocabulary (A2 level)",
                    "Understanding of nominative and partitive cases",
                    "Present tense conjugation"
                ],
                "estimated_study_hours": "60-80 hours"
            },
            "structure": {
                "main_categories": [
                    {
                        "name": "Verb System Mastery",
                        "description": "Complete understanding of Finnish verb conjugation across all tenses and moods",
                        "learning_outcomes": ["Conjugate verbs in all tenses", "Use conditional and imperative moods"],
                        "subcategories": [
                            {
                                "name": "Past Tense Forms",
                                "description": "Master imperfekt and perfekt formations",
                                "prerequisites": ["Present tense conjugation"],
                                "leaf_topics": [
                                    {
                                        "name": "Weak Grade Alternation in Past Tense",
                                        "description": "Understanding consonant gradation in past tense formation",
                                        "key_concepts": ["Consonant gradation rules", "Weak vs strong grade", "Past tense markers"],
                                        "question_strategy": {
                                            "multiple_choice": 30,
                                            "fill_in_blank": 35,
                                            "short_answer": 20,
                                            "true_false": 15
                                        },
                                        "difficulty_distribution": {
                                            "level_1": 20,
                                            "level_2": 30,
                                            "level_3": 30,
                                            "level_4": 15,
                                            "level_5": 5
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Case System Application",
                        "description": "Practical usage of Finnish cases in real communication",
                        "learning_outcomes": ["Choose correct cases in context", "Understand case meanings"],
                        "subcategories": [
                            {
                                "name": "Locative Cases",
                                "description": "Mastering inessive, elative, illative, adessive, ablative, allative",
                                "prerequisites": ["Basic case understanding"],
                                "leaf_topics": [
                                    {
                                        "name": "Movement vs Location Cases",
                                        "description": "Distinguishing when to use movement vs static location cases",
                                        "key_concepts": ["Static location", "Movement to", "Movement from"],
                                        "question_strategy": {
                                            "multiple_choice": 25,
                                            "fill_in_blank": 40,
                                            "short_answer": 25,
                                            "true_false": 10
                                        },
                                        "difficulty_distribution": {
                                            "level_1": 15,
                                            "level_2": 25,
                                            "level_3": 35,
                                            "level_4": 20,
                                            "level_5": 5
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def _python_programming_analysis(self, topic: str) -> Dict:
        return {
            "analysis": {
                "subject_area": "Computer Programming - Python",
                "complexity_level": "Beginner to Intermediate",
                "learning_objectives": [
                    "Write clean, readable Python code",
                    "Understand data structures and algorithms",
                    "Apply object-oriented programming concepts",
                    "Handle errors and exceptions properly"
                ],
                "prerequisites": [
                    "Basic computer literacy",
                    "Understanding of logical thinking",
                    "Familiarity with text editors"
                ],
                "estimated_study_hours": "40-60 hours"
            },
            "structure": {
                "main_categories": [
                    {
                        "name": "Python Fundamentals",
                        "description": "Core Python syntax and basic programming concepts",
                        "learning_outcomes": ["Write basic Python programs", "Understand variables and data types"],
                        "subcategories": [
                            {
                                "name": "Data Types and Variables",
                                "description": "Understanding Python's built-in data types",
                                "prerequisites": ["None"],
                                "leaf_topics": [
                                    {
                                        "name": "String Manipulation Methods",
                                        "description": "Master built-in string methods for text processing",
                                        "key_concepts": ["String methods", "String formatting", "String slicing"],
                                        "question_strategy": {
                                            "multiple_choice": 30,
                                            "fill_in_blank": 25,
                                            "short_answer": 30,
                                            "true_false": 15
                                        },
                                        "difficulty_distribution": {
                                            "level_1": 25,
                                            "level_2": 35,
                                            "level_3": 25,
                                            "level_4": 10,
                                            "level_5": 5
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def _marketing_analysis(self, topic: str) -> Dict:
        return {
            "analysis": {
                "subject_area": "Digital Marketing",
                "complexity_level": "Beginner to Intermediate",
                "learning_objectives": [
                    "Understand digital marketing channels",
                    "Create effective marketing campaigns",
                    "Analyze marketing metrics and ROI",
                    "Develop brand positioning strategies"
                ],
                "prerequisites": [
                    "Basic business understanding",
                    "Familiarity with social media platforms",
                    "Basic analytical thinking"
                ],
                "estimated_study_hours": "30-45 hours"
            },
            "structure": {
                "main_categories": [
                    {
                        "name": "Social Media Marketing",
                        "description": "Leveraging social platforms for business growth",
                        "learning_outcomes": ["Create engaging content", "Build social media strategy"],
                        "subcategories": [
                            {
                                "name": "Content Strategy",
                                "description": "Planning and creating effective social media content",
                                "prerequisites": ["Understanding of target audiences"],
                                "leaf_topics": [
                                    {
                                        "name": "Visual Content Creation",
                                        "description": "Designing compelling visual content for social media",
                                        "key_concepts": ["Visual hierarchy", "Brand consistency", "Platform specifications"],
                                        "question_strategy": {
                                            "multiple_choice": 35,
                                            "short_answer": 30,
                                            "true_false": 20,
                                            "fill_in_blank": 15
                                        },
                                        "difficulty_distribution": {
                                            "level_1": 30,
                                            "level_2": 30,
                                            "level_3": 25,
                                            "level_4": 10,
                                            "level_5": 5
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def _generic_analysis(self, topic: str) -> Dict:
        return {
            "analysis": {
                "subject_area": "General Knowledge",
                "complexity_level": "Intermediate",
                "learning_objectives": [
                    f"Understand key concepts in {topic}",
                    f"Apply {topic} principles in practice",
                    f"Analyze {topic} scenarios critically"
                ],
                "prerequisites": [
                    "Basic foundational knowledge",
                    "Critical thinking skills"
                ],
                "estimated_study_hours": "20-30 hours"
            },
            "structure": {
                "main_categories": [
                    {
                        "name": f"Core {topic} Concepts",
                        "description": f"Fundamental principles and ideas in {topic}",
                        "learning_outcomes": [f"Master {topic} fundamentals"],
                        "subcategories": [
                            {
                                "name": f"Basic {topic} Principles",
                                "description": f"Understanding the foundation of {topic}",
                                "prerequisites": ["General knowledge"],
                                "leaf_topics": [
                                    {
                                        "name": f"Introduction to {topic}",
                                        "description": f"Basic understanding of what {topic} encompasses",
                                        "key_concepts": ["Core principles", "Key terminology", "Basic applications"],
                                        "question_strategy": {
                                            "multiple_choice": 30,
                                            "true_false": 25,
                                            "short_answer": 25,
                                            "fill_in_blank": 20
                                        },
                                        "difficulty_distribution": {
                                            "level_1": 25,
                                            "level_2": 30,
                                            "level_3": 25,
                                            "level_4": 15,
                                            "level_5": 5
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def _generate_sample_questions(self, topic_name: str, num_questions: int) -> List[Dict]:
        """Generate sample questions based on topic"""
        
        questions = []
        question_types = ["multiple_choice", "true_false", "short_answer", "fill_in_blank"]
        
        # Sample question templates
        templates = {
            "multiple_choice": {
                "finnish": [
                    ("What is the correct past tense form of 'antaa' (to give) in first person singular?", 
                     [("annoin", True), ("annan", False), ("antaisin", False), ("olen antanut", False)]),
                    ("Which case is used after the preposition 'kanssa' (with)?", 
                     [("Genetiivi", True), ("Partitiivi", False), ("Inessiivi", False), ("Adessiivi", False)])
                ],
                "python": [
                    ("Which method removes whitespace from both ends of a string?", 
                     [("strip()", True), ("remove()", False), ("trim()", False), ("clean()", False)]),
                    ("What does the len() function return for a string?", 
                     [("Number of characters", True), ("Memory size", False), ("ASCII values", False), ("Number of words", False)])
                ],
                "generic": [
                    (f"What is a key characteristic of {topic_name}?", 
                     [("It follows established principles", True), ("It ignores basic rules", False), ("It has no structure", False), ("It cannot be learned", False)])
                ]
            },
            "true_false": {
                "finnish": [
                    ("The Finnish language has exactly 15 grammatical cases.", False),
                    ("Consonant gradation affects the stem of Finnish words.", True)
                ],
                "python": [
                    ("Python lists are mutable data structures.", True),
                    ("Strings in Python can be modified after creation.", False)
                ],
                "generic": [
                    (f"{topic_name} requires careful study to master.", True)
                ]
            },
            "short_answer": {
                "finnish": [
                    "Explain when to use the partitive case in Finnish.",
                    "Describe the difference between strong and weak consonant gradation."
                ],
                "python": [
                    "Explain the difference between a list and a tuple in Python.",
                    "What is the purpose of the __init__ method in a Python class?"
                ],
                "generic": [
                    f"Explain the main purpose of studying {topic_name}."
                ]
            },
            "fill_in_blank": {
                "finnish": [
                    "The Finnish sentence 'Minä _____ kouluun' uses the verb 'mennä' in present tense.",
                    "In the phrase 'punainen ____', the adjective agrees with the noun in case."
                ],
                "python": [
                    "To create an empty list in Python, you write: my_list = ____",
                    "The _____ function converts a string to an integer in Python."
                ],
                "generic": [
                    f"The most important aspect of {topic_name} is ____."
                ]
            }
        }
        
        # Determine topic category
        topic_lower = topic_name.lower()
        if any(word in topic_lower for word in ['finnish', 'suomi', 'grammar']):
            category = "finnish"
        elif any(word in topic_lower for word in ['python', 'programming', 'code']):
            category = "python"
        else:
            category = "generic"
        
        # Generate questions
        for i in range(num_questions):
            q_type = random.choice(question_types)
            
            if q_type == "multiple_choice":
                if category in templates[q_type] and templates[q_type][category]:
                    question_text, choices = random.choice(templates[q_type][category])
                    question = {
                        "question_text": question_text,
                        "question_type": q_type,
                        "explanation": f"This tests understanding of {topic_name} concepts.",
                        "difficulty_level": random.randint(1, 4),
                        "points": random.choice([1, 2]),
                        "cognitive_level": random.choice(["understanding", "application", "recall"]),
                        "key_concept": f"{topic_name} fundamentals",
                        "choices": [{"text": choice[0], "is_correct": choice[1]} for choice in choices]
                    }
                else:
                    continue
            
            elif q_type == "true_false":
                if category in templates[q_type] and templates[q_type][category]:
                    statement, correct_answer = random.choice(templates[q_type][category])
                    question = {
                        "question_text": statement,
                        "question_type": q_type,
                        "explanation": f"This statement tests knowledge of {topic_name}.",
                        "difficulty_level": random.randint(1, 3),
                        "points": 1,
                        "cognitive_level": "recall",
                        "key_concept": f"{topic_name} facts",
                        "choices": [
                            {"text": "True", "is_correct": correct_answer},
                            {"text": "False", "is_correct": not correct_answer}
                        ]
                    }
                else:
                    continue
            
            elif q_type in ["short_answer", "fill_in_blank"]:
                if category in templates[q_type] and templates[q_type][category]:
                    question_text = random.choice(templates[q_type][category])
                    question = {
                        "question_text": question_text,
                        "question_type": q_type,
                        "explanation": f"This requires application of {topic_name} knowledge.",
                        "difficulty_level": random.randint(2, 4),
                        "points": random.choice([2, 3]),
                        "cognitive_level": "application",
                        "key_concept": f"{topic_name} application",
                        "correct_answers": [
                            {"text": "Sample correct answer", "is_case_sensitive": False, "is_exact_match": False, "points": 2}
                        ]
                    }
                else:
                    continue
            
            questions.append(question)
        
        return questions

class MockResponse:
    """Mock response object"""
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]

class MockChoice:
    """Mock choice object"""
    def __init__(self, content: str):
        self.message = MockMessage(content)

class MockMessage:
    """Mock message object"""
    def __init__(self, content: str):
        self.content = content

# Usage: Replace the OpenAI import and initialization in your original code
"""
# Instead of:
# self.openai_client = openai.OpenAI(api_key=openai_api_key)

# Use:
# self.openai_client = MockOpenAI(api_key=openai_api_key)

# Everything else stays exactly the same!
"""

# Test the mock
if __name__ == "__main__":
    mock_client = MockOpenAI()
    
    # Test topic analysis
    analysis_response = mock_client.chat.create(
        model="gpt-4",
        messages=[{"role": "user", "content": 'TASK 1 - TOPIC ANALYSIS:\nFirst, determine:\nlearning goal: "Finnish B1 Grammar"'}],
        temperature=0.3
    )
    
    print("=== TOPIC ANALYSIS RESPONSE ===")
    print(analysis_response.choices[0].message.content[:500] + "...")
    
    # Test question generation
    questions_response = mock_client.chat.create(
        model="gpt-4",
        messages=[{"role": "user", "content": 'You are an expert question designer creating assessment items for: "Finnish Past Tense"\nGenerate 5 high-quality questions'}],
        temperature=0.4
    )
    
    print("\n=== QUESTIONS RESPONSE ===")
    print(questions_response.choices[0].message.content[:500] + "...")