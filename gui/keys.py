# gui/keys.py
"""
Event keys for application navigation and control.
"""

class EventKeys:
    """Keys for application navigation and control events."""

    # Main navigation
    EXIT = "exit"
    BACK = "back"
    HOME = "home"

    # Invoice operations
    ADD_INVOICE = "add_invoice"
    EDIT_INVOICE = "edit_invoice"
    DELETE_INVOICE = "delete_invoice"
    EXPORT_INVOICES = "export_invoices"

    # Customer operations
    CUSTOMER_REGISTRATION = "customer_registration"

    # System functionalities
    REPORT = "report"
    BACKUPS = "backups"
    THEME = "theme"
    CONFIG = "config"

    # Data control
    DATA_CHANGED = "data_changed"
    RELOAD = "reload"
    REFRESH = "refresh"