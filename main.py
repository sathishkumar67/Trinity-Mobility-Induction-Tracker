import asyncio
import random
from typing import List, Tuple, Dict, Optional

# 1. Async function to fetch quiz questions
async def fetch_questions(quiz_id: int) -> Dict[str, List[Tuple[str, bool]]]:
    """Fetch quiz questions from a simulated database"""
    await asyncio.sleep(0.5)  # Simulate network delay
    
    questions_db = {
        1: [
            ("Is Python dynamically typed?", True),
            ("Does async/await require threads?", False),
            ("Is 'list' mutable in Python?", True),
            ("Are Python strings immutable?", True),
            ("Does 1 == True in Python?", False)
        ],
        2: [
            ("Is JavaScript single-threaded?", True),
            ("Are all Python objects hashable?", False),
            ("Is asyncio part of standard library?", True),
            ("Does Python have tail call optimization?", False),
            ("Can dict keys be mutable types?", False)
        ]
    }
    
    return {"questions": questions_db.get(quiz_id, [])}

# 2. Async function to administer a single question
async def ask_question(
    question: str, 
    correct_answer: bool, 
    question_num: int
) -> bool:
    """Ask a single question and return if answer was correct"""
    print(f"\nQ{question_num}: {question}")
    print("(True/False) or (T/F) or (1/0)")
    
    # Simulate async user input with timeout
    try:
        # In real app, you'd use async input libraries
        await asyncio.sleep(0.3)  # Simulate thinking time
        user_input = input("Your answer: ").strip().lower()
        
        # Parse multiple input formats
        if user_input in ['true', 't', '1']:
            user_bool = True
        elif user_input in ['false', 'f', '0']:
            user_bool = False
        else:
            print("Invalid input, counting as incorrect")
            return False
            
        if user_bool == correct_answer:
            print("✓ Correct!")
            return True
        else:
            print(f"✗ Incorrect. The answer was {correct_answer}")
            return False
            
    except asyncio.TimeoutError:
        print("Time's up!")
        return False

# 3. Async function to run complete quiz
async def run_quiz(minimum_score: float = 0.8) -> Tuple[int, int, bool]:
    """Run a quiz and return (correct, total, passed)"""
    print("=" * 50)
    print("PYTHON KNOWLEDGE QUIZ")
    print("=" * 50)
    
    # Fetch questions
    result = await fetch_questions(1)
    questions = result["questions"]
    
    if not questions:
        print("No questions available!")
        return (0, 0, False)
    
    # Ask all questions
    tasks = []
    for i, (q_text, correct_ans) in enumerate(questions, 1):
        task = ask_question(q_text, correct_ans, i)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # Calculate score
    correct = sum(results)
    total = len(questions)
    score = correct / total if total > 0 else 0
    
    # Display results
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Correct: {correct}/{total}")
    print(f"Score: {score:.1%}")
    print(f"Minimum to pass: {minimum_score:.0%}")
    
    passed = score >= minimum_score
    if passed:
        print("✅ Congratulations! You passed!")
    else:
        print("❌ Try again to reach 80% or higher")
    
    return (correct, total, passed)

# Main async entry point
async def main() -> None:
    """Main program entry point"""
    try:
        correct, total, passed = await run_quiz(0.8)
        
        # Optional: Retry logic if failed
        if not passed:
            print("\nWould you like to try again? (yes/no)")
            retry = input().strip().lower()
            if retry in ['yes', 'y']:
                await main()
    except KeyboardInterrupt:
        print("\n\nQuiz interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

# Run the program
if __name__ == "__main__":
    asyncio.run(main())