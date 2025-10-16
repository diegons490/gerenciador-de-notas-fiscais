# gui/modules/report.py
"""
Interface para geração de relatórios de notas fiscais usando ttkbootstrap.
Permite criar relatórios gerais, por período ou por cliente.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from datetime import datetime
from core import utils
from ..keys import EventKeys
from ..utils.popups import show_info, show_error, ask_yes_no
from ..utils import create_info_tooltip, create_success_tooltip, create_warning_tooltip


class Report(tb.Frame):
    """View de relatórios com interface ttkbootstrap."""

    def __init__(self, parent, controller, theme_manager, database):
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = theme_manager
        self.database = database

        self.create_widgets()

    def create_widgets(self):
        """Cria a interface de relatórios."""
        main_container = tb.Frame(self)
        main_container.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Título
        title_label = tb.Label(
            main_container,
            text="Relatório Completo",
            font=("Helvetica", 18, "bold"),
            bootstyle=PRIMARY,
        )
        title_label.pack(pady=(0, 20))

        # Container dos botões
        button_container = tb.Frame(main_container)
        button_container.pack(fill=BOTH, expand=True, pady=10)

        # Botões de relatório
        self.create_report_buttons(button_container)

        # Área de resultados
        self.create_results_area(main_container)

        # Botão Voltar
        self.create_back_button(main_container)

    def create_report_buttons(self, parent):
        """Cria os botões de geração de relatórios."""
        button_frame = tb.Frame(parent)
        button_frame.pack(fill=X, pady=10)

        # Botão Relatório Geral
        btn_geral = tb.Button(
            button_frame,
            text="Relatório Geral",
            bootstyle=SUCCESS,
            command=self._generate_general_report,
            width=20,
        )
        btn_geral.pack(pady=5)
        create_success_tooltip(
            btn_geral, "Gera relatório com todas as notas do sistema"
        )

        # Botão Relatório por Período
        btn_periodo = tb.Button(
            button_frame,
            text="Relatório por Período",
            bootstyle=INFO,
            command=self._generate_period_report,
            width=20,
        )
        btn_periodo.pack(pady=5)
        create_info_tooltip(
            btn_periodo, "Gera relatório filtrando por período específico"
        )

        # Botão Relatório por Cliente
        btn_cliente = tb.Button(
            button_frame,
            text="Relatório por Cliente",
            bootstyle=PRIMARY,
            command=self._generate_client_report,
            width=20,
        )
        btn_cliente.pack(pady=5)
        create_info_tooltip(btn_cliente, "Gera relatório filtrando por nome do cliente")

    def create_results_area(self, parent):
        """Cria a área de exibição dos resultados."""
        results_frame = tb.LabelFrame(
            parent, text="Resultado do Relatório", bootstyle=INFO
        )
        results_frame.pack(fill=BOTH, expand=True, pady=10)

        # Text widget com scrollbar
        text_frame = tb.Frame(results_frame)
        text_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Scrollbar vertical
        scrollbar = tb.Scrollbar(text_frame, bootstyle=ROUND)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Área de texto
        self.results_text = tb.Text(
            text_frame,
            wrap=WORD,
            yscrollcommand=scrollbar.set,
            height=15,
            font=("Courier New", 10),
        )
        self.results_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)

        # Configurar tags para formatação - usando bootstyle para cores temáticas
        self.results_text.tag_configure("title", font=("Courier New", 12, "bold"))
        self.results_text.tag_configure("header", font=("Courier New", 10, "bold"))
        self.results_text.tag_configure("normal", font=("Courier New", 10))

        # Usar cor do tema para sucesso
        success_color = self.theme_manager.style.colors.success
        self.results_text.tag_configure(
            "total", font=("Courier New", 10, "bold"), foreground=success_color
        )

    def create_back_button(self, parent):
        """Cria o botão para voltar ao menu principal."""
        button_container = tb.Frame(parent)
        button_container.pack(fill=X, pady=(20, 0))

        back_btn = tb.Button(
            button_container,
            text="Voltar ao Menu Principal",
            bootstyle=SECONDARY,
            command=lambda: self.controller.handle_event(EventKeys.BACK),
            width=20,
        )
        back_btn.pack(pady=10)
        create_info_tooltip(back_btn, "Retornar ao menu principal")

    def _generate_general_report(self):
        """Gera relatório geral com todas as notas."""
        # CORREÇÃO: get_all_notas() -> get_all_invoices()
        notas = self.database.get_all_invoices()
        self._display_report(notas, "Relatório Geral - Todas as Notas")

    def _generate_period_report(self):
        """Gera relatório por período específico usando calendário."""
        periodo = self._show_period_selection()
        if not periodo:
            return

        inicio, fim = periodo

        try:
            inicio_sql = datetime.strptime(inicio, "%d/%m/%Y").strftime("%Y-%m-%d")
            fim_sql = datetime.strptime(fim, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            show_error(self, "Formato de data inválido!")
            return

        # CORREÇÃO: get_notas_por_periodo() -> get_invoices_by_period()
        notas = self.database.get_invoices_by_period(inicio_sql, fim_sql)
        self._display_report(notas, f"Relatório - Período: {inicio} a {fim}")

    def _generate_client_report(self):
        """Gera relatório por cliente específico."""
        cliente = self._show_client_selection()
        if cliente is None:
            return

        cliente = cliente.strip()
        if not cliente:
            show_error(self, "Digite o nome do cliente.")
            return

        # CORREÇÃO: get_notas_por_cliente() -> get_invoices_by_customer()
        notas = self.database.get_invoices_by_customer(cliente)
        self._display_report(notas, f"Relatório - Cliente: '{cliente}'")

    def _show_period_selection(self):
        """Exibe diálogo para seleção de período com layout vertical."""
        dialog = tb.Toplevel(self)
        dialog.title("Selecionar Período")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Variáveis para as datas
        data_inicio_var = tk.StringVar()
        data_fim_var = tk.StringVar()

        # Frame principal
        content = tb.Frame(dialog, padding=20)
        content.pack(fill=BOTH, expand=True)

        tb.Label(
            content,
            text="Selecione o período:",
            font=("Helvetica", 12, "bold"),
            bootstyle=PRIMARY,
        ).pack(pady=(0, 15))

        # Container para organizar verticalmente
        dates_container = tb.Frame(content)
        dates_container.pack(fill=BOTH, expand=True, pady=10)

        # Data inicial - linha vertical
        inicio_frame = tb.Frame(dates_container)
        inicio_frame.pack(fill=X, pady=8)

        tb.Label(inicio_frame, text="Data Inicial:", font=("Helvetica", 10)).pack(
            side=LEFT, padx=(0, 10)
        )

        date_inicio = DateEntry(
            inicio_frame,
            dateformat="%d/%m/%Y",
            firstweekday=6,
            startdate=datetime.now(),
            bootstyle=PRIMARY,
            width=15,
        )
        date_inicio.pack(side=LEFT, fill=X, expand=True)
        date_inicio.bind(
            "<<DateEntrySelected>>",
            lambda e: data_inicio_var.set(date_inicio.entry.get()),
        )

        # Data final - linha vertical
        fim_frame = tb.Frame(dates_container)
        fim_frame.pack(fill=X, pady=8)

        tb.Label(fim_frame, text="Data Final:", font=("Helvetica", 10)).pack(
            side=LEFT, padx=(0, 10)
        )

        date_fim = DateEntry(
            fim_frame,
            dateformat="%d/%m/%Y",
            firstweekday=6,
            startdate=datetime.now(),
            bootstyle=PRIMARY,
            width=15,
        )
        date_fim.pack(side=LEFT, fill=X, expand=True)
        date_fim.bind(
            "<<DateEntrySelected>>", lambda e: data_fim_var.set(date_fim.entry.get())
        )

        # Botões centralizados horizontalmente
        buttons_frame = tb.Frame(content)
        buttons_frame.pack(fill=X, pady=(20, 0))

        def confirmar():
            if not data_inicio_var.get() or not data_fim_var.get():
                show_error(dialog, "Selecione ambas as datas!")
                return

            # Validar se data inicial é anterior à data final
            try:
                dt_inicio = datetime.strptime(data_inicio_var.get(), "%d/%m/%Y")
                dt_fim = datetime.strptime(data_fim_var.get(), "%d/%m/%Y")

                if dt_inicio > dt_fim:
                    show_error(dialog, "Data inicial deve ser anterior à data final!")
                    return

            except ValueError:
                show_error(dialog, "Formato de data inválido!")
                return

            dialog.result = (data_inicio_var.get(), data_fim_var.get())
            dialog.destroy()

        # Container para centralizar os botões
        button_container = tb.Frame(buttons_frame)
        button_container.pack(expand=True)

        tb.Button(
            button_container,
            text="Gerar Relatório",
            bootstyle=SUCCESS,
            command=confirmar,
            width=15,
        ).pack(side=LEFT, padx=5)

        tb.Button(
            button_container,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
            width=15,
        ).pack(side=LEFT, padx=5)

        # Configurar datas iniciais
        data_inicio_var.set(date_inicio.entry.get())
        data_fim_var.set(date_fim.entry.get())

        # Centralizar diálogo
        dialog.update_idletasks()
        w, h = 350, 250
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()
        return getattr(dialog, "result", None)

    def _show_client_selection(self):
        """Exibe diálogo para seleção de cliente."""
        dialog = tb.Toplevel(self)
        dialog.title("Relatório por Cliente")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        cliente_var = tk.StringVar()

        content = tb.Frame(dialog, padding=20)
        content.pack(fill=BOTH, expand=True)

        tb.Label(
            content,
            text="Digite o nome do cliente:",
            font=("Helvetica", 12, "bold"),
            bootstyle=PRIMARY,
        ).pack(pady=(0, 15))

        entry_frame = tb.Frame(content)
        entry_frame.pack(fill=X, pady=15)

        entry = tb.Entry(entry_frame, textvariable=cliente_var, font=("Helvetica", 11))
        entry.pack(fill=X, padx=5)
        entry.focus()

        # Botões centralizados
        buttons_frame = tb.Frame(content)
        buttons_frame.pack(fill=X, pady=(10, 0))

        button_container = tb.Frame(buttons_frame)
        button_container.pack(expand=True)

        def confirmar():
            if not cliente_var.get().strip():
                show_error(dialog, "Digite o nome do cliente!")
                return

            dialog.result = cliente_var.get().strip()
            dialog.destroy()

        tb.Button(
            button_container,
            text="Gerar Relatório",
            bootstyle=PRIMARY,
            command=confirmar,
            width=15,
        ).pack(side=LEFT, padx=5)

        tb.Button(
            button_container,
            text="Cancelar",
            bootstyle=SECONDARY,
            command=dialog.destroy,
            width=15,
        ).pack(side=LEFT, padx=5)

        # Centralizar diálogo
        dialog.update_idletasks()
        w, h = 350, 180
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        dialog.wait_window()
        return getattr(dialog, "result", None)

    def _display_report(self, notas, title):
        """Exibe o relatório gerado na área de texto."""
        self.results_text.delete(1.0, tk.END)

        if not notas:
            self.results_text.insert(
                tk.END, "Nenhuma nota encontrada para o relatório.\n", "normal"
            )
            return

        total_valor = sum(nota[4] for nota in notas)
        total_notas = len(notas)

        # Título do relatório
        self.results_text.insert(tk.END, f"{title}\n\n", "title")

        # Cabeçalho
        self.results_text.insert(tk.END, "Data       Número     Cliente", "header")
        self.results_text.insert(tk.END, " " * 20)  # Espaçamento
        self.results_text.insert(tk.END, "Valor\n", "header")
        self.results_text.insert(tk.END, "-" * 80 + "\n", "normal")

        # Dados das notas
        for nota in notas:
            id_nota, data_br, numero, cliente, valor = nota[:5]
            # Formatar para caber melhor na tela
            cliente_display = cliente[:30] + "..." if len(cliente) > 30 else cliente
            linha = f"{data_br:10} {numero:10} {cliente_display:33} {utils.format_currency(valor):>15}\n"
            self.results_text.insert(tk.END, linha, "normal")

        # Totais - usando estilo SUCCESS do tema
        self.results_text.insert(tk.END, "\n" + "=" * 80 + "\n", "normal")
        self.results_text.insert(tk.END, f"Total de notas: {total_notas}\n", "total")
        self.results_text.insert(tk.END, f"Valor total: {utils.format_currency(total_valor)}\n", "total")

        # Perguntar se deseja exportar
        self.results_text.insert(tk.END, "\n" + "-" * 80 + "\n", "normal")
        exportar = ask_yes_no(
            self, "Deseja exportar este relatório para um arquivo CSV?"
        )

        if exportar == "Sim":
            self._export_report(notas, title)

    def _export_report(self, notas, title):
        """Exporta o relatório para CSV."""
        # CORREÇÃO: Importar o módulo correto (invoice_export em vez de export_note)
        from ..modules.invoice_export import InvoiceExport

        # Extrair IDs das notas
        note_ids = [nota[0] for nota in notas]

        # Usar o módulo de exportação existente
        export_module = InvoiceExport(
            self, self.controller, self.theme_manager, self.database
        )
        export_module.export_invoices(
            note_ids, f"relatorio_{title.lower().replace(' ', '_')}"
        )

    def refresh_data(self):
        """Atualiza os dados da view (implementação para compatibilidade)."""
        # Limpar área de resultados
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(
            tk.END, "Selecione um tipo de relatório para gerar...", "normal"
        )