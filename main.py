# main.py
"""
Main entry point for the invoice management application.
Initializes all components and starts the graphical interface with ttkbootstrap.
"""

import tkinter as tk
import ttkbootstrap as tb
from core import ThemeManager, Database
from gui.app_controller import AppController

def main():
    """Main application function"""
    try:
        # Create main window FIRST
        root = tb.Window()
        root.title("Gerenciador de Notas Fiscais")

        # Initialize ThemeManager with real window
        theme_manager = ThemeManager(style=root.style)

        # Register custom themes BEFORE any operation
        print("Registrando temas customizados...")
        theme_manager._register_custom_themes()

        # List available themes for debug
        available_themes = theme_manager.style.theme_names() if theme_manager.style else []
        print(f"Temas disponíveis: {available_themes}")

        # Verify if current theme is valid
        current_theme = theme_manager.get_available_theme(theme_manager.current_theme)

        if theme_manager.current_theme != current_theme:
            print(f"Tema '{theme_manager.current_theme}' não disponível. Usando '{current_theme}'.")
            theme_manager.current_theme = current_theme
            theme_manager.config["theme"] = current_theme
            theme_manager.save_config()

        print(f"Tema a ser aplicado: {current_theme}")

        # Apply theme BEFORE restoring window state
        success = theme_manager.apply_theme(current_theme, root)

        if not success:
            print("Falha ao aplicar tema, usando fallback...")
            fallback_theme = theme_manager.get_available_theme("darkly")
            theme_manager.apply_theme(fallback_theme, root)

        # Restore window state
        theme_manager.restore_window_state(root)

        # Configure icon
        theme_manager.set_window_icon(root)

        # Configure close protocol to save state
        def on_closing():
            theme_manager.save_window_state(root)
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Initialize Database
        database = Database()

        # Initialize AppController
        app_controller = AppController(root, theme_manager, database)
        app_controller.show_main_menu()

        # Start main loop
        root.mainloop()

    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()