from django import template

register = template.Library()


@register.simple_tag
def avatar_url(user):
    profile = getattr(user, "profile", None)
    if profile and getattr(profile, "avatar", None):
        try:
            return profile.avatar.url
        except ValueError:
            return ""
    return ""


@register.simple_tag
def avatar_initials(user):
    username = getattr(user, "get_username", lambda: "")()
    if not username:
        username = getattr(user, "username", "") or ""
    username = username.strip()
    if not username:
        return "?"
    parts = username.split()
    if len(parts) > 1:
        return (parts[0][0] + parts[-1][0]).upper()
    return username[0].upper()
