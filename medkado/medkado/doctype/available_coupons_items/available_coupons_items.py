# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import sys
import pandas as pd
from ast import literal_eval
from frappe import utils
from medkado.medkado.doctype.medkado_admin_settings.medkado_admin_settings import razorpay_payment_by_users

class AvailableCouponsItems(Document):
	pass

@frappe.whitelist(["POST"])
def adding_family_details(family_details):
	if not isinstance(family_details,list):
		family_details = literal_eval(family_details)
	if not len(family_details)>0:
		return False
	for item in family_details:
		item['name1'] = item.pop('name')
	frappe.db.delete("Family Members",{"parent":frappe.session.user})
	frappe.db.commit()
	user_doc = frappe.get_doc("Medkado User",frappe.session.user)
	for i in family_details:
		user_doc.append("family_members",i)
	user_doc.save(ignore_permissions=True)
	frappe.db.commit()
	amount = frappe.db.get_value("Medical Plan",{"count_of_persons":len(family_details)},["money"])
	response_of_razor_pay = razorpay_payment_by_users(amount=amount)
	return response_of_razor_pay

def updating_after_payment_success(category):
	try:
		selected_medical_plan = frappe.get_doc("Medical Plan",category)
		medical_plan_items = selected_medical_plan.medical_plan_items
		medkado_user_doc = frappe.get_doc("Medkado User",frappe.session.user)
		for i in medical_plan_items:
			i = i.__dict__
			medkado_user_doc.append("available_coupons",{"category":i["category"],"available_number_of_coupons":int(i["coupons"].replace("x",""))})
		medkado_user_doc.my_plan = category
		medkado_user_doc.date_of_purchase = utils.today()
		medkado_user_doc.validity = utils.add_to_date(utils.now(),years=1)
		medkado_user_doc.save(ignore_permissions=True)
		frappe.db.commit()
		return True
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Getting Plan Error.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in updating_after_payment_success."}
	
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