from __future__ import annotations

import os
from io import BytesIO
from math import ceil
from xml.sax.saxutils import escape

from django.utils import timezone


def _rl():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    return {
        "A4": A4,
        "Image": Image,
        "PageBreak": PageBreak,
        "Paragraph": Paragraph,
        "ParagraphStyle": ParagraphStyle,
        "Table": Table,
        "TableStyle": TableStyle,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "colors": colors,
        "cm": cm,
        "getSampleStyleSheet": getSampleStyleSheet,
    }


def _fmt_date(value):
    if not value:
        return "Not set"
    if hasattr(value, "strftime"):
        return value.strftime("%d %b %Y")
    return str(value)


def _fmt_datetime(value):
    if not value:
        return "Not set"
    localized = timezone.localtime(value)
    return localized.strftime("%d %b %Y %H:%M")


def _styles(rl):
    styles = rl["getSampleStyleSheet"]()
    styles.add(
        rl["ParagraphStyle"](
            name="BrandTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=30,
            textColor=rl["colors"].HexColor("#0f172a"),
            alignment=1,
            spaceAfter=8,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="BrandSub",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=rl["colors"].HexColor("#475569"),
            alignment=1,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=rl["colors"].HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="SectionNote",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=rl["colors"].HexColor("#64748b"),
            spaceAfter=4,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=rl["colors"].HexColor("#334155"),
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="CardValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=24,
            textColor=rl["colors"].white,
            alignment=0,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="CardLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=rl["colors"].white,
            alignment=0,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="CardHint",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=rl["colors"].HexColor("#dbeafe"),
            alignment=0,
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=rl["colors"].HexColor("#0f172a"),
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="TableCellBold",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=rl["colors"].HexColor("#0f172a"),
        )
    )
    styles.add(
        rl["ParagraphStyle"](
            name="InsightTitle",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=rl["colors"].white,
        )
    )
    return styles


def _table(rl, rows, col_widths=None, style=None, repeat_rows=0):
    table = rl["Table"](rows, colWidths=col_widths, hAlign="LEFT", repeatRows=repeat_rows)
    base_style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, rl["colors"].HexColor("#dbe3ef")),
        ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl["colors"].white, rl["colors"].HexColor("#f8fafc")]),
    ]
    if style:
        base_style.extend(style)
    table.setStyle(rl["TableStyle"](base_style))
    return table


def _font(size, bold=False):
    candidates = [
        rf"C:\Windows\Fonts\{'arialbd.ttf' if bold else 'arial.ttf'}",
        f"/usr/share/fonts/truetype/dejavu/{'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'}",
        f"/usr/share/fonts/truetype/liberation2/{'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf'}",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            from PIL import ImageFont

            return ImageFont.truetype(candidate, size=size)
    from PIL import ImageFont

    return ImageFont.load_default()


def _pil_to_image(rl, pil_image, width, height):
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    buffer.seek(0)
    return rl["Image"](buffer, width=width, height=height)


def _base_card(size, fill="#ffffff", border="#cbd5e1", radius=18):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", size, fill)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, outline=border, width=2)
    return img, draw


def _metric_card(rl, title, value, color_hex, accent_hex, hint):
    from PIL import ImageColor, ImageDraw

    img = _base_card((260, 108), fill=color_hex, border=color_hex)[0]
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, 259, 107), radius=18, fill=ImageColor.getrgb(color_hex), outline=ImageColor.getrgb(color_hex), width=2)
    draw.rounded_rectangle((0, 0, 10, 107), radius=18, fill=ImageColor.getrgb(accent_hex), outline=ImageColor.getrgb(accent_hex), width=1)
    draw.text((20, 16), title, font=_font(11, bold=True), fill="white")
    draw.text((20, 42), str(value), font=_font(26, bold=True), fill="white")
    draw.text((20, 77), hint, font=_font(8, bold=False), fill="#dbeafe")
    return _pil_to_image(rl, img, width=260, height=108)


def _placeholder_chart(rl, title, note):
    from PIL import ImageColor, ImageDraw

    img, draw = _base_card((420, 280))
    draw.text((20, 20), title, font=_font(14, bold=True), fill=ImageColor.getrgb("#0f172a"))
    draw.text((20, 140), note, font=_font(12), fill=ImageColor.getrgb("#64748b"))
    return _pil_to_image(rl, img, width=420, height=280)


