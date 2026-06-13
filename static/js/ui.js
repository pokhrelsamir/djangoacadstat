/**
 * AcadStat UI — modal dialogs, toasts, scroll reveal, password change
 */
const AcadStatUI = (() => {
    let modalOverlay = null;
    let toastContainer = null;
    let passwordOverlay = null;

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.getAttribute('content')) return meta.getAttribute('content');
        const match = document.cookie.match(/(^|;\s*)csrftoken\s*=\s*([^;]+)/);
        return match ? decodeURIComponent(match[2]) : '';
    }

    function lockBodyScroll() {
        document.body.style.overflow = 'hidden';
    }

    function unlockBodyScroll() {
        const anyOpen = (modalOverlay && modalOverlay.classList.contains('active'))
            || (passwordOverlay && passwordOverlay.classList.contains('active'));
        if (!anyOpen) document.body.style.overflow = '';
    }

    function ensureModal() {
        if (modalOverlay) return modalOverlay;
        modalOverlay = document.createElement('div');
        modalOverlay.className = 'acad-modal-overlay';
        modalOverlay.innerHTML = `
            <div class="acad-modal" role="dialog" aria-modal="true" aria-labelledby="acadModalTitle">
                <div class="acad-modal-icon success" id="acadModalIcon">
                    <span class="pulse-ring"></span>
                    <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20 6L9 17l-5-5"/>
                    </svg>
                </div>
                <h3 id="acadModalTitle"></h3>
                <p id="acadModalMessage"></p>
                <div class="acad-modal-stats" id="acadModalStats" style="display:none;">
                    <div class="acad-modal-stat"><div class="num" id="acadModalSaved">0</div><div class="lbl">Saved</div></div>
                    <div class="acad-modal-stat"><div class="num" id="acadModalFailed">0</div><div class="lbl">Failed</div></div>
                </div>
                <div class="acad-modal-actions">
                    <button type="button" class="btn ds ds-primary" id="acadModalOk">OK</button>
                </div>
            </div>`;
        document.body.appendChild(modalOverlay);
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });
        document.getElementById('acadModalOk').addEventListener('click', closeModal);
        return modalOverlay;
    }

    function ensurePasswordModal() {
        if (passwordOverlay) return passwordOverlay;

        passwordOverlay = document.createElement('div');
        passwordOverlay.className = 'acad-form-modal-overlay';
        passwordOverlay.id = 'acadPasswordModal';
        passwordOverlay.setAttribute('role', 'presentation');
        passwordOverlay.innerHTML = `
            <div class="acad-form-modal" role="dialog" aria-modal="true" aria-labelledby="acadPasswordTitle">
                <div class="acad-form-modal-header">
                    <h3 id="acadPasswordTitle"><i class="fas fa-lock"></i> Change Password</h3>
                    <button type="button" class="acad-form-modal-close" aria-label="Close">&times;</button>
                </div>
                <form id="acadPasswordForm" novalidate>
                    <div class="form-group ds">
                        <label for="acadCurrentPassword">Current Password</label>
                        <input type="password" id="acadCurrentPassword" name="current_password" required autocomplete="current-password">
                    </div>
                    <div class="form-group ds">
                        <label for="acadNewPassword">New Password</label>
                        <input type="password" id="acadNewPassword" name="new_password" required minlength="4" autocomplete="new-password">
                    </div>
                    <div class="form-group ds">
                        <label for="acadConfirmPassword">Confirm New Password</label>
                        <input type="password" id="acadConfirmPassword" name="confirm_password" required minlength="4" autocomplete="new-password">
                    </div>
                    <div class="alert-banner error" id="acadPasswordError" style="display:none;"></div>
                    <div class="acad-form-modal-actions">
                        <button type="button" class="btn ds ds-ghost" id="acadPasswordCancel">Cancel</button>
                        <button type="submit" class="btn ds ds-primary" id="acadPasswordSave">Save Password</button>
                    </div>
                </form>
            </div>`;
        document.body.appendChild(passwordOverlay);

        const form = passwordOverlay.querySelector('#acadPasswordForm');
        const errorEl = passwordOverlay.querySelector('#acadPasswordError');
        const saveBtn = passwordOverlay.querySelector('#acadPasswordSave');

        passwordOverlay.querySelector('.acad-form-modal-close').addEventListener('click', closePasswordModal);
        passwordOverlay.querySelector('#acadPasswordCancel').addEventListener('click', closePasswordModal);
        passwordOverlay.addEventListener('click', (e) => {
            if (e.target === passwordOverlay) closePasswordModal();
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorEl.style.display = 'none';

            const currentPassword = passwordOverlay.querySelector('#acadCurrentPassword').value;
            const newPassword = passwordOverlay.querySelector('#acadNewPassword').value;
            const confirmPassword = passwordOverlay.querySelector('#acadConfirmPassword').value;

            if (newPassword !== confirmPassword) {
                errorEl.textContent = 'New passwords do not match';
                errorEl.style.display = 'block';
                return;
            }
            if (newPassword.length < 4) {
                errorEl.textContent = 'Password must be at least 4 characters';
                errorEl.style.display = 'block';
                return;
            }

            const csrfToken = getCsrfToken();
            if (!csrfToken) {
                errorEl.textContent = 'Security token missing. Please reload the page.';
                errorEl.style.display = 'block';
                return;
            }

            setButtonLoading(saveBtn, true);
            try {
                const response = await fetch('/change-password/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword,
                    }),
                });

                const contentType = response.headers.get('content-type') || '';
                let data = null;
                if (contentType.includes('application/json')) {
                    data = await response.json();
                }

                if (!response.ok || !data?.success) {
                    errorEl.textContent = data?.message || 'Could not change password. Please try again.';
                    errorEl.style.display = 'block';
                    return;
                }

                closePasswordModal();
                toast(data.message || 'Password changed successfully!', 'success');
            } catch (err) {
                errorEl.textContent = 'A network error occurred. Please try again.';
                errorEl.style.display = 'block';
            } finally {
                setButtonLoading(saveBtn, false);
            }
        });

        return passwordOverlay;
    }

    function openPasswordModal() {
        ensurePasswordModal();
        passwordOverlay.querySelector('#acadPasswordForm').reset();
        passwordOverlay.querySelector('#acadPasswordError').style.display = 'none';
        passwordOverlay.classList.add('active');
        lockBodyScroll();
        requestAnimationFrame(() => {
            passwordOverlay.querySelector('#acadCurrentPassword')?.focus();
        });
    }

    function closePasswordModal() {
        if (!passwordOverlay) return;
        passwordOverlay.classList.remove('active');
        passwordOverlay.querySelector('#acadPasswordForm')?.reset();
        passwordOverlay.querySelector('#acadPasswordError').style.display = 'none';
        unlockBodyScroll();
    }

    function ensureToastContainer() {
        if (toastContainer) return toastContainer;
        toastContainer = document.createElement('div');
        toastContainer.className = 'acad-toast-container';
        document.body.appendChild(toastContainer);
        return toastContainer;
    }

    function showModal({ title, message, type = 'success', saved, failed, onClose, okLabel = 'OK' }) {
        ensureModal();
        const icon = document.getElementById('acadModalIcon');
        const statsEl = document.getElementById('acadModalStats');
        const okBtn = document.getElementById('acadModalOk');
        icon.className = 'acad-modal-icon ' + type;

        if (type === 'success') {
            icon.innerHTML = `<span class="pulse-ring"></span>
                <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 6L9 17l-5-5"/>
                </svg>`;
        } else if (type === 'error') {
            icon.innerHTML = `<i class="fas fa-times" style="font-size:1.75rem;"></i>`;
        } else {
            icon.innerHTML = `<i class="fas fa-exclamation-triangle" style="font-size:1.75rem;"></i>`;
        }

        document.getElementById('acadModalTitle').textContent = title;
        document.getElementById('acadModalMessage').textContent = message;
        if (okBtn) okBtn.textContent = okLabel;

        if (saved !== undefined) {
            statsEl.style.display = 'flex';
            document.getElementById('acadModalSaved').textContent = saved;
            document.getElementById('acadModalFailed').textContent = failed || 0;
        } else {
            statsEl.style.display = 'none';
        }

        modalOverlay._onClose = onClose;
        modalOverlay.classList.add('active');
        lockBodyScroll();
    }

    function closeModal() {
        if (!modalOverlay) return;
        modalOverlay.classList.remove('active');
        unlockBodyScroll();
        if (typeof modalOverlay._onClose === 'function') modalOverlay._onClose();
    }

    function toast(message, type = 'success', duration = 4000) {
        ensureToastContainer();
        const icons = { success: 'fa-check-circle', error: 'fa-times-circle', warning: 'fa-exclamation-circle' };
        const el = document.createElement('div');
        el.className = 'acad-toast ' + type;
        el.innerHTML = `<i class="fas ${icons[type] || icons.success}"></i><span>${message}</span>`;
        toastContainer.appendChild(el);
        setTimeout(() => {
            el.classList.add('fade-out');
            setTimeout(() => el.remove(), 300);
        }, duration);
    }

    function initScrollReveal() {
        const els = document.querySelectorAll('.reveal, .fade-in-on-scroll');
        if (!els.length) return;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -32px 0px' });
        els.forEach((el) => observer.observe(el));
    }

    function initPasswordTriggers() {
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-open-password-modal]');
            if (!trigger) return;
            e.preventDefault();
            openPasswordModal();
        });
    }

    function setButtonLoading(btn, loading) {
        if (!btn) return;
        btn.disabled = loading;
        btn.classList.toggle('loading', loading);
    }

    function initGlassNav() {
        const navs = document.querySelectorAll('.liquid-glass-nav, .app-page .navbar.app-nav-style');
        if (!navs.length) return;

        const sync = () => {
            const y = window.scrollY || document.documentElement.scrollTop;
            navs.forEach((nav) => {
                if (!nav.classList.contains('landing-nav')) {
                    nav.classList.toggle('is-scrolled', y > 12);
                }
            });
        };

        window.addEventListener('scroll', sync, { passive: true });
        sync();
    }

    function initCampusBg() {
        const body = document.body;
        if (!body.classList.contains('app-page') || body.classList.contains('login-page-wrapper')) return;
        if (document.querySelector('.app-campus-bg')) return;
        const src = window.ACADSTAT_CAMPUS_BG || '/static/images/tu/tu-6-web.jpg';
        const bg = document.createElement('div');
        bg.className = 'app-campus-bg';
        bg.setAttribute('aria-hidden', 'true');
        bg.style.backgroundImage = `url("${src}")`;
        body.insertBefore(bg, body.firstChild);
    }

    function removeLegacyPasswordModals() {
        document.querySelectorAll('#passwordModal').forEach((el) => el.remove());
    }

    document.addEventListener('DOMContentLoaded', () => {
        removeLegacyPasswordModals();
        initCampusBg();
        initScrollReveal();
        initGlassNav();
        initPasswordTriggers();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (passwordOverlay?.classList.contains('active')) closePasswordModal();
        else closeModal();
    });

    return {
        showModal,
        closeModal,
        openPasswordModal,
        closePasswordModal,
        toast,
        initScrollReveal,
        setButtonLoading,
    };
})();

window.openPasswordModal = () => AcadStatUI.openPasswordModal();
window.closePasswordModal = () => AcadStatUI.closePasswordModal();
