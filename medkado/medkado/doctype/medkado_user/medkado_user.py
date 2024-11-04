# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime
import random, string
from frappe.utils.password import check_password
# from frappe.core.doctype.user.user import generate_keys

class MedkadoUser(Document):
	def after_insert(self):
		self.referral_code = creation_of_unique_referal_code()
		frappe.db.commit()
		super().save() # call the base save method

@frappe.whitelist(allow_guest=True)
def sign_up(email:str,password:str,referral_code=None):
	try:
		signing_new_user = frappe.new_doc("Medkado User")
		signing_new_user.email = email

		###### Adding new user in frappe
		new_frappe_user = frappe.new_doc("User")
		new_frappe_user.email = email
		new_frappe_user.first_name = email.split("@")[0]
		new_frappe_user.new_password = password
		new_frappe_user.append("roles",{"role":"Medkado User"})
		
		new_frappe_user.insert(ignore_permissions=True)
		frappe.db.commit()
		new_frappe_user.reload()
		response = {}
		if referral_code :
			if frappe.db.exists("Medkado User",{"referral_code":referral_code}):
				refferer_user_doc = frappe.get_doc("Medkado User",{"referral_code":referral_code})
				refferer_user_doc.append("referred_people",{"email":email})
				refferer_user_doc.save(ignore_permissions=True)
				frappe.db.commit()
				refferer_user_doc.reload()
				response = response | {"pop_up":"Done!"}
			else:
				response = response | {"pop_up":"Referral Code doesn't exists."}

		signing_new_user.insert(ignore_permissions=True)
		frappe.db.commit()
		signing_new_user.reload()
		response = response | {"message":api_generate_keys(email=email)}
		return response
	except Exception as e:
		frappe.log_error("Error in Signing-Up",f"'{email}' got an error -> \n {str(e)}")
		return {"success":False,"message":"Please Contact Our Support Team OR Try again Signing Up.","pop_up":"Sorry for the inconvenience caused. Contact Our Support Team."}

@frappe.whitelist(allow_guest=True)
def login_medkado(email,password):
	try:
		get_decrypted_pwd = check_password(email,password)
		frappe.session.user = email
		user = frappe.get_doc("User", email)
		if not user.api_key:
			user.api_key = frappe.gene3rate_hash(length=15)   # Generate a 15-character generate_hash for the API key
		api_secret = frappe.generate_hash(length=15)
		user.api_secret = api_secret  # Generate a 15-character generate_hash for the API secret
		user.save(ignore_permissions=True)  # Save the keys to the database
		frappe.db.commit()  # Ensure the changes are committed to the database
		return {"success":True,"message":{'Authorization': f'token {user.api_key}:{api_secret}'}}
	except Exception as e:
		return {"success":False,"message":str(e)}

		
def creation_of_unique_referal_code()->str:
	# Get the current date and time (fixed for this moment)
	now = datetime.datetime.now()
	seconds_since_epoch = str(int(now.timestamp()))

	# Generate a unique code with 4 characters, excluding 'o'
	allowed_chars = string.ascii_letters.replace('o', '') + string.digits.replace('o', '')
	unique_code = ''.join(random.choice(allowed_chars) for _ in range(5)).lower()

	# Combine timestamp and unique code ensuring total length is 12 characters
	combined = seconds_since_epoch[:8] + unique_code  # Use 8 digits from the timestamp

	# Adjust to ensure combined length is exactly 12 characters
	return combined[:12]

def api_generate_keys(email:str):
	user = frappe.get_doc("User", email)
	if not user.api_key:
		user.api_key = frappe.generate_hash(length=15)   # Generate a 15-character generate_hash for the API key
	api_secret = frappe.generate_hash(length=15)
	user.api_secret = api_secret  # Generate a 15-character generate_hash for the API secret
	user.save(ignore_permissions=True)  # Save the keys to the database
	frappe.db.commit()  # Ensure the changes are committed to the database
	return {'Authorization': f'token {user.api_key}:{api_secret}'}