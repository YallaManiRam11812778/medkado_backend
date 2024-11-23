# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import sys
import pandas as pd
from ast import literal_eval
class AvailableCouponsItems(Document):
	pass

def payment_response():
	pass

@frappe.whitelist(["POST"])
def adding_family_details(family_details):
	if not isinstance(family_details,list):
		family_details = literal_eval(family_details)
	user_doc = frappe.get_doc("Medkado User",frappe.session.user)
	for i in family_details:
		user_doc.append("family_members",i)
	user_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"success":True}

@frappe.whitelist()
def get_this_plan(category:str,payemnt=None):
	try:
		if payemnt==None:
			response_from_gateway = payment_response()
			if not response_from_gateway:return False
		selected_medical_plan = frappe.get_doc("Medical Plan",category)
		medical_plan_items = selected_medical_plan.medical_plan_items
		medkado_user_doc = frappe.get_doc("Medkado User",frappe.session.user)
		medkado_user_doc.my_plan = category
		for i in medical_plan_items:
			medkado_user_doc.append("available_coupons",{"category":i["category"],"coupons":i["coupons"]})
		medkado_user_doc.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Getting Plan Error.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Getting Plans."}
	
@frappe.whitelist()
def coupons_page():
	try:
		medkado_user_doc = frappe.get_doc("Medkado User",frappe.session.user)
		available_coupons =  [i.as_dict() for i in medkado_user_doc.available_coupons]
		if not len(available_coupons)>0: return {"success":True,"message":[{"category": "No Coupons Left","available_number_of_coupons": 0}]}
		df = pd.DataFrame.from_records(available_coupons)
		df["available_number_of_coupons"] = df["available_number_of_coupons"].astype(int)
		df = df.groupby(["category"])["available_number_of_coupons"].agg("sum").reset_index()
		df = df[df['available_number_of_coupons'] > 0].to_dict("records")
		return {"success":True,"message":df}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Coupons Left Error.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": f"Error in Coupons Fetch for user - '{frappe.session.user}'."}