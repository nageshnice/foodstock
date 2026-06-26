from enum import StrEnum


class Role(StrEnum):
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Permission(StrEnum):
    VIEW_ADMIN = "view_admin"
    MANAGE_CATALOG = "manage_catalog"
    MANAGE_INVENTORY = "manage_inventory"
    MANAGE_ORDERS = "manage_orders"
    MANAGE_USERS = "manage_users"
    MANAGE_VENDORS = "manage_vendors"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.CUSTOMER: frozenset(),
    Role.STAFF: frozenset(
        {
            Permission.MANAGE_INVENTORY,
            Permission.MANAGE_ORDERS,
        }
    ),
    Role.ADMIN: frozenset(Permission),
    Role.SUPER_ADMIN: frozenset(Permission),
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check a role against the centralized permission policy."""

    return permission in ROLE_PERMISSIONS.get(role, frozenset())
