/* ==================== */
/* Home Page JavaScript */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    // Animate stats on scroll
    const statNumbers = document.querySelectorAll('.stat-number');
    
    const animateStats = () => {
        statNumbers.forEach(stat => {
            const target = parseInt(stat.getAttribute('data-count'));
            if (Number.isNaN(target)) return;
            const duration = 2000;
            const step = target / (duration / 16);
            let current = 0;
            
            const updateNumber = () => {
                current += step;
                if (current < target) {
                    stat.textContent = Math.floor(current);
                    requestAnimationFrame(updateNumber);
                } else {
                    stat.textContent = target;
                }
            };
            
            updateNumber();
        });
    };
    
    // Intersection Observer for stats animation
    const statsSection = document.querySelector('.stats');
    if (statsSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateStats();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        observer.observe(statsSection);
    }
    
    // Intersection Observer for scroll animations
    const animatedElements = document.querySelectorAll('.slide-up, .fade-in');
    
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
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease-out';
        animationObserver.observe(el);
    });
    
    // Voice wave animation in hero
    const voiceWaveBars = document.querySelectorAll('.voice-wave-demo .voice-wave-bar');
    if (voiceWaveBars.length > 0) {
        // Stagger the animation
        voiceWaveBars.forEach((bar, index) => {
            bar.style.animationDelay = `${index * 0.1}s`;
        });
    }
});
