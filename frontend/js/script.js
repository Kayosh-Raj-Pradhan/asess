// Dynamically load nav.html and footer.html into placeholders
document.addEventListener("DOMContentLoaded", function () {
    const headerEl = document.getElementById("header-placeholder");
    const footerEl = document.getElementById("footer-placeholder");

    if (headerEl) {
        fetch("/nav.html")
            .then((r) => r.text())
            .then((html) => {
                headerEl.innerHTML = html;
                // Highlight active nav link
                const currentPath = window.location.pathname;
                headerEl.querySelectorAll(".nav-links a").forEach((link) => {
                    if (link.getAttribute("href") === currentPath) {
                        link.classList.add("active");
                    }
                });
                // Mobile nav toggle
                const navToggle = document.getElementById("navToggle");
                const navLinks = document.getElementById("navLinks");
                const navToggleIcon = document.getElementById("navToggleIcon");
                if (navToggle && navLinks) {
                    navToggle.addEventListener("click", () => {
                        navLinks.classList.toggle("show-mobile");
                        if (navToggleIcon) {
                            navToggleIcon.className = navLinks.classList.contains("show-mobile")
                                ? "ri-close-line"
                                : "ri-menu-line";
                        }
                    });
                }
                // Role-based nav visibility
                const token = localStorage.getItem("access_token");
                if (token) {
                    try {
                        const payload = JSON.parse(atob(token.split('.')[1]));
                        const role = payload.role;
                        // Superadmin: hide New Scan, Eye Test, Patients (admin-only system access)
                        if (role === "superadmin") {
                            headerEl.querySelectorAll('.nav-links a').forEach(link => {
                                const href = link.getAttribute('href');
                                if (href === '/capture' || href === '/test' || href === '/patients') {
                                    link.style.display = 'none';
                                }
                            });
                        }
                        // Doctors: hide New Scan only
                        if (role === "doctor") {
                            headerEl.querySelectorAll('.nav-links a').forEach(link => {
                                if (link.getAttribute('href') === '/capture') link.style.display = 'none';
                            });
                        }
                    } catch(e) { /* ignore parse errors */ }
                }
            })
            .catch((err) => console.error("Failed to load nav:", err));
    }

    if (footerEl) {
        fetch("/footer.html")
            .then((r) => r.text())
            .then((html) => {
                footerEl.innerHTML = html;
            })
            .catch((err) => console.error("Failed to load footer:", err));
    }
});
