import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class CustomPopup(tk.Toplevel):
    """
    Popup customizado com título, mensagem e botões de ação,
    centralizado na tela e exibindo a mensagem corretamente.
    """

    def __init__(
        self, parent, title="Mensagem", message="Mensagem do sistema", buttons=None
    ):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)
        self.transient(parent)  # Torna a janela modal
        self.grab_set()  # Impede interação com a janela pai

        self.message = message
        self._popup_result = None
        self.buttons = buttons or [("OK", "success")]

        self.create_widgets()
        self.center_window()

        # Espera até que o popup seja fechado
        self.wait_window(self)

    def create_widgets(self):
        """Cria o conteúdo do popup."""
        # Frame principal
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Mensagem
        message_label = ttk.Label(
            main_frame,
            text=self.message,
            bootstyle="info",
            font=("Helvetica", 11),
            justify=CENTER,
            wraplength=400,  # Permite quebra de linha para textos longos
        )
        message_label.pack(pady=10)

        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Botões
        for text, style in self.buttons:
            ttk.Button(
                button_frame,
                text=text,
                bootstyle=style,
                command=lambda action=text: self.on_button_click(action),
                width=10,
            ).pack(side=LEFT, padx=5)

    def center_window(self):
        """Centraliza o popup na tela."""
        self.update_idletasks()  # Atualiza geometria

        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_button_click(self, action):
        """Lida com o clique nos botões."""
        self._popup_result = action
        self.destroy()

    @property
    def result(self):
        return self._popup_result


# ---------- Funções rápidas ----------
def show_info(parent, message, title="Informação"):
    dialog = CustomPopup(
        parent, title=title, message=message, buttons=[("OK", SUCCESS)]
    )
    return dialog.result


def show_warning(parent, message, title="Aviso"):
    dialog = CustomPopup(
        parent, title=title, message=message, buttons=[("OK", WARNING)]
    )
    return dialog.result


def show_error(parent, message, title="Erro"):
    dialog = CustomPopup(parent, title=title, message=message, buttons=[("OK", DANGER)])
    return dialog.result


# ---------- Funções interativas ----------
def ask_yes_no(parent, message, title="Confirmação"):
    dialog = CustomPopup(
        parent,
        title=title,
        message=message,
        buttons=[("Sim", SUCCESS), ("Não", DANGER)],
    )
    return dialog.result


def ask_ok_cancel(parent, message, title="Confirmação"):
    dialog = CustomPopup(
        parent,
        title=title,
        message=message,
        buttons=[("OK", SUCCESS), ("Cancelar", SECONDARY)],
    )
    return dialog.result


def ask_retry_cancel(parent, message, title="Tentar novamente?"):
    dialog = CustomPopup(
        parent,
        title=title,
        message=message,
        buttons=[("Tentar Novamente", WARNING), ("Cancelar", SECONDARY)],
    )
    return dialog.result
