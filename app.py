from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'secret123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    project_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)
    due_date = db.Column(db.String(20)) 

# ---------------- HELPER ---------------- #

def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'admin'

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return redirect('/login')

# ---------- SIGNUP ---------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Validation
        if not username or not password:
            flash("All fields required")
            return redirect('/signup')

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already exists")
            return redirect('/signup')

        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        flash("Signup successful")
        return redirect('/login')

    return render_template('signup.html')

# ---------- LOGIN ---------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if not user:
            flash("Invalid credentials")
            return redirect('/login')

        session['user_id'] = user.id
        session['role'] = user.role

        return redirect('/dashboard')

    return render_template('login.html')

# ---------- LOGOUT ---------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------- DASHBOARD ---------- #
@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/login')
    if session.get('role') == 'admin':
        tasks = Task.query.all()
    else:
        tasks = Task.query.filter_by(assigned_to=session['user_id']).all()
    users = User.query.all()
    projects = Project.query.all()

    return render_template('dashboard.html',
                           tasks=tasks,
                           users=users,
                           projects=projects)

# ---------- CREATE PROJECT ---------- #
@app.route('/create_project', methods=['POST'])
def create_project():
    if not is_admin():
        flash("Only admin can create projects")
        return redirect('/dashboard')

    name = request.form['name']
    if not name:
        flash("Project name required")
        return redirect('/dashboard')

    project = Project(name=name, created_by=session['user_id'])
    db.session.add(project)
    db.session.commit()

    return redirect('/dashboard')

# ---------- CREATE TASK ---------- #
@app.route('/create_task', methods=['POST'])
def create_task():
    if not is_logged_in():
        return redirect('/login')

    title = request.form['title']
    project_id = request.form['project_id']
    user_id = request.form['user_id']
    due_date = request.form['due_date']

    if not title:
        flash("Task title required")
        return redirect('/dashboard')

    task = Task(
        title=title,
        project_id=project_id,
        assigned_to=user_id,
        due_date=due_date
    )

    db.session.add(task)
    db.session.commit()

    return redirect('/dashboard')

# ---------- UPDATE TASK ---------- #
@app.route('/update_task/<int:id>')
def update_task(id):
    if not is_logged_in():
        return redirect('/login')

    task = Task.query.get(id)
    task.status = 'completed'
    db.session.commit()

    return redirect('/dashboard')

# ---------------- RUN ---------------- #

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))