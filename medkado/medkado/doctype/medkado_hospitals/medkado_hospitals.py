# Copyright (c) 2024, ramunavailable@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import random
from frappe.utils import now as frappe_now
import sys

class MedkadoHospitals(Document):
	def autoname(self):
		self.name = self.hospital_short_name + " - " + self.district
	def after_insert(self):
		self.hospital_code = shuffle_and_add_number(self.hospital_short_name)
		frappe.db.commit()
		super().save() # call the base save method

@frappe.whitelist()
def redeem_coupon(category:str,hospital_code:str):
	try:
		user_district = frappe.db.get_value('Medkado User', frappe.session.user, "location")
		coupons_avaiablity_for_user = frappe.db.get_all("Available Coupons Items",{"parentfield":"available_coupons","parenttype":"Medkado User","parent":frappe.session.user,"category":category,"available_number_of_coupons":[">",0]},pluck="name")
		if not len(coupons_avaiablity_for_user)>0:return {"success":False,"message":f"{category} - is not avaiable for you."}
		hospital_name = frappe.db.get_all("Medkado Hospitals",{"hospital_code":hospital_code},["hospital_short_name"])

		if not len(hospital_name)>0:return {"success":False,"message":f"Invalid Code. - {hospital_code}"}
		hospital_name = hospital_name[0]["hospital_short_name"]
		hospital_name_loc = f'{hospital_name +" - "+ user_district}'
		check_coupon_avaialablity = frappe.db.sql(f"""select category from `tabAvailable Coupons Items` where parenttype='Medkado Hospitals' and parent='{hospital_name_loc}' and parentfield='available_coupons_items';""",as_dict=True)
		if not len(check_coupon_avaialablity)>0: return {"success":False,"message":"Coupon is not available in Hospital."}
		check_coupon_avaialablity = [d['category'] for d in check_coupon_avaialablity if 'category' in d]
		if category not in check_coupon_avaialablity: return {"success":False,"message":f"selected '{category}' is not availabe in Hospital."}
		hospital_doc = frappe.get_doc("Medkado Hospitals",hospital_name_loc)
		hospital_doc.append("redeem_coupon_workflow",{"category":category,"medkado_user":frappe.session.user,"time":frappe_now()})
		hospital_doc.save(ignore_permissions=True)
		hospital_doc.reload()
		frappe.db.commit()
		available_number_of_coupons = frappe.db.get_value("Available Coupons Items",coupons_avaiablity_for_user[0],"available_number_of_coupons")
		decreasing_count_of_coupon = frappe.db.set_value("Available Coupons Items",coupons_avaiablity_for_user[0],{"available_number_of_coupons":int(available_number_of_coupons)-1})
		frappe.db.commit()
		reload_doc = frappe.get_doc("Medkado User",frappe.session.user)
		reload_doc.reload()
		return {"success":True,"message":"Redeemed."}
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		frappe.log_error("Error in Redemption of Coupons.",
						 "line No:{}\n{}".format(exc_tb.tb_lineno, str(e)))
		frappe.throw(str(e))
		return {"success": False, "message": "Error in Redemption of Coupons."}

def shuffle_and_add_number(word):
	# Create a list of digits from '1' to '9', excluding '0'
	valid_digits = [str(i) for i in range(1, 10)]  # This excludes '0'

	# Shuffle the characters in the word, excluding 'o' if present
	word_list = [ch for ch in word if ch != 'o']  # Remove any 'o' from the word
	random.shuffle(word_list)  # Shuffle the list in place
	shuffled_word = ''.join(word_list)  # Join the list back into a string
	
	# Ensure the shuffled word has 3 characters (if it's smaller or missing characters, pad it)
	if len(shuffled_word) < 3:
		shuffled_word = shuffled_word.ljust(3, random.choice(valid_digits))  # Pad with random digits
	
	# Generate 5 random digits (from '1' to '9')
	random_digits = ''.join(random.choice(valid_digits) for _ in range(5))
	
	# Combine the shuffled word with the random digits to make the final result
	result = shuffled_word + random_digits
	
	return result