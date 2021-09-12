import datetime

from flask_bcrypt import generate_password_hash #type:ignore
from flask_login import UserMixin #type:ignore

from peewee import * #type:ignore

DATABASE = SqliteDatabase('social.db')  #type:ignore

class User(UserMixin, Model): #type:ignore
	username = CharField() #type:ignore
	email = CharField(unique = True) #type:ignore
	dob = CharField() #type:ignore
	gender = CharField() #type:ignore
	password = CharField(max_length = 100) #type:ignore
	joined_at = DateTimeField(default = datetime.datetime.now) #type:ignore

	class Meta:
		database = DATABASE
		order_by = ('-joined_at',)




	@classmethod
	def create_user(cls, username, email, password, dob, gender):
		try:
			with DATABASE.transaction():
				cls.create(
					username = username,
					email = email,
					dob = dob,
					gender = gender,
					password = generate_password_hash(password),
					)

		except IntegrityError: #type:ignore
			raise ValueError("User already exists")


# DATABASE.create_tables([User])


def initialize():
	DATABASE.connect()
	DATABASE.create_tables([User], safe = True)
	DATABASE.close()
