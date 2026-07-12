/* ==================== */
/* Profile Page JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const menuItems = document.querySelectorAll('.menu-item');
    const contentSections = document.querySelectorAll('.content-section');
    const profileForms = document.querySelectorAll('.profile-form');
    
    // Section switching
    menuItems.forEach(item => {
        item.addEventListener('click', () => {
            const sectionId = item.dataset.section;
            
            // Update menu active state
            menuItems.forEach(mi => mi.classList.remove('active'));
            item.classList.add('active');
            
            // Show corresponding section
            contentSections.forEach(section => {
                section.classList.remove('active');
                if (section.id === sectionId) {
                    section.classList.add('active');
                }
            });
        });
    });
    
    // Edit section
    window.editSection = function(sectionId) {
        const form = document.getElementById(`${sectionId}Form`);
        const actions = document.getElementById(`${sectionId}Actions`);
        
        if (form && actions) {
            form.classList.add('editing');
            
            // Enable form fields
            const fields = form.querySelectorAll('input, select, textarea');
            fields.forEach(field => {
                field.disabled = false;
            });
            
            // Show actions
            actions.style.display = 'flex';
        }
    };
    
    // Cancel edit
    window.cancelEdit = function(sectionId) {
        const form = document.getElementById(`${sectionId}Form`);
        const actions = document.getElementById(`${sectionId}Actions`);
        
        if (form && actions) {
            form.classList.remove('editing');
            
            // Disable form fields
            const fields = form.querySelectorAll('input, select, textarea');
            fields.forEach(field => {
                field.disabled = true;
            });
            
            // Hide actions
            actions.style.display = 'none';
            
            // Reset form to original values
            form.reset();
        }
    };
    
    // Handle avatar upload
    window.handleAvatarUpload = function(event) {
        const file = event.target.files[0];
        
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showToast('Please select an image file', 'error');
                return;
            }
            
            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                showToast('File size must be less than 5MB', 'error');
                return;
            }
            
            // Upload avatar
            uploadAvatar(file);
        }
    };
    
    // Upload avatar
    async function uploadAvatar(file) {
        const formData = new FormData();
        formData.append('avatar', file);
        
        try {
            showToast('Uploading avatar...', 'info');
            
            const response = await API.postForm('/api/profile/avatar/', formData);
            
            showToast('Avatar updated successfully!', 'success');
            
            // Update avatar display
            const avatar = document.querySelector('.avatar');
            avatar.innerHTML = `<img src="${response.avatar_url}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
            
        } catch (error) {
            showToast('Failed to upload avatar. Please try again.', 'error');
        }
    }
    
    // Form submissions
    profileForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const sectionId = form.id.replace('Form', '');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            try {
                showToast('Saving changes...', 'info');
                
                const response = await API.put(`/api/profile/${sectionId}/`, data);
                
                showToast('Changes saved successfully!', 'success');
                
                // Disable form fields
                const fields = form.querySelectorAll('input, select, textarea');
                fields.forEach(field => {
                    field.disabled = true;
                });
                
                // Hide actions
                const actions = document.getElementById(`${sectionId}Actions`);
                if (actions) {
                    actions.style.display = 'none';
                }
                
                form.classList.remove('editing');
                
            } catch (error) {
                showToast('Failed to save changes. Please try again.', 'error');
            }
        });
    });
    
    // Pincode formatting
    const pincodeInput = document.getElementById('pincode');
    if (pincodeInput) {
        pincodeInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 6) value = value.slice(0, 6);
            e.target.value = value;
        });
    }
    
    // Mobile number formatting
    const mobileInputs = document.querySelectorAll('input[type="tel"]');
    mobileInputs.forEach(input => {
        if (input.id.includes('mobile')) {
            input.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 10) value = value.slice(0, 10);
                e.target.value = value;
            });
        }
    });
    
    // IFSC code formatting
    const ifscInput = document.getElementById('ifscCode');
    if (ifscInput) {
        ifscInput.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase();
            e.target.value = value;
        });
    }
    
    // Account number formatting (only numbers)
    const accountInput = document.getElementById('accountNumber');
    if (accountInput) {
        accountInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            e.target.value = value;
        });
    }
    
    // Load profile data
    async function loadProfileData() {
        try {
            const response = await API.get('/api/profile/');
            
            // Populate forms with data
            if (response.personal) {
                populateForm('personalForm', response.personal);
            }
            
            if (response.contact) {
                populateForm('contactForm', response.contact);
            }
            
            if (response.location) {
                populateForm('locationForm', response.location);
            }
            
            if (response.economic) {
                populateForm('economicForm', response.economic);
            }
            
            if (response.bank) {
                populateForm('bankForm', response.bank);
            }
            
            if (response.preferences) {
                populateForm('preferencesForm', response.preferences);
            }
            
            // Update avatar if available
            if (response.avatar) {
                const avatar = document.querySelector('.avatar');
                avatar.innerHTML = `<img src="${response.avatar}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
            }
            
        } catch (error) {
            console.error('Failed to load profile data:', error);
        }
    }
    
    // Populate form with data
    function populateForm(formId, data) {
        const form = document.getElementById(formId);
        if (!form || !data) return;
        
        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = data[key];
            }
        });
    }
    
    // Load profile data on page load
    loadProfileData();
});