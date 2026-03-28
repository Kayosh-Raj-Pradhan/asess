// Dashboard logic: verify user is authenticated and show profile info.

// Returns the correct API prefix based on current user's role
function getApiPrefix() {
    return window._currentUserRole === "superadmin" ? "/users/superadmin" : "/users/admin";
}

async function initDashboard() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    try {
        const user = await apiRequest("/users/me", "GET");
        const displayName = user.full_name || user.username;

        const setText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setText("userName", displayName);
        setText("userEmail", user.email);
        setText("userRole", user.role);
        setText("userEmail2", user.email);
        setText("userRole2", user.role);
        document.querySelectorAll(".userName").forEach((el) => (el.textContent = displayName));

        // Show admin panel button for admin/superadmin users
        if (user.role === "admin" || user.role === "superadmin") {
            const adminBtn = document.getElementById("adminPanelBtn");
            if (adminBtn) adminBtn.style.display = "flex";
        }

        // Superadmin: hide New Scan, Eye Test, Patients quick action cards
        if (user.role === "superadmin") {
            document.querySelectorAll('a[href="/capture"], a[href="/capture/"], a[href="/test"], a[href="/test/"], a[href="/patients"], a[href="/patients/"]').forEach(el => el.style.display = "none");
        }

        // Hide "New Scan" for doctors
        if (user.role === "doctor") {
            document.querySelectorAll('a[href="/capture"], a[href="/capture/"]').forEach(el => el.style.display = "none");
        }

        // If on admin dashboard page, load user list
        if (document.getElementById("adminUserTable")) {
            if (user.role !== "admin" && user.role !== "superadmin") {
                showToast("Access denied. Admins only.", "error");
                setTimeout(() => { window.location.href = "/index"; }, 1500);
                return;
            }
            window._currentUserRole = user.role;

            // Update panel title for superadmin
            const panelTitle = document.querySelector('#adminUserTable')?.closest('.card')?.querySelector('h3, h2');
            if (panelTitle && user.role === "superadmin") {
                panelTitle.textContent = "Admin Management (Superadmin)";
            }

            loadUserList();
        }
    } catch (error) {
        console.error("Failed to load user profile", error);
        logout();
    }
}

// ===== Admin CRUD Functions =====
async function loadUserList() {
    try {
        const prefix = getApiPrefix();
        const users = await apiRequest(`${prefix}/users`, "GET");
        const tbody = document.getElementById("adminUserTable");
        if (!tbody) return;

        tbody.innerHTML = "";
        users.forEach((u) => {
            const roleBadgeClass = `role-${u.role}`;
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.full_name || "—"}</td>
                <td>${u.username}</td>
                <td>${u.email}</td>
                <td><span class="role-badge ${roleBadgeClass}">${u.role}</span></td>
                <td>${u.is_active ? '<span style="color:#15803d; font-weight:600;">Active</span>' : '<span style="color:#dc2626; font-weight:600;">Inactive</span>'}</td>
                <td class="action-cell">
                    <button class="btn-sm btn-edit" onclick="openEditModal(${u.id}, '${(u.full_name || '').replace(/'/g, "\\'")}', '${u.email}', '${u.role}', ${u.is_active})">Edit</button>
                    <button class="btn-sm btn-delete" onclick="openDeleteModal(${u.id}, '${u.email}', '${(u.full_name || u.username).replace(/'/g, "\\'")}')">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        showToast("Failed to load users: " + error.message, "error");
    }
}

// ===== Edit User Modal =====
function openEditModal(userId, fullName, email, currentRole, isActive) {
    const role = window._currentUserRole || "admin";
    let roleOptions;
    if (role === "superadmin") {
        // Superadmin can only manage admins — only admin role option
        roleOptions = ["admin"];
    } else {
        // Admin can manage doctors, staff, and assign admin role
        roleOptions = ["doctor", "staff", "admin"];
    }

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.id = "editUserModal";
    overlay.innerHTML = `
        <div class="modal-card">
            <h3><i class="ri-edit-line" style="margin-right:8px; color:#1565c0;"></i>Edit User</h3>
            <div style="margin-bottom:20px; padding:14px; background:#f0f9ff; border-radius:10px; border:1px solid #bae6fd;">
                <p style="margin:0; color:#1e40af; font-weight:600; font-size:0.9rem;">${fullName || email}</p>
                <p style="margin:4px 0 0; color:#64748b; font-size:0.82rem;">${email}</p>
            </div>
            <form id="editUserForm">
                <div class="form-group">
                    <label>Role</label>
                    <select id="editRole" required>
                        ${roleOptions.map(r => `<option value="${r}" ${r === currentRole ? 'selected' : ''}>${r.charAt(0).toUpperCase() + r.slice(1)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Status</label>
                    <select id="editStatus" required>
                        <option value="true" ${isActive ? 'selected' : ''}>Active</option>
                        <option value="false" ${!isActive ? 'selected' : ''}>Inactive</option>
                    </select>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-cancel" onclick="closeEditModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) closeEditModal(); });

    document.getElementById("editUserForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const newRole = document.getElementById("editRole").value;
        const newActive = document.getElementById("editStatus").value === "true";
        const prefix = getApiPrefix();
        try {
            await apiRequest(`${prefix}/users/${userId}`, "PUT", {
                role: newRole,
                is_active: newActive,
            });
            showToast("User updated successfully!", "success");
            closeEditModal();
            loadUserList();
        } catch (error) {
            showToast("Failed to update user: " + error.message, "error");
        }
    });
}

