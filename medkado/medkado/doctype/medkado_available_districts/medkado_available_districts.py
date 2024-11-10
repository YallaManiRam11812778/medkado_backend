# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MedkadoAvailableDistricts(Document):
	pass

@frappe.whitelist()
def maps_page():
	location = frappe.db.get_all("Medkado User",{"name":frappe.session.user},pluck="location")[0]
	list_of_hospitals = frappe.db.get_all("Medkado Hospitals",{"district":location},["location","hospital_short_name","hospital_name"])
	for i in list_of_hospitals:
		check_coupon_avaialablity = frappe.db.get_all("Available Coupons Items", {"parenttype":'Medkado Hospitals',"parent":f'{i["hospital_short_name"]} - {location}',"parentfield":"available_coupons_items"},pluck="category")
		i["category"] = check_coupon_avaialablity
	return {"success":True,"message":list_of_hospitals}
