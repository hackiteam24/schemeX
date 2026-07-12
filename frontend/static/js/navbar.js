/* ==================== */
/* Navbar JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('menu-btn');
    const mobileMenu = document.getElementById('mobileMenu');
    const navLinks = document.querySelectorAll('.nav-links a');

    // Auth-aware navbar — AppState.user is already populated from
    // localStorage by main.js, which loads before this file.
    const isLoggedIn = !!(window.AppState && AppState.user && AppState.user.token);

    // Toggle navigation items based on authentication state using body classes
    if (isLoggedIn) {
        document.body.classList.add('is-authenticated');
        document.body.classList.remove('is-guest');
    } else {
        document.body.classList.add('is-guest');
        document.body.classList.remove('is-authenticated');
    }

    // Populate user details if logged in
    if (isLoggedIn) {
        const isAdmin = window.AppState && AppState.user && AppState.user.role === 'admin';
        
        if (isAdmin) {
            const navLinksContainer = document.querySelector('.nav-links');
            if (navLinksContainer) {
                navLinksContainer.innerHTML = `
                    <li><a href="/admin-dashboard/">Admin Dashboard</a></li>
                `;
            }
            const mobileMenuContainer = document.getElementById('mobileMenu');
            if (mobileMenuContainer) {
                mobileMenuContainer.innerHTML = `
                    <a href="/admin-dashboard/">Admin Dashboard</a>
                    <a href="#" id="navLogoutBtnMobile" class="login-btn auth-only mobile-logout-btn">Logout</a>
                `;
            }
            const dropdownMenu = document.getElementById('userDropdownMenu');
            if (dropdownMenu) {
                dropdownMenu.innerHTML = `
                    <a href="/admin-dashboard/">Admin Dashboard</a>
                    <hr>
                    <a href="#" id="navLogoutBtn" class="dropdown-danger">Logout</a>
                `;
            }
        }

        const displayName = AppState.user.first_name || AppState.user.username || 'Account';
        const navbarUserName = document.getElementById('navbarUserName');
        if (navbarUserName) {
            navbarUserName.textContent = displayName;
        }

        // Initialize User Dropdown
        const dropdownToggle = document.getElementById('userDropdownToggle');
        const dropdownMenu = document.getElementById('userDropdownMenu');

        if (dropdownToggle && dropdownMenu) {
            dropdownToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdownMenu.classList.toggle('show');
            });

            document.addEventListener('click', () => {
                dropdownMenu.classList.remove('show');
            });
        }

        // Bind logout event handlers
        const handleLogout = (e) => {
            e.preventDefault();
            localStorage.removeItem('user');
            if (window.AppState) {
                AppState.user = null;
            }
            showToast('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = '/login/';
            }, 1000);
        };

        const logoutBtn = document.getElementById('navLogoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', handleLogout);
        }

        const logoutBtnMobile = document.getElementById('navLogoutBtnMobile');
        if (logoutBtnMobile) {
            logoutBtnMobile.addEventListener('click', handleLogout);
        }
    }

    // Path protection
    const protectedPaths = ['/dashboard/', '/profile/', '/application/', '/documents/', '/chat/', '/eligibility/'];
    const currentPath = window.location.pathname;
    const isProtected = protectedPaths.some(path => {
        return currentPath === path || currentPath === path.replace(/\/$/, '') || currentPath === path + '/';
    });
    if (!isLoggedIn && isProtected) {
        window.location.href = '/login/?next=' + encodeURIComponent(currentPath);
    }

    // Toggle mobile menu
    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('active');

            // Toggle icon
            const icon = menuBtn.querySelector('i');
            if (mobileMenu.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // Close mobile menu when clicking a link
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('active');
                const icon = menuBtn.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            });
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !menuBtn.contains(e.target)) {
                mobileMenu.classList.remove('active');
                const icon = menuBtn.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    // Set active link based on current page
    const currentPage = window.location.pathname;
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPage || (currentPage === '/' && linkPath === '')) {
            link.classList.add('active');
        }
    });

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = 'var(--shadow-md)';
            } else {
                navbar.style.boxShadow = 'var(--shadow-sm)';
            }
        });
    }
});
