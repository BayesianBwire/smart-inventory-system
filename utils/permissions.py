role_permissions = {
    "super_admin": [
        "create_user",
        "view_logs",
        "view_audit_logs",
        "manage_inventory",
        "manage_sales",
        "export_data",
        "view_reports",
        "view_users",
        "assign_roles",
        "reset_passwords",
        "view_inventory"  # ✅ ADDED THIS LINE
    ],

    "admin": [
        "create_user",
        "assign_roles",
        "reset_passwords",
        "manage_inventory",
        "manage_sales",
        "view_reports",
        "view_users"
    ],

    "manager": [
        "create_user",
        "assign_roles",
        "reset_passwords",
        "manage_inventory",
        "manage_sales",
        "view_reports",
        "export_data",
        "view_users"
    ],

    "hr": [
        "create_user",
        "assign_roles",
        "reset_passwords",
        "manage_inventory",
        "manage_sales",
        "view_reports",
        "export_data",
        "view_users"
    ],

    "sales": [
        "view_sales",
        "make_sale",
        "export_data",
        "view_reports"
    ],

    "inventory": [
        "manage_inventory",
        "view_inventory",
        "view_sales",
        "view_users"
    ],

    "finance": [
        "view_reports",
        "export_data",
        "view_users"
    ],

    "support": [
        "view_inventory",
        "view_sales",
        "view_users"
    ],

    "attendant": [
        "view_sales",
        "make_sale"
    ]
}

def has_permission(role, permission):
    """
    Check if a given role has a specific permission.
    Usage: has_permission(current_user.role, 'create_user')
    """
    return permission in role_permissions.get(role, [])
