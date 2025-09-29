import openai
from supabase import create_client, Client
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
import os
import generate_questions_test
load_dotenv()

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_IN_BLANK = "fill_in_blank"
    ESSAY = "essay"
    MATCHING = "matching"
    ORDERING = "ordering"

class IntelligentQuestionGenerator:
    def __init__(self, openai_client, supabase_url: str, supabase_key: str):
        self.openai_client = openai_client
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
    def analyze_topic_and_generate_structure(self, topic_input: str, test_mode: bool = False) -> Dict:
        """Analyze any topic input and generate appropriate learning structure with comprehensive prompting"""
        
        analysis_prompt = f"""
        You are an expert educational content architect. Analyze this learning goal: "{topic_input}"

        TASK 1 - TOPIC ANALYSIS:
        First, determine:
        1. What subject area is this? (language learning, programming, science, etc.)
        2. What level/complexity is implied? (beginner, intermediate, advanced, or specific level like B1)
        3. What are the key learning objectives?
        4. What prerequisite knowledge is assumed?

        TASK 2 - LEARNING STRUCTURE:
        Create a hierarchical learning structure optimized for mastery and retention:
        - Main categories should represent major conceptual areas
        - Subcategories should break down into teachable units
        - Leaf topics should be specific, testable knowledge areas that can be mastered independently
        - Each leaf topic should be narrow enough that 50-100 questions can comprehensively test it

        TASK 3 - QUESTION STRATEGY:
        For each leaf topic, specify the optimal question mix based on the content type:
        - Factual knowledge → multiple choice, true/false
        - Application/usage → fill-in-blank, short answer
        - Analysis/evaluation → essay, matching
        - Procedural knowledge → ordering, step-by-step questions

        Return as JSON in this exact format:
        {{
            "analysis": {{
                "subject_area": "Subject area",
                "complexity_level": "Level description",
                "learning_objectives": ["Objective 1", "Objective 2", "..."],
                "prerequisites": ["Prerequisite 1", "Prerequisite 2", "..."],
                "estimated_study_hours": "X-Y hours"
            }},
            "structure": {{
                "main_categories": [
                    {{
                        "name": "Category Name",
                        "description": "Why this category is essential for mastery",
                        "learning_outcomes": ["What students will achieve"],
                        "subcategories": [
                            {{
                                "name": "Subcategory Name", 
                                "description": "Specific learning focus",
                                "prerequisites": ["What must be known first"],
                                "leaf_topics": [
                                    {{
                                        "name": "Specific Topic Name",
                                        "description": "Detailed learning objective",
                                        "key_concepts": ["Concept 1", "Concept 2"],
                                        "question_strategy": {{
                                            "multiple_choice": 30,
                                            "true_false": 20,
                                            "short_answer": 25,
                                            "fill_in_blank": 25
                                        }},
                                        "difficulty_distribution": {{
                                            "level_1": 20,
                                            "level_2": 30,
                                            "level_3": 30,
                                            "level_4": 15,
                                            "level_5": 5
                                        }}
                                    }}
                                ]
                            }}
                        ]
                    }}
                ]
            }}
        }}
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3  # Lower temperature for more structured output
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_comprehensive_questions(self, topic_data: Dict, test_mode: bool = False) -> List[Dict]:
        """Generate comprehensive questions based on topic analysis and strategy"""
        
        topic_name = topic_data["name"]
        topic_description = topic_data["description"]
        key_concepts = topic_data.get("key_concepts", [])
        question_strategy = topic_data.get("question_strategy", {})
        difficulty_distribution = topic_data.get("difficulty_distribution", {})
        
        # Adjust quantities based on test mode
        if test_mode:
            # In test mode, generate 4-6 questions total per topic
            total_questions = 5
            strategy_text = "Generate 5 high-quality questions that cover the most essential concepts"
            question_distribution = {
                "multiple_choice": 2,
                "true_false": 1,
                "short_answer": 1,
                "fill_in_blank": 1
            }
        else:
            # Full mode based on strategy
            total_questions = sum(question_strategy.values()) if question_strategy else 100
            strategy_text = f"Generate {total_questions} comprehensive questions following the specified distribution"
            question_distribution = question_strategy
        
        concepts_text = "\n".join([f"- {concept}" for concept in key_concepts]) if key_concepts else "Focus on core topic elements"
        
        question_prompt = f"""
        You are an expert question designer creating assessment items for: "{topic_name}"

        TOPIC CONTEXT:
        Description: {topic_description}
        Key Concepts to Test:
        {concepts_text}

        GENERATION STRATEGY:
        {strategy_text}
        
        Question Distribution:
        {json.dumps(question_distribution, indent=2)}

        QUALITY REQUIREMENTS:
        1. COMPREHENSIVE COVERAGE: Questions should test all key concepts and learning objectives
        2. COGNITIVE LEVELS: Mix of recall, understanding, application, and analysis
        3. REAL-WORLD RELEVANCE: Include practical scenarios and authentic contexts
        4. CLEAR LANGUAGE: Unambiguous wording with precise terminology
        5. APPROPRIATE DIFFICULTY: Balanced progression from basic to challenging
        6. NO TRICK QUESTIONS: Fair, straightforward assessment of genuine knowledge

        QUESTION TYPE GUIDELINES:
        
        MULTIPLE CHOICE:
        - 4 options with one clearly correct answer
        - Distractors should be plausible but definitively wrong
        - Test conceptual understanding, not just memorization
        
        TRUE/FALSE:
        - Clear, unambiguous statements
        - Test important facts and principles
        - Avoid absolute terms unless genuinely absolute
        
        SHORT ANSWER:
        - Require specific knowledge demonstration
        - Clear criteria for correct answers
        - Test application and explanation skills
        
        FILL-IN-BLANK:
        - Natural context with meaningful blanks
        - Test vocabulary, syntax, or key terms
        - One clear correct answer per blank
        
        Return as JSON array with this exact structure:
        [
            {{
                "question_text": "Complete question text",
                "question_type": "multiple_choice|true_false|short_answer|fill_in_blank",
                "explanation": "Detailed explanation of why this is the correct answer and why others are wrong",
                "difficulty_level": 1-5,
                "points": 1-3,
                "cognitive_level": "recall|understanding|application|analysis",
                "key_concept": "Which key concept this question tests",
                "choices": [
                    {{"text": "Option A", "is_correct": false}},
                    {{"text": "Option B", "is_correct": true}},
                    {{"text": "Option C", "is_correct": false}},
                    {{"text": "Option D", "is_correct": false}}
                ],
                "correct_answers": [
                    {{"text": "Expected answer", "is_case_sensitive": false, "is_exact_match": true, "points": 1}}
                ]
            }}
        ]
        
        IMPORTANT:
        - Include "choices" only for multiple_choice and true_false questions
        - Include "correct_answers" only for short_answer and fill_in_blank questions
        - For true_false, use exactly 2 choices: True and False
        - Make every question count - no filler content
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question_prompt}],
            temperature=0.4,
            max_tokens=4000
        )
        
        try:
            questions_data = json.loads(response.choices[0].message.content)
            return questions_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print("Raw response:", response.choices[0].message.content)
            return []
    
    def insert_topic_hierarchy(self, analysis_data: Dict, main_topic_name: str) -> str:
        """Insert topic hierarchy into Supabase with enhanced metadata"""
        
        try:
            # Insert main topic with analysis metadata
            main_topic_data = {
                "name": main_topic_name,
                "description": f"Complete course: {main_topic_name}",
                "parent_id": None,
                "metadata": {
                    "analysis": analysis_data.get("analysis", {}),
                    "course_type": "auto_generated",
                    "total_estimated_questions": 0
                }
            }
            
            main_topic_result = self.supabase.table("topics").upsert(main_topic_data,on_conflict='slug').execute()
            main_topic_id = main_topic_result.data[0]["id"]
            
            total_estimated_questions = 0
            
            # Insert categories and subcategories with metadata
            for category in analysis_data["structure"]["main_categories"]:
                category_data = {
                    "name": category["name"],
                    "description": category["description"],
                    "parent_id": main_topic_id,
                    "metadata": {
                        "learning_outcomes": category.get("learning_outcomes", []),
                        "category_type": "main_category"
                    }
                }
                category_result = self.supabase.table("topics").insert(category_data).execute()
                category_id = category_result.data[0]["id"]
                
                for subcategory in category["subcategories"]:
                    subcategory_data = {
                        "name": subcategory["name"],
                        "description": subcategory["description"],
                        "parent_id": category_id,
                        "metadata": {
                            "prerequisites": subcategory.get("prerequisites", []),
                            "category_type": "subcategory"
                        }
                    }
                    subcategory_result = self.supabase.table("topics").insert(subcategory_data).execute()
                    subcategory_id = subcategory_result.data[0]["id"]
                    
                    # Insert leaf topics with question strategy
                    for leaf_topic in subcategory["leaf_topics"]:
                        leaf_data = {
                            "name": leaf_topic["name"],
                            "description": leaf_topic["description"],
                            "parent_id": subcategory_id,
                            "metadata": {
                                "key_concepts": leaf_topic.get("key_concepts", []),
                                "question_strategy": leaf_topic.get("question_strategy", {}),
                                "difficulty_distribution": leaf_topic.get("difficulty_distribution", {}),
                                "category_type": "leaf_topic"
                            }
                        }
                        self.supabase.table("topics").insert(leaf_data).execute()
                        
                        # Count estimated questions
                        strategy = leaf_topic.get("question_strategy", {})
                        total_estimated_questions += sum(strategy.values()) if strategy else 100
            
            # Update main topic with total question count
            self.supabase.table("topics").update({
                "metadata": {
                    **main_topic_data["metadata"],
                    "total_estimated_questions": total_estimated_questions
                }
            }).eq("id", main_topic_id).execute()
            
            return main_topic_id
            
        except Exception as e:
            print(f"Error inserting topic hierarchy: {e}")
            raise e
    
    def insert_questions_with_metadata(self, topic_id: str, questions_data: List[Dict]) -> List[str]:
        """Insert questions with enhanced metadata tracking"""
        question_ids = []
        
        try:
            for q_data in questions_data:
                # Enhanced question metadata
                metadata = {
                    "cognitive_level": q_data.get("cognitive_level", "understanding"),
                    "key_concept": q_data.get("key_concept", ""),
                    "auto_generated": True,
                    "generation_timestamp": "now()"
                }
                
                question_data = {
                    "topic_id": topic_id,
                    "question_text": q_data["question_text"],
                    "question_type": q_data["question_type"],
                    "explanation": q_data["explanation"],
                    "points": q_data.get("points", 1),
                    "difficulty_level": q_data.get("difficulty_level", 1),
                    "metadata": metadata
                }
                
                question_result = self.supabase.table("questions").insert(question_data).execute()
                question_id = question_result.data[0]["id"]
                question_ids.append(question_id)
                
                # Insert choices with metadata
                if q_data.get("choices"):
                    choices_data = []
                    for i, choice in enumerate(q_data["choices"]):
                        choice_data = {
                            "question_id": question_id,
                            "choice_text": choice["text"],
                            "is_correct": choice["is_correct"],
                            "sort_order": i,
                            "metadata": {"auto_generated": True}
                        }
                        choices_data.append(choice_data)
                    
                    self.supabase.table("choices").insert(choices_data).execute()
                
                # Insert correct answers with metadata
                if q_data.get("correct_answers"):
                    answers_data = []
                    for i, answer in enumerate(q_data["correct_answers"]):
                        answer_data = {
                            "question_id": question_id,
                            "answer_text": answer["text"],
                            "is_case_sensitive": answer.get("is_case_sensitive", False),
                            "is_exact_match": answer.get("is_exact_match", True),
                            "points": answer.get("points", 1),
                            "sort_order": i
                        }
                        answers_data.append(answer_data)
                    
                    self.supabase.table("correct_answers").insert(answers_data).execute()
            
            return question_ids
            
        except Exception as e:
            print(f"Error inserting questions: {e}")
            raise e
    
    def generate_intelligent_course(self, topic_input: str, test_mode: bool = False):
        """Main method to generate an intelligent course from any topic input"""
        
        print(f"🎯 Generating course for: '{topic_input}'")
        print(f"📊 Mode: {'TEST (4-6 questions per topic)' if test_mode else 'FULL (50-100 questions per topic)'}")
        
        # Step 1: Analyze topic and generate structure
        print("\n🔍 Step 1: Analyzing topic and generating learning structure...")
        analysis_data = self.analyze_topic_and_generate_structure(topic_input, test_mode)
        
        print(f"   📚 Subject area: {analysis_data['analysis']['subject_area']}")
        print(f"   📈 Level: {analysis_data['analysis']['complexity_level']}")
        print(f"   ⏱️  Estimated study time: {analysis_data['analysis']['estimated_study_hours']}")
        
        # Step 2: Insert hierarchy
        print("\n💾 Step 2: Creating topic hierarchy in database...")
        main_topic_id = self.insert_topic_hierarchy(analysis_data, topic_input)
        
        # Step 3: Get leaf topics with their strategies
        print("\n🌿 Step 3: Retrieving leaf topics...")
        leaf_topics_response = self.supabase.table("topics").select("*").eq("metadata->>category_type", "leaf_topic").execute()
        leaf_topics = leaf_topics_response.data
        
        print(f"   Found {len(leaf_topics)} leaf topics to generate questions for")
        
        # Step 4: Generate questions for each leaf topic
        print(f"\n❓ Step 4: Generating questions...")
        
        total_questions = 0
        failed_topics = []
        
        for i, topic in enumerate(leaf_topics, 1):
            print(f"   [{i}/{len(leaf_topics)}] {topic['name']}")
            
            try:
                # Use the metadata to inform question generation
                topic_metadata = topic.get("metadata", {})
                topic_data = {
                    "name": topic["name"],
                    "description": topic["description"],
                    "key_concepts": topic_metadata.get("key_concepts", []),
                    "question_strategy": topic_metadata.get("question_strategy", {}),
                    "difficulty_distribution": topic_metadata.get("difficulty_distribution", {})
                }
                
                questions_data = self.generate_comprehensive_questions(topic_data, test_mode)
                
                if questions_data:
                    question_ids = self.insert_questions_with_metadata(topic["id"], questions_data)
                    total_questions += len(question_ids)
                    print(f"      ✅ Created {len(question_ids)} questions")
                else:
                    failed_topics.append(topic["name"])
                    print(f"      ❌ Failed to generate questions")
                    
            except Exception as e:
                failed_topics.append(topic["name"])
                print(f"      ❌ Error: {str(e)}")
        
        # Summary
        print(f"\n🎉 Course generation complete!")
        print(f"   📊 Total topics: {len(leaf_topics)}")
        print(f"   ❓ Total questions: {total_questions}")
        if failed_topics:
            print(f"   ⚠️  Failed topics: {len(failed_topics)} - {', '.join(failed_topics[:3])}{'...' if len(failed_topics) > 3 else ''}")
        
        return {
            "main_topic_id": main_topic_id,
            "total_topics": len(leaf_topics),
            "total_questions": total_questions,
            "failed_topics": failed_topics,
            "analysis": analysis_data["analysis"]
        }

