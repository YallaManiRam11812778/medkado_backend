# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime
import random, string
from frappe.utils.password import check_password
import sys

class MedkadoUser(Document):
	def after_insert(self):
		self.referral_code = creation_of_unique_referal_code()
		frappe.db.commit()
		super().save() # call the base save method

@frappe.whitelist(allow_guest=True)
def locations_dropdown():
	try:
		locations = frappe.db.get_all("Medkado Available Districts",["name"])
		if len(locations)>0:
			for idx, district in enumerate(locations, start=1):
				district["id"] = idx
		if not len(locations)>0:return {"success":False,"message":"Districts are not defined yet."}
		return {"success":True,"message":locations}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Fetching Available Districts.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Fetching Available Districts."}

@frappe.whitelist(allow_guest=True)
def sign_up(email:str,password:str,referral_code=None,mobile_no:str=None,district:str=None):
	try:
		signing_new_user = frappe.new_doc("Medkado User")
		signing_new_user.email = email
		signing_new_user.location = district

		###### Adding new user in frappe
		try:
			new_frappe_user = frappe.new_doc("User")
			new_frappe_user.email = email
			new_frappe_user.first_name = email.split("@")[0]
			new_frappe_user.new_password = password
			new_frappe_user.mobile_no = mobile_no
			new_frappe_user.location = district
			new_frappe_user.append("roles",{"role":"Medkado User"})
			
			new_frappe_user.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			if "Duplicate" in str(e):
				if "mobile_no" in str(e): error = "Mobile Number"
				if f"{email}" in str(e): error = "Email"
				return {"success":False,"message":f" {error} is already Used."}
			if "easy to guess" in str(e):
				return {"success":False,"message":"Password is easy to guess."}
		new_frappe_user.reload()
		if referral_code :
			if frappe.db.exists("Medkado User",{"referral_code":referral_code}):
				refferer_user_doc = frappe.get_doc("Medkado User",{"referral_code":referral_code})
				refferer_user_doc.append("referred_people",{"email":email})
				refferer_user_doc.save(ignore_permissions=True)
				frappe.db.commit()
				refferer_user_doc.reload()

		signing_new_user.insert(ignore_permissions=True)
		frappe.db.commit()
		signing_new_user.reload()
		return {"success":True,"message":api_generate_keys(email=email)}
	except Exception as e:
		frappe.log_error("Error in Signing-Up",f"'{email}' got an error -> \n {str(e)}")
		return {"success":False,"message":"Please Contact Our Support Team OR Try again Signing Up."}

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

@frappe.whitelist(allow_guest=True)
def forgot_pwd(user_name,phone_num,pwd):
	try:
		exists_or_not = frappe.db.get_all("User",{"name":user_name,"phone":["like",f"%{phone_num}"]})
		if not len(exists_or_not)>0:return {"success":False,"message":"Invalid User or Phone number."}
		user_doc = frappe.get_doc("User",user_name)
		user_doc.new_password = pwd
		if not user_doc.api_key:
			user_doc.api_key = frappe.gene3rate_hash(length=15)   # Generate a 15-character generate_hash for the API key
		api_secret = frappe.generate_hash(length=15)
		user_doc.api_secret = api_secret  # Generate a 15-character generate_hash for the API secret
		user_doc.save(ignore_permissions=True)  # Save the keys to the database
		frappe.db.commit()  # Ensure the changes are committed to the database
		return {"success":True,"message":{'Authorization': f'token {user_doc.api_key}:{api_secret}'}}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error while Updating Password.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error while Updating Password."}

@frappe.whitelist(allow_guest=True)
def validate_auth_token(auth_token):
	try:
		if "Authorization" not in str(auth_token):return {"success":False}
		api = str(auth_token).split("token ")[-1].split("'}")[0].split(":")
		api_key = api[0]
		api_secret = api[-1]
		api_key_user = frappe.db.get_all("User",{"api_key":api_key},pluck="name")
		if len(api_key_user)>0:
			user_secret_validation = frappe.get_doc("User",api_key_user[0])
			if api_secret != user_secret_validation.get_password('api_secret'):
				return False
			else:
				return True
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Validating Tokens.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Fetching Plans."}

		
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