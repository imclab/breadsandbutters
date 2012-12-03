import os, datetime, sys, csv
import re
import models
import data_setup

from unidecode import unidecode
from flask import Flask, request, render_template, redirect, abort
from mongoengine import *
from flask.ext.mongoengine import mongoengine
from werkzeug import secure_filename


import boto # Amazon AWS library
import StringIO # Python Image Library




# -------------------------------------------------------------- "/"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') # put SECRET_KEY variable inside .env file with a random string of alphanumeric characters
app.config['CSRF_ENABLED'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 megabyte file upload

mongoengine.connect('mydata', host=os.environ.get('MONGOLAB_URI'))
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

@app.route("/")
def mainpage():

    featured = {
        'pic' : '/static/img/featured.png',
        'name' : 'Electric Elvis',
        'descrip' : 'Almond butter, bananas, and guava paste slices on toasted home-made wheat bread. "An Elvis man should love it."',
        'author' : 'Matthew Epler'
    }

    return render_template('index.html', **featured)


# ----------------------------------------------------------------- /SHARE 
@app.route("/share", methods=['GET', 'POST'])
def share():
    
    sandwich_form = models.SandwichForm(request.form)
    
    if request.method == "POST" and sandwich_form.validate():
        
        uploaded_file = request.files['fileupload']
        # app.logger.info(file)
        # app.logger.info(file.mimetype)
        # app.logger.info(dir(file))
        
        # Uploading is fun
        # 1 - Generate a file name with the datetime prefixing filename
        # 2 - Connect to s3
        # 3 - Get the s3 bucket, put the file
        # 4 - After saving to s3, save data to database

        if uploaded_file and allowed_file(uploaded_file.filename):
            # create filename, prefixed with datetime
            now = datetime.datetime.now()
            filename = now.strftime('%Y%m%d%H%M%s') + "-" + secure_filename(uploaded_file.filename)
            # thumb_filename = now.strftime('%Y%m%d%H%M%s') + "-" + secure_filename(uploaded_file.filename)

            # connect to s3
            s3conn = boto.connect_s3(os.environ.get('AWS_ACCESS_KEY_ID'),os.environ.get('AWS_SECRET_ACCESS_KEY'))

            # open s3 bucket, create new Key/file
            # set the mimetype, content and access control
            b = s3conn.get_bucket(os.environ.get('AWS_BUCKET')) # bucket name defined in .env
            k = b.new_key(b)
            k.key = filename
            k.set_metadata("Content-Type", uploaded_file.mimetype)
            k.set_contents_from_string(uploaded_file.stream.read())
            k.make_public()

            # save information to MONGO database
            # did something actually save to S3
            templateData = {}
            if k and k.size > 0:
                
                sandwich = models.Sandwich()
                sandwich.title = request.form.get('title', 'untitled sandwich' )
                sandwich.author = request.form.get('author', 'mystery maker')
                sandwich.descrip = request.form.get('descrip', 'it is what it is')
                sandwich.bread_type = request.form.get('bread_type')
                sandwich.butter_type = request.form.get('butter_type')
                sandwich.instructions = request.form.get('instructions')
                sandwich.files.append(filename)
                sandwich.save()

                templateData = {
                    'sandwich' : sandwich
                }

            return render_template( 'success.html', **templateData )
    
    else:

        allBreads = models.Product.objects(shelf="bread")
        allButters = models.Product.objects(shelf="butter")
    
        templateData = {
            'breads' : allBreads,
            'butters' : allButters,
            'form' : sandwich_form
        }

    return render_template( 'share.html', **templateData )


# ------------------------------------------------------------------------- DATA
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


# ------------------------------------------------------------------ SERVER STARTUP

if __name__ == "__main__":
	app.debug = True
	
	port = int(os.environ.get('PORT', 5000)) # locally PORT 5000, Heroku will assign its own port
	app.run(host='0.0.0.0', port=port)



