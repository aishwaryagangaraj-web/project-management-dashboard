from io import BytesIO

from django.utils import timezone


def _reportlab():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    return {
        "colors": colors,
        "A4": A4,
        "ParagraphStyle": ParagraphStyle,
        "getSampleStyleSheet": getSampleStyleSheet,
        "cm": cm,
        "Paragraph": Paragraph,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
    }


def _styles(rl):
    styles = rl["getSampleStyleSheet"]()
    styles.add(rl["ParagraphStyle"](name="SectionTitle", parent=styles["Heading2"], textColor=rl["colors"].HexColor("#0f172a")))
    styles.add(rl["ParagraphStyle"](name="Small", parent=styles["BodyText"], fontSize=9, leading=12, textColor=rl["colors"].HexColor("#475569")))
    return styles


def _table(rl, rows, col_widths=None):
    table = rl["Table"](rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        rl["TableStyle"](
            [
                ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 1), (-1, -1), rl["colors"].whitesmoke),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl["colors"].whitesmoke, rl["colors"].HexColor("#e2e8f0")]),
                ("GRID", (0, 0), (-1, -1), 0.35, rl["colors"].HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEADING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    return table


def _chart_table(rl, labels, counts):
    rows = [["Category", "Count", "Bar"]]
    max_count = max(counts) if counts else 0
    for label, count in zip(labels, counts):
        bar_length = int((count / max_count) * 24) if max_count else 0
        rows.append([label, count, "█" * bar_length])
    return _table(rl, rows, [6 * rl["cm"], 2 * rl["cm"], 8 * rl["cm"]])


def _build_doc(rl, filename, story):
    buffer = BytesIO()
    doc = rl["SimpleDocTemplate"](
        buffer,
        pagesize=rl["A4"],
        title=filename,
        leftMargin=1.6 * rl["cm"],
        rightMargin=1.6 * rl["cm"],
        topMargin=1.4 * rl["cm"],
        bottomMargin=1.4 * rl["cm"],
    )
    doc.build(story)
    return buffer.getvalue()


def project_report_pdf(project, tasks, activities):
    rl = _reportlab()
    styles = _styles(rl)
    story = [
        rl["Paragraph"](f"Project Report: {project.name}", styles["Title"]),
        rl["Paragraph"](f"Generated {timezone.localtime(timezone.now()).strftime('%d %b %Y %H:%M')}", styles["Small"]),
        rl["Spacer"](1, 0.35 * rl["cm"]),
        _table(
            rl,
            [
                ["Owner", project.owner.get_username()],
                ["Status", project.get_status_display()],
                ["Priority", project.get_priority_display()],
                ["Start date", project.start_date or "Not set"],
                ["Due date", project.due_date or "Not set"],
                ["Progress", f"{project.progress}%"],
            ],
            [5 * rl["cm"], 10 * rl["cm"]],
        ),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Task Status Overview", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
    ]

    status_map = {}
    for task in tasks:
        status_map[task.get_status_display()] = status_map.get(task.get_status_display(), 0) + 1
    story.append(_chart_table(rl, list(status_map.keys()), list(status_map.values())))
    story.extend(
        [
            rl["Spacer"](1, 0.4 * rl["cm"]),
            rl["Paragraph"]("Recent Tasks", styles["SectionTitle"]),
            rl["Spacer"](1, 0.12 * rl["cm"]),
        ]
    )

    task_rows = [["Task", "Assignee", "Status", "Priority", "Due"]]
    for task in tasks:
        task_rows.append(
            [
                task.title,
                task.assignee.get_username() if task.assignee else "Unassigned",
                task.get_status_display(),
                task.get_priority_display(),
                task.due_date or "Not set",
            ]
        )
    story.append(_table(rl, task_rows))
    story.extend(
        [
            rl["Spacer"](1, 0.4 * rl["cm"]),
            rl["Paragraph"]("Recent Activity", styles["SectionTitle"]),
            rl["Spacer"](1, 0.12 * rl["cm"]),
        ]
    )

    activity_rows = [["Action", "Details", "When"]]
    for activity in activities:
        activity_rows.append(
            [
                activity.get_action_display(),
                activity.metadata.get("message") or activity.metadata.get("object_name") or activity.object_type,
                timezone.localtime(activity.created_at).strftime("%d %b %Y %H:%M"),
            ]
        )
    story.append(_table(rl, activity_rows))
    return _build_doc(rl, f"project-{project.slug}.pdf", story)


def task_report_pdf(task, comments, activities):
    rl = _reportlab()
    styles = _styles(rl)
    story = [
        rl["Paragraph"](f"Task Report: {task.title}", styles["Title"]),
        rl["Paragraph"](f"Generated {timezone.localtime(timezone.now()).strftime('%d %b %Y %H:%M')}", styles["Small"]),
        rl["Spacer"](1, 0.35 * rl["cm"]),
        _table(
            rl,
            [
                ["Project", task.project.name],
                ["Assignee", task.assignee.get_username() if task.assignee else "Unassigned"],
                ["Reporter", task.reporter.get_username() if task.reporter else "Not set"],
                ["Status", task.get_status_display()],
                ["Priority", task.get_priority_display()],
                ["Due date", task.due_date or "Not set"],
                ["Estimate", f"{task.estimate_hours}h"],
            ],
            [5 * rl["cm"], 10 * rl["cm"]],
        ),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Status Snapshot", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
        _chart_table(rl, ["Done", "Open"], [1 if task.status == "done" else 0, 0 if task.status == "done" else 1]),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Comments", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
    ]

    comment_rows = [["User", "Comment", "When"]]
    for comment in comments:
        comment_rows.append(
            [
                comment.user.get_username(),
                comment.comment,
                timezone.localtime(comment.created_at).strftime("%d %b %Y %H:%M"),
            ]
        )
    story.append(_table(rl, comment_rows))
    story.extend(
        [
            rl["Spacer"](1, 0.4 * rl["cm"]),
            rl["Paragraph"]("Activity Trail", styles["SectionTitle"]),
            rl["Spacer"](1, 0.12 * rl["cm"]),
        ]
    )
    activity_rows = [["Action", "Details", "When"]]
    for activity in activities:
        activity_rows.append(
            [
                activity.get_action_display(),
                activity.metadata.get("message") or activity.metadata.get("object_name") or activity.object_type,
                timezone.localtime(activity.created_at).strftime("%d %b %Y %H:%M"),
            ]
        )
    story.append(_table(rl, activity_rows))
    return _build_doc(rl, f"task-{task.pk}.pdf", story)


def analytics_report_pdf(summary, projects_by_status, tasks_by_status, monthly_completion):
    rl = _reportlab()
    styles = _styles(rl)
    story = [
        rl["Paragraph"]("Analytics Summary", styles["Title"]),
        rl["Paragraph"](f"Generated {timezone.localtime(timezone.now()).strftime('%d %b %Y %H:%M')}", styles["Small"]),
        rl["Spacer"](1, 0.35 * rl["cm"]),
        _table(
            rl,
            [
                ["Total projects", summary["projects"]],
                ["Total tasks", summary["tasks"]],
                ["Completed tasks", summary["completed_tasks"]],
                ["Overdue tasks", summary["overdue_tasks"]],
            ],
            [5 * rl["cm"], 10 * rl["cm"]],
        ),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Project Status Distribution", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
        _chart_table(
            rl,
            [item["status"].replace("_", " ").title() for item in projects_by_status],
            [item["total"] for item in projects_by_status],
        ),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Task Status Distribution", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
        _chart_table(
            rl,
            [item["status"].replace("_", " ").title() for item in tasks_by_status],
            [item["total"] for item in tasks_by_status],
        ),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Monthly Completions", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
    ]
    month_rows = [["Month", "Completed"]]
    for item in monthly_completion:
        month_rows.append([item["month"].strftime("%b %Y"), item["total"]])
    story.append(_table(rl, month_rows))
    return _build_doc(rl, "analytics-summary.pdf", story)
