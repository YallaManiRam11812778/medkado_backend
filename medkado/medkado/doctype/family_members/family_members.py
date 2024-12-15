# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import sys
from frappe.utils import add_to_date

class FamilyMembers(Document):
	pass

@frappe.whitelist()
def my_family_members():
	try:
		family_members = frappe.get_doc("Medkado User",frappe.session.user).as_dict()
		members_filtering = family_members.family_members
		keys_to_pick = ["name1", "age","gender"]
		members_filtered = [{key: d[key] for key in keys_to_pick if key in d} for d in members_filtering]
		return {"success":True,"message":members_filtered,"plan":family_members.my_plan,"date_of_purchase":add_to_date(family_members.date_of_purchase,seconds=1,as_string=True),"validity":add_to_date(family_members.validity,seconds=1,as_string=True)}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Fetching Family Members.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Fetching Plans."}
