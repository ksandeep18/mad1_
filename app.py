import os
import logging
import datetime
import json
import ast
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import check_password_hash
from sqlalchemy import func, desc

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy with the new API
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///quiz_platform.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        # First try to parse as JSON
        return json.loads(value)
    except:
        try:
            # If JSON parsing fails, try ast.literal_eval
            return ast.literal_eval(value)
        except:
            # If all parsing fails, return an empty list
            return []
            
@app.template_filter('slice')
def slice_filter(value, start, end=None):
    """Return a slice of the list."""
    if end is None:
        return value[start:]
    return value[start:end]

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf = CSRFProtect()
csrf.init_app(app)

# Import models and forms after initializing db to avoid circular imports
with app.app_context():
    from models import User, Subject, Chapter, Quiz, Question, Score, UserAnswer
    from forms import LoginForm, RegistrationForm, SubjectForm, ChapterForm, QuizForm, QuestionForm

    # Create all tables
    db.create_all()

    # Check if admin user exists, create if not
    admin_exists = User.query.filter_by(username='admin').first()
    if not admin_exists:
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            full_name='Admin User',
            qualification='Administrator',
            dob=datetime.datetime(1990, 1, 1),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Admin user created")

@login_manager.user_loader
def load_user(id):
    from models import User
    return User.query.get(int(id))