def _pie_chart(rl, title, labels, values, palette):
    from PIL import ImageColor, ImageDraw

    if not values or sum(values) == 0:
        return _placeholder_chart(rl, title, "No data available")

    img, draw = _base_card((420, 280))
    draw.text((20, 18), title, font=_font(14, bold=True), fill=ImageColor.getrgb("#0f172a"))

    total = sum(values)
    bbox = (20, 60, 190, 230)
    start = -90
    for index, value in enumerate(values):
        end = start + (value / total) * 360
        color = ImageColor.getrgb(palette[index % len(palette)])
        draw.pieslice(bbox, start=start, end=end, fill=color, outline="white")
        start = end
    draw.ellipse((72, 112, 138, 178), fill="white", outline="white")

    legend_x = 235
    legend_y = 80
    for index, (label, value) in enumerate(zip(labels, values)):
        y = legend_y + index * 28
        color = ImageColor.getrgb(palette[index % len(palette)])
        draw.rounded_rectangle((legend_x, y, legend_x + 12, y + 12), radius=3, fill=color, outline=color)
        draw.text((legend_x + 18, y - 3), f"{label} ({value})", font=_font(10), fill=ImageColor.getrgb("#0f172a"))

    return _pil_to_image(rl, img, width=420, height=280)


def _doughnut_chart(rl, title, labels, values, palette):
    from PIL import ImageColor, ImageDraw

    if not values or sum(values) == 0:
        return _placeholder_chart(rl, title, "No data available")

    img, draw = _base_card((420, 280))
    draw.text((20, 18), title, font=_font(14, bold=True), fill=ImageColor.getrgb("#0f172a"))

    total = sum(values)
    bbox = (20, 60, 190, 230)
    start = -90
    for index, value in enumerate(values):
        end = start + (value / total) * 360
        color = ImageColor.getrgb(palette[index % len(palette)])
        draw.pieslice(bbox, start=start, end=end, fill=color, outline="white")
        start = end
    draw.ellipse((60, 100, 150, 190), fill="white", outline="white")

    legend_x = 235
    legend_y = 80
    for index, (label, value) in enumerate(zip(labels, values)):
        y = legend_y + index * 28
        color = ImageColor.getrgb(palette[index % len(palette)])
        draw.rounded_rectangle((legend_x, y, legend_x + 12, y + 12), radius=3, fill=color, outline=color)
        draw.text((legend_x + 18, y - 3), f"{label} ({value})", font=_font(10), fill=ImageColor.getrgb("#0f172a"))

    return _pil_to_image(rl, img, width=420, height=280)


def _bar_chart(rl, title, labels, values, palette):
    from PIL import ImageColor, ImageDraw

    if not values:
        return _placeholder_chart(rl, title, "No data available")

    img, draw = _base_card((420, 280))
    draw.text((20, 18), title, font=_font(14, bold=True), fill=ImageColor.getrgb("#0f172a"))

    left, top, right, bottom = 45, 60, 390, 220
    draw.line((left, bottom, right, bottom), fill=ImageColor.getrgb("#94a3b8"), width=2)
    draw.line((left, top, left, bottom), fill=ImageColor.getrgb("#94a3b8"), width=2)

    max_value = max(values) if values else 1
    chart_height = bottom - top - 10
    bar_space = (right - left - 30) / max(len(values), 1)
    bar_width = min(28, bar_space * 0.6)
    for index, value in enumerate(values):
        bar_height = 0 if max_value == 0 else int((value / max_value) * chart_height)
        x = left + 18 + index * bar_space
        y = bottom - bar_height
        color = ImageColor.getrgb(palette[index % len(palette)])
        draw.rounded_rectangle((x, y, x + bar_width, bottom), radius=4, fill=color, outline=color)
        label = labels[index]
        label_w = draw.textbbox((0, 0), label, font=_font(8))[2]
        draw.text((x + bar_width / 2 - label_w / 2, bottom + 6), label, font=_font(8), fill=ImageColor.getrgb("#475569"))
        value_text = str(value)
        value_w = draw.textbbox((0, 0), value_text, font=_font(8, bold=True))[2]
        draw.text((x + bar_width / 2 - value_w / 2, y - 13), value_text, font=_font(8, bold=True), fill=ImageColor.getrgb("#0f172a"))

    return _pil_to_image(rl, img, width=420, height=280)


