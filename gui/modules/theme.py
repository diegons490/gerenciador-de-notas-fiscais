# gui/modules/theme.py
"""
Interface para seleção e aplicação de temas visuais.
Permite personalizar a aparência da aplicação.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ..keys import EventKeys


class ConfigTheme(tb.Frame):
    def __init__(self, parent, controller, theme_manager, database):
        """
        Inicializa a view de configuração de temas.
        """
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database
        self.selected_theme_name = None

        # Inicializar atributos para evitar AttributeError
        self.preview_elements = None
        self.preview_label = None
        self.tree = None
        self.tree_frame = None
        self.preview_frame = None
        self.paned_window = None

        self.create_widgets()

    def create_widgets(self):
        """Cria os widgets da view usando grid layout"""
        # Frame principal
        self.grid_rowconfigure(0, weight=0)  # Título
        self.grid_rowconfigure(1, weight=1)  # Conteúdo principal
        self.grid_rowconfigure(2, weight=0)  # Botões
        self.grid_columnconfigure(0, weight=1)  # Expande para permitir centralização

        # Título centralizado
        title_label = tb.Label(
            self,
            text="Configurações de Tema",
            font=("Helvetica", 18, "bold"),
            bootstyle=PRIMARY,
        )
        title_label.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="n")


        # PanedWindow para divisão da tela
        self.paned_window = tb.PanedWindow(self, orient=HORIZONTAL, bootstyle=SECONDARY)
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Frame para árvore de temas (40%)
        self.tree_frame = tb.Frame(self.paned_window)
        self.paned_window.add(self.tree_frame, weight=40)

        # Frame para preview (60%)
        self.preview_frame = tb.Frame(self.paned_window)
        self.paned_window.add(self.preview_frame, weight=60)

        # Configurar grids dos frames internos
        self.configure_tree_frame()
        self.configure_preview_frame()

        # Frame para botões
        button_frame = tb.Frame(self)
        button_frame.grid(row=2, column=0, sticky="ew", pady=20, padx=20)
        button_frame.grid_columnconfigure(0, weight=1)

        # Botão voltar centralizado
        back_btn = tb.Button(
            button_frame,
            text="Voltar",
            command=self.go_back,
            bootstyle=SECONDARY,
            width=15,
        )
        back_btn.grid(row=0, column=0)

        # Selecionar tema atual
        self.select_current_theme()

    def configure_tree_frame(self):
        """Configura o frame da árvore de temas com grid"""
        self.tree_frame.grid_rowconfigure(0, weight=0)  # Label
        self.tree_frame.grid_rowconfigure(1, weight=1)  # Árvore
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Label
        label = tb.Label(
            self.tree_frame, text="Selecione um tema:", font=("Helvetica", 12)
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Container para árvore com scrollbars
        tree_container = tb.Frame(self.tree_frame)
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Treeview
        self.tree = tb.Treeview(
            tree_container,
            columns=("type",),
            show="tree headings",
            bootstyle=PRIMARY,
        )
        self.tree.heading("#0", text="Temas Disponíveis")
        self.tree.column("#0", width=250, minwidth=200)
        self.tree.heading("type", text="Tipo")
        self.tree.column("type", width=80, minwidth=60)

        # Scrollbars
        v_scrollbar = tb.Scrollbar(
            tree_container, orient=VERTICAL, command=self.tree.yview
        )
        h_scrollbar = tb.Scrollbar(
            tree_container, orient=HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Posicionar com grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Popular árvore
        self.populate_theme_tree()
        self.tree.bind("<<TreeviewSelect>>", self.on_theme_select)

    def configure_preview_frame(self):
        """Configura o frame de preview com grid"""
        self.preview_frame.grid_rowconfigure(0, weight=0)  # Título
        self.preview_frame.grid_rowconfigure(1, weight=1)  # Conteúdo
        self.preview_frame.grid_columnconfigure(0, weight=1)

        # Título do preview
        self.preview_title = tb.Label(
            self.preview_frame,
            text="Preview do Tema",
            font=("Helvetica", 12, "bold"),
            bootstyle=PRIMARY,
        )
        self.preview_title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Container para conteúdo rolável
        content_container = tb.Frame(self.preview_frame)
        content_container.grid(row=1, column=0, sticky="nsew")
        content_container.grid_rowconfigure(0, weight=1)
        content_container.grid_columnconfigure(0, weight=1)

        # Canvas e scrollbars
        self.preview_canvas = tk.Canvas(content_container, highlightthickness=0)
        v_scrollbar = tb.Scrollbar(
            content_container, orient=VERTICAL, command=self.preview_canvas.yview
        )
        h_scrollbar = tb.Scrollbar(
            content_container, orient=HORIZONTAL, command=self.preview_canvas.xview
        )

        self.preview_canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Frame rolável
        self.scrollable_frame = tb.Frame(self.preview_canvas)
        self.scrollable_frame_id = self.preview_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        # Bind events
        self.scrollable_frame.bind("<Configure>", self.on_preview_frame_configure)
        self.preview_canvas.bind("<Configure>", self.on_canvas_configure)

        # Posicionar com grid
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Preview vazio inicial
        self.create_empty_preview()

    def populate_theme_tree(self):
        """Preenche a árvore com os temas organizados por categoria"""
        tree_data = self.theme_manager.get_themes_tree_data()

        # Limpar árvore existente
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Adicionar categorias e temas
        for category_name, themes in tree_data:
            category_id = self.tree.insert(
                "", "end", text=category_name, values=("Categoria",)
            )

            for theme_name, theme_display in themes:
                if "custom" in category_name.lower():
                    theme_type = "Customizado"
                elif "claro" in category_name.lower() or "light" in theme_name.lower():
                    theme_type = "Claro"
                else:
                    theme_type = "Escuro"

                self.tree.insert(
                    category_id,
                    "end",
                    text=theme_display,
                    values=(theme_type,),
                    tags=(theme_name,),
                )

        # Expandir categorias
        for category_id in self.tree.get_children():
            self.tree.item(category_id, open=True)

    def create_empty_preview(self):
        """Cria um preview vazio inicial"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        empty_label = tb.Label(
            self.scrollable_frame,
            text="Selecione um tema para visualizar o preview",
            font=("Helvetica", 10),
            bootstyle=SECONDARY,
        )
        empty_label.grid(row=0, column=0, sticky="nsew")
        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def on_preview_frame_configure(self, event):
        """Atualiza a região de scroll quando o frame é configurado"""
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Redimensiona o frame interno quando o canvas é redimensionado"""
        self.preview_canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def select_current_theme(self):
        """Seleciona o tema atual na árvore"""
        if not self.tree:
            return

        current_theme = self.theme_manager.current_theme

        for category_id in self.tree.get_children():
            for theme_id in self.tree.get_children(category_id):
                tags = self.tree.item(theme_id, "tags")
                if tags and len(tags) > 0:
                    theme_name = tags[0]
                    if theme_name.lower() == current_theme.lower():
                        self.tree.selection_set(theme_id)
                        self.tree.focus(theme_id)
                        self.tree.see(theme_id)
                        self.selected_theme_name = current_theme
                        self.update_preview(current_theme)
                        return

    def update_preview(self, theme_name):
        """Atualiza a área de preview com elementos do tema selecionado"""
        if not hasattr(self, "scrollable_frame") or not self.scrollable_frame:
            return

        # Limpar elementos anteriores
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Atualizar título
        if hasattr(self, "preview_title") and self.preview_title:
            self.preview_title.config(text=f"Preview do Tema: {theme_name}")

        # Configurar grid do frame rolável
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        current_row = 0

        # 1. SEÇÃO DE CORES PRINCIPAIS
        colors_frame = tb.Frame(
            self.scrollable_frame, relief=GROOVE, borderwidth=1, padding=10
        )
        colors_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        colors_frame.grid_columnconfigure(0, weight=1)
        current_row += 1

        tb.Label(
            colors_frame, text="Paleta de Cores", font=("Helvetica", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Cores principais em grid
        main_colors = [
            ("primary", "Primária"),
            ("secondary", "Secundária"),
            ("success", "Sucesso"),
            ("info", "Informação"),
            ("warning", "Aviso"),
            ("danger", "Perigo"),
            ("light", "Clara"),
            ("dark", "Escura"),
        ]

        color_grid = tb.Frame(colors_frame)
        color_grid.grid(row=1, column=0, sticky="ew")

        for i in range(4):  # 4 colunas
            color_grid.grid_columnconfigure(i, weight=1)

        for i, (color_key, color_name) in enumerate(main_colors):
            row = i // 4
            col = i % 4

            color_frame = tb.Frame(color_grid, width=100, height=80)
            color_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            color_frame.grid_propagate(False)
            color_frame.grid_columnconfigure(0, weight=1)

            # Quadrado de cor
            color_canvas = tk.Canvas(
                color_frame, width=80, height=40, highlightthickness=0
            )
            color_canvas.grid(row=0, column=0, pady=5)

            try:
                style = tb.Style()
                bg_color = (
                    style.lookup(f"{color_key}.TButton", "background") or "#cccccc"
                )
            except:
                bg_color = "#cccccc"

            color_canvas.create_rectangle(
                0, 0, 80, 40, fill=bg_color, outline="black", width=1
            )

            # Label
            tb.Label(
                color_frame, text=color_name, font=("Helvetica", 8), anchor="center"
            ).grid(row=1, column=0, sticky="ew", padx=5)

        # 2. SEÇÃO DE BOTÕES
        buttons_frame = tb.Frame(
            self.scrollable_frame, relief=GROOVE, borderwidth=1, padding=10
        )
        buttons_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        buttons_frame.grid_columnconfigure(0, weight=1)
        current_row += 1

        tb.Label(buttons_frame, text="Botões", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # Botões sólidos
        tb.Label(buttons_frame, text="Sólidos:", font=("Helvetica", 9)).grid(
            row=1, column=0, sticky="w", pady=(5, 2)
        )

        solid_frame = tb.Frame(buttons_frame)
        solid_frame.grid(row=2, column=0, sticky="w", pady=(0, 5))

        for i, style in enumerate([PRIMARY, SECONDARY, SUCCESS, INFO, WARNING, DANGER]):
            tb.Button(
                solid_frame, text=style.capitalize(), bootstyle=style, width=12
            ).grid(row=0, column=i, padx=2)

        # Botões outline
        tb.Label(buttons_frame, text="Outline:", font=("Helvetica", 9)).grid(
            row=3, column=0, sticky="w", pady=(5, 2)
        )

        outline_frame = tb.Frame(buttons_frame)
        outline_frame.grid(row=4, column=0, sticky="w", pady=(0, 5))

        outline_styles = [
            "outline-primary",
            "outline-secondary",
            "outline-success",
            "outline-info",
            "outline-warning",
            "outline-danger",
        ]

        for i, style in enumerate(outline_styles):
            style_name = style.replace("outline-", "").capitalize()
            tb.Button(outline_frame, text=style_name, bootstyle=style, width=12).grid(
                row=0, column=i, padx=2
            )

        # 3. SEÇÃO DE FORMULÁRIOS
        forms_frame = tb.Frame(
            self.scrollable_frame, relief=GROOVE, borderwidth=1, padding=10
        )
        forms_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        forms_frame.grid_columnconfigure(0, weight=1)
        current_row += 1

        tb.Label(
            forms_frame, text="Elementos de Formulário", font=("Helvetica", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Entradas de texto
        entry_frame = tb.Frame(forms_frame)
        entry_frame.grid(row=1, column=0, sticky="w", pady=2)

        tb.Label(entry_frame, text="Campo de texto:").grid(row=0, column=0, sticky="w")
        tb.Entry(entry_frame, width=20).grid(row=0, column=1, padx=5)
        tb.Entry(entry_frame, width=20, bootstyle=SUCCESS).grid(row=0, column=2, padx=5)
        tb.Entry(entry_frame, width=20, bootstyle=WARNING).grid(row=0, column=3, padx=5)

        # Checkbuttons e Radiobuttons
        check_radio_frame = tb.Frame(forms_frame)
        check_radio_frame.grid(row=2, column=0, sticky="w", pady=5)
        check_radio_frame.grid_columnconfigure(0, weight=1)
        check_radio_frame.grid_columnconfigure(1, weight=1)

        # Checkbuttons
        check_frame = tb.Frame(check_radio_frame)
        check_frame.grid(row=0, column=0, sticky="w", padx=10)

        tb.Label(check_frame, text="Checkbuttons:", font=("Helvetica", 9)).grid(
            row=0, column=0, sticky="w"
        )

        self.check_var1 = tk.BooleanVar(value=True)
        self.check_var2 = tk.BooleanVar(value=False)

        tb.Checkbutton(
            check_frame,
            text="Selecionado",
            bootstyle="primary-toolbutton",
            variable=self.check_var1,
        ).grid(row=1, column=0, sticky="w")
        tb.Checkbutton(
            check_frame,
            text="Deselecionado",
            bootstyle="primary-toolbutton",
            variable=self.check_var2,
        ).grid(row=2, column=0, sticky="w")
        tb.Checkbutton(
            check_frame,
            text="Desabilitado",
            bootstyle="primary-toolbutton",
            state=DISABLED,
        ).grid(row=3, column=0, sticky="w")

        # Radiobuttons
        radio_frame = tb.Frame(check_radio_frame)
        radio_frame.grid(row=0, column=1, sticky="w", padx=10)

        tb.Label(radio_frame, text="Radiobuttons:", font=("Helvetica", 9)).grid(
            row=0, column=0, sticky="w"
        )

        self.radio_var = tk.StringVar(value="1")
        tb.Radiobutton(
            radio_frame,
            text="Opção 1",
            bootstyle="primary-toolbutton",
            variable=self.radio_var,
            value="1",
        ).grid(row=1, column=0, sticky="w")
        tb.Radiobutton(
            radio_frame,
            text="Opção 2",
            bootstyle="primary-toolbutton",
            variable=self.radio_var,
            value="2",
        ).grid(row=2, column=0, sticky="w")
        tb.Radiobutton(
            radio_frame,
            text="Desabilitado",
            bootstyle="primary-toolbutton",
            state=DISABLED,
        ).grid(row=3, column=0, sticky="w")

        # 4. SEÇÃO DE OUTROS ELEMENTOS
        other_frame = tb.Frame(
            self.scrollable_frame, relief=GROOVE, borderwidth=1, padding=10
        )
        other_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        other_frame.grid_columnconfigure(0, weight=1)
        current_row += 1

        tb.Label(
            other_frame, text="Outros Elementos", font=("Helvetica", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Progressbar
        tb.Label(other_frame, text="Barras de progresso:").grid(
            row=1, column=0, sticky="w"
        )
        tb.Progressbar(other_frame, bootstyle=PRIMARY, value=50).grid(
            row=2, column=0, sticky="ew", pady=1
        )
        tb.Progressbar(other_frame, bootstyle=SUCCESS, value=75).grid(
            row=3, column=0, sticky="ew", pady=1
        )
        tb.Progressbar(other_frame, bootstyle=WARNING, value=25).grid(
            row=4, column=0, sticky="ew", pady=1
        )

        # Combobox
        combo_frame = tb.Frame(other_frame)
        combo_frame.grid(row=5, column=0, sticky="w", pady=5)

        tb.Label(combo_frame, text="Combobox:").grid(row=0, column=0, sticky="w")
        values = ["Opção 1", "Opção 2", "Opção 3"]
        combo = tb.Combobox(combo_frame, values=values, width=15)
        combo.grid(row=0, column=1, padx=5)
        combo.set("Opção 1")

        # Atualizar canvas
        self.scrollable_frame.update_idletasks()
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def on_theme_select(self, event):
        """Callback quando um tema é selecionado na árvore"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            tags = self.tree.item(item, "tags")

            if tags and len(tags) > 0:
                theme_name = tags[0]
                self.selected_theme_name = theme_name

                success = self.apply_theme_automatically(theme_name)
                if success:
                    self.update_preview(theme_name)

    def apply_theme_automatically(self, theme_name):
        """Aplica o tema selecionado automaticamente"""
        try:
            if theme_name in self.theme_manager.custom_themes:
                self.theme_manager._register_custom_themes()

            success = self.theme_manager.apply_theme(theme_name, self.controller.root)

            if success and hasattr(self, "layout"):
                self.layout.update_colors_from_theme()

            return success
        except Exception as e:
            print(f"Erro ao aplicar tema {theme_name}: {e}")
            return False

    def go_back(self):
        """Volta para a view anterior"""
        self.controller.handle_event(EventKeys.BACK)
