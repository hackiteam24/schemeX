/* ==================== */
/* Eligibility Checker JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('eligibilityForm');
    const progressFill = document.getElementById('progressFill');
    const steps = document.querySelectorAll('.step');
    const formSteps = document.querySelectorAll('.form-step');
    const submitBtn = document.getElementById('submitBtn');
    const resultsSection = document.getElementById('resultsSection');
    const resultsGrid = document.getElementById('resultsGrid');
    
    let currentStep = 1;
    const totalSteps = 4;
    
    // Update progress
    function updateProgress(step) {
        const progress = (step / totalSteps) * 100;
        progressFill.style.width = `${progress}%`;
        
        steps.forEach(stepEl => {
            const stepNum = parseInt(stepEl.dataset.step);
            stepEl.classList.remove('active', 'completed');
            
            if (stepNum < step) {
                stepEl.classList.add('completed');
            } else if (stepNum === step) {
                stepEl.classList.add('active');
            }
        });
    }
    
    // Navigate to next step
    window.nextStep = function(step) {
        // Validate current step
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
        
        if (!isValid) {
            showToast('Please fill in all required fields', 'error');
        }
        
        return isValid;
    }
    
    // Toggle land fields
    window.toggleLandFields = function() {
        const ownsLand = document.getElementById('ownsLand').value;
        const landFields = document.querySelectorAll('.land-field');
        
        landFields.forEach(field => {
            field.style.display = ownsLand === 'yes' ? 'block' : 'none';
        });
    };
    
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
            age: document.getElementById('age').value,
            gender: document.getElementById('gender').value,
            category: document.getElementById('category').value,
            maritalStatus: document.getElementById('maritalStatus').value,
            state: document.getElementById('state').value,
            district: document.getElementById('district').value,
            ruralUrban: document.getElementById('ruralUrban').value,
            pincode: document.getElementById('pincode').value,
            annualIncome: document.getElementById('annualIncome').value,
            incomeSource: document.getElementById('incomeSource').value,
            bplStatus: document.getElementById('bplStatus').value,
            bankAccount: document.getElementById('bankAccount').value,
            occupation: document.getElementById('occupation').value,
            ownsLand: document.getElementById('ownsLand').value,
            landArea: document.getElementById('landArea').value,
            landType: document.getElementById('landType').value
        };
        
        try {
            const response = await API.post('/api/eligibility/check/', formData);
            const results = response.results || [];
            
            // Display results
            displayResults(results);
            
            // Hide form, show results
            document.querySelector('.eligibility-form').style.display = 'none';
            document.querySelector('.progress-container').style.display = 'none';
            resultsSection.style.display = 'block';
            
            showToast('Eligibility check complete!', 'success');
            
        } catch (error) {
            showToast('Failed to check eligibility. Please try again.', 'error');
        } finally {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });
    
    // Generate mock results
    function generateMockResults(formData) {
        const results = [];
        
        // PM Kisan eligibility
        if (formData.ownsLand === 'yes' && parseFloat(formData.landArea) > 0) {
            results.push({
                id: 1,
                name: 'PM Kisan Samman Nidhi',
                name_hi: 'पीएम किसान सम्मान निधि',
                eligible: true,
                confidence: 95,
                reasons: ['Owns agricultural land', 'Income within limit']
            });
        }
        
        // PM Awas eligibility
        if (formData.bplStatus === 'yes' || parseFloat(formData.annualIncome) < 300000) {
            results.push({
                id: 2,
                name: 'PM Awas Yojana',
                name_hi: 'प्रधानमंत्री आवास योजना',
                eligible: true,
                confidence: 88,
                reasons: ['Income within limit', 'BPL status']
            });
        }
        
        // Ayushman Bharat eligibility
        if (formData.bplStatus === 'yes') {
            results.push({
                id: 3,
                name: 'Ayushman Bharat',
                name_hi: 'आयुष्मान भारत',
                eligible: true,
                confidence: 92,
                reasons: ['BPL card holder', 'No existing health insurance']
            });
        }
        
        // Add some not eligible results
        results.push({
            id: 4,
            name: 'National Scholarship',
            name_hi: 'राष्ट्रीय छात्रवृत्ति',
            eligible: false,
            confidence: 85,
            reasons: ['Age exceeds limit', 'Not a student']
        });
        
        return results;
    }
    
    // Display results
    function displayResults(results) {
        if (results.length === 0) {
            resultsGrid.innerHTML = `
                <div class="empty-state col-span-full">
                    <i class="fa-solid fa-search"></i>
                    <h3>No matching schemes found</h3>
                    <p>Try adjusting your profile information</p>
                </div>
            `;
            return;
        }
        
        resultsGrid.innerHTML = results.map(result => `
            <div class="result-card slide-up ${result.eligible ? 'eligible' : 'not-eligible'}">
                <div class="result-header">
                    <div>
                        <h3 class="result-title">${result.name}</h3>
                        <p class="result-subtitle">${result.name_hi}</p>
                    </div>
                    <span class="eligibility-badge ${result.eligible ? 'eligible' : 'not-eligible'}">
                        ${result.eligible ? 'Eligible' : 'Not Eligible'}
                    </span>
                </div>
                <div class="confidence-score">
                    <i class="fa-solid fa-chart-line"></i>
                    <span>${result.confidence}% confidence</span>
                </div>
                <div class="result-reasons">
                    <h4>Reasons:</h4>
                    <ul>
                        ${result.reasons.map(reason => `
                            <li><i class="fa-solid fa-check"></i> ${reason}</li>
                        `).join('')}
                    </ul>
                </div>
                <div class="result-actions">
                    ${result.eligible ? `
                        <a href="/schemes/${result.id}/" class="btn btn-primary btn-sm">Apply Now</a>
                        <button class="btn btn-outline btn-sm" onclick="listenToScheme('${result.name}')">
                            <i class="fa-solid fa-headphones"></i>
                        </button>
                    ` : `
                        <button class="btn btn-outline btn-sm" onclick="viewAlternatives('${result.id}')">
                            View Alternatives
                        </button>
                    `}
                </div>
            </div>
        `).join('');
        
        // Initialize animations
        const cards = resultsGrid.querySelectorAll('.result-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }
    
    // Reset form
    window.resetForm = function() {
        form.reset();
        currentStep = 1;
        updateProgress(1);
        
        formSteps.forEach(formStep => {
            formStep.classList.remove('active');
            if (parseInt(formStep.dataset.step) === 1) {
                formStep.classList.add('active');
            }
        });
        
        document.querySelector('.eligibility-form').style.display = 'block';
        document.querySelector('.progress-container').style.display = 'block';
        resultsSection.style.display = 'none';
    };
    
    // Download report
    window.downloadReport = async function() {
        try {
            showToast('Generating report...', 'info');
            
            const headers = {};
            if (AppState.user?.token) {
                headers.Authorization = `Bearer ${AppState.user.token}`;
            }
            
            const response = await fetch('/api/eligibility/report/', {
                method: 'GET',
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate report');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'SchemeX_Eligibility_Report.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Report downloaded successfully!', 'success');
        } catch (error) {
            console.error('Error downloading report:', error);
            showToast('Failed to download report. Please try again.', 'error');
        }
    };
    
    // Listen to scheme
    window.listenToScheme = function(name) {
        if (SpeechService.speak(name)) {
            showToast('Playing scheme details', 'info');
        } else {
            showToast('Text-to-speech not supported', 'error');
        }
    };
    
    // View alternatives
    window.viewAlternatives = function(id) {
        showToast('Showing alternative schemes...', 'info');
    };
    
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
    
    // Pincode formatting
    const pincodeInput = document.getElementById('pincode');
    if (pincodeInput) {
        pincodeInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 6) value = value.slice(0, 6);
            e.target.value = value;
        });
    }
});