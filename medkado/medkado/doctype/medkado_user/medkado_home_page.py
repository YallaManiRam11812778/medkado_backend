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
