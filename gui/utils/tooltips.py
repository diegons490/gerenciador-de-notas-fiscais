import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Literal, Optional


class ToolTip:
    def __init__(self, widget, text: str, bootstyle=None, delay=250, **kwargs):
        self.widget = widget
        self.text = text
        self.bootstyle = bootstyle
        self.delay = delay
        self.toplevel = None
        self.id = None
        self.toplevel_kwargs = {
            "overrideredirect": True,
            "master": self.widget,
            "windowtype": "tooltip",
            "alpha": 0.95,
        }
        self.toplevel_kwargs.update(kwargs)
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.move_tip)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide_tip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tip(self):
        if self.toplevel:
            return
        self.toplevel = ttk.Toplevel(**self.toplevel_kwargs)
        lbl = ttk.Label(
            self.toplevel,
            text=self.text,
            bootstyle=self.bootstyle or "secondary",
            padding=10,
            wraplength=300,
        )
        lbl.pack(fill=BOTH, expand=True)
        x = self.widget.winfo_pointerx() + 25
        y = self.widget.winfo_pointery() + 10
        self.toplevel.geometry(f"+{x}+{y}")

    def move_tip(self, *_):
        if self.toplevel:
            x = self.widget.winfo_pointerx() + 25
            y = self.widget.winfo_pointery() + 10
            self.toplevel.geometry(f"+{x}+{y}")

    def hide_tip(self, *_):
        if self.toplevel:
            self.toplevel.destroy()
            self.toplevel = None


# -------- TIPOS PRONTOS -------- #
def create_default_tooltip(widget, text):
    return ToolTip(widget, text, bootstyle="secondary")


def create_warning_tooltip(widget, text):
    return ToolTip(widget, text, bootstyle="warning")


def create_error_tooltip(widget, text):
    return ToolTip(widget, text, bootstyle="danger")


def create_info_tooltip(widget, text):
    return ToolTip(widget, text, bootstyle="info")


def create_success_tooltip(widget, text):
    return ToolTip(widget, text, bootstyle="success")
