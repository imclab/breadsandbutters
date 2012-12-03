# -*- coding: utf-8 -*-
from flask.ext.mongoengine.wtf import model_form
from wtforms.fields import * # for our custom signup form
from flask.ext.mongoengine.wtf.orm import validators
from mongoengine import *
from flask.ext.mongoengine import mongoengine
from datetime import datetime


# # PROFILE OBJECT 

# class Profile(mongoengine.Document):
# 	name = StringField()
# 	nickname = StringField()
# 	pic = URLField()
# 	fav = EmbeddedDocumentField()
# 	sandwiches = ListField( EmbeddedDocumentField() )
# 	reviews = ListField( EmbeddedDocumentField() )
# 	likes = IntField()

# ProfileForm = model_form(Profile)

	  
# SANDWICH OBJECT 

class Sandwich(mongoengine.Document):
	title = mongoengine.StringField()
	author = mongoengine.StringField()
	descrip = mongoengine.StringField()
	bread_type = mongoengine.StringField()
	butter_type = mongoengine.StringField()
	instructions = mongoengine.StringField()
	files = mongoengine.ListField( StringField() )

SandwichForm = model_form(Sandwich)	


# # REVIEW OBJECT 

# class Review (mongoengine.Document):
# 	# author = EmbeddedDocumentField()
# 	rating = IntField()
# 	text = StringField()

# ReviewForm = model_form(Review)


# # PRODUCT OBJECT  
	
class Product(mongoengine.Document):
	shelf = mongoengine.StringField() # bread, butter, something
	name = mongoengine.StringField()  # white, wheat ---- almond, cashew
	brand = mongoengine.StringField()

# ProductForm = model_form(Product)


