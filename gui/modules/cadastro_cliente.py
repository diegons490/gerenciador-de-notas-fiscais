# gui/modules/cadastro_cliente.py
"""
Interface completa para cadastro e gerenciamento de clientes usando ttkbootstrap.
Correções:
- Barra de pesquisa implementada localmente para evitar perda de foco do Entry durante digitação.
- Botão 'Limpar' ao lado da pesquisa fica habilitado apenas quando há texto.
- Botão 'Limpar Campos' fica habilitado apenas quando houver qualquer caractere em algum input do formulário.
- Após atualização da tabela, o foco e o cursor do Entry são restaurados usando after_idle.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from core import utils
from ..keys import EventKeys
from ..utils import (
    create_info_tooltip,
    create_warning_tooltip,
    create_error_tooltip,
    create_success_tooltip,
)
from ..utils.popups import ask_yes_no, show_info, show_error
from ..modules.table_manager import TableManagerFactory


class CadastroCliente(tb.Frame):
    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

        # Inicializar table manager para clientes
        self.table_manager = TableManagerFactory.create_table_manager(
            "clients", database
        )

        self.selected_ids = []
        self.all_clientes = []
        self.filtered_clientes = []
        self.editando_id = None
        self.modo_edicao = False

        # search_entry widget reference (para restaurar foco)
        self.search_entry = None
        self.btn_search_clear = None

        self.initialize_variables()
        self.create_widgets()
        self._attach_traces()
        self.refresh_data()

    def initialize_variables(self):
        self.nome_var = tk.StringVar()
        self.telefone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.cnpj_var = tk.StringVar()
        self.endereco_var = tk.StringVar()
        # manter search_var por compatibilidade, mas o Entry será gerenciado localmente
        self.search_var = tk.StringVar()

    def _attach_traces(self):
        """Anexa traces para atualizar estados de botões dinamicamente."""
        # Habilitar/desabilitar botão limpar pesquisa
        self.search_var.trace_add("write", lambda *a: self.update_search_clear_state())

        # Habilitar/desabilitar botão limpar campos quando qualquer campo mudar
        for var in (
            self.nome_var,
            self.telefone_var,
            self.email_var,
            self.cnpj_var,
            self.endereco_var,
        ):
            var.trace_add("write", lambda *a: self.update_limpar_campos_state())

    def create_widgets(self):
        """Cria os widgets usando grid para layout consistente"""
        # Configurar grid principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Frame principal
        main_frame = tb.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configurar grid do main_frame
        main_frame.grid_rowconfigure(2, weight=1)  # Linha da tabela expande
        main_frame.grid_columnconfigure(0, weight=1)

        # Título centralizado
        title_label = tb.Label(
            main_frame,
            text="Cadastro e Gerenciamento de Clientes",
            font=("Helvetica", 18, "bold"),
            bootstyle=PRIMARY,
            anchor="center",
            justify="center",
        )
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="ew")

        # garante que a coluna expanda para centralizar
        main_frame.grid_columnconfigure(0, weight=1)


        # Barra de pesquisa (implementação local para evitar perda de foco)
        self.create_search_bar(main_frame)

        # Tabela de clientes
        self.create_clientes_list(main_frame)

        # Frame do último cliente
        self.create_ultimo_cliente_frame(main_frame)

        # Formulário
        self.create_formulario(main_frame)

        # Botões de ação
        self.create_action_buttons(main_frame)

    def create_search_bar(self, parent):
        """Cria a barra de pesquisa localmente (evita perda de foco)."""
        search_frame = tb.Frame(parent)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)

        tb.Label(search_frame, text="Pesquisar cliente:").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )

        # Entry de pesquisa local (usa self.search_var)
        self.search_entry = tb.Entry(
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
        btn_clear = tb.Button(
            search_frame,
            text="Limpar",
            command=self.clear_search,
            bootstyle="outline-warning",
            width=8,
        )
        btn_clear.grid(row=0, column=2, padx=(10, 0))
        self.btn_search_clear = btn_clear
        self.btn_search_clear.config(state=DISABLED)

    def create_clientes_list(self, parent):
        """Cria a lista de clientes usando o table manager."""
        table_frame = self.table_manager.create_table(parent)
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        # Vincular evento de seleção
        self.table_manager.bind_selection_event(self.on_table_select)

    def create_ultimo_cliente_frame(self, parent):
        """Cria o frame para exibir o último cliente cadastrado."""
        self.ultimo_cliente_frame = tb.LabelFrame(
            parent, text="Último Cliente Cadastrado", bootstyle=WARNING
        )
        self.ultimo_cliente_frame.grid(row=3, column=0, sticky="ew", pady=(10, 10))
        self.ultimo_cliente_frame.columnconfigure(0, weight=1)

        inner_frame = tb.Frame(self.ultimo_cliente_frame, padding=10)
        inner_frame.grid(row=0, column=0, sticky="ew")

        for i in range(4):
            inner_frame.columnconfigure(i, weight=1)

        self.ultimo_cliente_labels = {
            "nome": tb.Label(inner_frame, text="Nome: -", font=("Helvetica", 9)),
            "telefone": tb.Label(
                inner_frame, text="Telefone: -", font=("Helvetica", 9)
            ),
            "email": tb.Label(inner_frame, text="Email: -", font=("Helvetica", 9)),
            "cnpj": tb.Label(inner_frame, text="CNPJ: -", font=("Helvetica", 9)),
        }

        self.ultimo_cliente_labels["nome"].grid(row=0, column=0, sticky="w", padx=5)
        self.ultimo_cliente_labels["telefone"].grid(row=0, column=1, sticky="w", padx=5)
        self.ultimo_cliente_labels["email"].grid(row=0, column=2, sticky="w", padx=5)
        self.ultimo_cliente_labels["cnpj"].grid(row=0, column=3, sticky="w", padx=5)

    def create_formulario(self, parent):
        """Cria o formulário de cadastro/edição"""
        form_frame = tb.LabelFrame(
            parent, text="Cadastrar/Editar Cliente", bootstyle=SUCCESS
        )
        form_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        form_frame.grid_columnconfigure(1, weight=1)

        campos = [
            ("Nome*:", "nome_var", self.nome_var, 0),
            ("Telefone:", "telefone_var", self.telefone_var, 1),
            ("Email:", "email_var", self.email_var, 2),
            ("CNPJ:", "cnpj_var", self.cnpj_var, 3),
            ("Endereço:", "endereco_var", self.endereco_var, 4),
        ]

        for i, (label_text, var_name, var, row) in enumerate(campos):
            lbl = tb.Label(form_frame, text=label_text)
            lbl.grid(row=row, column=0, sticky="w", pady=5, padx=10)

            entry = tb.Entry(form_frame, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=10)

            # Adicionar bindings específicos
            if var_name == "telefone_var":
                entry.bind("<KeyRelease>", self.formatar_telefone_wrapper)
                create_info_tooltip(
                    entry, "Telefone do cliente (formato: (00) 00000-0000)."
                )
            elif var_name == "email_var":
                entry.bind("<FocusOut>", self.validar_email_wrapper)
                create_info_tooltip(entry, "Email do cliente (exemplo@dominio.com).")
            elif var_name == "cnpj_var":
                entry.bind("<KeyRelease>", self.formatar_cnpj_wrapper)
                create_info_tooltip(entry, "CNPJ do cliente (00.000.000/0000-00).")
            else:
                create_info_tooltip(entry, f"{label_text.replace(':', '')} do cliente.")

    def create_action_buttons(self, parent):
        """Cria os botões de ação"""
        button_frame = tb.Frame(parent)
        button_frame.grid(row=5, column=0, sticky="ew", pady=20)
        button_frame.grid_columnconfigure(0, weight=1)

        btn_container = tb.Frame(button_frame)
        btn_container.grid(row=0, column=0)

        botoes = [
            (
                "Salvar Cliente",
                self.salvar_cliente,
                SUCCESS,
                "Salvar cliente no sistema.",
                0,
            ),
            (
                "Editar Cliente",
                self.editar_cliente,
                WARNING,
                "Editar cliente selecionado.",
                1,
            ),
            (
                "Excluir",
                self.excluir_clientes_choice,
                DANGER,
                "Excluir clientes selecionados.",
                2,
            ),
            (
                "Limpar Campos",
                self.limpar_campos,
                "outline-warning",
                "Limpar campos do formulário.",
                3,
            ),
            (
                "Voltar ao Menu",
                lambda: self.controller.handle_event(EventKeys.BACK),
                OUTLINE,
                "Voltar ao menu principal.",
                4,
            ),
        ]

        for text, command, style, tooltip, col in botoes:
            btn = tb.Button(
                btn_container, text=text, command=command, bootstyle=style, width=15
            )
            btn.grid(row=0, column=col, padx=5)

            if tooltip:
                if style == SUCCESS:
                    create_success_tooltip(btn, tooltip)
                elif style == WARNING:
                    create_warning_tooltip(btn, tooltip)
                elif style == DANGER:
                    create_error_tooltip(btn, tooltip)
                else:
                    create_info_tooltip(btn, tooltip)

            if text == "Salvar Cliente":
                self.btn_salvar = btn
            elif text == "Editar Cliente":
                self.btn_editar = btn
            elif text == "Excluir Selecionados":
                self.btn_excluir = btn
            elif text == "Limpar Campos":
                self.btn_limpar_campos = btn
                # desabilitar inicialmente
                self.btn_limpar_campos.config(state=DISABLED)

        # Configurar estados iniciais
        try:
            self.btn_editar.config(state=DISABLED)
            self.btn_excluir.config(state=DISABLED)
        except Exception:
            pass

    def update_search_clear_state(self):
        """Habilita/desabilita o botão limpar da pesquisa."""
        if self.btn_search_clear is None:
            return
        termo = (self.search_var.get() or "").strip()
        state = NORMAL if termo else DISABLED
        try:
            self.btn_search_clear.config(state=state)
        except Exception:
            pass

    def update_limpar_campos_state(self):
        """Habilita/desabilita o botão 'Limpar Campos' se qualquer campo do formulário tiver texto."""
        btn = getattr(self, "btn_limpar_campos", None)
        if btn is None:
            return
        any_filled = any(
            (v.get() or "").strip()
            for v in (
                self.nome_var,
                self.telefone_var,
                self.email_var,
                self.cnpj_var,
                self.endereco_var,
            )
        )
        try:
            btn.config(state=NORMAL if any_filled else DISABLED)
        except Exception:
            pass

    def atualizar_ultimo_cliente(self):
        """Atualiza o frame com os dados do último cliente cadastrado."""
        todos_clientes = self.database.get_all_clientes()

        if todos_clientes:
            ultimo_cliente = todos_clientes[0] if todos_clientes else None

            if ultimo_cliente and len(ultimo_cliente) >= 5:
                id, nome, telefone, email, cnpj, endereco = ultimo_cliente

                self.ultimo_cliente_labels["nome"].config(text=f"Nome: {nome}")
                self.ultimo_cliente_labels["telefone"].config(
                    text=f"Telefone: {telefone or '-'}"
                )
                self.ultimo_cliente_labels["email"].config(
                    text=f"Email: {email or '-'}"
                )
                self.ultimo_cliente_labels["cnpj"].config(text=f"CNPJ: {cnpj or '-'}")
            else:
                self.limpar_ultimo_cliente_labels()
        else:
            self.limpar_ultimo_cliente_labels()

    def limpar_ultimo_cliente_labels(self):
        """Limpa os labels do último cliente."""
        for label in self.ultimo_cliente_labels.values():
            label.config(text="-")

    def formatar_telefone_wrapper(self, event=None):
        telefone = self.telefone_var.get()
        formatted = utils.formatar_telefone(telefone)
        if telefone != formatted:
            self.telefone_var.set(formatted)
            try:
                if event and getattr(event, "widget", None):
                    event.widget.after_idle(lambda: event.widget.icursor(tk.END))
            except Exception:
                pass

    def formatar_cnpj_wrapper(self, event=None):
        cnpj = self.cnpj_var.get()
        formatted = utils.formatar_cnpj(cnpj)
        if cnpj != formatted:
            self.cnpj_var.set(formatted)
            try:
                if event and getattr(event, "widget", None):
                    event.widget.after_idle(lambda: event.widget.icursor(tk.END))
            except Exception:
                pass

    def validar_email_wrapper(self, event=None):
        email = self.email_var.get()
        if email and not utils.validar_email(email):
            event.widget.configure(bootstyle=DANGER)
        else:
            event.widget.configure(bootstyle=PRIMARY)

    def on_search(self, event=None):
        """Handler para pesquisa. Usa self.search_var para evitar perda de foco."""
        termo = (self.search_var.get() or "").strip()

        try:
            if termo:
                if hasattr(self.database, "search_clientes"):
                    self.filtered_clientes = self.database.search_clientes(termo)
                else:
                    lower = termo.lower()
                    self.filtered_clientes = [
                        row
                        for row in self.all_clientes
                        if any(lower in (str(col) or "").lower() for col in row)
                    ]
            else:
                self.filtered_clientes = self.all_clientes[:]
        except Exception:
            if termo:
                lower = termo.lower()
                self.filtered_clientes = [
                    row
                    for row in self.all_clientes
                    if any(lower in (str(col) or "").lower() for col in row)
                ]
            else:
                self.filtered_clientes = self.all_clientes[:]

        try:
            self.table_manager.update_table_data(self.filtered_clientes)
        except Exception as e:
            show_error(
                self.winfo_toplevel(), f"Erro ao atualizar tabela de clientes: {e}"
            )

        try:
            self.table_manager.clear_selection()
            if hasattr(self.table_manager, "selected_ids"):
                self.table_manager.selected_ids = []
        except Exception:
            pass

        # Restaurar foco/cursor para a search_entry após atualização
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

        # atualizar estado do botão limpar pesquisa
        self.update_search_clear_state()

    def clear_search(self):
        """Limpa a pesquisa: apaga o entry, restaura a tabela e foca o campo."""
        try:
            self.search_var.set("")
        except Exception:
            pass

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
        # estado do botão será atualizado por trace

    def on_table_select(self, event=None):
        self.selected_ids = self.table_manager.get_selected_ids()
        self.atualizar_estado_botoes()

    def refresh_data(self):
        self.all_clientes = self.database.get_all_clientes()
        self.filtered_clientes = self.all_clientes[:]
        self.selected_ids = []
        self.modo_edicao = False
        self.editando_id = None
        self.update_table()
        self.limpar_campos()
        self.atualizar_estado_botoes()
        self.atualizar_ultimo_cliente()
        # atualizar estados
        self.update_limpar_campos_state()
        self.update_search_clear_state()

    def update_table(self):
        try:
            self.table_manager.update_table_data(self.filtered_clientes)
        except Exception as e:
            show_error(
                self.winfo_toplevel(), f"Erro ao atualizar tabela de clientes: {e}"
            )

    def atualizar_estado_botoes(self):
        """Atualiza o estado dos botões baseado na seleção e modo de edição."""
        has_selection = len(self.selected_ids) > 0
        single_selection = len(self.selected_ids) == 1

        try:
            self.btn_excluir.config(state=NORMAL if has_selection else DISABLED)
        except Exception:
            pass

        if self.modo_edicao:
            try:
                self.btn_editar.config(
                    state=NORMAL,
                    text="Cancelar Edição",
                    bootstyle=DANGER,
                    command=self.cancelar_edicao,
                )
                # Modo edição: alterar botão Salvar para Atualizar
                self.btn_salvar.config(
                    text="Atualizar Cliente",
                    bootstyle=WARNING,
                    command=self.salvar_cliente,
                )
                create_warning_tooltip(self.btn_salvar, "Atualizar cliente editado.")
            except Exception:
                pass
        else:
            try:
                self.btn_editar.config(
                    state=NORMAL if single_selection else DISABLED,
                    text="Editar Cliente",
                    bootstyle=WARNING,
                    command=self.editar_cliente,
                )
                self.btn_salvar.config(
                    text="Salvar Cliente",
                    bootstyle=SUCCESS,
                    command=self.salvar_cliente,
                )
                create_success_tooltip(self.btn_salvar, "Salvar cliente no sistema.")
            except Exception:
                pass

    def excluir_clientes_choice(self):
        total_clientes = self.database.get_total_clientes()

        if total_clientes == 0:
            show_error(self.winfo_toplevel(), "Não há clientes no sistema!")
            return

        if not self.selected_ids:
            show_error(
                self.winfo_toplevel(), "Nenhum cliente selecionado para exclusão!"
            )
            return

        parent = self.winfo_toplevel()
        dialog = tb.Toplevel(parent)
        dialog.title("Excluir Clientes")
        dialog.transient(parent)
        dialog.grab_set()

        content = tb.Frame(dialog, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        tb.Label(
            content,
            text="Como deseja excluir os clientes?",
            font=("Helvetica", 14, "bold"),
        ).grid(row=0, column=0, pady=(0, 8))

        buttons_frame = tb.Frame(content)
        buttons_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)

        botoes_dialogo = [
            (
                "Apenas Selecionados",
                WARNING,
                lambda: self._delete_selected_confirm(self.selected_ids, dialog),
            ),
            ("Todos os Clientes", DANGER, lambda: self._confirm_and_delete_all(dialog)),
            ("Cancelar", SECONDARY, dialog.destroy),
        ]

        for i, (text, style, command) in enumerate(botoes_dialogo):
            btn = tb.Button(buttons_frame, text=text, bootstyle=style, command=command)
            btn.grid(row=i, column=0, sticky="ew", pady=6)

        dialog.update_idletasks()
        w, h = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()

    def _delete_selected_confirm(self, selected_ids, dialog):
        try:
            for cid in selected_ids:
                self.database.delete_cliente(cid)
        except Exception as e:
            show_error(self.winfo_toplevel(), f"Erro ao excluir clientes: {e}")
            dialog.destroy()
            return

        dialog.destroy()
        show_info(
            self.winfo_toplevel(),
            f"{len(selected_ids)} cliente(s) excluído(s) com sucesso!",
        )
        self.refresh_data()

    def _confirm_and_delete_all(self, dialog):
        total = self.database.get_total_clientes()
        msg = f"ATENÇÃO: Esta ação excluirá TODOS os {total} cliente(s) do sistema!\n\nEsta operação NÃO pode ser desfeita.\n\nDeseja realmente prosseguir?"

        resposta = ask_yes_no(self.winfo_toplevel(), msg, title="CONFIRMAÇÃO PERIGOSA")

        if resposta == "Sim":
            try:
                self.database.delete_all_clientes()
            except Exception as e:
                dialog.destroy()
                show_error(
                    self.winfo_toplevel(), f"Erro ao excluir todos os clientes: {e}"
                )
                return

            dialog.destroy()
            show_info(
                self.winfo_toplevel(),
                f"Todas as {total} cliente(s) foram excluídas com sucesso!",
            )
            self.refresh_data()

    def salvar_cliente(self):
        valido, mensagem = utils.validar_formulario_cliente(
            self.nome_var.get().strip(),
            self.telefone_var.get().strip(),
            self.email_var.get().strip(),
            self.cnpj_var.get().strip(),
        )

        if not valido:
            show_error(self.winfo_toplevel(), mensagem)
            return

        nome = self.nome_var.get().strip()
        telefone = self.telefone_var.get().strip()
        email = self.email_var.get().strip()
        cnpj = self.cnpj_var.get().strip()
        endereco = self.endereco_var.get().strip()

        try:
            if self.modo_edicao and self.editando_id:
                success = self.database.update_cliente(
                    self.editando_id, nome, telefone, email, cnpj, endereco
                )
                if success:
                    show_info(self.winfo_toplevel(), "Cliente atualizado com sucesso!")
                    self.modo_edicao = False
                    self.editando_id = None
                    self.atualizar_estado_botoes()
                else:
                    show_error(
                        self.winfo_toplevel(),
                        "Erro ao atualizar cliente! Verifique se o nome já existe.",
                    )
            else:
                success = self.database.insert_cliente(
                    nome, telefone, email, cnpj, endereco
                )
                if success:
                    show_info(self.winfo_toplevel(), "Cliente cadastrado com sucesso!")
                    self.atualizar_ultimo_cliente()
                else:
                    show_error(
                        self.winfo_toplevel(), "Já existe um cliente com este nome!"
                    )

            self.refresh_data()
        except Exception as e:
            show_error(self.winfo_toplevel(), f"Erro ao salvar cliente: {str(e)}")

    def editar_cliente(self):
        if not self.selected_ids or len(self.selected_ids) != 1:
            show_error(
                self.winfo_toplevel(), "Selecione exatamente um cliente para edição!"
            )
            return

        cliente_id = self.selected_ids[0]
        cliente = self.database.get_cliente_por_id(cliente_id)

        if cliente:
            id, nome, telefone, email, cnpj, endereco = cliente
            self.nome_var.set(nome or "")
            self.telefone_var.set(telefone or "")
            self.email_var.set(email or "")
            self.cnpj_var.set(cnpj or "")
            self.endereco_var.set(endereco or "")

            self.modo_edicao = True
            self.editando_id = id
            self.atualizar_estado_botoes()
            show_info(
                self.winfo_toplevel(),
                "Cliente carregado para edição. Modifique os campos e clique em Atualizar.",
            )

    def cancelar_edicao(self):
        self.modo_edicao = False
        self.editando_id = None
        self.limpar_campos()
        self.atualizar_estado_botoes()
        show_info(self.winfo_toplevel(), "Edição cancelada. Campos limpos.")

    def limpar_campos(self):
        self.nome_var.set("")
        self.telefone_var.set("")
        self.email_var.set("")
        self.cnpj_var.set("")
        self.endereco_var.set("")
        self.modo_edicao = False
        self.editando_id = None
        self.atualizar_estado_botoes()
        # estado do botão será atualizado via trace (update_limpar_campos_state)
