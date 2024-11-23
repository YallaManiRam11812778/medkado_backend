frappe.ui.form.on('Medkado Admin Settings', {
    refresh: function(frm) {
        frm.add_custom_button(__('Generate Code'), function() {
            // Generate a unique referral code
            const generatedCode = generateUniqueReferralCode();

            // Set the generated code in the 'generated_code' field
            frm.set_value('generated_code', generatedCode);
            frm.save()
        }, __("Utilities"));
    }
});

// Function to generate a unique referral code
function generateUniqueReferralCode() {
    const now = new Date();
    const secondsSinceEpoch = Math.floor(now.getTime() / 1000).toString();

    const allowedChars = 'abcdefghijklmnpqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ123456789';
    let uniqueCode = '';
    for (let i = 0; i < 5; i++) {
        uniqueCode += allowedChars.charAt(Math.floor(Math.random() * allowedChars.length));
    }

    // Combine timestamp and unique code
    const combined = secondsSinceEpoch.substring(0, 8) + uniqueCode.toLowerCase();

    // Shuffle the combined string
    return shuffleString(combined).substring(0, 12); // Ensure length is exactly 12 characters
}

// Function to shuffle a string
function shuffleString(string) {
    const array = string.split('');
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]]; // Swap elements
    }
    return array.join('');
}