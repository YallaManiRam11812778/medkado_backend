# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import razorpay
import sys
import time 
from frappe.utils import now as frappe_now, get_datetime
from frappe import utils
from ast import literal_eval
import json

class MedkadoAdminSettings(Document):
	pass

@frappe.whitelist()
def razorpay_payment_by_users(amount):
	try:
		payment_logs_rp = frappe.new_doc("RazorPay Payment Logs")
		amount_in_rs_to_paise = int(amount)*100
		client_credentials_razorpay = frappe.get_single("Medkado Admin Settings")		
		
		# Initialize Razorpay client
		client = razorpay.Client(auth=(client_credentials_razorpay.client_id, client_credentials_razorpay.client_secret))
		user_doc = frappe.get_doc("User",frappe.session.user)
		expiry_time_unix = int(time.time()) + 3  # 3600 seconds = 1 hour
		payment_link = client.payment_link.create({
		"amount": amount_in_rs_to_paise,     # Amount in smallest currency unit (e.g., paise for INR)
		"currency": "INR",
		"description": "Get MedKado Health-Care Plan.",
		"customer": {
			"name": user_doc.full_name,
			"email": user_doc.email,
			"contact": user_doc.mobile_no
		},
		"notify": {
			"sms": True,
			"email": True
		},
			"expire_by": expiry_time_unix
		})
		if "id" not in payment_link:
			("Payment link creation failed: Missing payment link ID.")
			return False
		if payment_link.get("status") != "created":
			("Payment link not created successfully.")
			return False
		payment_logs_rp.unique_payment_id = payment_link.get("id")
		payment_logs_rp.razor_pay_response = f"{payment_link}"
		payment_logs_rp.status = payment_link.get("status")
		return True
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error(f"Error in Razor Pay Payment  for '{frappe.session.user}'.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		payment_logs_rp.error_message = str(e)
		frappe.throw(str(e))
		return False
	finally:
		payment_logs_rp.insert(ignore_permissions=True)
		frappe.db.commit()

def get_payment_status():
	try:
		only_created_not_payment_done = frappe.db.get_list("RazorPay Payment Logs",filters={"status":"created","active":1},pluck='name')
		if not len(only_created_not_payment_done)>0:
			return
		client_credentials_razorpay = frappe.get_single("Medkado Admin Settings")
		client = razorpay.Client(auth=(client_credentials_razorpay.client_id, client_credentials_razorpay.client_secret))
		for _ in only_created_not_payment_done:
			payment_details = client.payment_link.fetch(_)
			rp_log_status = frappe.get_doc("RazorPay Payment Logs",_)
			rp_log_status.status = payment_details.get("status")
			if rp_log_status.status == "paid":
				user = frappe.get_doc("Medkado User",rp_log_status.owner)
				frappe.session.user = rp_log_status.owner
				from medkado.medkado.doctype.available_coupons_items.available_coupons_items import updating_after_payment_success
				updating_after_payment_success(user.my_plan)
				rp_log_status.save(ignore_permissions=True)
				frappe.db.commit()
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error(f"Error in Getting Payment status.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		return False

@frappe.whitelist(allow_guest=True)
def payment_details_of_user():
	try:
		payload = frappe.request.get_data(as_text=True)
		payload = frappe.parse_json(payload)
		frappe.log_error("Expired linked json",f"{payload}")
		status = payload["payload"]["order"]["entity"]["status"]
		amount_paid = payload["payload"]["order"]["entity"]["amount_paid"]
		name_of_razorpaylogs = payload["payload"]["payment_link"]["entity"]["id"]
		updation_of_doc = frappe.get_doc("RazorPay Payment Logs",name_of_razorpaylogs)
		frappe.session.user = updation_of_doc.owner
		updation_of_doc.status = status
		updation_of_doc.amount = amount_paid
		if status == "expired":updation_of_doc.active = 0
		updation_of_doc.entire_message = f"{payload}"
		updation_of_doc.save(ignore_permissions=True)
		frappe.db.commit()
		if status == "paid":
			user = frappe.get_doc("Medkado User",frappe.session.user)
			from medkado.medkado.doctype.available_coupons_items.available_coupons_items import updating_after_payment_success
			updating_after_payment_success(user.my_plan)
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error(f"Error in payment_details_of_user --- {frappe.session.user}.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		return {'success':False}

@frappe.whitelist()
def payment_details_of_user_dashboard():
	try:
		list_of_details = frappe.db.get_all("RazorPay Payment Logs",{"owner":frappe.session.user},["active","creation","status","razor_pay_response"])
		if not len(list_of_details)>0:
			return {"success":True,"message":[]}
		for _ in list_of_details:
			response = literal_eval(_["razor_pay_response"])
			_["amount"] = response["amount"]/100
			_["url"] = response["short_url"]
			_["amount_paid"] = response["amount_paid"]
			_["url_expiry"] = utils.add_to_date(_["creation"],hours=1)
			del _["razor_pay_response"]
		return {"success":True,"message":list_of_details}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error(f"Error in payment_details_of_user.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		return {'success':False}