document.addEventListener("DOMContentLoaded", () => {
    window.projectFlowShowToast = window.projectFlowShowToast || ((message, type = "success") => {
        const stack = document.querySelector(".toast-stack");
        if (!stack) {
            return;
        }
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        stack.appendChild(toast);
        window.setTimeout(() => toast.remove(), 3200);
    });

    const currentPath = window.location.pathname;
    document.querySelectorAll(".sidebar-nav a").forEach((link) => {
        const href = link.getAttribute("href");
        if (href === currentPath || (href !== "/" && currentPath.startsWith(href))) {
            link.classList.add("active");
        }
    });

    const themeToggle = document.querySelector("[data-theme-toggle]");
    const themeKey = "projectflow-theme";
    const root = document.documentElement;
    const applyTheme = (theme) => {
        root.dataset.theme = theme;
        localStorage.setItem(themeKey, theme);
    };
    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
        });
    }
    if (!root.dataset.theme) {
        applyTheme(localStorage.getItem(themeKey) || "dark");
    }

    document.querySelectorAll(".messages .message").forEach((message) => {
        window.setTimeout(() => {
            message.classList.add("fade-out");
        }, 3200);
        window.setTimeout(() => {
            message.remove();
        }, 4200);
    });

    const kanbanBoard = document.querySelector("[data-kanban-board]");
    if (kanbanBoard) {
        const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
        const csrfToken = csrfInput ? csrfInput.value : "";
        let draggedCard = null;

        const refreshColumn = (zone) => {
            const column = zone.closest(".kanban-column");
            const count = column ? column.querySelector(".kanban-column-header strong") : null;
            const cards = zone.querySelectorAll(".kanban-card");
            const empty = zone.querySelector(".kanban-empty");
            if (count) {
                count.textContent = cards.length;
            }
            if (empty && cards.length > 0) {
                empty.remove();
            }
            if (!empty && cards.length === 0) {
                const emptyState = document.createElement("div");
                emptyState.className = "kanban-empty";
                emptyState.textContent = "No tasks";
                zone.appendChild(emptyState);
            }
        };

        kanbanBoard.querySelectorAll(".kanban-card").forEach((card) => {
            card.addEventListener("dragstart", () => {
                draggedCard = card;
                card.classList.add("is-dragging");
            });
            card.addEventListener("dragend", () => {
                card.classList.remove("is-dragging");
                draggedCard = null;
            });
        });

        kanbanBoard.querySelectorAll(".kanban-dropzone").forEach((zone) => {
            zone.addEventListener("dragover", (event) => {
                event.preventDefault();
                zone.classList.add("is-over");
            });
            zone.addEventListener("dragleave", () => {
                zone.classList.remove("is-over");
            });
            zone.addEventListener("drop", async (event) => {
                event.preventDefault();
                zone.classList.remove("is-over");
                if (!draggedCard) {
                    return;
                }

                const card = draggedCard;
                const previousParent = card.parentElement;
                const previousStatus = card.dataset.currentStatus;
                const nextStatus = zone.dataset.status;
                if (previousStatus === nextStatus) {
                    zone.appendChild(card);
                    refreshColumn(zone);
                    return;
                }

                zone.appendChild(card);
                refreshColumn(zone);
                refreshColumn(previousParent);
                try {
                    const response = await fetch(card.dataset.updateUrl, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfToken,
                            "X-Requested-With": "XMLHttpRequest",
                        },
                        body: JSON.stringify({ status: nextStatus }),
                    });
                    const data = await response.json();
                    if (!response.ok || !data.ok) {
                        throw new Error(data.error || "Could not update task status.");
                    }
                    card.dataset.currentStatus = nextStatus;
                    const badge = card.querySelector(".kanban-card-topline .badge");
                    if (badge) {
                        badge.className = `badge status-${nextStatus}`;
                        badge.textContent = data.status_label;
                    }
                    window.projectFlowShowToast(data.message || "Task status updated.");
                } catch (error) {
                    previousParent.appendChild(card);
                    refreshColumn(zone);
                    refreshColumn(previousParent);
                    window.projectFlowShowToast(error.message || "Task status update failed.", "error");
                }
            });
        });
    }

    if (!window.Chart || !window.dashboardCharts) {
        return;
    }

    const palette = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"];
    const buildDataset = (label, data, type) => ({
        label,
        data: data.data,
        backgroundColor: type === "line" ? "rgba(37, 99, 235, 0.16)" : palette,
        borderColor: type === "line" ? "#2563eb" : "#ffffff",
        borderWidth: type === "line" ? 3 : 2,
        fill: type === "line",
        tension: 0.35,
        borderRadius: type === "bar" ? 10 : 0,
    });
    window.projectFlowCharts = window.projectFlowCharts || {};

    const render = (id, type, data, label) => {
        const canvas = document.getElementById(id);
        if (!canvas || !data) {
            return;
        }
        if (window.projectFlowCharts[id]) {
            window.projectFlowCharts[id].destroy();
        }
        window.projectFlowCharts[id] = new Chart(canvas, {
            type,
            data: {
                labels: data.labels,
                datasets: [buildDataset(label, data, type)],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { boxWidth: 12, usePointStyle: true } },
                },
                scales: type === "pie" ? {} : {
                    y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#eef2f7" } },
                    x: { grid: { display: false } },
                },
            },
        });
    };

    render("taskStatusChart", "pie", window.dashboardCharts.taskStatus, "Tasks");
    render("projectStatusChart", "bar", window.dashboardCharts.projectStatus, "Projects");
    render("projectProgressChart", "bar", window.dashboardCharts.projectProgress, "Progress");
    render("taskPriorityChart", "bar", window.dashboardCharts.taskPriority, "Tasks");
    render("monthlyCompletionChart", "line", window.dashboardCharts.monthlyCompletion, "Completed tasks");
});
