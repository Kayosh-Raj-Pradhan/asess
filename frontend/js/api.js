// Simple wrapper around fetch to talk to the backend API.
// This file is intentionally written without a bundler so it can be loaded
// directly in the browser via a plain <script> tag.

const API_BASE_URL = "http://localhost:8000";

async function apiRequest(path, method = "GET", body = null, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const headers = options.headers ? { ...options.headers } : {};

    const token = localStorage.getItem("access_token");
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const fetchOptions = {
        method,
        headers,
    };

    if (body != null) {
        if (options.formData) {
            const form = new URLSearchParams();
            Object.entries(body).forEach(([key, value]) => {
                form.append(key, value);
            });
            fetchOptions.body = form;
            headers["Content-Type"] = "application/x-www-form-urlencoded";
        } else {
            fetchOptions.body = JSON.stringify(body);
            headers["Content-Type"] = "application/json";
        }
    }

    const response = await fetch(url, fetchOptions);
    const contentType = response.headers.get("content-type") || "";

    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();
    if (!response.ok) {
        let message = response.statusText;
        if (data) {
            if (typeof data.detail === "string") {
                message = data.detail;
            } else if (Array.isArray(data.detail)) {
                message = data.detail.map((e) => e.msg || JSON.stringify(e)).join("; ");
            } else if (data.message) {
                message = data.message;
            }
        }
        throw new Error(message);
    }

    return data;
}

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/users/login";
}

