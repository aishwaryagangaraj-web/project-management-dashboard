from django.db.models import Q


ADMIN_ROLE = "admin"
MANAGER_ROLE = "manager"
MEMBER_ROLE = "member"


def profile_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "profile", None)


def user_role(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if getattr(user, "is_superuser", False):
        return ADMIN_ROLE
    profile = profile_for(user)
    return getattr(profile, "role", MEMBER_ROLE) if profile else MEMBER_ROLE


def is_admin(user):
    return user_role(user) == ADMIN_ROLE


def is_manager(user):
    return user_role(user) == MANAGER_ROLE


def is_member(user):
    role = user_role(user)
    return role in {MEMBER_ROLE, MANAGER_ROLE}


def can_create_project(user):
    return is_admin(user) or is_manager(user)


def can_view_project(user, project):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_admin(user):
        return True
    if not project:
        return False
    return project.owner_id == user.id or project.members.filter(pk=user.pk).exists()


def can_manage_project(user, project):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_admin(user):
        return True
    return bool(project and project.owner_id == user.id)


def can_assign_members(user, project):
    return can_manage_project(user, project)


def can_create_task(user, project=None):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_admin(user):
        return True
    if not project:
        if is_manager(user):
            return True
        from projects.models import Project

        return Project.objects.filter(owner=user).exists()
    return can_manage_project(user, project)


def can_view_task(user, task):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_admin(user):
        return True
    if not task:
        return False
    return task.project.owner_id == user.id or task.assignee_id == user.id


def can_edit_task_details(user, task):
    return can_manage_project(user, task.project)


def can_update_task_status(user, task):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_admin(user):
        return True
    return bool(task and (task.project.owner_id == user.id or task.assignee_id == user.id))


def can_manage_task_content(user, task):
    if not getattr(user, "is_authenticated", False):
        return False
    if is_admin(user):
        return True
    return bool(
        task
        and (
            task.project.owner_id == user.id
            or task.assignee_id == user.id
            or task.reporter_id == user.id
        )
    )


def visible_projects_queryset(user, queryset):
    if is_admin(user):
        return queryset
    return queryset.filter(Q(owner=user) | Q(members=user)).distinct()


def visible_tasks_queryset(user, queryset):
    if is_admin(user):
        return queryset
    return queryset.filter(Q(project__owner=user) | Q(assignee=user)).distinct()
