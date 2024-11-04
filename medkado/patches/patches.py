import frappe
##### Patches

def execute():
	if not frappe.db.exists("Role",{"role_name":"Medkado User"}):
		new_role = frappe.new_doc("Role")
		new_role.role_name = "Medkado User"
		new_role.insert()
		frappe.db.commit()