# Helper function to get leaf topics (add to Supabase SQL editor)
CREATE_LEAF_TOPICS_FUNCTION = """
CREATE OR REPLACE FUNCTION get_leaf_topics()
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    path LTREE,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.name, t.description, t.path, t.metadata
    FROM topics t
    WHERE NOT EXISTS (
        SELECT 1 FROM topics child 
        WHERE child.parent_id = t.id
    )
    AND t.parent_id IS NOT NULL;
END;
$$ LANGUAGE plpgsql;
"""

# Usage examples
mock_test = False  # Set to False for full generation
if __name__ == "__main__":
    if mock_test:
        openai_client = generate_questions_test.MockOpenAI()
    else:
        openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    # Initialize the generator
    generator = IntelligentQuestionGenerator(
        openai_client=openai_client,
        supabase_url=os.environ.get("SUPABASE_URL"),
        supabase_key=os.environ.get("SUPABASE_KEY")
    )
    
    # Example 1: Test mode for quick validation
    result = generator.generate_intelligent_course(
        "Finnish B1 Grammar and Language Skills",
        test_mode=True  # Only 4-6 questions per topic
    )
    
    # Example 2: Full course generation
    # result = generator.generate_intelligent_course(
    #     "Python Data Science for Beginners",
    #     test_mode=False  # Full question set
    # )
    
    # Example 3: Any topic works!
    # result = generator.generate_intelligent_course(
    #     "Digital Marketing Fundamentals",
    #     test_mode=True
    # )
    
    print(f"\n📋 Course Summary:")
    print(f"   Course ID: {result['main_topic_id']}")
    print(f"   Topics: {result['total_topics']}")
    print(f"   Questions: {result['total_questions']}")
