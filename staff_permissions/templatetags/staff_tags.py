from django import template
from staff_permissions.utils import has_staff_permission, is_college_admin

register = template.Library()

@register.filter(name='has_perm_filter')
def has_perm_filter(user, permission_name):
    if not user or not user.is_authenticated:
        return False
    return has_staff_permission(user, permission_name)

@register.filter(name='is_college_admin_filter')
def is_college_admin_filter(user):
    if not user or not user.is_authenticated:
        return False
    return is_college_admin(user)

@register.filter(name='can_edit_filter')
def can_edit_filter(user):
    """Returns True if user is College Admin or Editor. False for View Only."""
    if not user or not user.is_authenticated:
        return False
    if is_college_admin(user):
        return True
    if hasattr(user, 'staff_profile'):
        return user.staff_profile.role == 'EDITOR'
    return False
