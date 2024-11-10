# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MedicalPlan(Document):
	pass

@frappe.whitelist()
def adding_medical_plan(number_of_persons:str):
	med_plan = frappe.new_doc("Medical Plan")
	med_plan.number_of_persons = number_of_persons
	med_plan.insert()
	frappe.db.commit()