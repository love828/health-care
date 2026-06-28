/**
 * Daily Care - Main JavaScript
 * 巧克力囊肿患者健康管理应用的交互逻辑
 */

(function() {
    'use strict';

    // ---- DOM Ready ----
    document.addEventListener('DOMContentLoaded', function() {

        // ---- Mobile Nav Toggle ----
        const navToggle = document.querySelector('.nav-toggle');
        const navMenu = document.querySelector('.nav-menu');

        if (navToggle && navMenu) {
            navToggle.addEventListener('click', function(e) {
                e.stopPropagation();
                navMenu.classList.toggle('show');
            });

            // 点击页面其他地方关闭菜单
            document.addEventListener('click', function(e) {
                if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                    navMenu.classList.remove('show');
                }
            });
        }

        // ---- Auto-dismiss Flash Messages ----
        document.querySelectorAll('.flash-message').forEach(function(msg) {
            setTimeout(function() {
                if (msg.parentElement) {
                    msg.style.opacity = '0';
                    msg.style.transition = 'opacity 0.3s';
                    setTimeout(function() {
                        if (msg.parentElement) msg.remove();
                    }, 300);
                }
            }, 5000);
        });

        // ---- Smooth Scroll for Anchor Links ----
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId && targetId !== '#') {
                    const target = document.querySelector(targetId);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            });
        });

        // ---- Form Validation Enhancements ----
        document.querySelectorAll('form').forEach(function(form) {
            // Password confirmation check
            const password = form.querySelector('input[name="password"]');
            const confirm = form.querySelector('input[name="confirm_password"]');
            if (password && confirm) {
                confirm.addEventListener('input', function() {
                    if (this.value && this.value !== password.value) {
                        this.setCustomValidity('两次密码不一致');
                    } else {
                        this.setCustomValidity('');
                    }
                });
                password.addEventListener('input', function() {
                    if (confirm.value && this.value !== confirm.value) {
                        confirm.setCustomValidity('两次密码不一致');
                    } else {
                        confirm.setCustomValidity('');
                    }
                });
            }
        });

        // ---- Points Preview Animation ----
        const pointsSpan = document.querySelector('.points-count');
        if (pointsSpan) {
            // Animate number change
            const observer = new MutationObserver(function() {
                animateNumber(pointsSpan);
            });
            observer.observe(pointsSpan, { childList: true });
        }

        // ---- Check-in: date picker restriction ----
        // Can only check in for today
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(function(input) {
            const today = new Date().toISOString().split('T')[0];
            input.setAttribute('max', today);
        });

        console.log('🌸 Daily Care loaded successfully');
    });

    // ---- Helper: Animate Number Changes ----
    function animateNumber(element) {
        // Simple visual feedback when number changes
        element.style.transition = 'transform 0.15s';
        element.style.transform = 'scale(1.3)';
        setTimeout(function() {
            element.style.transform = 'scale(1)';
        }, 150);
    }

    // ---- Helper: Format Date ----
    function formatDate(dateStr) {
        const d = new Date(dateStr);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return year + '-' + month + '-' + day;
    }

    // ---- Helper: Get Weekday Chinese Name ----
    function getWeekday(dayIndex) {
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return weekdays[dayIndex];
    }

    // ---- Export ----
    window.DailyCare = {
        formatDate: formatDate,
        getWeekday: getWeekday,
        animateNumber: animateNumber,
    };

})();
