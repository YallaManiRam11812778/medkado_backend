# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MedicalPlan(Document):
	def after_insert(self):
		if self.number_of_persons == "Couple":
			self.append("medical_plan_items",{"category":"Dental","coupons":"x5"})
			self.save()
			frappe.db.commit()
	
	def on_update(self):
		print("Updated ======= ",self.as_dict())

@frappe.whitelist()
def adding_medical_plan(number_of_persons:str,money):
	med_plan = frappe.new_doc("Medical Plan")
	med_plan.number_of_persons = number_of_persons
	med_plan.money = money
	med_plan.insert()
	frappe.db.commit()