def _line_chart(rl, title, labels, values, stroke_hex):
    from PIL import ImageColor, ImageDraw

    if not values:
        return _placeholder_chart(rl, title, "No data available")

    img, draw = _base_card((420, 280))
    draw.text((20, 18), title, font=_font(14, bold=True), fill=ImageColor.getrgb("#0f172a"))

    left, top, right, bottom = 45, 60, 390, 220
    draw.line((left, bottom, right, bottom), fill=ImageColor.getrgb("#94a3b8"), width=2)
    draw.line((left, top, left, bottom), fill=ImageColor.getrgb("#94a3b8"), width=2)

    max_value = max(values) if values else 1
    chart_height = bottom - top - 10
    chart_width = right - left - 20
    points = []
    for index, value in enumerate(values):
        x = left + 10 + (chart_width * index / max(len(values) - 1, 1))
        y = bottom - int((value / max_value) * chart_height) if max_value else bottom
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=ImageColor.getrgb(stroke_hex), width=3)
    for x, y in points:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=ImageColor.getrgb(stroke_hex), outline="white")

    for index, label in enumerate(labels):
        x = left + 10 + (chart_width * index / max(len(labels) - 1, 1))
        label_w = draw.textbbox((0, 0), label, font=_font(8))[2]
        draw.text((x - label_w / 2, bottom + 6), label, font=_font(8), fill=ImageColor.getrgb("#475569"))
    return _pil_to_image(rl, img, width=420, height=280)


