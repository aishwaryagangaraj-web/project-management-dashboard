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
        root.style.colorScheme = theme;
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
    } else {
        root.style.colorScheme = root.dataset.theme;
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

    const analyticsDashboard = window.analyticsDashboard || {};
    const chartData = {
        ...(window.dashboardCharts || {}),
        ...(analyticsDashboard.charts || {}),
    };

    const animateCounter = (element) => {
        const rawTarget = Number.parseFloat(element.dataset.countTo || "0");
        const decimals = Number.parseInt(element.dataset.countDecimals || "0", 10);
        const suffix = element.dataset.countSuffix || "";
        const duration = 900;
        const start = performance.now();
        const from = 0;

        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = from + (rawTarget - from) * eased;
            element.textContent = `${value.toFixed(decimals)}${suffix}`;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };

        window.requestAnimationFrame(step);
    };

    document.querySelectorAll("[data-count-to]").forEach(animateCounter);

    if (!window.Chart) {
        return;
    }

    window.projectFlowCharts = window.projectFlowCharts || {};
    const rootStyles = getComputedStyle(document.documentElement);
    const palette = {
        blue: rootStyles.getPropertyValue("--primary").trim() || "#2563eb",
        green: rootStyles.getPropertyValue("--success").trim() || "#16a34a",
        amber: rootStyles.getPropertyValue("--warning").trim() || "#f59e0b",
        red: rootStyles.getPropertyValue("--danger").trim() || "#dc2626",
        indigo: rootStyles.getPropertyValue("--indigo").trim() || "#7c3aed",
        teal: "#0891b2",
    };

    const rgba = (hex, alpha) => {
        const normalized = hex.replace("#", "");
        const value = normalized.length === 3
            ? normalized.split("").map((character) => character + character).join("")
            : normalized;
        const red = Number.parseInt(value.slice(0, 2), 16);
        const green = Number.parseInt(value.slice(2, 4), 16);
        const blue = Number.parseInt(value.slice(4, 6), 16);
        return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
    };

    const defaultColors = [palette.blue, palette.green, palette.amber, palette.red, palette.indigo, palette.teal];

    const normalizeConfig = (source, fallbackLabel, typeHint) => {
        if (!source) {
            return null;
        }
        if (source.datasets) {
            return source;
        }
        return {
            type: typeHint,
            labels: source.labels || [],
            datasets: [
                {
                    label: fallbackLabel,
                    data: source.data || [],
                    backgroundColor: typeHint === "line" ? rgba(palette.blue, 0.18) : defaultColors,
                    borderColor: palette.blue,
                    borderWidth: typeHint === "line" ? 3 : 0,
                    fill: typeHint === "line",
                    tension: 0.35,
                },
            ],
        };
    };

    const renderChart = (canvasId, source, fallbackLabel, typeHint = "bar") => {
        const canvas = document.getElementById(canvasId);
        const config = normalizeConfig(source, fallbackLabel, typeHint);
        if (!canvas || !config) {
            return;
        }

        if (window.projectFlowCharts[canvasId]) {
            window.projectFlowCharts[canvasId].destroy();
        }

        const type = config.type || typeHint;
        const datasets = (config.datasets || []).map((dataset, index) => ({
            borderRadius: type === "bar" ? 10 : 0,
            borderWidth: 2,
            tension: 0.35,
            fill: type === "line",
            pointRadius: type === "line" ? 0 : 4,
            pointHoverRadius: type === "line" ? 4 : 6,
            backgroundColor: Array.isArray(dataset.backgroundColor)
                ? dataset.backgroundColor
                : dataset.backgroundColor || defaultColors[index % defaultColors.length],
            borderColor: dataset.borderColor || defaultColors[index % defaultColors.length],
            ...dataset,
        }));

        const isDoughnut = type === "doughnut" || type === "pie";
        const stacked = Boolean(config.options && config.options.stacked);
        const indexAxis = config.options && config.options.indexAxis ? config.options.indexAxis : undefined;

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 900,
                easing: "easeOutQuart",
            },
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 12,
                        usePointStyle: true,
                    },
                },
                tooltip: {
                    enabled: true,
                },
            },
        };

        if (isDoughnut) {
            options.cutout = config.options && config.options.cutout ? config.options.cutout : "68%";
            options.plugins.legend.position = "bottom";
        } else {
            options.scales = {
                y: {
                    beginAtZero: true,
                    stacked,
                    ticks: { precision: 0 },
                    grid: {
                        color: rootStyles.getPropertyValue("--border").trim() || "#e2e8f0",
                    },
                },
                x: {
                    stacked,
                    grid: {
                        display: false,
                    },
                },
            };
            if (indexAxis) {
                options.indexAxis = indexAxis;
            }
        }

        if (type === "line") {
            options.elements = {
                point: {
                    radius: 0,
                    hoverRadius: 5,
                },
            };
        }

        window.projectFlowCharts[canvasId] = new Chart(canvas, {
            type,
            data: {
                labels: config.labels || [],
                datasets,
            },
            options,
        });
    };

    const renderSparkline = (canvasId, series, color) => {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !Array.isArray(series) || !series.length) {
            return;
        }

        if (window.projectFlowCharts[canvasId]) {
            window.projectFlowCharts[canvasId].destroy();
        }

        window.projectFlowCharts[canvasId] = new Chart(canvas, {
            type: "line",
            data: {
                labels: series.map((_, index) => index + 1),
                datasets: [
                    {
                        data: series,
                        borderColor: color,
                        backgroundColor: rgba(color, 0.16),
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                },
                elements: {
                    point: { radius: 0 },
                },
                scales: {
                    x: { display: false },
                    y: { display: false },
                },
            },
        });
    };

    const toneColors = {
        "accent-blue": palette.blue,
        "accent-green": palette.green,
        "accent-amber": palette.amber,
        "accent-red": palette.red,
        "accent-indigo": palette.indigo,
        "accent-teal": palette.teal,
    };

    (analyticsDashboard.kpis || []).forEach((card) => {
        renderSparkline(`kpi-sparkline-${card.id}`, card.series || [], toneColors[card.tone] || palette.blue);
    });

    renderChart("taskStatusChart", chartData.taskStatus, "Tasks", analyticsDashboard.charts ? "doughnut" : "pie");
    renderChart("projectStatusChart", chartData.projectStatus, "Projects", "doughnut");
    renderChart("projectProgressChart", chartData.projectProgress, "Progress", "bar");
    renderChart("taskPriorityChart", chartData.taskPriority, "Tasks", "bar");
    renderChart("monthlyCompletionChart", chartData.monthlyCompletion, "Completed tasks", "line");
    renderChart("weeklyStackChart", chartData.weeklyStack, "Weekly flow", "bar");
    renderChart("productivityAreaChart", chartData.productivityArea, "Productivity", "line");
    renderChart("burndownChart", chartData.burndown, "Burndown", "line");
    renderChart("timelineChart", chartData.timeline, "Timeline", "line");
    renderChart("workloadChart", chartData.workload, "Workload", "bar");
});
