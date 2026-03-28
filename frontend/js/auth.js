const registerForm = document.getElementById("registerForm");
const loginForm = document.getElementById("loginForm");

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const userData = {
            full_name: document.getElementById("fullName").value,
            username: document.getElementById("username").value,
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
            role: document.getElementById("role").value,
        };

        try {
            await apiRequest("/users/register", "POST", userData);
            showToast("Account created successfully! Redirecting to login...", "success");
            setTimeout(() => { window.location.href = "/login"; }, 1500);
        } catch (error) {
            showToast("Registration failed: " + error.message, "error");
        }
    });
}

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            const response = await apiRequest(
                "/users/login",
                "POST",
                { username: email, password },
                { formData: true }
            );

            localStorage.setItem("access_token", response.access_token);
            localStorage.setItem("refresh_token", response.refresh_token);

            showToast("Login successful! Redirecting...", "success");
            setTimeout(() => { window.location.href = "/index"; }, 1200);
        } catch (error) {
            showToast("Login failed: " + error.message, "error");
        }
    });
}
