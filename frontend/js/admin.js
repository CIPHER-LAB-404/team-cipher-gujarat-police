// Admin Portal Logic

document.addEventListener('DOMContentLoaded', async () => {
    const profile = await window.Auth.getUserProfile();
    if (profile) {
      document.getElementById('auth-admin-name').textContent = profile.full_name + ' (ADMIN)';
    }

    const form = document.getElementById('admin-provision-form');
    const alertBox = document.getElementById('admin-alert');
    const btn = document.getElementById('btn-provision');

    function showAlert(msg, isSuccess) {
        alertBox.textContent = msg;
        alertBox.style.display = 'block';
        if (isSuccess) {
            alertBox.style.background = 'rgba(16, 185, 129, 0.1)';
            alertBox.style.border = '1px solid #10b981';
            alertBox.style.color = '#10b981';
        } else {
            alertBox.style.background = 'rgba(239, 68, 68, 0.1)';
            alertBox.style.border = '1px solid #ef4444';
            alertBox.style.color = '#ef4444';
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        alertBox.style.display = 'none';

        const payload = {
            username: document.getElementById('prov-username').value,
            password: document.getElementById('prov-password').value,
            full_name: document.getElementById('prov-fullname').value,
            email: document.getElementById('prov-email').value,
            role: document.getElementById('prov-role').value,
            badge_number: document.getElementById('prov-badge').value,
            department: document.getElementById('prov-department').value,
            clearance_level: 'LEVEL-4'
        };

        const origHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Provisioning...';
        btn.disabled = true;

        try {
            const res = await window.Auth.apiFetch('/api/auth/admin/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to provision user');
            }

            const data = await res.json();
            showAlert(data.message || 'User provisioned successfully', true);
            form.reset();
            
        } catch (err) {
            showAlert(err.message, false);
        } finally {
            btn.innerHTML = origHtml;
            btn.disabled = false;
        }
    });
});
