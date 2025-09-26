# main.py (corrigido)
"""
Ponto de entrada principal do aplicativo de gerenciamento de notas fiscais.
Inicializa todos os componentes e inicia a interface gráfica com ttkbootstrap.
"""

import tkinter as tk
import ttkbootstrap as tb
from core import ThemeManager, Database
from gui.app_controller import AppController


def main():
    """Função principal do aplicativo"""
    try:
        # Criar a janela principal PRIMEIRO
        root = tb.Window()
        root.title("Gerenciador de Notas Fiscais")

        # Inicializar o ThemeManager com a janela real
        theme_manager = ThemeManager(style=root.style)

        # Registrar temas customizados ANTES de qualquer operação
        print("Registrando temas customizados...")
        theme_manager._register_custom_themes()

        # Listar temas disponíveis para debug
        available_themes = (
            theme_manager.style.theme_names() if theme_manager.style else []
        )
        print(f"Temas disponíveis: {available_themes}")

        # Verificar se o tema atual é válido
        current_theme = theme_manager.get_available_theme(theme_manager.current_theme)

        if theme_manager.current_theme != current_theme:
            print(
                f"Tema '{theme_manager.current_theme}' não disponível. Usando '{current_theme}'."
            )
            theme_manager.current_theme = current_theme
            theme_manager.config["theme"] = current_theme
            theme_manager.save_config()

        print(f"Tema a ser aplicado: {current_theme}")

        # Aplicar o tema ANTES de restaurar o estado da janela
        success = theme_manager.apply_theme(current_theme, root)

        if not success:
            print("Falha ao aplicar tema, usando fallback...")
            fallback_theme = theme_manager.get_available_theme("darkly")
            theme_manager.apply_theme(fallback_theme, root)

        # Restaurar o estado da janela
        theme_manager.restore_window_state(root)

        # Configurar ícone
        theme_manager.set_window_icon(root)

        # Configurar o protocolo de fechamento para salvar o estado
        def on_closing():
            theme_manager.save_window_state(root)
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Inicializar o Database
        database = Database()

        # Inicializar o AppController
        app_controller = AppController(root, theme_manager, database)
        app_controller.show_main_menu()

        # Iniciar o loop principal
        root.mainloop()

    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