function closeEditModal() {
    const m = document.getElementById("editUserModal");
    if (m) m.remove();
}

// ===== Delete User Modal =====
function openDeleteModal(userId, email, name) {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.id = "deleteUserModal";
    overlay.innerHTML = `
        <div class="modal-card" style="text-align:center;">
            <div style="font-size:3rem; margin-bottom:12px;">⚠️</div>
            <h3 style="margin-bottom:8px;">Delete User?</h3>
            <p style="color:#64748b; margin-bottom:20px; font-size:0.9rem;">Are you sure you want to permanently delete this user?</p>
            <div style="margin-bottom:24px; padding:14px; background:#fef2f2; border-radius:10px; border:1px solid #fecaca;">
                <p style="margin:0; color:#dc2626; font-weight:600; font-size:0.95rem;">${name}</p>
                <p style="margin:4px 0 0; color:#64748b; font-size:0.82rem;">${email}</p>
            </div>
            <p style="color:#ef4444; font-size:0.82rem; margin-bottom:20px; font-weight:500;">This action cannot be undone.</p>
            <div class="modal-actions" style="justify-content:center;">
                <button type="button" class="btn-cancel" onclick="closeDeleteModal()">Cancel</button>
                <button type="button" class="btn btn-primary" id="confirmDeleteBtn" style="background:#dc2626; border-color:#dc2626;">Delete User</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) closeDeleteModal(); });

    document.getElementById("confirmDeleteBtn").addEventListener("click", async () => {
        const prefix = getApiPrefix();
        try {
            await apiRequest(`${prefix}/users/${userId}`, "DELETE");
            showToast("User deleted successfully.", "success");
            closeDeleteModal();
            loadUserList();
        } catch (error) {
            showToast("Failed to delete: " + error.message, "error");
        }
    });
}

function closeDeleteModal() {
    const m = document.getElementById("deleteUserModal");
    if (m) m.remove();
}

// ===== Create User Modal =====
function openCreateUserModal() {
    const role = window._currentUserRole || "admin";
    let roleOptions;
    if (role === "superadmin") {
        // Superadmin can only create admins
        roleOptions = `<option value="admin">Admin</option>`;
    } else {
        // Admin can create doctors and staff
        roleOptions = `
            <option value="doctor">Doctor</option>
            <option value="staff">Staff</option>`;
    }

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.id = "createUserModal";
    overlay.innerHTML = `
        <div class="modal-card">
            <h3><i class="ri-user-add-line" style="margin-right:8px; color:#1565c0;"></i>Create New ${role === "superadmin" ? "Admin" : "User"}</h3>
            <form id="createUserForm">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" id="newFullName" placeholder="Dr. John Smith" required>
                </div>
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="newUsername" placeholder="johnsmith123" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="newEmail" placeholder="name@clinic.com" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="newPassword" placeholder="Min 8 chars, 1 uppercase, 1 number" required>
                </div>
                <div class="form-group">
                    <label>Role</label>
                    <select id="newRole" required>${roleOptions}</select>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-cancel" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Create ${role === "superadmin" ? "Admin" : "User"}</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });

    document.getElementById("createUserForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const userData = {
            full_name: document.getElementById("newFullName").value,
            username: document.getElementById("newUsername").value,
            email: document.getElementById("newEmail").value,
            password: document.getElementById("newPassword").value,
            role: document.getElementById("newRole").value,
        };
        try {
            await apiRequest("/users/register", "POST", userData);
            showToast("User created successfully!", "success");
            closeModal();
            loadUserList();
        } catch (error) {
            showToast("Failed to create user: " + error.message, "error");
        }
    });
}

function closeModal() {
    const m = document.getElementById("createUserModal");
    if (m) m.remove();
}

function filterAdminTable() {
    const query = document.getElementById('adminSearchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#adminUserTable tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

window.addEventListener("DOMContentLoaded", initDashboard);
document.getElementById("logoutBtn")?.addEventListener("click", logout);
