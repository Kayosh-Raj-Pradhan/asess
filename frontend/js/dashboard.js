// Dashboard logic: verify user is authenticated and show profile info.

async function initDashboard() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/users/login";
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

        // Show admin panel button for admin users
        if (user.role === "admin") {
            const adminBtn = document.getElementById("adminPanelBtn");
            if (adminBtn) adminBtn.style.display = "inline-block";
        }

        // If on admin dashboard page, load user list
        if (document.getElementById("adminUserTable")) {
            if (user.role !== "admin") {
                showToast("Access denied. Admins only.", "error");
                setTimeout(() => { window.location.href = "/static/index.html"; }, 1500);
                return;
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
        const users = await apiRequest("/users/admin/users", "GET");
        const tbody = document.getElementById("adminUserTable");
        if (!tbody) return;

        tbody.innerHTML = "";
        users.forEach((u) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.full_name || "—"}</td>
                <td>${u.username}</td>
                <td>${u.email}</td>
                <td><span class="role-badge role-${u.role}">${u.role}</span></td>
                <td>${u.is_active ? '<span class="text-success">Active</span>' : '<span class="text-danger">Inactive</span>'}</td>
                <td class="action-cell">
                    <button class="btn-sm btn-edit" onclick="editUser(${u.id}, '${u.role}', ${u.is_active})">Edit</button>
                    <button class="btn-sm btn-delete" onclick="deleteUser(${u.id}, '${u.email}')">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        showToast("Failed to load users: " + error.message, "error");
    }
}

async function editUser(userId, currentRole, isActive) {
    const newRole = prompt("Enter new role (doctor, staff, admin):", currentRole);
    if (!newRole || !["doctor", "staff", "admin"].includes(newRole)) {
        if (newRole !== null) showToast("Invalid role. Must be doctor, staff, or admin.", "warning");
        return;
    }
    const toggleActive = confirm(`User is currently ${isActive ? "Active" : "Inactive"}.\nClick OK to toggle, Cancel to keep.`);

    try {
        await apiRequest(`/users/admin/users/${userId}`, "PUT", {
            role: newRole,
            is_active: toggleActive ? !isActive : isActive,
        });
        showToast("User updated successfully!", "success");
        loadUserList();
    } catch (error) {
        showToast("Failed to update user: " + error.message, "error");
    }
}

async function deleteUser(userId, email) {
    if (!confirm(`Are you sure you want to delete user ${email}? This cannot be undone.`)) return;

    try {
        await apiRequest(`/users/admin/users/${userId}`, "DELETE");
        showToast("User deleted.", "success");
        loadUserList();
    } catch (error) {
        showToast("Failed to delete: " + error.message, "error");
    }
}

// ===== Create User Modal =====
function openCreateUserModal() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.id = "createUserModal";
    overlay.innerHTML = `
        <div class="modal-card">
            <h3>Create New User</h3>
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
                    <select id="newRole" required>
                        <option value="doctor">Doctor</option>
                        <option value="staff">Staff</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-cancel" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Create User</button>
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

window.addEventListener("DOMContentLoaded", initDashboard);
document.getElementById("logoutBtn")?.addEventListener("click", logout);
