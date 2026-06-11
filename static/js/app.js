document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;
    document.querySelectorAll(".sidebar-nav a").forEach((link) => {
        const href = link.getAttribute("href");
        if (href === currentPath || (href !== "/" && currentPath.startsWith(href))) {
            link.classList.add("active");
        }
    });

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
