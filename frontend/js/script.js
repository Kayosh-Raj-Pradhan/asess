// Dynamically load nav.html and footer.html into placeholders
document.addEventListener("DOMContentLoaded", function () {
    const headerEl = document.getElementById("header-placeholder");
    const footerEl = document.getElementById("footer-placeholder");

    if (headerEl) {
        fetch("/static/nav.html")
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
            })
            .catch((err) => console.error("Failed to load nav:", err));
    }

    if (footerEl) {
        fetch("/static/footer.html")
            .then((r) => r.text())
            .then((html) => {
                footerEl.innerHTML = html;
            })
            .catch((err) => console.error("Failed to load footer:", err));
    }
});
