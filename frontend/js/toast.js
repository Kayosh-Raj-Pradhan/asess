// ===== Toast Notification System =====
// Usage: showToast("Message here", "success"|"error"|"info"|"warning")

function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const icons = {
        success: "✅",
        error: "❌",
        info: "ℹ️",
        warning: "⚠️",
    };

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-msg">${message}</span>
        <button class="toast-close" onclick="this.parentElement.classList.add('removing'); setTimeout(() => this.parentElement.remove(), 300)">&times;</button>
    `;
    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.add("removing");
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}
