def is_college_admin(user):
    """Check if user has primary College Admin (Super Admin) status."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if getattr(user, 'role', '') == 'COLLEGE_ADMIN':
        return not hasattr(user, 'staff_profile')
    return False

def has_staff_permission(user, permission_name):
    """
    Check if a user has access to a specific action or category.
    College Admin has all access.
    Editor can view and perform write operations except on settings and staff management.
    View Only can only view and cannot write.
    """
    if not user.is_authenticated:
        return False
    if is_college_admin(user):
        return True
    if getattr(user, 'role', '') != 'COLLEGE_ADMIN':
        return False

    try:
        profile = user.staff_profile
    except AttributeError:
        return False

    parts = permission_name.split('.')
    if len(parts) != 2:
        return False
    module, action = parts

    # Staff users can never access settings or staff management
    if module in ['staff_management', 'role_management', 'system_settings', 'activity_logs']:
        return False

    role = profile.role
    if role == 'EDITOR':
        # Editor can manage everything else (view, create, edit, delete, approve, export)
        return True
    elif role == 'VIEW_ONLY':
        # View Only can only view
        return action == 'view'

    return False
