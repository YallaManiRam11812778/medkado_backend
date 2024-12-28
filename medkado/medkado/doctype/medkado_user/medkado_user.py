# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime
import random, string
from frappe.utils.password import check_password
import sys
from medkado.medkado.doctype.available_coupons_items.available_coupons_items import updating_after_payment_success
import traceback

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
			if "easy to guess" in str(e) or "Capitalization" in str(e) or "Common names" in str(e) or "Better add a few" in str(e):
				return {"success":False,"message":"Password is easy to guess."}
		new_frappe_user.reload()
		if frappe.db.get_single_value('Medkado Admin Settings', 'generated_code')==referral_code:
			frappe.session.user = email
			updating_after_payment_success(category="Single")
		elif referral_code :
			if frappe.db.exists("Medkado User",{"referral_code":referral_code}):
				refferer_user_doc = frappe.get_doc("Medkado User",{"referral_code":referral_code})
				refferer_user_doc.balance_amount = refferer_user_doc.balance_amount + int(frappe.db.get_single_value('Medkado Admin Settings', 'referral_amount'))
				refferer_user_doc.append("referred_people",{"email":email})
				refferer_user_doc.save(ignore_permissions=True)
				frappe.db.commit()
				refferer_user_doc.reload()

		signing_new_user.insert(ignore_permissions=True)
		frappe.db.commit()
		signing_new_user.reload()
		return {"success":True,"message":api_generate_keys(email=email)}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error(
			"Error Near Sign-Up.",
			"line No:{}\n{}".format(exc_tb.tb_lineno, traceback.format_exc()),
		)
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
def forgot_pwd(email,phoneDigits,newPassword):
	try:
		exists_or_not = frappe.db.get_all("User",{"name":email,"mobile_no":["like",f"%{phoneDigits}"]})
		if not len(exists_or_not)>0:return {"success":False,"message":"Invalid User or Phone number."}
		user_doc = frappe.get_doc("User",email)
		user_doc.new_password = newPassword
		if not user_doc.api_key:
			user_doc.api_key = frappe.gene3rate_hash(length=15)   # Generate a 15-character generate_hash for the API key
		api_secret = frappe.generate_hash(length=15)
		user_doc.api_secret = api_secret  # Generate a 15-character generate_hash for the API secret
		user_doc.save(ignore_permissions=True)  # Save the keys to the database
		frappe.db.commit()  # Ensure the changes are committed to the database
		return {"success":True,"message":{'Authorization': f'token {user_doc.api_key}:{api_secret}'}}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		if "easy to guess" in str(e) or "Capitalization" in str(e) or "Common names" in str(e) or "Better add a few" in str(e):
			return {"success":False,"message":"Password is easy to guess."}
		if "Repeats like" in str(e):
			return {"success":False,"message":"Try to avoid repeated words and characters"}
		frappe.log_error("Error while Updating Password.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		return {"success": False, "message": "Password too weak."}

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

@frappe.whitelist()
def withdrawal_requesting():
	try:
		medkado_user = frappe.get_doc("Medkado User",frappe.session.user)
		user_list = frappe.db.get_value("User",frappe.session.user,"mobile_no")
		prev_balance_amount = float(medkado_user.balance_amount)
		medkado_user.balance_amount = 0
		medkado_user.save(ignore_permissions=True)

		updating_withraw_request = frappe.new_doc("Withdrawal Request")
		updating_withraw_request.username = frappe.session.user
		updating_withraw_request.amount = prev_balance_amount
		updating_withraw_request.phone = user_list
		updating_withraw_request.insert(ignore_permissions=True)
		frappe.db.commit()
		medkado_user.reload()
		return {"success":True,"message":"Withdraw Request Sent."}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Updating Withdrawal Request.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Withdrawal Request."}

@frappe.whitelist()
def referred_people():
	try:
		list_of_referrals = frappe.get_doc("Medkado User",frappe.session.user)
		referral_code = list_of_referrals.referral_code
		list_of_referrals = list_of_referrals.as_dict()
		list_of_referrals = list_of_referrals.referred_people
		if len(list_of_referrals)>0:
			array_of_mails = [i["email"] for i in list_of_referrals]
		else:
			array_of_mails = []
		return {"success":True,"referred_users":array_of_mails,"referral_code":referral_code}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Referred People Fetching.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Referred People Fetching."}

@frappe.whitelist()
def done_payment_for_user():
	try:
		withdraw_amount = frappe.db.get_value("Medkado User",frappe.session.user,"balance_amount")
		all_payments_done = frappe.db.get_all("Withdrawal Request",{"username":frappe.session.user},["amount","status","creation as requested_time","modified as paid_time"])
		return {"success":True,"message":all_payments_done,"withdraw_amount":withdraw_amount}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Fetching Payment Recieved.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw("Error in Fetching Payment Recieved."+str(e))
		return {"success": False, "message": "Error in Fetching Payment Recieved."}
	
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