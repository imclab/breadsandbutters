import os, datetime, sys, csv
import re
import models
import data_setup
import random
import boto # Amazon AWS library
import StringIO # Python Image Library

from unidecode import unidecode
from flask import Flask, session, request, url_for, escape, render_template, json, jsonify, flash, redirect, abort
from mongoengine import *
from flask.ext.mongoengine import mongoengine
from werkzeug import secure_filename

# Flask-Login 
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)

# Library
from flaskext.bcrypt import Bcrypt

#custom user library - maps User object to User model
from libs.user import *


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') # put SECRET_KEY variable inside .env file with a random string of alphanumeric characters
app.config['CSRF_ENABLED'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 megabyte file upload

mongoengine.connect('mydata', host=os.environ.get('MONGOLAB_URI'))
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

flask_bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"


# ------------------------------------------------------- LOAD USER >>>
@login_manager.user_loader
def load_user(id):
    if id is None:
        redirect('/login')

    user = User()
    user.get_by_id(id)
    if user.is_active():
        return user
    else:
        return None

login_manager.setup_app(app)


# ----------------------------------------------------------- INDEX >>>
@app.route("/")
def mainpage():


    featured = models.Sandwich.objects.get(title="Electric Elvis")

    sandwiches = models.Sandwich.objects()

    templateData = {
        'sandwiches' : sandwiches,
        'featured' : featured
    }

    return render_template('index.html', **templateData)


# ----------------------------------------------------------- /REGISTER >>>
@app.route("/register", methods=['GET','POST'])
def register():
    
    # prepare registration form 
    registerForm = models.SignupForm(request.form)
    app.logger.info(request.form)

    if request.method == 'POST' and registerForm.validate():

        email = request.form['email']
        username = request.form['username']
        uploaded_file = request.files['fileupload']
        
        filename = secure_filename(uploaded_file.filename)
        s3conn = boto.connect_s3(os.environ.get('AWS_ACCESS_KEY_ID'),os.environ.get('AWS_SECRET_ACCESS_KEY'))
        b = s3conn.get_bucket(os.environ.get('AWS_BUCKET')) 
        k = b.new_key(b)
        k.key = filename
        k.set_metadata("Content-Type", uploaded_file.mimetype)
        k.set_contents_from_string(uploaded_file.stream.read())
        k.make_public()

        # generate password hash
        password_hash = flask_bcrypt.generate_password_hash(request.form['password'])
        
        user = User(username=username, email=email, password=str(password_hash))

        # save new user, but there might be exceptions (uniqueness of email and/or username)
        try:
            user.save() 
            if login_user(user, remember="no"):
                flash("Logged in!")

                return redirect(request.args.get("next") or '/')
            else:
                flash("unable to log you in")

        # got an error, most likely a uniqueness error
        except mongoengine.queryset.NotUniqueError:
            e = sys.exc_info()
            exception, error, obj = e
            
            app.logger.error(e)
            app.logger.error(error)
            app.logger.error(type(error))

            # uniqueness error was raised. tell user (via flash messaging) which error they need to fix.
            if str(error).find("email") > -1:           
                flash("Email submitted is already registered.","register")
    
            elif str(error).find("username") > -1:
                flash("Username is already registered. Pick another.","register")

            app.logger.error(error) 


    # prepare registration form         
    templateData = {
        'form' : registerForm
    }
    
    return render_template("/auth/register.html", **templateData)

    
# Login route - will display login form and receive POST to authenicate a user
@app.route("/login", methods=["GET", "POST"])
def login():

    # get the login and registration forms
    loginForm = models.LoginForm(request.form)
    
    # is user trying to log in?
    # 
    if request.method == "POST" and 'email' in request.form:
        email = request.form["email"]

        user = User().get_by_email_w_password(email)
        
        # if user in database and password hash match then log in.
        if user and flask_bcrypt.check_password_hash(user.password,request.form["password"]) and user.is_active():
            remember = request.form.get("remember", "no") == "yes"

            if login_user(user, remember=remember):
                flash("Logged in!")
                return redirect(request.args.get("next") or '/admin')
            else:

                flash("unable to log you in","login")
    
        else:
            flash("Incorrect email and password submission","login")
            return redirect("/login")

    else:

        templateData = {
            'form' : loginForm
        }

        return render_template('/auth/login.html', **templateData)



# ----------------------------------------------------------------- /USER >>>
@app.route("/user/<username>")
def user(username):

    try:
        user = models.User.objects.get(username=username)
        app.logger.debug( user.photo )

    except Exception:
        e = sys.exc_info()
        app.logger.error(e)
        abort(404)

    templateData = {
        'user' : user,
        'current_user' : current_user,
    }

    return render_template("user.html", **templateData) 



# ----------------------------------------------------------------- /SHARE >>>
@app.route("/share", methods=['GET', 'POST'])
def share():
    
    sandwich_form = models.SandwichForm(request.form)
    templateData = {}

    if request.method == "POST":
        
        uploaded_file = request.files['fileupload']

        if uploaded_file:
            now = datetime.datetime.now()
            filename = secure_filename(uploaded_file.filename)
            s3conn = boto.connect_s3(os.environ.get('AWS_ACCESS_KEY_ID'),os.environ.get('AWS_SECRET_ACCESS_KEY'))
            b = s3conn.get_bucket(os.environ.get('AWS_BUCKET')) 
            k = b.new_key(b)
            k.key = filename
            k.set_metadata("Content-Type", uploaded_file.mimetype)
            k.set_contents_from_string(uploaded_file.stream.read())
            k.make_public()

            if k and k.size > 0:
                
                sandwich = models.Sandwich()
                sandwich.title = request.form.get('title', 'untitled sandwich' )
                sandwich.author = request.form.get('author', 'mystery maker')
                sandwich.descrip = request.form.get('descrip', 'it is what it is')
                sandwich.bread_type = request.form.get('bread_type', 'other')
                sandwich.butter_type = request.form.get('butter_type', 'other')
                sandwich.additions = request.form.get('additions', 'none')
                sandwich.instructions = request.form.get('instructions', 'put it in your mouth and chew')
                sandwich.files.append(filename)
                app.logger.debug( filename )
                sandwich.timestamp = now
                sandwich.slug = slugify( sandwich.author + "-" + sandwich.title )
                sandwich.save()

                templateData = {
                    'sandwich' : sandwich
                }

            return render_template( 'success.html', **templateData )
    
    else:

        products  = models.Product.objects()
    
        templateData = {
            'products' : products,
            'form' : sandwich_form
        }

    return render_template( 'share.html', **templateData )



# ------------------------------------------------------------------------- LOOK >>>
@app.route("/look/<sandwich_slug>")
def look(sandwich_slug):

    try:
        sandwich = models.Sandwich.objects.get(slug=sandwich_slug)

        templateData = {
            'sandwich' : sandwich
        }

        return render_template("look.html", **templateData)

    except:

        return render_template("404.html"), 404



# ------------------------------------------------------------------------- EDIT >>>
@app.route( "/edit/<sandwich_slug>", methods=['POST', 'GET'] )
def edit(sandwich_slug):
    
    sandwich = models.Sandwich.objects.get(slug=sandwich_slug)
    
    if request.method == "GET":
        try:
            products  = models.Product.objects()
    
            templateData = {
                'products' : products,
                'sandwich' : sandwich
            }
    
            return render_template("edit.html", **templateData)
    
        except:
    
            return render_template("404.html"), 404

    if request.method == 'POST':

        # photo file upload
        uploaded_file = request.files['fileupload']

        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            s3conn = boto.connect_s3(os.environ.get('AWS_ACCESS_KEY_ID'),os.environ.get('AWS_SECRET_ACCESS_KEY'))
            b = s3conn.get_bucket(os.environ.get('AWS_BUCKET')) 
            k = b.new_key(b)
            k.key = filename
            sandwich.files.append(filename)
            k.set_metadata("Content-Type", uploaded_file.mimetype)
            k.set_contents_from_string(uploaded_file.stream.read())
            k.make_public()

        sandwich.title = request.form.get('title', 'untitled sandwich' )
        sandwich.author = request.form.get('author', 'mystery maker')
        sandwich.descrip = request.form.get('descrip', 'it is what it is')
        sandwich.bread_type = request.form.get('bread_type', 'other')
        sandwich.butter_type = request.form.get('butter_type', 'other')
        sandwich.additions = request.form.get('additions', 'none')
        sandwich.instructions = request.form.get('instructions', 'put it in your mouth and chew')
        sandwich.slug = slugify( sandwich.author + "-" + sandwich.title )
        sandwich.save()

        templateData = {
            'sandwich' : sandwich
        }

        return render_template("success.html", **templateData)



# ------------------------------------------------------------------------- DATA >>>
@app.route("/automateproducts")
def test():

    breads = ['White', 'Wheat', 'Pumpernickel', 'Rye', 'Homemade', 'Cinnamon Raisin', 'Grain']
    butters = ['Almond', 'Cashew', "Peanut"]

    # 2 loops , 1 per list, create document for db

    for b in breads:
        tmpBread = models.Product(shelf="bread",name=b)
        tmpBread.save()

    for b in butters:
        tmpButter = models.Product(shelf="butter",name=b)
        tmpButter.save()

    return "ok"



# ------------------------------------------------------------------------ ERRORS
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

def allowed_file(filename):
    return '.' in filename and \
           filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



# ------------------------------------------------------------------------ SLUGIFY
# Slugify the title to create URLS
# via http://flask.pocoo.org/snippets/5/
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))


# ------------------------------------------------------------------ SERVER STARTUP

if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)



