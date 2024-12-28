import frappe
import sys

@frappe.whitelist()
def explore_plans():
	try:
		medical_plans = frappe.db.get_all("Medical Plan",["name","count_of_persons","money"])
		available_coupons_in_medical_plan_items = [{"plan_type":f"{_['name']}","money":f"{_['money']}","count_of_persons":_["count_of_persons"],"plan_details": frappe.db.get_all("Medical Plan Items",{"parent":_["name"]},["category","coupons","price"])} for _ in medical_plans]
		sorted_available_coupons_in_medical_plan_items = sorted(available_coupons_in_medical_plan_items, key=lambda person: person["count_of_persons"])
		return {"success":True,"message":sorted_available_coupons_in_medical_plan_items}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Fetching Plans.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Fetching Plans."}

@frappe.whitelist()
def dashboard_data():
	try:
		medkado_user_doc = frappe.get_doc("Medkado User",frappe.session.user)
		dop = str(medkado_user_doc.date_of_purchase if type(medkado_user_doc.date_of_purchase)!=None or medkado_user_doc.date_of_purchase!="" else "0-0-0")
		doe = str(medkado_user_doc.validity if type(medkado_user_doc.validity)!=None or medkado_user_doc.validity!="" else "0-0-0")
		referral_code = medkado_user_doc.referral_code
		if not len(medkado_user_doc.available_coupons)>0:return {"success":True,"message":{"dop":dop,"doe":doe,"available_coupons":0,"withdrawal":medkado_user_doc.balance_amount,"card_number":referral_code}}
		available_coupons =  sum([i.as_dict()["available_number_of_coupons"] for i in medkado_user_doc.available_coupons])
		return {"success":True,"message":{"dop":dop,"doe":doe,"available_coupons":available_coupons,"withdrawal":medkado_user_doc.balance_amount,"card_number":referral_code}}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in DashBoard Data.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in DashBoard."}