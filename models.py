# -*- coding: utf-8 -*-
from flask.ext.mongoengine.wtf import model_form
from wtforms.fields import * # for our custom signup form
from flask.ext.mongoengine.wtf.orm import validators
from mongoengine import *
from flask.ext.mongoengine import mongoengine
from datetime import datetime


class Review (mongoengine.EmbeddedDocument):
	rating = mongoengine.IntField()
	text = mongoengine.StringField()

ReviewForm = model_form(Review)


class Product(mongoengine.Document):
	shelf = mongoengine.StringField() # bread, butter, something
	name = mongoengine.StringField()  # white, wheat ---- almond, cashew
	brand = mongoengine.StringField()

ProductForm = model_form(Product)



class User(mongoengine.Document):
	username = mongoengine.StringField(unique=True, max_length=30, required=True, verbose_name="Pick a Username")
	email = mongoengine.EmailField(unique=True, required=True, verbose_name="Email Address")
	password = mongoengine.StringField(default=True,required=True)
	photo = mongoengine.StringField()
	reviews = mongoengine.ListField( mongoengine.EmbeddedDocumentField( Review ))
	likes = mongoengine.IntField()

	active = mongoengine.BooleanField(default=True)
	isAdmin = mongoengine.BooleanField(default=False)

user_form = model_form(User, exclude=['password', 'fileupload'])


# Signup Form created from user_form
class SignupForm(user_form):
	password = PasswordField('Password', validators=[validators.Required(), validators.EqualTo('confirm', message='Passwords must match')])
	confirm = PasswordField('Repeat Password')

# Login form will provide a Password field (WTForm form field)
class LoginForm(user_form):
	password = PasswordField('Password',validators=[validators.Required()])

#################  end of user models/forms ##########################


class Sandwich(mongoengine.Document):
	title = mongoengine.StringField()
	# author = mongoengine.ReferenceField(Profile)  #Sandwich.author.name - example of how to pull
	user = mongoengine.ReferenceField( 'User', dbref=True )
	descrip = mongoengine.StringField()
	bread_type = mongoengine.StringField()
	butter_type = mongoengine.StringField()
	instructions = mongoengine.StringField()
	additions = mongoengine.StringField()
	files = mongoengine.ListField( StringField() )
	slug = mongoengine.StringField()
	timestamp = mongoengine.DateTimeField()
	products = mongoengine.ListField( mongoengine.ReferenceField(Product) )
	favored = mongoengine.ListField( mongoengine.ReferenceField(User) )

SandwichForm = model_form(Sandwich)


	