# Context processors
@app.context_processor
def inject_global_variables():
    return {
        'current_year': datetime.datetime.now().year
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            if user.is_admin:
                next_page = url_for('admin_dashboard')
            else:
                next_page = url_for('user_dashboard')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        user = User(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data),
            full_name=form.full_name.data,
            qualification=form.qualification.data,
            dob=form.dob.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user_count = User.query.filter_by(is_admin=False).count()
    subject_count = Subject.query.count()
    quiz_count = Quiz.query.count()
    recent_quizzes = Quiz.query.order_by(Quiz.date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', user_count=user_count, 
                           subject_count=subject_count, quiz_count=quiz_count,
                           recent_quizzes=recent_quizzes)

@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data, description=form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully.', 'success')
        return redirect(url_for('manage_subjects'))
    
    search_query = request.args.get('search', '')
    if search_query:
        subjects = Subject.query.filter(Subject.name.contains(search_query)).all()
    else:
        subjects = Subject.query.all()
    
    return render_template('admin/manage_subjects.html', subjects=subjects, form=form, search_query=search_query)

@app.route('/admin/subjects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        flash('Subject updated successfully.', 'success')
        return redirect(url_for('manage_subjects'))
    
    return render_template('admin/manage_subjects.html', form=form, edit_mode=True, subject=subject)

@app.route('/admin/subjects/delete/<int:id>', methods=['POST'])
@login_required
def delete_subject(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully.', 'success')
    return redirect(url_for('manage_subjects'))

@app.route('/admin/chapters', methods=['GET', 'POST'])
@login_required
def manage_chapters():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        chapter = Chapter(
            subject_id=form.subject_id.data,
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter added successfully.', 'success')
        return redirect(url_for('manage_chapters'))
    
    search_query = request.args.get('search', '')
    subject_filter = request.args.get('subject_id', type=int)
    
    query = db.session.query(Chapter, Subject.name).join(Subject, Chapter.subject_id == Subject.id)
    
    if search_query:
        query = query.filter(Chapter.name.contains(search_query))
    if subject_filter:
        query = query.filter(Chapter.subject_id == subject_filter)
    
    chapters_with_subjects = query.all()
    subjects = Subject.query.all()
    
    return render_template('admin/manage_chapters.html', 
                          chapters=chapters_with_subjects, 
                          form=form, 
                          subjects=subjects,
                          search_query=search_query,
                          subject_filter=subject_filter)

@app.route('/admin/chapters/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    chapter = Chapter.query.get_or_404(id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        chapter.subject_id = form.subject_id.data
        chapter.name = form.name.data
        chapter.description = form.description.data
        db.session.commit()
        flash('Chapter updated successfully.', 'success')
        return redirect(url_for('manage_chapters'))
    
    return render_template('admin/manage_chapters.html', form=form, edit_mode=True, chapter=chapter)

@app.route('/admin/chapters/delete/<int:id>', methods=['POST'])
@login_required
def delete_chapter(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    chapter = Chapter.query.get_or_404(id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully.', 'success')
    return redirect(url_for('manage_chapters'))

@app.route('/admin/quizzes', methods=['GET', 'POST'])
@login_required
def manage_quizzes():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    form = QuizForm()
    form.chapter_id.choices = [(c.id, f"{c.name} ({Subject.query.get(c.subject_id).name})") 
                              for c in Chapter.query.all()]
    
    if form.validate_on_submit():
        quiz = Quiz(
            chapter_id=form.chapter_id.data,
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            duration=form.duration.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz added successfully.', 'success')
        return redirect(url_for('manage_quizzes'))
    
    search_query = request.args.get('search', '')
    chapter_filter = request.args.get('chapter_id', type=int)
    
    query = db.session.query(Quiz, Chapter.name.label('chapter_name'), Subject.name.label('subject_name'))\
        .join(Chapter, Quiz.chapter_id == Chapter.id)\
        .join(Subject, Chapter.subject_id == Subject.id)
    
    if search_query:
        query = query.filter(Quiz.title.contains(search_query))
    if chapter_filter:
        query = query.filter(Quiz.chapter_id == chapter_filter)
    
    quizzes = query.all()
    chapters = Chapter.query.all()
    
    return render_template('admin/manage_quizzes.html', 
                          quizzes=quizzes, 
                          form=form, 
                          chapters=chapters,
                          search_query=search_query,
                          chapter_filter=chapter_filter)

@app.route('/admin/quizzes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(id)
    form = QuizForm(obj=quiz)
    form.chapter_id.choices = [(c.id, f"{c.name} ({Subject.query.get(c.subject_id).name})") 
                              for c in Chapter.query.all()]
    
    if form.validate_on_submit():
        quiz.chapter_id = form.chapter_id.data
        quiz.title = form.title.data
        quiz.description = form.description.data
        quiz.date = form.date.data
        quiz.duration = form.duration.data
        db.session.commit()
        flash('Quiz updated successfully.', 'success')
        return redirect(url_for('manage_quizzes'))
    
    return render_template('admin/manage_quizzes.html', form=form, edit_mode=True, quiz=quiz)

@app.route('/admin/quizzes/delete/<int:id>', methods=['POST'])
@login_required
def delete_quiz(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('manage_quizzes'))

@app.route('/admin/questions/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def manage_questions(quiz_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        options = [
            form.option_a.data,
            form.option_b.data,
            form.option_c.data,
            form.option_d.data
        ]
        
        question = Question(
            quiz_id=quiz_id,
            question_text=form.question_text.data,
            options=str(options),
            correct_answer=form.correct_answer.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully.', 'success')
        return redirect(url_for('manage_questions', quiz_id=quiz_id))
    
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('admin/manage_questions.html', 
                          quiz=quiz, 
                          questions=questions, 
                          form=form)

@app.route('/admin/questions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    question = Question.query.get_or_404(id)
    quiz = Quiz.query.get(question.quiz_id)
    
    # Parse options from string to list
    import ast
    options = ast.literal_eval(question.options)
    
    form = QuestionForm(obj=question)
    if request.method == 'GET':
        form.option_a.data = options[0]
        form.option_b.data = options[1]
        form.option_c.data = options[2]
        form.option_d.data = options[3]
    
    if form.validate_on_submit():
        options = [
            form.option_a.data,
            form.option_b.data,
            form.option_c.data,
            form.option_d.data
        ]
        
        question.question_text = form.question_text.data
        question.options = str(options)
        question.correct_answer = form.correct_answer.data
        db.session.commit()
        flash('Question updated successfully.', 'success')
        return redirect(url_for('manage_questions', quiz_id=question.quiz_id))
    
    questions = Question.query.filter_by(quiz_id=question.quiz_id).all()
    
    return render_template('admin/manage_questions.html', 
                          quiz=quiz,
                          questions=questions,
                          form=form, 
                          edit_mode=True, 
                          question=question)

@app.route('/admin/questions/delete/<int:id>', methods=['POST'])
@login_required
def delete_question(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    question = Question.query.get_or_404(id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('manage_questions', quiz_id=quiz_id))

@app.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '')
    
    if search_query:
        users = User.query.filter(
            (User.username.contains(search_query)) | 
            (User.full_name.contains(search_query))
        ).filter_by(is_admin=False).all()
    else:
        users = User.query.filter_by(is_admin=False).all()
    
    return render_template('admin/manage_users.html', users=users, search_query=search_query)

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    
    if user.is_admin:
        flash('Cannot delete an admin user.', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{user.username}" has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    # Get total users, quizzes, and subjects
    total_users = User.query.filter_by(is_admin=False).count()
    total_quizzes = Quiz.query.count()
    total_subjects = Subject.query.count()
    
    # Get quiz participation data
    quiz_participation = db.session.query(
        Quiz.id, 
        Quiz.title,
        func.count(Score.id).label('attempt_count')
    ).outerjoin(Score).group_by(Quiz.id).order_by(desc('attempt_count')).limit(10).all()
    
    # Get subject popularity
    subject_popularity = db.session.query(
        Subject.id,
        Subject.name,
        func.count(Score.id).label('attempt_count')
    ).join(Chapter, Subject.id == Chapter.subject_id)\
     .join(Quiz, Chapter.id == Quiz.chapter_id)\
     .outerjoin(Score, Quiz.id == Score.quiz_id)\
     .group_by(Subject.id)\
     .order_by(desc('attempt_count'))\
     .all()
    
    # Get average scores by subject
    avg_scores_by_subject = db.session.query(
        Subject.name,
        func.avg(Score.total_score).label('avg_score')
    ).join(Chapter, Subject.id == Chapter.subject_id)\
     .join(Quiz, Chapter.id == Quiz.chapter_id)\
     .join(Score, Quiz.id == Score.quiz_id)\
     .group_by(Subject.name)\
     .order_by(desc('avg_score'))\
     .all()
    
    return render_template('admin/analytics.html',
                          total_users=total_users,
                          total_quizzes=total_quizzes,
                          total_subjects=total_subjects,
                          quiz_participation=quiz_participation,
                          subject_popularity=subject_popularity,
                          avg_scores_by_subject=avg_scores_by_subject)

# User routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get user's recent quizzes
    recent_scores = Score.query.filter_by(user_id=current_user.id)\
                              .order_by(Score.timestamp.desc())\
                              .limit(5)\
                              .all()
    
    # Calculate user's average score
    avg_score = db.session.query(func.avg(Score.total_score))\
                         .filter_by(user_id=current_user.id)\
                         .scalar() or 0
                         
    # Get all subjects for quick navigation
    subjects = Subject.query.all()
    
    # Get upcoming quizzes
    today = datetime.date.today()
    upcoming_quizzes = Quiz.query.filter(Quiz.date >= today)\
                                .order_by(Quiz.date)\
                                .limit(5)\
                                .all()
    
    # Count total quizzes taken
    total_quizzes_taken = Score.query.filter_by(user_id=current_user.id).count()
    
    return render_template('user/dashboard.html',
                          recent_scores=recent_scores,
                          avg_score=avg_score,
                          subjects=subjects,
                          upcoming_quizzes=upcoming_quizzes,
                          total_quizzes_taken=total_quizzes_taken)

@app.route('/user/quizzes')
@login_required
def quiz_list():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get filter parameters
    subject_id = request.args.get('subject_id', type=int)
    search_query = request.args.get('search', '')
    
    # Base query joining quizzes with chapters and subjects
    query = db.session.query(Quiz, Chapter.name.label('chapter_name'), Subject.name.label('subject_name'))\
        .join(Chapter, Quiz.chapter_id == Chapter.id)\
        .join(Subject, Chapter.subject_id == Subject.id)
    
    # Apply filters if provided
    if subject_id:
        query = query.filter(Chapter.subject_id == subject_id)
    
    if search_query:
        query = query.filter(
            (Quiz.title.contains(search_query)) |
            (Chapter.name.contains(search_query)) |
            (Subject.name.contains(search_query))
        )
    
    # Get all quizzes with their chapter and subject info
    quizzes = query.order_by(Quiz.date.desc()).all()
    
    # Get all subjects for the filter dropdown
    subjects = Subject.query.all()
    
    # Get the user's completed quizzes to show completion status
    completed_quiz_ids = [score.quiz_id for score in Score.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('user/quiz_list.html',
                          quizzes=quizzes,
                          subjects=subjects,
                          subject_id=subject_id,
                          search_query=search_query,
                          completed_quiz_ids=completed_quiz_ids)

@app.route('/user/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Check if the user has already completed this quiz
    existing_score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if existing_score:
        flash('You have already completed this quiz.', 'info')
        return redirect(url_for('quiz_results', score_id=existing_score.id))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('quiz_list'))
    
    # Parse options from string to list for each question
    for question in questions:
        # Use our custom from_json filter
        question.options_list = from_json_filter(question.options)
    
    return render_template('user/take_quiz.html', quiz=quiz, questions=questions)

@app.route('/user/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Check if the user has already completed this quiz
    existing_score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if existing_score:
        flash('You have already completed this quiz.', 'info')
        return redirect(url_for('quiz_results', score_id=existing_score.id))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Calculate score
    total_questions = len(questions)
    correct_answers = 0
    
    # Create a new score record
    new_score = Score(
        quiz_id=quiz_id,
        user_id=current_user.id,
        timestamp=datetime.datetime.now()
    )
    db.session.add(new_score)
    db.session.flush()  # Get the ID without committing
    
    # Process each question and save user answers
    for question in questions:
        answer_key = f'question_{question.id}'
        user_answer = request.form.get(answer_key)
        
        # Save user's answer
        user_answer_record = UserAnswer(
            score_id=new_score.id,
            question_id=question.id,
            user_answer=user_answer
        )
        db.session.add(user_answer_record)
        
        # Check if correct
        if user_answer and int(user_answer) == question.correct_answer:
            correct_answers += 1
    
    # Calculate percentage score
    if total_questions > 0:
        score_percentage = (correct_answers / total_questions) * 100
    else:
        score_percentage = 0
    
    # Update score record
    new_score.correct_answers = correct_answers
    new_score.total_questions = total_questions
    new_score.total_score = score_percentage
    
    db.session.commit()
    
    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('quiz_results', score_id=new_score.id))

@app.route('/user/quiz/results/<int:score_id>')
@login_required
def quiz_results(score_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    score = Score.query.get_or_404(score_id)
    
    # Ensure the user can only view their own results
    if score.user_id != current_user.id:
        flash('You are not authorized to view these results.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    quiz = Quiz.query.get(score.quiz_id)
    
    # Get user answers with questions
    user_answers = db.session.query(UserAnswer, Question)\
        .join(Question, UserAnswer.question_id == Question.id)\
        .filter(UserAnswer.score_id == score_id)\
        .all()
    
    # Parse options from string to list for each question
    for _, question in user_answers:
        # Use our custom from_json filter
        question.options_list = from_json_filter(question.options)
    
    return render_template('user/quiz_results.html',
                          score=score,
                          quiz=quiz,
                          user_answers=user_answers)

@app.route('/user/history')
@login_required
def user_history():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get all user's scores with quiz information
    scores = db.session.query(Score, Quiz.title, Chapter.name.label('chapter_name'), Subject.name.label('subject_name'))\
        .join(Quiz, Score.quiz_id == Quiz.id)\
        .join(Chapter, Quiz.chapter_id == Chapter.id)\
        .join(Subject, Chapter.subject_id == Subject.id)\
        .filter(Score.user_id == current_user.id)\
        .order_by(Score.timestamp.desc())\
        .all()
    
    return render_template('user/history.html', scores=scores)
