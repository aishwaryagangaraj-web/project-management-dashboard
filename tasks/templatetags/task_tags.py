import os

from django import template

register = template.Library()


@register.simple_tag
def file_kind(file_obj):
    if not file_obj:
        return ""
    extension = os.path.splitext(file_obj.name)[1].lstrip(".").lower()
    if extension in {"png", "jpg", "jpeg"}:
        return "image"
    if extension == "pdf":
        return "pdf"
    if extension == "docx":
        return "doc"
    if extension == "txt":
        return "txt"
    return "file"
