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
        const requiredFields = currentFormStep.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.style.borderColor = 'var(--error)';
                isValid = false;
            } else {
                field.style.borderColor = 'var(--gray-300)';
            }
        });
        
        // Special validation for account number confirmation
        if (step === 3) {
            const accountNumber = document.getElementById('accountNumber').value;
            const confirmAccountNumber = document.getElementById('confirmAccountNumber').value;
            
            if (accountNumber !== confirmAccountNumber) {
                document.getElementById('confirmAccountNumber').style.borderColor = 'var(--error)';
                showToast('Account numbers do not match', 'error');
                isValid = false;
            }
        }
        
        if (!isValid) {
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
    
    // Read scheme ID from the URL once (falls back to null if not provided)
    const urlParams = new URLSearchParams(window.location.search);
    const schemeId = urlParams.get('scheme');

    if (selectedSchemeInput) {
        selectedSchemeInput.value = schemeId || '';
    }
    
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
                
                // Update required documents checklist
                const checklistContainer = document.getElementById('requiredDocsChecklist');
                if (checklistContainer) {
                    checklistContainer.innerHTML = '';
                    const docs = response.required_documents_list || [];
                    if (docs.length === 0) {
                        checklistContainer.innerHTML = '<p style="color: var(--gray-500); font-size: 0.9rem;">No specific documents required.</p>';
                    } else {
                        docs.forEach(docName => {
                            const docItem = document.createElement('div');
                            docItem.className = 'doc-upload-item';
                            docItem.innerHTML = `
                                <div class="doc-upload-info" style="display: flex; align-items: center; gap: var(--spacing-xs); font-size: 0.9rem;">
                                    <i class="fa-solid fa-file-circle-exclamation" style="color: var(--warning);"></i>
                                    <span class="doc-upload-name" style="color: var(--gray-700); font-weight: 500;">${docName}</span>
                                </div>
                                <div class="doc-upload-actions" style="display: flex; align-items: center;">
                                    <span style="font-size: 0.85rem; color: var(--gray-400); font-style: italic;">Provide on next page</span>
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