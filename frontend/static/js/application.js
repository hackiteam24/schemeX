/* ==================== */
/* Application Form JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('applicationForm');
    const progressFill = document.querySelector('.progress-fill');
    const stepIndicator = document.querySelector('.step-indicator');
    const formSteps = document.querySelectorAll('.form-step');
    const submitBtn = document.getElementById('submitBtn');
    
    let currentStep = 1;
    const totalSteps = 3;
    
    // Update progress
    function updateProgress(step) {
        const progress = (step / totalSteps) * 100;
        progressFill.style.width = `${progress}%`;
        stepIndicator.textContent = `Step ${step} of ${totalSteps}`;
    }
    
    // Navigate to next step
    window.nextStep = function(step) {
        if (!validateStep(currentStep)) {
            return;
        }
        
        currentStep = step;
        updateProgress(step);
        
        formSteps.forEach(formStep => {
            formStep.classList.remove('active');
            if (parseInt(formStep.dataset.step) === step) {
                formStep.classList.add('active');
            }
        });
    };
    
    // Navigate to previous step
    window.previousStep = function(step) {
        currentStep = step;
        updateProgress(step);
        
        formSteps.forEach(formStep => {
            formStep.classList.remove('active');
            if (parseInt(formStep.dataset.step) === step) {
                formStep.classList.add('active');
            }
        });
    };
    
    // Validate current step
    function validateStep(step) {
        const currentFormStep = document.querySelector(`.form-step[data-step="${step}"]`);
        const requiredFields = currentFormStep ? currentFormStep.querySelectorAll('[required]') : [];
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.style.borderColor = 'var(--error)';
                isValid = false;
            } else {
                field.style.borderColor = 'var(--gray-300)';
            }
        });
        
        // 1. Aadhaar and Mobile validation (Step 1)
        if (step === 1) {
            const aadhaarInput = document.getElementById('aadhaar');
            if (aadhaarInput && aadhaarInput.value.trim()) {
                const val = aadhaarInput.value.trim();
                if (!/^\d{12}$/.test(val)) {
                    aadhaarInput.style.borderColor = 'var(--error)';
                    showToast('Aadhaar number must be exactly 12 digits', 'error');
                    isValid = false;
                }
            }
            
            const mobileInput = document.getElementById('mobile');
            if (mobileInput && mobileInput.value.trim()) {
                const val = mobileInput.value.trim();
                if (!/^[5-9]\d{9}$/.test(val)) {
                    mobileInput.style.borderColor = 'var(--error)';
                    showToast('Mobile number must be exactly 10 digits starting with 5-9', 'error');
                    isValid = false;
                }
            }
        }
        
        // 2. Location & Pincode validation (Step 2)
        if (step === 2) {
            const pincodeInput = document.getElementById('pincode');
            if (pincodeInput && pincodeInput.value.trim()) {
                const val = pincodeInput.value.trim();
                if (!/^\d{6}$/.test(val)) {
                    pincodeInput.style.borderColor = 'var(--error)';
                    showToast('Pincode must be exactly 6 digits', 'error');
                    isValid = false;
                }
            }
        }
        
        // 3. Bank validation (Step 3)
        if (step === 3) {
            const accountInput = document.getElementById('accountNumber');
            const confirmInput = document.getElementById('confirmAccountNumber');
            const ifscInput = document.getElementById('ifscCode');
            
            if (accountInput && accountInput.value.trim()) {
                const val = accountInput.value.trim();
                if (!/^\d{9,18}$/.test(val)) {
                    accountInput.style.borderColor = 'var(--error)';
                    showToast('Bank Account number must be between 9 and 18 digits', 'error');
                    isValid = false;
                }
            }
            
            if (accountInput && confirmInput && accountInput.value.trim() !== confirmInput.value.trim()) {
                confirmInput.style.borderColor = 'var(--error)';
                showToast('Account numbers do not match', 'error');
                isValid = false;
            }
            
            if (ifscInput && ifscInput.value.trim()) {
                const val = ifscInput.value.trim().toUpperCase();
                if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(val)) {
                    ifscInput.style.borderColor = 'var(--error)';
                    showToast('IFSC code must be exactly 11 characters (e.g. SBIN0000301)', 'error');
                    isValid = false;
                }
            }
        }
        
        if (!isValid && requiredFields.length > 0 && Array.from(requiredFields).some(f => !f.value.trim())) {
            showToast('Please fill in all required fields', 'error');
        }
        
        return isValid;
    }
    
    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!validateStep(currentStep)) {
            return;
        }
        
        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        
        // Collect form data
        const formData = {
            scheme: document.getElementById('selectedSchemeId')?.value || schemeId
        };
        
        try {
            // Submit to API
            const response = await API.post('/api/applications/', formData);
            
            // Show success state
            showSuccessState(response.application_id);
            
            showToast('Application submitted successfully!', 'success');
            
        } catch (error) {
            showToast('Failed to submit application. Please try again.', 'error');
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });
    
    // Show success state
    function showSuccessState(applicationId) {
        const formCard = document.querySelector('.application-form-card');
        
        formCard.innerHTML = `
            <div class="success-state">
                <div class="success-icon">
                    <i class="fa-solid fa-check-circle"></i>
                </div>
                <h2>Application Submitted Successfully!</h2>
                <p>Your application has been submitted and is being processed. You can track your application status from the dashboard.</p>
                <div class="success-actions">
                    <a href="/dashboard/" class="btn btn-primary">
                        <i class="fa-solid fa-tachometer-alt"></i>
                        Go to Dashboard
                    </a>
                    <a href="/documents/" class="btn btn-outline">
                        <i class="fa-solid fa-folder-open"></i>
                        Upload Documents
                    </a>
                </div>
                <div class="application-reference">
                    <p>Application Reference: <strong>${applicationId}</strong></p>
                </div>
            </div>
        `;
    }
    
    // Input validation on blur
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (input.required && !input.value.trim()) {
                input.style.borderColor = 'var(--error)';
            } else {
                input.style.borderColor = 'var(--gray-300)';
            }
        });
    });
    
    // Aadhaar formatting
    const aadhaarInput = document.getElementById('aadhaar');
    if (aadhaarInput) {
        aadhaarInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 12) value = value.slice(0, 12);
            e.target.value = value;
        });
    }
    
    // Mobile number formatting
    const mobileInput = document.getElementById('mobile');
    if (mobileInput) {
        mobileInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) value = value.slice(0, 10);
            e.target.value = value;
        });
    }
    
    // Account number formatting
    const accountInput = document.getElementById('accountNumber');
    if (accountInput) {
        accountInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            e.target.value = value;
        });
    }
    
    // IFSC code formatting
    const ifscInput = document.getElementById('ifscCode');
    if (ifscInput) {
        ifscInput.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase();
            e.target.value = value;
        });
    }
    
    // Autocomplete/Search Select logic for Schemes
    const schemeSearchInput = document.getElementById('schemeSearchInput');
    const schemeSearchResults = document.getElementById('schemeSearchResults');
    const selectedSchemeInput = document.getElementById('selectedSchemeId');
    
    if (schemeSearchInput && schemeSearchResults) {
        let debounceTimer;
        schemeSearchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const query = schemeSearchInput.value.trim();
            
            if (query.length < 1) {
                schemeSearchResults.innerHTML = '';
                schemeSearchResults.style.display = 'none';
                return;
            }
            
            debounceTimer = setTimeout(async () => {
                try {
                    const response = await API.get(`/api/schemes/?search=${encodeURIComponent(query)}&is_active=true`);
                    const schemes = response.results || response || [];
                    
                    if (schemes.length === 0) {
                        schemeSearchResults.innerHTML = `
                            <div class="search-result-item" style="cursor: default; pointer-events: none; color: var(--gray-500); padding: var(--spacing-sm) var(--spacing-md);">
                                No schemes found
                            </div>
                        `;
                    } else {
                        schemeSearchResults.innerHTML = schemes.map(scheme => `
                            <div class="search-result-item" data-id="${scheme.id}" data-name="${scheme.name}" style="padding: var(--spacing-sm) var(--spacing-md); cursor: pointer; border-bottom: 1px solid var(--gray-100);">
                                <div class="search-result-title" style="font-weight: 600; color: var(--gray-800);">${scheme.name}</div>
                                <div class="search-result-subtitle" style="font-size: 0.8rem; color: var(--gray-500);">${scheme.department || 'Government Welfare'} • ${scheme.category}</div>
                            </div>
                        `).join('');
                        
                        // Add click handlers to search result items
                        schemeSearchResults.querySelectorAll('.search-result-item').forEach(item => {
                            item.addEventListener('click', () => {
                                const id = item.dataset.id;
                                const name = item.dataset.name;
                                
                                schemeSearchInput.value = name;
                                if (selectedSchemeInput) {
                                    selectedSchemeInput.value = id;
                                }
                                schemeSearchResults.innerHTML = '';
                                schemeSearchResults.style.display = 'none';
                                
                                // Load details for the newly selected scheme
                                loadSchemeDetails(id);
                            });
                        });
                    }
                    schemeSearchResults.style.display = 'block';
                } catch (err) {
                    console.error('Error fetching autocomplete schemes:', err);
                }
            }, 300);
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!schemeSearchInput.contains(e.target) && !schemeSearchResults.contains(e.target)) {
                schemeSearchResults.style.display = 'none';
            }
        });
        
        // Show dropdown if input is focused and has text
        schemeSearchInput.addEventListener('focus', () => {
            if (schemeSearchInput.value.trim().length >= 1 && schemeSearchResults.children.length > 0) {
                schemeSearchResults.style.display = 'block';
            }
        });
    }
    
    // Prefill profile details from verified documents stored in user profile
    async function prefillProfileData() {
        try {
            const profile = await API.get('/api/profiles/');
            if (!profile) return;
            
            // Step 1: Personal Details
            const firstName = profile.personal?.firstName || '';
            const lastName = profile.personal?.lastName || '';
            const fullName = `${firstName} ${lastName}`.trim();
            
            const fullNameInput = document.getElementById('fullName') || document.getElementById('fullNameInput') || document.querySelector('[name="full_name"]');
            if (fullNameInput) fullNameInput.value = fullName;
            
            const fatherNameInput = document.getElementById('fatherName') || document.getElementById('father_name') || document.querySelector('[name="father_name"]');
            // Since fatherName isn't explicitly in the django profile model, we can try alternate fields
            
            const aadhaarInput = document.getElementById('aadhaar') || document.getElementById('aadhaarNumber') || document.querySelector('[name="aadhaar_number"]');
            if (aadhaarInput) aadhaarInput.value = profile.personal?.aadhaarNumber || '';
            
            const mobileInput = document.getElementById('mobile') || document.getElementById('mobileNumber') || document.querySelector('[name="mobile_number"]');
            if (mobileInput) mobileInput.value = profile.contact?.mobile || '';
            
            const genderSelect = document.getElementById('gender') || document.querySelector('[name="gender"]') || document.querySelector('select[name="gender"]');
            if (genderSelect && profile.personal?.gender) genderSelect.value = profile.personal.gender;
            
            const categorySelect = document.getElementById('category') || document.querySelector('[name="category"]') || document.querySelector('select[name="category"]');
            if (categorySelect && profile.personal?.category) categorySelect.value = profile.personal.category;
            
            // Step 2: Location/Land details
            const stateInput = document.getElementById('state') || document.querySelector('[name="state"]');
            if (stateInput) stateInput.value = profile.location?.state || '';
            
            const districtInput = document.getElementById('district') || document.querySelector('[name="district"]');
            if (districtInput) districtInput.value = profile.location?.district || '';
            
            const tehsilInput = document.getElementById('tehsil') || document.getElementById('block') || document.querySelector('[name="tehsil"]') || document.querySelector('[name="block"]');
            if (tehsilInput) tehsilInput.value = profile.location?.tehsil || '';
            
            const villageInput = document.getElementById('village') || document.querySelector('[name="village"]');
            if (villageInput) villageInput.value = profile.location?.village || '';
            
            const landAreaInput = document.getElementById('landArea') || document.querySelector('[name="land_area"]');
            if (landAreaInput) landAreaInput.value = profile.economic?.landArea || '';
            
            const landTypeSelect = document.getElementById('landType') || document.querySelector('[name="land_type"]') || document.querySelector('select[name="land_type"]');
            if (landTypeSelect && profile.economic?.landType) landTypeSelect.value = profile.economic.landType;
            
            // Step 3: Bank Details
            const bankNameInput = document.getElementById('bankName') || document.querySelector('[name="bank_name"]');
            if (bankNameInput) bankNameInput.value = profile.bank?.bankName || '';
            
            const accountNumberInput = document.getElementById('accountNumber') || document.querySelector('[name="account_number"]');
            if (accountNumberInput) {
                accountNumberInput.value = profile.bank?.accountNumber || '';
                const confirmInput = document.getElementById('confirmAccountNumber') || document.querySelector('[name="confirm_account_number"]');
                if (confirmInput) confirmInput.value = profile.bank?.accountNumber || '';
            }
            
            const ifscInput = document.getElementById('ifscCode') || document.querySelector('[name="ifsc_code"]');
            if (ifscInput) ifscInput.value = profile.bank?.ifscCode || '';
            
            const accountTypeSelect = document.getElementById('accountType') || document.querySelector('[name="account_type"]') || document.querySelector('select[name="account_type"]');
            if (accountTypeSelect && profile.bank?.accountType) accountTypeSelect.value = profile.bank.accountType;
            
            showToast('Form pre-filled using your verified documents!', 'success');
        } catch (err) {
            console.error('Failed to pre-fill profile data:', err);
        }
    }

    // Read scheme ID from the URL once (falls back to null if not provided)
    const urlParams = new URLSearchParams(window.location.search);
    const schemeId = urlParams.get('scheme');

    if (selectedSchemeInput) {
        selectedSchemeInput.value = schemeId || '';
    }
    
    // Trigger pre-fill automatically on page load
    prefillProfileData();
    
    if (schemeId) {
        loadSchemeDetails(schemeId);
    }
    
    // Load scheme details
    async function loadSchemeDetails(schemeId) {
        try {
            const response = await API.get(`/api/schemes/${schemeId}/`);
            
            // Update scheme info card
            const schemeCard = document.querySelector('.scheme-info-card');
            const schemeSearchInput = document.getElementById('schemeSearchInput');
            if (schemeCard && response) {
                schemeCard.style.display = 'block';
                schemeCard.querySelector('.scheme-header h2').textContent = response.name;
                schemeCard.querySelector('.scheme-subtitle').textContent = response.name_hi || 'Selected welfare scheme';
                schemeCard.querySelector('.scheme-description p').textContent = response.description || 'Continue with the application form for this scheme.';
                
                // Fetch the user's uploaded documents list from the API for this scheme
                let userDocs = [];
                try {
                    const docsResponse = await API.get(`/api/documents/?scheme=${schemeId}`);
                    userDocs = docsResponse.required_documents || [];
                } catch (err) {
                    console.error('Failed to load user document states:', err);
                }

                // Update required documents checklist
                const checklistContainer = document.getElementById('requiredDocsChecklist');
                if (checklistContainer) {
                    checklistContainer.innerHTML = '';
                    
                    if (userDocs.length === 0) {
                        checklistContainer.innerHTML = '<p style="color: var(--gray-500); font-size: 0.9rem;">No specific documents required.</p>';
                    } else {
                        userDocs.forEach(reqDoc => {
                            const docItem = document.createElement('div');
                            docItem.className = 'doc-upload-item';
                            
                            const iconClass = reqDoc.uploaded ? 'fa-solid fa-file-circle-check' : 'fa-solid fa-file-circle-exclamation';
                            const iconColor = reqDoc.uploaded ? 'var(--success)' : 'var(--warning)';
                            const statusText = reqDoc.uploaded ? 'Uploaded' : 'Provide on next page';
                            const statusColor = reqDoc.uploaded ? 'var(--success)' : 'var(--gray-400)';
                            const statusWeight = reqDoc.uploaded ? '500' : 'normal';
                            const statusStyle = reqDoc.uploaded ? 'normal' : 'italic';

                            docItem.innerHTML = `
                                <div class="doc-upload-info" style="display: flex; align-items: center; gap: var(--spacing-xs); font-size: 0.9rem;">
                                    <i class="${iconClass}" style="color: ${iconColor};"></i>
                                    <span class="doc-upload-name" style="color: var(--gray-700); font-weight: 500;">${reqDoc.name}</span>
                                </div>
                                <div class="doc-upload-actions" style="display: flex; align-items: center;">
                                    <span style="font-size: 0.85rem; color: ${statusColor}; font-weight: ${statusWeight}; font-style: ${statusStyle};">${statusText}</span>
                                </div>
                            `;
                            checklistContainer.appendChild(docItem);
                        });
                    }
                }
            }
            if (schemeSearchInput && response) {
                schemeSearchInput.value = response.name;
            }
            
        } catch (error) {
            console.error('Failed to load scheme details:', error);
        }
    }
});