def _footer(canvas, doc):
    canvas.saveState()
    width, height = doc.pagesize
    canvas.setStrokeColorRGB(0.82, 0.87, 0.93)
    canvas.line(doc.leftMargin, 1.1 * 28.35, width - doc.rightMargin, 1.1 * 28.35)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.36, 0.41, 0.49)
    canvas.drawString(doc.leftMargin, 0.72 * 28.35, "Generated by ProjectFlow Dashboard")
    canvas.drawRightString(width - doc.rightMargin, 0.72 * 28.35, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _build_doc(rl, filename, story):
    buffer = BytesIO()
    doc = rl["SimpleDocTemplate"](
        buffer,
        pagesize=rl["A4"],
        title=filename,
        author="ProjectFlow",
        subject="Executive analytics report",
        leftMargin=1.4 * rl["cm"],
        rightMargin=1.4 * rl["cm"],
        topMargin=1.3 * rl["cm"],
        bottomMargin=1.35 * rl["cm"],
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _table_row(label, value, styles, rl):
    return [
        rl["Paragraph"](escape(str(label)), styles["TableCellBold"]),
        rl["Paragraph"](escape(str(value)), styles["TableCell"]),
    ]


def _task_insight_table(rl, styles, title, items, empty_message):
    header = [
        rl["Paragraph"](escape(title), styles["InsightTitle"]),
        "",
    ]
    rows = [header, [rl["Paragraph"]("Task", styles["TableCellBold"]), rl["Paragraph"]("Details", styles["TableCellBold"])]]

    if not items:
        rows.append([rl["Paragraph"](escape(empty_message), styles["TableCell"]), ""])
    else:
        for item in items:
            task_title = escape(item.get("title", "Untitled task"))
            details_bits = [
                item.get("project", "Unknown project"),
                item.get("status_display", item.get("status", "unknown")).replace("_", " ").title(),
                item.get("priority_display", item.get("priority", "medium")).replace("_", " ").title(),
            ]
            due_date = item.get("due_date")
            if due_date:
                details_bits.append(f"Due {due_date}")
            completed_at = item.get("completed_at")
            if completed_at:
                details_bits.append(f"Completed {completed_at}")
            rows.append(
                [
                    rl["Paragraph"](task_title, styles["TableCellBold"]),
                    rl["Paragraph"]("<br/>".join(escape(str(bit)) for bit in details_bits), styles["TableCell"]),
                ]
            )

    table = rl["Table"](rows, colWidths=[6.2 * rl["cm"], 8.0 * rl["cm"]], repeatRows=2)
    table.setStyle(
        rl["TableStyle"](
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("SPAN", (0, 1), (0, 1)),
                ("SPAN", (1, 1), (1, 1)),
                ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#1d4ed8")),
                ("BACKGROUND", (0, 1), (-1, 1), rl["colors"].HexColor("#dbeafe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
                ("BOX", (0, 0), (-1, -1), 0.6, rl["colors"].HexColor("#cbd5e1")),
                ("GRID", (0, 1), (-1, -1), 0.35, rl["colors"].HexColor("#dbe3ef")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def analytics_report_pdf(summary, projects_by_status, tasks_by_status, monthly_completion, project_rows=None, task_insights=None):
    rl = _rl()
    styles = _styles(rl)
    project_rows = project_rows or []
    task_insights = task_insights or {}

    generated_at = timezone.localtime(timezone.now()).strftime("%d %b %Y %H:%M")

    project_status_labels = [escape(str(item["status"]).replace("_", " ").title()) for item in projects_by_status]
    project_status_values = [int(item["total"]) for item in projects_by_status]
    task_status_labels = [escape(str(item["status"]).replace("_", " ").title()) for item in tasks_by_status]
    task_status_values = [int(item["total"]) for item in tasks_by_status]
    month_labels = [item["month"].strftime("%b %y") for item in monthly_completion]
    month_values = [int(item["total"]) for item in monthly_completion]

    story = []

    title_band = rl["Table"](
        [
            [
                rl["Paragraph"](
                    '<font name="Helvetica-Bold" size="12" color="#2563eb">ProjectFlow</font><br/>'
                    '<font name="Helvetica-Bold" size="24" color="#0f172a">Project Management Analytics Report</font><br/>'
                    f'<font name="Helvetica" size="10" color="#64748b">Generated {escape(generated_at)}</font>',
                    styles["BodyText"],
                )
            ]
        ],
        colWidths=[17 * rl["cm"]],
    )
    title_band.setStyle(
        rl["TableStyle"](
            [
                ("BACKGROUND", (0, 0), (-1, -1), rl["colors"].white),
                ("BOX", (0, 0), (-1, -1), 0.8, rl["colors"].HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (-1, -1), 18),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
            ]
        )
    )

    brand_card = rl["Table"](
        [
            [
                rl["Paragraph"](
                    '<font name="Helvetica-Bold" size="32" color="#ffffff">PF</font>',
                    styles["BodyText"],
                )
            ]
        ],
        colWidths=[3.2 * rl["cm"]],
        rowHeights=[3.2 * rl["cm"]],
    )
    brand_card.setStyle(
        rl["TableStyle"](
            [
                ("BACKGROUND", (0, 0), (-1, -1), rl["colors"].HexColor("#1d4ed8")),
                ("BOX", (0, 0), (-1, -1), 0.8, rl["colors"].HexColor("#1d4ed8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )

    cover = rl["Table"](
        [[brand_card, title_band]],
        colWidths=[3.8 * rl["cm"], 13.2 * rl["cm"]],
    )
    cover.setStyle(
        rl["TableStyle"](
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.extend(
        [
            rl["Spacer"](1, 3.0 * rl["cm"]),
            cover,
            rl["Spacer"](1, 1.0 * rl["cm"]),
            rl["Paragraph"](
                "An executive overview of delivery health, workload distribution, and recent throughput across projects and tasks.",
                styles["BrandSub"],
            ),
            rl["Spacer"](1, 0.8 * rl["cm"]),
            rl["Table"](
                [[
                    rl["Paragraph"](f'<font name="Helvetica-Bold" size="10" color="#475569">Total Projects</font><br/><font name="Helvetica-Bold" size="22" color="#0f172a">{summary.get("projects", 0)}</font>', styles["BodyText"]),
                    rl["Paragraph"](f'<font name="Helvetica-Bold" size="10" color="#475569">Total Tasks</font><br/><font name="Helvetica-Bold" size="22" color="#0f172a">{summary.get("tasks", 0)}</font>', styles["BodyText"]),
                    rl["Paragraph"](f'<font name="Helvetica-Bold" size="10" color="#475569">Overdue Tasks</font><br/><font name="Helvetica-Bold" size="22" color="#ef4444">{summary.get("overdue_tasks", 0)}</font>', styles["BodyText"]),
                ]],
                colWidths=[5.4 * rl["cm"], 5.4 * rl["cm"], 5.4 * rl["cm"]],
            ),
        ]
    )

    story.append(rl["PageBreak"]())

    metric_cards = [
        _metric_card(rl, "Total Projects", summary.get("projects", 0), "#2563eb", "#1d4ed8", "All visible projects"),
        _metric_card(rl, "Active Projects", summary.get("active_projects", 0), "#10b981", "#059669", "Currently in motion"),
        _metric_card(rl, "Total Tasks", summary.get("tasks", 0), "#f59e0b", "#d97706", "Visible workload"),
        _metric_card(rl, "Completed Tasks", summary.get("completed_tasks", 0), "#14b8a6", "#0f766e", "Delivered work"),
        _metric_card(rl, "Pending Tasks", summary.get("pending_tasks", 0), "#fb923c", "#ea580c", "Still active"),
        _metric_card(rl, "Overdue Tasks", summary.get("overdue_tasks", 0), "#ef4444", "#dc2626", "Needs attention"),
    ]
    metric_grid = rl["Table"](
        [
            metric_cards[0:3],
            metric_cards[3:6],
        ],
        colWidths=[5.35 * rl["cm"], 5.35 * rl["cm"], 5.35 * rl["cm"]],
    )
    metric_grid.setStyle(
        rl["TableStyle"](
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    charts = rl["Table"](
        [
            [
                _pie_chart(rl, "Project Status Pie Chart", project_status_labels, project_status_values, ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]),
                _doughnut_chart(rl, "Task Status Doughnut Chart", task_status_labels, task_status_values, ["#1d4ed8", "#0f766e", "#f59e0b", "#10b981", "#ef4444"]),
            ],
            [
                _bar_chart(rl, "Monthly Completion Bar Chart", month_labels, month_values, ["#2563eb"]),
                _line_chart(rl, "Productivity Trend Line Chart", month_labels, month_values, "#8b5cf6"),
            ],
        ],
        colWidths=[8.45 * rl["cm"], 8.45 * rl["cm"]],
    )
    charts.setStyle(
        rl["TableStyle"](
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.extend(
        [
            rl["Paragraph"]("Dashboard Statistics", styles["SectionTitle"]),
            rl["Paragraph"]("Executive KPI cards summarizing the portfolio state.", styles["SectionNote"]),
            metric_grid,
            rl["Spacer"](1, 0.45 * rl["cm"]),
            rl["Paragraph"]("Charts", styles["SectionTitle"]),
            rl["Paragraph"]("Visual summary of delivery patterns and workload flow.", styles["SectionNote"]),
            charts,
        ]
    )

    story.append(rl["PageBreak"]())

    story.extend(
        [
            rl["Paragraph"]("Project Summary", styles["SectionTitle"]),
            rl["Paragraph"]("Portfolio status for every visible project.", styles["SectionNote"]),
        ]
    )

    project_table_rows = [
        [
            rl["Paragraph"]("Project", styles["TableCellBold"]),
            rl["Paragraph"]("Progress", styles["TableCellBold"]),
            rl["Paragraph"]("Status", styles["TableCellBold"]),
            rl["Paragraph"]("Total Tasks", styles["TableCellBold"]),
            rl["Paragraph"]("Completed Tasks", styles["TableCellBold"]),
            rl["Paragraph"]("Due Date", styles["TableCellBold"]),
        ]
    ]
    for row in project_rows:
        project_table_rows.append(
            [
                rl["Paragraph"](escape(str(row.get("name", "Untitled project"))), styles["TableCell"]),
                rl["Paragraph"](f"{row.get('progress', 0)}%", styles["TableCell"]),
                rl["Paragraph"](escape(str(row.get("status_display", row.get("status", "unknown"))).replace("_", " ").title()), styles["TableCell"]),
                rl["Paragraph"](str(row.get("total_tasks", 0)), styles["TableCell"]),
                rl["Paragraph"](str(row.get("completed_tasks", 0)), styles["TableCell"]),
                rl["Paragraph"](_fmt_date(row.get("due_date")), styles["TableCell"]),
            ]
        )
    if len(project_table_rows) == 1:
        project_table_rows.append(
            [
                rl["Paragraph"]("No projects available", styles["TableCell"]),
                "",
                "",
                "",
                "",
                "",
            ]
        )
    project_table = rl["Table"](
        project_table_rows,
        colWidths=[4.5 * rl["cm"], 2.1 * rl["cm"], 3.0 * rl["cm"], 2.0 * rl["cm"], 2.3 * rl["cm"], 2.3 * rl["cm"]],
        repeatRows=1,
    )
    project_table.setStyle(
        rl["TableStyle"](
            [
                ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl["colors"].white, rl["colors"].HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.35, rl["colors"].HexColor("#dbe3ef")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(project_table)
    story.append(rl["Spacer"](1, 0.45 * rl["cm"]))

    story.extend(
        [
            rl["Paragraph"]("Task Insights", styles["SectionTitle"]),
            rl["Paragraph"]("Focused lists for operational follow-up.", styles["SectionNote"]),
        ]
    )

    insight_blocks = [
        _task_insight_table(rl, styles, "High Priority Tasks", task_insights.get("high_priority", []), "No high priority tasks"),
        _task_insight_table(rl, styles, "Overdue Tasks", task_insights.get("overdue", []), "No overdue tasks"),
        _task_insight_table(rl, styles, "Blocked Tasks", task_insights.get("blocked", []), "No blocked tasks"),
        _task_insight_table(rl, styles, "Recently Completed", task_insights.get("recently_completed", []), "No recent completions"),
    ]

    insight_grid = rl["Table"](
        [
            [insight_blocks[0], insight_blocks[1]],
            [insight_blocks[2], insight_blocks[3]],
        ],
        colWidths=[8.55 * rl["cm"], 8.55 * rl["cm"]],
    )
    insight_grid.setStyle(
        rl["TableStyle"](
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(insight_grid)

    return _build_doc(rl, "analytics-summary.pdf", story)


def project_report_pdf(project, tasks, activities):
    rl = _rl()
    styles = _styles(rl)
    story = [
        rl["Paragraph"](f"Project Report: {escape(project.name)}", styles["Title"]),
        rl["Paragraph"](f"Generated {_fmt_datetime(timezone.now())}", styles["BodySmall"]),
        rl["Spacer"](1, 0.35 * rl["cm"]),
        _table(
            rl,
            [
                _table_row("Owner", project.owner.get_username(), styles, rl),
                _table_row("Status", project.get_status_display(), styles, rl),
                _table_row("Priority", project.get_priority_display(), styles, rl),
                _table_row("Start date", _fmt_date(project.start_date), styles, rl),
                _table_row("Due date", _fmt_date(project.due_date), styles, rl),
                _table_row("Progress", f"{project.progress}%", styles, rl),
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
    story.append(_table(rl, [[k, v, ""] for k, v in status_map.items()], [7 * rl["cm"], 2 * rl["cm"], 7 * rl["cm"]]))
    story.extend(
        [
            rl["Spacer"](1, 0.4 * rl["cm"]),
            rl["Paragraph"]("Recent Tasks", styles["SectionTitle"]),
            rl["Spacer"](1, 0.12 * rl["cm"]),
        ]
    )

    task_rows = [[rl["Paragraph"]("Task", styles["TableCellBold"]), rl["Paragraph"]("Assignee", styles["TableCellBold"]), rl["Paragraph"]("Status", styles["TableCellBold"]), rl["Paragraph"]("Priority", styles["TableCellBold"]), rl["Paragraph"]("Due", styles["TableCellBold"])]]
    for task in tasks:
        task_rows.append(
            [
                rl["Paragraph"](escape(task.title), styles["TableCell"]),
                rl["Paragraph"](escape(task.assignee.get_username() if task.assignee else "Unassigned"), styles["TableCell"]),
                rl["Paragraph"](escape(task.get_status_display()), styles["TableCell"]),
                rl["Paragraph"](escape(task.get_priority_display()), styles["TableCell"]),
                rl["Paragraph"](_fmt_date(task.due_date), styles["TableCell"]),
            ]
        )
    story.append(rl["Table"](task_rows, repeatRows=1))
    story.extend(
        [
            rl["Spacer"](1, 0.4 * rl["cm"]),
            rl["Paragraph"]("Recent Activity", styles["SectionTitle"]),
            rl["Spacer"](1, 0.12 * rl["cm"]),
        ]
    )

    activity_rows = [[rl["Paragraph"]("Action", styles["TableCellBold"]), rl["Paragraph"]("Details", styles["TableCellBold"]), rl["Paragraph"]("When", styles["TableCellBold"])]]
    for activity in activities:
        activity_rows.append(
            [
                rl["Paragraph"](escape(activity.get_action_display()), styles["TableCell"]),
                rl["Paragraph"](escape(activity.metadata.get("message") or activity.metadata.get("object_name") or activity.object_type), styles["TableCell"]),
                rl["Paragraph"](_fmt_datetime(activity.created_at), styles["TableCell"]),
            ]
        )
    story.append(rl["Table"](activity_rows, repeatRows=1))
    return _build_doc(rl, f"project-{project.slug}.pdf", story)


def task_report_pdf(task, comments, activities):
    rl = _rl()
    styles = _styles(rl)
    story = [
        rl["Paragraph"](f"Task Report: {escape(task.title)}", styles["Title"]),
        rl["Paragraph"](f"Generated {_fmt_datetime(timezone.now())}", styles["BodySmall"]),
        rl["Spacer"](1, 0.35 * rl["cm"]),
        _table(
            rl,
            [
                _table_row("Project", task.project.name, styles, rl),
                _table_row("Assignee", task.assignee.get_username() if task.assignee else "Unassigned", styles, rl),
                _table_row("Reporter", task.reporter.get_username() if task.reporter else "Not set", styles, rl),
                _table_row("Status", task.get_status_display(), styles, rl),
                _table_row("Priority", task.get_priority_display(), styles, rl),
                _table_row("Due date", _fmt_date(task.due_date), styles, rl),
                _table_row("Estimate", f"{task.estimate_hours}h", styles, rl),
            ],
            [5 * rl["cm"], 10 * rl["cm"]],
        ),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Status Snapshot", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
        _placeholder_chart(rl, "Status Snapshot", task.get_status_display()),
        rl["Spacer"](1, 0.4 * rl["cm"]),
        rl["Paragraph"]("Comments", styles["SectionTitle"]),
        rl["Spacer"](1, 0.12 * rl["cm"]),
    ]

    comment_rows = [[rl["Paragraph"]("User", styles["TableCellBold"]), rl["Paragraph"]("Comment", styles["TableCellBold"]), rl["Paragraph"]("When", styles["TableCellBold"])]]
    for comment in comments:
        comment_rows.append(
            [
                rl["Paragraph"](escape(comment.user.get_username()), styles["TableCell"]),
                rl["Paragraph"](escape(comment.comment), styles["TableCell"]),
                rl["Paragraph"](_fmt_datetime(comment.created_at), styles["TableCell"]),
            ]
        )
    story.append(rl["Table"](comment_rows, repeatRows=1))
    story.extend(
        [
            rl["Spacer"](1, 0.4 * rl["cm"]),
            rl["Paragraph"]("Activity Trail", styles["SectionTitle"]),
            rl["Spacer"](1, 0.12 * rl["cm"]),
        ]
    )
    activity_rows = [[rl["Paragraph"]("Action", styles["TableCellBold"]), rl["Paragraph"]("Details", styles["TableCellBold"]), rl["Paragraph"]("When", styles["TableCellBold"])]]
    for activity in activities:
        activity_rows.append(
            [
                rl["Paragraph"](escape(activity.get_action_display()), styles["TableCell"]),
                rl["Paragraph"](escape(activity.metadata.get("message") or activity.metadata.get("object_name") or activity.object_type), styles["TableCell"]),
                rl["Paragraph"](_fmt_datetime(activity.created_at), styles["TableCell"]),
            ]
        )
    story.append(rl["Table"](activity_rows, repeatRows=1))
    return _build_doc(rl, f"task-{task.pk}.pdf", story)
