import os
import sys
import datetime
from werkzeug.security import generate_password_hash

# Add the current directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Subject, Chapter, Quiz, Question

def init_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            full_name='Admin User',
            qualification='Administrator',
            dob=datetime.date(1990, 1, 1),
            is_admin=True
        )
        db.session.add(admin)
        
        # Create test user
        test_user = User(
            username='testuser',
            password_hash=generate_password_hash('password123'),
            full_name='Test User',
            qualification='Student',
            dob=datetime.date(1995, 5, 15),
            is_admin=False
        )
        db.session.add(test_user)
        
        # Create subjects
        subjects = [
            {
                'name': 'Mathematics',
                'description': 'Study of numbers, quantities, and shapes'
            },
            {
                'name': 'Science',
                'description': 'Study of the physical and natural world'
            },
            {
                'name': 'Computer Science',
                'description': 'Study of computers and computational systems'
            }
        ]
        
        subject_objects = []
        for subject_data in subjects:
            subject = Subject(**subject_data)
            db.session.add(subject)
            subject_objects.append(subject)
        
        # Commit to get subject IDs
        db.session.commit()
        
        # Create chapters
        chapters = [
            # Mathematics chapters
            {
                'subject_id': subject_objects[0].id,
                'name': 'Algebra',
                'description': 'Study of mathematical symbols and rules'
            },
            {
                'subject_id': subject_objects[0].id,
                'name': 'Geometry',
                'description': 'Study of shapes and properties of space'
            },
            # Science chapters
            {
                'subject_id': subject_objects[1].id,
                'name': 'Physics',
                'description': 'Study of matter, energy, and their interactions'
            },
            {
                'subject_id': subject_objects[1].id,
                'name': 'Biology',
                'description': 'Study of living organisms'
            },
            # Computer Science chapters
            {
                'subject_id': subject_objects[2].id,
                'name': 'Programming',
                'description': 'Study of creating computer programs'
            },
            {
                'subject_id': subject_objects[2].id,
                'name': 'Databases',
                'description': 'Study of data storage and retrieval'
            }
        ]
        
        chapter_objects = []
        for chapter_data in chapters:
            chapter = Chapter(**chapter_data)
            db.session.add(chapter)
            chapter_objects.append(chapter)
        
        # Commit to get chapter IDs
        db.session.commit()
        
        # Create quizzes
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        
        quizzes = [
            {
                'chapter_id': chapter_objects[0].id,  # Algebra
                'title': 'Algebra Fundamentals',
                'description': 'Test your knowledge of algebraic basics',
                'date': today,
                'duration': 30
            },
            {
                'chapter_id': chapter_objects[2].id,  # Physics
                'title': 'Mechanics Quiz',
                'description': 'Test your understanding of basic mechanics',
                'date': tomorrow,
                'duration': 45
            },
            {
                'chapter_id': chapter_objects[4].id,  # Programming
                'title': 'Python Programming',
                'description': 'Test your Python programming skills',
                'date': next_week,
                'duration': 60
            }
        ]
        
        quiz_objects = []
        for quiz_data in quizzes:
            quiz = Quiz(**quiz_data)
            db.session.add(quiz)
            quiz_objects.append(quiz)
            
        # Commit to get quiz IDs
        db.session.commit()
        
        # Create questions
        algebra_questions = [
            {
                'quiz_id': quiz_objects[0].id,
                'question_text': 'What is the solution to the equation 2x + 5 = 13?',
                'options': str(['x = 3', 'x = 4', 'x = 5', 'x = 6']),
                'correct_answer': 1  # x = 4
            },
            {
                'quiz_id': quiz_objects[0].id,
                'question_text': 'Simplify the expression 3(2x - 4) + 5.',
                'options': str(['6x - 12 + 5', '6x - 7', '6x - 12', '6x - 17']),
                'correct_answer': 1  # 6x - 7
            },
            {
                'quiz_id': quiz_objects[0].id,
                'question_text': 'If f(x) = 2x² + 3x - 5, what is f(2)?',
                'options': str(['9', '11', '13', '15']),
                'correct_answer': 1  # 11
            }
        ]
        
        physics_questions = [
            {
                'quiz_id': quiz_objects[1].id,
                'question_text': 'What is Newton\'s first law of motion?',
                'options': str(['F = ma', 'Objects at rest stay at rest unless acted upon by a force', 'Every action has an equal and opposite reaction', 'Energy can neither be created nor destroyed']),
                'correct_answer': 1  # Objects at rest...
            },
            {
                'quiz_id': quiz_objects[1].id,
                'question_text': 'What is the unit of force in the SI system?',
                'options': str(['Newton', 'Joule', 'Watt', 'Volt']),
                'correct_answer': 0  # Newton
            },
            {
                'quiz_id': quiz_objects[1].id,
                'question_text': 'What is the acceleration due to gravity on Earth?',
                'options': str(['9.8 m/s²', '8.9 m/s²', '10.0 m/s²', '7.6 m/s²']),
                'correct_answer': 0  # 9.8 m/s²
            }
        ]
        
        python_questions = [
            {
                'quiz_id': quiz_objects[2].id,
                'question_text': 'What is the correct way to create a function in Python?',
                'options': str(['function myFunc():', 'def myFunc():', 'create myFunc():', 'func myFunc():']),
                'correct_answer': 1  # def myFunc():
            },
            {
                'quiz_id': quiz_objects[2].id,
                'question_text': 'Which of the following is not a valid data type in Python?',
                'options': str(['List', 'Dictionary', 'Tuple', 'Array']),
                'correct_answer': 3  # Array
            },
            {
                'quiz_id': quiz_objects[2].id,
                'question_text': 'What will be the output of the following code: print(2**3)?',
                'options': str(['6', '8', '5', 'Error']),
                'correct_answer': 1  # 8
            }
        ]
        
        all_questions = algebra_questions + physics_questions + python_questions
        for question_data in all_questions:
            question = Question(**question_data)
            db.session.add(question)
        
        # Commit everything
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
