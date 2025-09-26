# gui/modules/main_menu.py
"""
Interface principal do sistema - versão modularizada com grid.
Correções:
- Implementação própria da barra de pesquisa para evitar perda de foco do Entry durante digitação.
- Clear (Limpar) agora apaga totalmente a string, restaura a tabela e refoca o Entry.
- Botão "Limpar Campos" fica habilitado apenas quando algum campo do formulário contém caractere.
- Botão "Limpar" ao lado da pesquisa fica habilitado apenas quando há texto na pesquisa.
- Após atualização da tabela, o foco e o cursor do Entry são restaurados usando after_idle.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from functools import partial
from ..keys import EventKeys
from ..utils.popups import show_error, show_info, show_warning
from ..utils import create_info_tooltip, create_success_tooltip
from ..modules.table_manager import TableManagerFactory
from ..modules.search_manager import SearchManager
from ..modules.add_invoice import AddInvoiceManager
from ..modules.edit_invoice import EditInvoiceManager
from ..modules.delete_note import DeleteNotes
from ..modules.export_note import ExportNotes
from ..modules.backup import ConfigBackup


class MainMenu(ttk.Frame):
    """View principal modularizada usando grid."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

        # Inicializar módulos
        self.table_manager = TableManagerFactory.create_table_manager("notes", database)
        self.search_manager = SearchManager(
            database
        )  # mantemos para funções utilitárias
        self.add_manager = AddInvoiceManager(database, theme_manager)
        self.edit_manager = EditInvoiceManager(database, theme_manager)
        self.delete_module = DeleteNotes(self, controller, theme_manager, database)
        self.export_module = ExportNotes(self, controller, theme_manager, database)
        self.backup_module = ConfigBackup(self, controller, theme_manager, database)

        # Estado da aplicação
        self.editando_id = None
        self.modo_edicao = False
        self.variables = self.add_manager.initialize_variables()  # dict of StringVar
        self.buttons = {}

        # Variável e widget da barra de pesquisa (implementação local para evitar problemas de foco)
        self.search_var = tk.StringVar()
        self.search_entry = None  # criado em create_search_bar
        self.btn_search_clear = None

        self.setup_ui()
        self._attach_traces()
        self.refresh_data()

    def setup_ui(self):
        """Configura toda a interface do usuário usando grid."""
        # Container principal
        self.main_container = ttk.Frame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configurar grid da MainMenu
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Configurar grid do main_container
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=0)  # título
        self.main_container.rowconfigure(1, weight=0)  # busca
        self.main_container.rowconfigure(2, weight=1)  # tabela (expande)
        self.main_container.rowconfigure(3, weight=0)  # última nota fiscal
        self.main_container.rowconfigure(4, weight=0)  # combobox
        self.main_container.rowconfigure(5, weight=0)  # formulário
        self.main_container.rowconfigure(6, weight=0)  # botões

        self.create_title()
        self.create_search_bar()  # implementação local
        self.create_table()
        self.create_ultima_nota_frame()  # abaixo da tabela
        self.create_cliente_combobox()
        self.create_form()
        self.create_buttons()

    def _attach_traces(self):
        """Anexa traces para manter estado dos botões de 'limpar' atualizados."""
        # Trace para botão limpar pesquisa
        self.search_var.trace_add("write", lambda *a: self.update_search_clear_state())

        # Traces para os campos do formulário -> habilita/desabilita botão "Limpar Campos"
        # usamos v=var no lambda para evitar late binding
        for name, var in self.variables.items():
            var.trace_add("write", lambda *a, v=var: self.update_limpar_campos_button_state())


    def create_title(self):
        """Cria o título da página."""
        title_label = ttk.Label(
            self.main_container,
            text="Gerenciador de Notas Fiscais",
            font=("Helvetica", 20, "bold"),
            bootstyle=PRIMARY,
            anchor="center",
            justify="center",
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")

        # garante expansão para centralizar
        self.main_container.grid_columnconfigure(0, weight=1)



    def create_search_bar(self):
        """
        Cria a barra de pesquisa localmente.
        Motivo: evitar perda de foco do Entry causada por atualizações de widgets externas.
        """
        search_frame = ttk.Frame(self.main_container)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        lbl = ttk.Label(search_frame, text="Pesquisar nota:")
        lbl.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Entry de pesquisa local (usa self.search_var)
        self.search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=50
        )
        self.search_entry.grid(row=0, column=1, sticky="ew")
        # KeyRelease para atualizar a tabela enquanto digita
        self.search_entry.bind("<KeyRelease>", self.on_search)
        # Garantir foco inicial na entry
        try:
            self.search_entry.focus_set()
        except Exception:
            pass

        # Botão Limpar: apaga toda a string e restaura a tabela
        btn_clear = ttk.Button(
            search_frame,
            text="Limpar",
            command=self.clear_search,
            bootstyle="outline-warning",
            width=8,
        )
        btn_clear.grid(row=0, column=2, padx=(10, 0))
        self.btn_search_clear = btn_clear
        # estado inicial: desabilitado (vazio)
        self.btn_search_clear.config(state=DISABLED)

    def create_table(self):
        """Cria a tabela de notas."""
        table_frame = self.table_manager.create_table(self.main_container)
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.table_manager.bind_selection_event(self.on_table_select)

    def create_ultima_nota_frame(self):
        """Cria o frame para exibir a última nota fiscal adicionada."""
        self.ultima_nota_frame = ttk.LabelFrame(
            self.main_container, text="Última Nota Fiscal Adicionada", bootstyle=WARNING
        )
        self.ultima_nota_frame.grid(row=3, column=0, sticky="ew", pady=(10, 10))
        self.ultima_nota_frame.columnconfigure(0, weight=1)

        inner_frame = ttk.Frame(self.ultima_nota_frame, padding=10)
        inner_frame.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            inner_frame.columnconfigure(i, weight=1)

        self.ultima_nota_labels = {
            "data": ttk.Label(inner_frame, text="Data: -", font=("Helvetica", 9)),
            "numero": ttk.Label(inner_frame, text="Número: -", font=("Helvetica", 9)),
            "cliente": ttk.Label(inner_frame, text="Cliente: -", font=("Helvetica", 9)),
            "valor": ttk.Label(inner_frame, text="Valor: -", font=("Helvetica", 9)),
        }

        self.ultima_nota_labels["data"].grid(row=0, column=0, sticky="w", padx=5)
        self.ultima_nota_labels["numero"].grid(row=0, column=1, sticky="w", padx=5)
        self.ultima_nota_labels["cliente"].grid(row=0, column=2, sticky="w", padx=5)
        self.ultima_nota_labels["valor"].grid(row=0, column=3, sticky="w", padx=5)

    def create_cliente_combobox(self):
        """Cria a combobox de clientes."""
        cliente_frame = self.search_manager.create_cliente_combobox(
            self.main_container,
            self.on_cliente_selecionado,
            self.limpar_selecao_cliente,
        )
        cliente_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))

    def create_form(self):
        """Cria o formulário de notas."""
        form_frame = ttk.LabelFrame(
            self.main_container, text="Adicionar/Editar Nota Fiscal", bootstyle=SUCCESS
        )
        form_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        form_frame.columnconfigure(0, weight=1)

        inner_frame = ttk.Frame(form_frame, padding=10)
        inner_frame.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            inner_frame.columnconfigure(i, weight=1 if i in [1, 3] else 0)

        self.create_form_fields(inner_frame)

    def formatar_telefone_wrapper(self, telefone_var, event=None):
        """Formata o telefone durante a digitação e reposiciona o cursor no fim."""
        from core import utils

        current = telefone_var.get()
        if current:
            formatted = utils.formatar_telefone(current)
            if current != formatted:
                telefone_var.set(formatted)
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def formatar_cnpj_wrapper(self, cnpj_var, event=None):
        """Formata o CNPJ durante a digitação e reposiciona o cursor no fim."""
        from core import utils

        current = cnpj_var.get()
        if current:
            formatted = utils.formatar_cnpj(current)
            if current != formatted:
                cnpj_var.set(formatted)
                try:
                    if event and getattr(event, "widget", None):
                        event.widget.after_idle(lambda: event.widget.icursor(tk.END))
                except Exception:
                    pass

    def create_form_fields(self, parent):
        """Cria os campos do formulário."""
        # Data Emissão
        ttk.Label(parent, text="Data Emissão*:").grid(
            row=0, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        self.date_entry = DateEntry(
            parent,
            dateformat="%d/%m/%Y",
            firstweekday=6,
            startdate=datetime.now(),
            bootstyle=PRIMARY,
        )
        self.date_entry.grid(row=0, column=1, sticky=EW, pady=5, padx=(0, 10))
        self.date_entry.bind(
            "<<DateEntrySelected>>",
            lambda e: self.add_manager.on_date_selected(
                self.date_entry, self.variables["data_var"]
            ),
        )
        self.variables["data_var"].set(datetime.now().strftime("%d/%m/%Y"))

        # Telefone
        ttk.Label(parent, text="Telefone:").grid(
            row=0, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_telefone = ttk.Entry(parent, textvariable=self.variables["telefone_var"])
        entry_telefone.grid(row=0, column=3, sticky=EW, pady=5)
        entry_telefone.bind(
            "<KeyRelease>",
            lambda e: self.formatar_telefone_wrapper(self.variables["telefone_var"], e),
        )

        # Número
        ttk.Label(parent, text="Número*:").grid(
            row=1, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        entry_numero = ttk.Entry(parent, textvariable=self.variables["numero_var"])
        entry_numero.grid(row=1, column=1, sticky=EW, pady=5, padx=(0, 10))
        entry_numero.bind(
            "<KeyRelease>",
            lambda e: self.add_manager.validar_numero_nota_wrapper(
                self.variables["numero_var"]
            ),
        )

        # Email
        ttk.Label(parent, text="Email:").grid(
            row=1, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_email = ttk.Entry(parent, textvariable=self.variables["email_var"])
        entry_email.grid(row=1, column=3, sticky=EW, pady=5)
        entry_email.bind(
            "<FocusOut>",
            lambda e: self.add_manager.validar_email_wrapper(
                self.variables["email_var"], entry_email
            ),
        )

        # Cliente
        ttk.Label(parent, text="Cliente*:").grid(
            row=2, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        entry_cliente = ttk.Entry(parent, textvariable=self.variables["cliente_var"])
        entry_cliente.grid(row=2, column=1, sticky=EW, pady=5, padx=(0, 10))

        # CNPJ
        ttk.Label(parent, text="CNPJ:").grid(
            row=2, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_cnpj = ttk.Entry(parent, textvariable=self.variables["cnpj_var"])
        entry_cnpj.grid(row=2, column=3, sticky=EW, pady=5)
        entry_cnpj.bind(
            "<KeyRelease>",
            lambda e: self.formatar_cnpj_wrapper(self.variables["cnpj_var"], e),
        )

        # Valor
        ttk.Label(parent, text="Valor (R$)*:").grid(
            row=3, column=0, sticky=E, pady=5, padx=(0, 5)
        )
        entry_valor = ttk.Entry(parent, textvariable=self.variables["valor_var"])
        entry_valor.grid(row=3, column=1, sticky=EW, pady=5, padx=(0, 10))
        entry_valor.bind(
            "<KeyRelease>",
            lambda e: self.add_manager.formatar_valor_wrapper(
                self.variables["valor_var"]
            ),
        )
        entry_valor.bind(
            "<FocusOut>",
            lambda e: self.add_manager.aplicar_formatacao_valor_wrapper(
                self.variables["valor_var"]
            ),
        )

        # Endereço
        ttk.Label(parent, text="Endereço:").grid(
            row=3, column=2, sticky=E, pady=5, padx=(10, 5)
        )
        entry_endereco = ttk.Entry(parent, textvariable=self.variables["endereco_var"])
        entry_endereco.grid(row=3, column=3, sticky=EW, pady=5)

    def create_buttons(self):
        """Cria os botões de ação."""
        button_frame = ttk.Frame(self.main_container)
        button_frame.grid(row=6, column=0, sticky="ew", pady=20)
        button_frame.columnconfigure(0, weight=1)

        # Linha 1
        line1 = ttk.Frame(button_frame)
        line1.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        line1.columnconfigure(0, weight=1)

        line1_inner = ttk.Frame(line1)
        line1_inner.grid(row=0, column=0)

        buttons_line1 = [
            (
                "Salvar Nota",
                SUCCESS,
                self.salvar_nota,
                "Salvar nota fiscal no sistema.",
            ),
            (
                "Editar Nota",
                WARNING,
                self.editar_nota,
                "Carregar nota selecionada para edição.",
            ),
            (
                "Excluir",
                DANGER,
                self.handle_delete_notes,
                "Excluir notas selecionadas.",
            ),
            (
                "Exportar",
                PRIMARY,
                self.handle_export_notes,
                "Exportar notas selecionadas para CSV.",
            ),
            (
                "Limpar Campos",
                "OUTLINE-WARNING",
                self.limpar_campos,
                "Limpar campos do formulário.",
            ),
        ]

        for i, (text, style, command, tooltip) in enumerate(buttons_line1):
            btn = ttk.Button(
                line1_inner, text=text, command=command, bootstyle=style, width=15
            )
            btn.grid(row=0, column=i, padx=5)

            if style == SUCCESS:
                create_success_tooltip(btn, tooltip)
            else:
                create_info_tooltip(btn, tooltip)

            # Armazenar referências aos botões importantes
            if text == "Salvar Nota":
                self.buttons["btn_salvar"] = btn
            elif text == "Editar Nota":
                self.buttons["btn_editar"] = btn
            elif text == "Excluir":
                self.buttons["btn_excluir"] = btn
            elif text == "Exportar":
                self.buttons["btn_exportar"] = btn
            elif text == "Limpar Campos":
                # guardamos referência para controlar estado
                self.buttons["btn_limpar_campos"] = btn
                # iniciar desabilitado (vazio)
                btn.config(state=DISABLED)

        # Linha 2
        line2 = ttk.Frame(button_frame)
        line2.grid(row=1, column=0, sticky="nsew")
        line2.columnconfigure(0, weight=1)

        line2_inner = ttk.Frame(line2)
        line2_inner.grid(row=0, column=0)

        buttons_line2 = [
            (
                "Cadastros",
                INFO,
                lambda: self.controller.handle_event(EventKeys.CADASTRO_CLIENTES),
                "Gerenciar cadastro de clientes.",
            ),
            (
                "Relatório",
                SECONDARY,
                lambda: self.controller.handle_event(EventKeys.REPORT),
                "Gerar relatório completo.",
            ),
            ("Backup", LIGHT, self.handle_backup, "Gerencia backups das notas."),
            (
                "Tema",
                "SUCCESS-OUTLINE",
                lambda: self.controller.handle_event(EventKeys.THEME),
                "Altera o tema da interface.",
            ),
            (
                "Sair",
                DARK,
                lambda: self.controller.handle_event(EventKeys.EXIT),
                "Sair do aplicativo.",
            ),
        ]

        for i, (text, style, command, tooltip) in enumerate(buttons_line2):
            btn = ttk.Button(
                line2_inner, text=text, command=command, bootstyle=style, width=12
            )
            btn.grid(row=0, column=i, padx=5)
            create_info_tooltip(btn, tooltip)

    def update_search_clear_state(self):
        """Ativa/desativa o botão 'Limpar' da pesquisa baseado no conteúdo."""
        if self.btn_search_clear is None:
            return
        termo = (self.search_var.get() or "").strip()
        state = NORMAL if termo else DISABLED
        try:
            self.btn_search_clear.config(state=state)
        except Exception:
            pass

    def update_limpar_campos_button_state(self):
        """Ativa/desativa o botão 'Limpar Campos' se houver qualquer texto em campos relevantes do formulário."""
        btn = self.buttons.get("btn_limpar_campos")
        if btn is None:
            return

        # Ignorar a data, pois data_var costuma ser preenchida automaticamente
        campos_a_verificar = [
            k for k in self.variables.keys() if k != "data_var"
        ]

        any_filled = any(
            (self.variables[k].get() or "").strip() for k in campos_a_verificar
        )

        state = NORMAL if any_filled else DISABLED
        try:
            btn.config(state=state)
        except Exception:
            pass    

    def atualizar_ultima_nota(self):
        """Atualiza o frame com os dados da última nota fiscal."""
        ultima_nota = self.database.get_ultima_nota()

        if ultima_nota:
            data_emissao, numero, cliente, valor = ultima_nota
            from core import utils  # Importar aqui para evitar circular imports

            self.ultima_nota_labels["data"].config(text=f"Data: {data_emissao}")
            self.ultima_nota_labels["numero"].config(text=f"Número: {numero}")
            self.ultima_nota_labels["cliente"].config(text=f"Cliente: {cliente}")
            self.ultima_nota_labels["valor"].config(
                text=f"Valor: {utils.formatar_moeda(valor)}"
            )
        else:
            for label in self.ultima_nota_labels.values():
                label.config(text="-")

    def on_search(self, event=None):
        """Handler para pesquisa.
        Usa self.search_var (implementação local) para evitar perda de foco
        e garantir comportamento consistente do botão 'Limpar'.
        """
        termo = (self.search_var.get() or "").strip()

        # Usar o filtro do SearchManager (se disponível) para consistência
        try:
            if termo:
                resultado = self.search_manager.filter_notes(
                    self.table_manager.all_data, termo
                )
                self.table_manager.filtered_data = resultado
            else:
                self.table_manager.filtered_data = self.table_manager.all_data.copy()
        except Exception:
            # fallback simples
            if termo:
                lower = termo.lower()
                filtered = [
                    row
                    for row in self.table_manager.all_data
                    if any(lower in (str(col) or "").lower() for col in row)
                ]
                self.table_manager.filtered_data = filtered
            else:
                self.table_manager.filtered_data = self.table_manager.all_data.copy()

        # Atualiza a tabela com os dados filtrados
        self.table_manager.update_table_data(self.table_manager.filtered_data)

        # Limpar seleção da tabela para evitar efeitos colaterais
        try:
            self.table_manager.clear_selection()
            self.table_manager.selected_ids = []
        except Exception:
            pass

        # Restaurar foco/cursor para a search_entry após atualização (evita "sair" do campo)
        if self.search_entry:
            try:
                self.search_entry.after_idle(
                    lambda: (
                        self.search_entry.focus_set(),
                        self.search_entry.icursor(tk.END),
                    )
                )
            except Exception:
                pass

        # atualizar estado do botão limpar pesquisa (trace também cuida, mas asseguramos aqui)
        self.update_search_clear_state()

    def on_table_select(self, event=None):
        """Handler para seleção na tabela."""
        self.table_manager.selected_ids = self.table_manager.get_selected_ids()
        self.atualizar_estado_botoes()

    def on_cliente_selecionado(self, event=None):
        """Handler para seleção de cliente."""
        self.search_manager.on_cliente_selecionado(event, self.variables)

    def limpar_selecao_cliente(self):
        """Limpa a seleção do cliente."""
        self.search_manager.limpar_selecao_cliente(self.variables)

    def clear_search(self):
        """Limpa a pesquisa: apaga o entry, restaura a tabela e foca o campo."""
        if self.search_var is not None:
            self.search_var.set("")
        # chama on_search para atualizar a tabela (restaurar todos os dados)
        self.on_search()
        # garantir foco no entry
        if self.search_entry:
            try:
                self.search_entry.after_idle(
                    lambda: (
                        self.search_entry.focus_set(),
                        self.search_entry.icursor(tk.END),
                    )
                )
            except Exception:
                pass
        # estado do botão será atualizado via trace

    def atualizar_estado_botoes(self):
        """Atualiza o estado dos botões baseado na seleção."""
        has_selection = len(getattr(self.table_manager, "selected_ids", [])) > 0
        single_selection = len(getattr(self.table_manager, "selected_ids", [])) == 1

        # Atualizar estados dos botões (alguns podem não existir até create_buttons)
        try:
            self.buttons["btn_excluir"].config(
                state=NORMAL if has_selection else DISABLED
            )
        except Exception:
            pass
        try:
            self.buttons["btn_exportar"].config(
                state=NORMAL if has_selection else DISABLED
            )
        except Exception:
            pass
        try:
            self.buttons["btn_editar"].config(
                state=NORMAL if single_selection else DISABLED
            )
        except Exception:
            pass

        # Configurar botão de edição/cancelamento
        try:
            if self.modo_edicao:
                self.buttons["btn_editar"].config(
                    text="Cancelar Edição",
                    bootstyle=DANGER,
                    command=self.cancelar_edicao,
                )
            else:
                self.buttons["btn_editar"].config(
                    text="Editar Nota", bootstyle=WARNING, command=self.editar_nota
                )
        except Exception:
            pass

    def salvar_nota(self):
        """Salva uma nova nota ou atualiza uma existente."""
        data = {
            "data": self.variables["data_var"].get().strip(),
            "numero": self.variables["numero_var"].get().strip(),
            "cliente": self.variables["cliente_var"].get().strip(),
            "valor": self.variables["valor_var"].get().strip(),
            "telefone": self.variables["telefone_var"].get().strip(),
            "email": self.variables["email_var"].get().strip(),
            "cnpj": self.variables["cnpj_var"].get().strip(),
            "endereco": self.variables["endereco_var"].get().strip(),
        }

        valido, mensagem = self.add_manager.validar_formulario(
            data=data["data"],
            numero=data["numero"],
            cliente=data["cliente"],
            valor=data["valor"],
            telefone=data["telefone"],
            email=data["email"],
            cnpj=data["cnpj"],
            endereco=data["endereco"],
        )

        if not valido:
            show_error(self, mensagem)
            return

        try:
            if self.modo_edicao and self.editando_id:
                success = self.edit_manager.atualizar_nota_existente(
                    self, self.editando_id, **data
                )
                if success:
                    self.modo_edicao = False
                    self.editando_id = None
                    self.buttons["btn_salvar"].config(
                        text="Salvar Nota", bootstyle=SUCCESS
                    )
            else:
                success = self.add_manager.salvar_nova_nota(self, **data)
                if success:
                    self.atualizar_ultima_nota()

            if success:
                self.refresh_data()

        except Exception as e:
            show_error(self, f"Erro ao salvar nota: {str(e)}")

    def editar_nota(self):
        """Carrega uma nota para edição."""
        if len(getattr(self.table_manager, "selected_ids", [])) != 1:
            show_warning(self, "Selecione exatamente uma nota para editar.")
            return

        nota_id = self.table_manager.selected_ids[0]
        success = self.edit_manager.carregar_nota_para_edicao(
            self, nota_id, self.date_entry, self.variables, self.buttons["btn_salvar"]
        )

        if success:
            self.modo_edicao = True
            self.editando_id = nota_id
            self.atualizar_estado_botoes()

    def cancelar_edicao(self):
        """Cancela o modo de edição."""
        self.edit_manager.cancelar_edicao(
            self, self.date_entry, self.variables, self.buttons["btn_salvar"]
        )
        self.modo_edicao = False
        self.editando_id = None
        self.atualizar_estado_botoes()

    def limpar_campos(self):
        """Limpa os campos do formulário."""
        self.add_manager.limpar_campos(self.date_entry, self.variables)
        self.modo_edicao = False
        self.editando_id = None
        try:
            self.buttons["btn_salvar"].config(text="Salvar Nota", bootstyle=SUCCESS)
        except Exception:
            pass
        # estado do botão limpar campos será atualizado pela trace

    def handle_delete_notes(self):
        """Handler para exclusão de notas."""
        selected_ids = getattr(self.table_manager, "selected_ids", [])
        total_notes = self.database.get_total_notas()

        if total_notes == 0:
            show_error(self, "Nenhuma nota encontrada no sistema!")
            return

        if not selected_ids:
            show_error(self, "Nenhuma nota selecionada!")
            return

        self.delete_module.handle_delete(selected_ids)
        self.refresh_data()

    def handle_export_notes(self):
        """Handler para exportação de notas."""
        selected_ids = getattr(self.table_manager, "selected_ids", [])
        total_notes = self.database.get_total_notas()

        if total_notes == 0:
            show_error(self, "Nenhuma nota encontrada no sistema!")
            return

        if not selected_ids:
            show_error(self, "Nenhuma nota selecionada!")
            return

        self.export_module.handle_export(selected_ids)

    def handle_backup(self):
        """Handler para backup."""
        self.backup_module.handle_backup()

    def refresh_data(self):
        """Atualiza os dados da view."""
        self.table_manager.all_data = self.database.get_all_notas()
        self.table_manager.filtered_data = self.table_manager.all_data.copy()
        self.table_manager.update_table_data(self.table_manager.filtered_data)
        try:
            self.table_manager.clear_selection()
        except Exception:
            pass
        self.table_manager.selected_ids = []
        self.limpar_campos()
        self.atualizar_estado_botoes()
        self.atualizar_ultima_nota()
        # atualizar estados relacionados a campos e pesquisa
        self.update_limpar_campos_button_state()
        self.update_search_clear_state()
