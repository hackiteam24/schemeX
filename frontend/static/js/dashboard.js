/* ==================== */
/* Dashboard Page JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    // Intersection Observer for scroll animations
    const animatedElements = document.querySelectorAll('.slide-up');
    
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.5s ease-out';
        animationObserver.observe(el);
    });
    
    // Quick action cards click handler
    const quickActionCards = document.querySelectorAll('.quick-action-card');
    quickActionCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Add ripple effect
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Load dashboard data from API
    async function loadDashboardData() {
        try {
            const data = await API.get('/api/dashboard/');
            
            // 1. Update Welcome Message
            const welcomeMessage = document.getElementById('welcomeMessage');
            if (welcomeMessage && data.first_name) {
                welcomeMessage.textContent = `Welcome back, ${data.first_name}!`;
            }

            // 2. Update stats
            if (data.stats) {
                updateStats(data.stats);
            }
            
            // 3. Update profile completion checklist & progress bar
            if (data.profile_completion) {
                updateProfileProgress(data.profile_completion);
            }

            // 4. Update recommendations
            if (data.recommended_schemes) {
                updateRecommendations(data.recommended_schemes);
            }

            // 5. Update activity feed
            if (data.activities) {
                updateActivityFeed(data.activities);
            }
            
            // 6. Update deadlines
            if (data.deadlines) {
                updateDeadlines(data.deadlines);
            }
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }
    
    // Update stats dynamically with counter animation
    function updateStats(stats) {
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach((card, index) => {
            const statNumber = card.querySelector('.stat-number');
            if (statNumber && stats[index] !== undefined) {
                const target = parseInt(stats[index]);
                if (isNaN(target)) {
                    statNumber.textContent = stats[index];
                    return;
                }
                const duration = 1000;
                const step = target / (duration / 16);
                let current = 0;
                
                const updateNumber = () => {
                    current += step;
                    if (current < target) {
                        statNumber.textContent = Math.floor(current);
                        requestAnimationFrame(updateNumber);
                    } else {
                        statNumber.textContent = target;
                    }
                };
                updateNumber();
            }
        });
    }

    // Update profile completion status
    function updateProfileProgress(completion) {
        const progressFill = document.querySelector('.progress-fill');
        const progressPercentage = document.querySelector('.progress-percentage');
        const progressRemaining = document.querySelector('.progress-remaining');
        const profileTasksList = document.querySelector('.profile-tasks');

        if (progressFill) progressFill.style.width = `${completion.percentage}%`;
        if (progressPercentage) progressPercentage.textContent = `${completion.percentage}%`;
        if (progressRemaining) progressRemaining.textContent = `${completion.remaining_count} task(s) remaining`;

        if (profileTasksList && completion.tasks) {
            profileTasksList.innerHTML = completion.tasks.map(task => `
                <li class="${task.completed ? 'completed' : 'pending'}">
                    <i class="fa-solid fa-${task.completed ? 'check-circle' : 'circle'}"></i>
                    <span>${task.name}</span>
                </li>
            `).join('');

            // Rebind click listeners for incomplete tasks
            const profileTasks = profileTasksList.querySelectorAll('li');
            profileTasks.forEach(task => {
                if (!task.classList.contains('completed')) {
                    task.style.cursor = 'pointer';
                    task.addEventListener('click', () => {
                        const taskName = task.querySelector('span').textContent;
                        showToast(`Redirecting to complete: ${taskName}`, 'info');
                        setTimeout(() => {
                            if (taskName.toLowerCase().includes('document') || taskName.toLowerCase().includes('upload')) {
                                window.location.href = '/documents/';
                            } else {
                                window.location.href = '/profile/';
                            }
                        }, 1000);
                    });
                }
            });
        }
    }

    // Update recommended schemes
    function updateRecommendations(schemes) {
        const container = document.querySelector('.recommended-schemes');
        if (!container) return;

        if (schemes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-seedling"></i>
                    <h3>No recommendations yet</h3>
                    <p>Complete your profile to discover eligible schemes.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = schemes.map(scheme => {
            let icon = 'seedling';
            if (scheme.category === 'housing') icon = 'home';
            else if (scheme.category === 'health') icon = 'heart-pulse';
            else if (scheme.category === 'education') icon = 'graduation-cap';
            else if (scheme.category === 'employment') icon = 'briefcase';
            else if (scheme.category === 'women') icon = 'person-dress';

            return `
                <div class="recommended-scheme" onclick="window.location.href='/schemes/'" style="cursor: pointer;">
                    <div class="scheme-icon">
                        <i class="fa-solid fa-${icon}"></i>
                    </div>
                    <div class="scheme-info">
                        <h4>${scheme.name}</h4>
                        <span class="match-score">${scheme.match_score}</span>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    // Update activity feed dynamically
    function updateActivityFeed(activities) {
        const activityFeed = document.querySelector('.activity-feed');
        if (!activityFeed) return;

        if (!activities.length) {
            activityFeed.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-clock-rotate-left"></i>
                    <h3>No Activity</h3>
                    <p>Your recent application and document updates will show up here.</p>
                </div>
            `;
            return;
        }
        
        activityFeed.innerHTML = activities.map((activity, index) => `
            <div class="activity-item slide-up" style="animation-delay: ${index * 0.1}s; cursor: pointer;">
                <div class="activity-icon ${activity.status}">
                    <i class="fa-solid fa-${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <h4>${activity.title}</h4>
                    <p>${activity.description}</p>
                    <span class="activity-time">${formatDateTime(activity.time)}</span>
                </div>
                <span class="activity-status ${activity.status}">${activity.statusText}</span>
            </div>
        `).join('');
    }
    
    // Update deadlines dynamically
    function updateDeadlines(deadlines) {
        const deadlineList = document.querySelector('.deadline-list');
        if (!deadlineList) return;

        if (!deadlines.length) {
            deadlineList.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-calendar-check"></i>
                    <h3>All caught up!</h3>
                    <p>No pending document or scheme tasks.</p>
                </div>
            `;
            return;
        }
        
        deadlineList.innerHTML = deadlines.map(deadline => `
            <div class="deadline-item" style="cursor: pointer;">
                <div class="deadline-icon">
                    <i class="fa-solid fa-calendar"></i>
                </div>
                <div class="deadline-content">
                    <h4>${deadline.scheme}</h4>
                    <p>${deadline.task}</p>
                </div>
                <span class="deadline-days ${deadline.urgency}">${deadline.days}</span>
            </div>
        `).join('');
    }

    function formatDateTime(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    }
    
    // Refresh dashboard data periodically
    let refreshInterval;
    
    function startAutoRefresh() {
        refreshInterval = setInterval(loadDashboardData, 60000); // Refresh every minute
    }
    
    function stopAutoRefresh() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
    }
    
    // Start auto refresh when page is visible
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            loadDashboardData();
            startAutoRefresh();
        }
    });
    
    // Initial load
    loadDashboardData();
    startAutoRefresh();
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        stopAutoRefresh();
    });
});
