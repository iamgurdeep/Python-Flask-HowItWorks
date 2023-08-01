from flask import Flask , render_template,flash,request,redirect,url_for,session
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

from data import Articles


app = Flask(__name__)

#Intialize URI for SQLLite DB for SQLALCHMEY

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///mydb.db'

#Wraping flask app in SQLALCHEMY

db=SQLAlchemy(app)

Articles=Articles()

#SQLAlchmey mapping with SQLLite DB
class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), unique=True, nullable=False)
    register_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class myarticles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    aurthor = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

def is_loged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Please login','danger')
            return  redirect(url_for('login'))
    return wrap
#URL Route
@app.route('/')
def index():
    return render_template('HOME.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    all_articles = myarticles.query.all()
    if all_articles:
        return render_template('articles.html', all_articles=all_articles)
    else:
        msg = 'No article Found'
        return render_template('articles.html', msg=msg)
    #return render_template('articles.html',articles=Articles)

@app.route('/article/<string:id>/')
@is_loged_in
def article(id):
    article=myarticles.query.filter_by(id=id).first()
    return render_template('article.html',article=article)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
        validators.data_required(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm= PasswordField('Confirm Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        registration = users(name=name, username=username, email=email, password=password)
        db.session.add(registration)
        db.session.commit()
        flash(' You are now registered .Your Username is: '+username,'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

#Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username_login=request.form['username']
        password_candidate=request.form['password']


        results=users.query.filter_by(username=username_login).first()
        if results :
            password=results.password
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in']=True
                session['username']=username_login

                flash('You are successfully logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)
        else:
            error='User is not registered'
            return render_template('login.html',error=error)

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out','success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_loged_in
def dashboard():
    all_articles=myarticles.query.all()
    if all_articles:
        return render_template('dashboard.html',all_articles=all_articles)
    else:
        msg='No article Found'
        return render_template('dashoard.html',msg=msg)

class ArticlesForm(Form):
    title = StringField('Title', [validators.Length(min=5, max=100)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_articles',methods=['GET','POST'])
@is_loged_in
def add_articles():
    form=ArticlesForm(request.form)
    if request.method=='POST' and form.validate():

        title=form.title.data
        body=form.body.data
        aurthor=session['username']
        data = myarticles(title=title,body=body,aurthor=aurthor)
        db.session.add(data)
        db.session.commit()
        flash('New article has been created ', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_articles.html',form=form)

@app.route('/edit_articles/<string:id>',methods=['GET','POST'])
@is_loged_in
def edit_articles(id):
    article = myarticles.query.filter_by(id=id).first()
    form=ArticlesForm(request.form)
    form.title.data=article.title
    form.body.data=article.body
    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']
        aurthor=session['username']
        article.title=title
        article.body=body
        article.aurthor=aurthor
        db.session.commit()
        flash('Article has been Updated ', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_articles.html',form=form)

if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)