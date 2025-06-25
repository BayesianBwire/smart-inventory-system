# utils/permissions.py

role_permissions = {
    "superadmin": [
        "create_user", "view_logs", "manage_inventory",
        "manage_sales", "export_data", "view_reports"
    ],
    "admin": [
        "create_user", "view_logs", "manage_inventory",
        "manage_sales"
    ],
    "hr_manager": ["create_user", "view_logs"],
    "sales_manager": ["view_sales", "export_data", "view_reports"],
    "inventory_manager": ["manage_inventory", "view_inventory"],
    "accountant": ["view_reports", "export_data"],
    "support": ["view_inventory", "view_sales"],
    "attendant": ["view_sales", "make_sale"]
}

def has_permission(role, permission):
    return permission in role_permissions.get(role, [])
