from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Regexp, ValidationError, Email, Length, EqualTo
from datetime import date
from models import User

def email_exists(form,field):
	if User.select().where(User.email == field.data).exists():
		raise ValidationError('User with this email already exists.')

def validate_dob(form, field):
	try:
		# if int(''.join(field.data.split('-')[::-1]))<1900:
		# 	raise ValidationError('Please enter a valid date of birth.')
		print(type(field.data))
		# elif int(''.join(field.data.split('-')[::-1]))>int(date.today().strftime('%Y%m%d')):
		# 	raise ValidationError('Please enter a valid date of birth.')
	except ValueError:
		raise ValidationError('Please enter a valid date of birth.')

class RegisterForm(Form):
	style={
			'class':'inputField'
		}

	username = StringField(
		'Username',
		validators=[
			DataRequired(),
			Regexp(
				r'^[a-zA-Z0-9_]+$',
				message = ("Invalid format for username.")
				)
		],
		render_kw=style)

	email = StringField(
		'Email',
		validators=[
			DataRequired(),
			Email(),
			email_exists
		],
		render_kw=style)

	dob = DateField(
		'Date of Birth',
		validators=[
			DataRequired(),
			validate_dob
		],
		format='%d-%m-%Y',
		render_kw=style
		
	)

	gender = SelectField(
		'Gender',
		choices = [(1, 'Male'), (2, 'Female')],
		validators=[
			DataRequired()
		],
		render_kw={
			'class':'inputField',
			'id':'genderSelect'
		}
	)

	password = PasswordField(
		'Password',
		validators=[
			DataRequired(),
			Length(min=5, message="Password must be atleast 5 characters long."),
			EqualTo('password2', message = 'Passwords must match.')
		],
		render_kw=style)
	password2 = PasswordField(
		'Confirm Password',
		validators=[DataRequired()
		],
		render_kw=style)


class LoginForm(Form):
	style={
		'class':'inputField'
	}
	email = StringField('Email', validators=[DataRequired(), Email()], render_kw=style)
	password = PasswordField('Password', validators=[DataRequired()], render_kw=style)

