/* ==================== */
/* Authentication JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // Toggle password visibility
    window.togglePassword = function (inputId) {
        const input = document.getElementById(inputId);
        const button = input.nextElementSibling;
        const icon = button.querySelector('i');

        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    };

    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('loginError');
            const submitBtn = document.getElementById('loginBtn');

            // Validate
            if (!username || !password) {
                errorDiv.textContent = 'Please fill in all fields';
                errorDiv.style.display = 'flex';
                return;
            }

            // Show loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            errorDiv.style.display = 'none';

            try {
                const response = await API.post('/api/auth/login/', {
                    username,
                    password
                });

                // Save user data
                AppState.user = response.user;
                localStorage.setItem('user', JSON.stringify(response.user));

                showToast('Login successful!', 'success');

                // Redirect back to whatever page sent the user to /login/,
                // falling back to the dashboard (or admin-dashboard for admins).
                let nextUrl = new URLSearchParams(window.location.search).get('next');
                if (!nextUrl) {
                    if (response.user.role === 'admin') {
                        nextUrl = '/admin-dashboard/';
                    } else {
                        nextUrl = '/dashboard/';
                    }
                }
                setTimeout(() => {
                    window.location.href = nextUrl;
                }, 1000);

            } catch (error) {
                errorDiv.textContent = error.message || 'Login failed. Please check your credentials.';
                errorDiv.style.display = 'flex';
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        });
    }

    // Register form handler
    if (registerForm) {
        const passwordInput = document.getElementById('password');
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');

        // Password strength checker
        if (passwordInput) {
            passwordInput.addEventListener('input', () => {
                const password = passwordInput.value;
                let strength = 0;

                if (password.length >= 8) strength++;
                if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
                if (password.match(/\d/)) strength++;
                if (password.match(/[^a-zA-Z\d]/)) strength++;

                strengthFill.className = 'strength-fill';

                if (strength <= 1) {
                    strengthFill.classList.add('weak');
                    strengthText.textContent = 'Weak password';
                } else if (strength <= 2) {
                    strengthFill.classList.add('medium');
                    strengthText.textContent = 'Medium password';
                } else {
                    strengthFill.classList.add('strong');
                    strengthText.textContent = 'Strong password';
                }
            });
        }

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                username: document.getElementById('username').value,
                mobile: document.getElementById('mobile').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                confirmPassword: document.getElementById('confirmPassword').value,
                firstName: document.getElementById('firstName').value,
                lastName: document.getElementById('lastName').value,
                language: document.getElementById('language').value
            };

            const errorDiv = document.getElementById('registerError');
            const submitBtn = document.getElementById('registerBtn');

            // Validate
            const validation = Validator.validate(formData, {
                username: [
                    { type: 'required', message: 'Username is required' },
                    { type: 'minLength', min: 3, message: 'Username must be at least 3 characters' }
                ],
                mobile: [
                    { type: 'required', message: 'Mobile number is required' },
                    { type: 'phone', message: 'Invalid mobile number' }
                ],
                email: [
                    { type: 'required', message: 'Email is required' },
                    { type: 'email', message: 'Invalid email address' }
                ],
                password: [
                    { type: 'required', message: 'Password is required' },
                    { type: 'minLength', min: 8, message: 'Password must be at least 8 characters' }
                ]
            });

            if (!validation.isValid) {
                const firstError = Object.values(validation.errors)[0];
                errorDiv.textContent = firstError;
                errorDiv.style.display = 'flex';
                return;
            }

            // Check password match
            if (formData.password !== formData.confirmPassword) {
                errorDiv.textContent = 'Passwords do not match';
                errorDiv.style.display = 'flex';
                return;
            }

            // Show loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            errorDiv.style.display = 'none';

            try {
                const response = await API.post('/api/auth/register/', {
                    username: formData.username,
                    mobile: formData.mobile,
                    email: formData.email,
                    password: formData.password,
                    first_name: formData.firstName,
                    last_name: formData.lastName,
                    language: formData.language
                });

                showToast('Registration successful! Please login.', 'success');

                // Redirect to login
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 1500);

            } catch (error) {
                errorDiv.textContent = error.message || 'Registration failed. Please try again.';
                errorDiv.style.display = 'flex';
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
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
});
