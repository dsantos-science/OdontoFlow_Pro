import customtkinter as ctk
import sqlite3
import os
from tkinter import messagebox, filedialog, ttk
from tkcalendar import Calendar
from datetime import datetime, timedelta

# Bibliotecas para Geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGURAÇÃO DE ESTILO (PADRÃO V19) ---
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

class BancoDados:
    def __init__(self):
        # Usando a pasta database se existir, senão na raiz
        db_path = 'database/agenda_araraquara_v22.db'
        os.makedirs('database', exist_ok=True)
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS agendamentos 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, horario TEXT, 
            paciente TEXT, nascimento TEXT, convenio TEXT, procedimento TEXT, valor REAL, UNIQUE(data, horario))''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tabela_precos 
            (id INTEGER PRIMARY KEY, servico TEXT UNIQUE, preco REAL)''')
        
        precos = [
            ('Avaliação / Consulta', 150.0), ('Limpeza (Profilaxia)', 250.0),
            ('Restauração Resina', 280.0), ('Extração Simples', 350.0),
            ('Tratamento de Canal', 950.0), ('Clareamento Dental', 700.0)
        ]
        self.cursor.executemany("INSERT OR IGNORE INTO tabela_precos (servico, preco) VALUES (?,?)", precos)
        self.conn.commit()

    def salvar(self, dados):
        try:
            self.cursor.execute("""INSERT OR REPLACE INTO agendamentos 
                (data, horario, paciente, nascimento, convenio, procedimento, valor) VALUES (?,?,?,?,?,?,?)""", dados)
            self.conn.commit()
            return True, "Sucesso"
        except sqlite3.IntegrityError:
            return False, "O horário selecionado já possui um agendamento. Conflito evitado."
        except Exception as e:
            return False, f"Erro inesperado no banco de dados: {e}"

    def buscar_no_dia(self, data, filtro=""):
        query = "SELECT * FROM agendamentos WHERE data = ?"
        params = [data]
        if filtro:
            query += " AND paciente LIKE ?"
            params.append(f"%{filtro}%")
        self.cursor.execute(query, params)
        return {row[2]: row for row in self.cursor.fetchall()}

    def busca_global(self, nome):
        self.cursor.execute("SELECT * FROM agendamentos WHERE paciente LIKE ? ORDER BY id DESC", (f"%{nome}%",))
        return self.cursor.fetchall()

    def excluir(self, id_a):
        self.cursor.execute("DELETE FROM agendamentos WHERE id = ?", (id_a,))
        self.conn.commit()

class AgendaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = BancoDados()
        self.title("Sistema Odonto Araraquara Pro")
        self.geometry("1150x850")
        self.configure(fg_color="#f8fafc") # Fundo Slate 50 (v19)

        self.horarios_semana = [f"{h:02d}:{m:02d}" for h in range(8, 19) for m in (0, 30)]
        self.feriados = ["01/01", "21/04", "01/05", "07/09", "12/10", "02/11", "15/11", "25/12"]
        
        self.setup_ui()
        self.definir_data_inicial()
        self.atualizar_interface()

    def definir_data_inicial(self):
        agora = datetime.now()
        data_ex = agora
        if agora.weekday() == 5 and agora.hour >= 11:
            data_ex = agora + timedelta(days=2)
            while data_ex.strftime("%d/%m") in self.feriados: 
                data_ex += timedelta(days=1)
        self.lbl_data_topo.configure(text=data_ex.strftime("%d/%m/%Y"))

    def setup_ui(self):
        # --- HEADER (V19 STYLE) ---
        self.header = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=20, border_width=1, border_color="#e2e8f0")
        self.header.pack(fill="x", padx=25, pady=20)

        ctk.CTkButton(self.header, text="📅 ALTERAR DATA", command=self.abrir_calendario_v19, 
                     fg_color="#3a86ff", hover_color="#2563eb", corner_radius=10, font=("Segoe UI", 12, "bold")).pack(side="left", padx=20, pady=20)

        self.lbl_data_topo = ctk.CTkLabel(self.header, text="", font=("Segoe UI", 22, "bold"), text_color="#1e3a8a")
        self.lbl_data_topo.pack(side="left", padx=10)

        self.ent_busca_global = ctk.CTkEntry(self.header, placeholder_text="🔍 Busca Global por Nome...", width=320, corner_radius=10)
        self.ent_busca_global.pack(side="left", padx=20)
        
        ctk.CTkButton(self.header, text="BUSCAR", command=self.executar_busca_global, fg_color="#6366f1", corner_radius=10).pack(side="left")

        # NOVO: Botão Relatório PDF
        ctk.CTkButton(self.header, text="📄 RELATÓRIO PDF", command=self.gerar_pdf_dia, 
                     fg_color="#f59e0b", hover_color="#d97706", corner_radius=10, width=120).pack(side="left", padx=20)

        ctk.CTkButton(self.header, text="+ NOVO", command=lambda: self.abrir_formulario(self.lbl_data_topo.cget("text")), 
                     fg_color="#10b981", hover_color="#059669", corner_radius=10, width=100).pack(side="right", padx=25)

        # --- DASHBOARD (V19 STYLE) ---
        self.dash = ctk.CTkFrame(self, height=60, fg_color="#eff6ff", corner_radius=15)
        self.dash.pack(fill="x", padx=25, pady=(0, 15))
        
        self.lbl_stats = ctk.CTkLabel(self.dash, text="Carregando indicadores...", font=("Segoe UI", 14, "bold"), text_color="#1d4ed8")
        self.lbl_stats.pack(expand=True)

        # --- LISTA DE ATENDIMENTOS ---
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=25, pady=(0, 20))

    def gerar_pdf_dia(self):
        """Novo Recurso: Gerar PDF com a lista de atendimentos do dia utilizando ReportLab"""
        data_f = self.lbl_data_topo.cget("text")
        agendados = self.db.buscar_no_dia(data_f)
        
        if not agendados:
            messagebox.showinfo("Exportar", f"Não há agendamentos para o dia {data_f}.")
            return
            
        os.makedirs("exports", exist_ok=True)
        nome_arquivo = f"exports/Agenda_{data_f.replace('/', '-')}.pdf"
        
        doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
        elementos = []
        estilos = getSampleStyleSheet()
        
        # Título
        titulo = Paragraph(f"Relatório de Agendamentos - {data_f}", estilos['Title'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 20))
        
        # Tabela de dados
        dados_tabela = [["Horário", "Paciente", "Procedimento", "Convênio", "Valor (R$)"]]
        
        total_valor = 0
        horarios_ordenados = sorted(agendados.keys())
        for h in horarios_ordenados:
            d = agendados[h]
            # Mapeamento: d[2]=hora, d[3]=paciente, d[6]=procedimento, d[5]=convenio, d[7]=valor
            dados_tabela.append([d[2], d[3], d[6], d[5], f"R$ {d[7]:.2f}"])
            total_valor += d[7]
            
        # Linha de Totais da Tabela (Opcional, porém muito util na gestão)
        dados_tabela.append(["", "", "", "TOTAL PREVISTO:", f"R$ {total_valor:.2f}"])
        
        tabela = Table(dados_tabela, colWidths=[60, 170, 150, 80, 80])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f1f5f9")), # Fundo na linha de TOTAL
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),             # Negrito no TOTAL
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elementos.append(tabela)
        
        try:
            doc.build(elementos)
            messagebox.showinfo("Sucesso", f"Relatório PDF gerado com sucesso!\nSalvo em: {nome_arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar o PDF: {e}")

    def abrir_calendario_v19(self):
        win = ctk.CTkToplevel(self)
        win.title("Seletor de Data")
        win.geometry("450x550")
        win.attributes("-topmost", True)
        win.configure(fg_color="#ffffff")

        ctk.CTkLabel(win, text="SELECIONE UMA DATA", font=("Segoe UI", 16, "bold"), text_color="#1e3a8a").pack(pady=15)

        hoje = datetime.now()
        cal = Calendar(win, selectmode='day', locale='pt_BR', date_pattern='dd/mm/yyyy',
                       mindate=hoje, maxdate=hoje + timedelta(days=120),
                       background='#3a86ff', foreground='white', 
                       selectbackground='#1e3a8a', selectforeground='white',
                       headersbackground='#f1f5f9', headersforeground='#475569',
                       bordercolor='#e2e8f0', normalbackground='#ffffff',
                       weekendbackground='#f8fafc', weekendforeground='#ef4444')
        cal.pack(pady=10, padx=20, expand=True, fill="both")

        def aplicar():
            data_sel = cal.get_date()
            dt = datetime.strptime(data_sel, "%d/%m/%Y")
            if dt.weekday() == 6:
                messagebox.showwarning("Fechado", "A clínica não abre aos domingos.")
                return
            self.lbl_data_topo.configure(text=data_sel)
            self.atualizar_interface()
            win.destroy()

        ctk.CTkButton(win, text="CONFIRMAR DATA", font=("Segoe UI", 13, "bold"),
                     fg_color="#3a86ff", height=45, corner_radius=10, command=aplicar).pack(pady=25, padx=40, fill="x")

    def atualizar_interface(self):
        for w in self.scroll.winfo_children(): 
            w.destroy()
            
        data_f = self.lbl_data_topo.cget("text")
        dt = datetime.strptime(data_f, "%d/%m/%Y")
        
        horarios = [f"{h:02d}:{m:02d}" for h in range(8, 12) for m in (0, 30)] + ["12:00"] if dt.weekday() == 5 else self.horarios_semana
        agendados = self.db.buscar_no_dia(data_f)
        
        # Cálculo de Dashboard
        total_vagas = len(horarios)
        total_ocupado = len(agendados)
        faturamento = sum(d[7] for d in agendados.values())
        perc = (total_ocupado/total_vagas)*100 if total_vagas > 0 else 0
        
        self.lbl_stats.configure(text=f"📊 OCUPAÇÃO: {perc:.1f}%   |   AGENDADOS: {total_ocupado}/{total_vagas}   |   💰 PREVISTO: R$ {faturamento:.2f}")

        for h in horarios:
            f = ctk.CTkFrame(self.scroll, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#f1f5f9")
            f.pack(fill="x", pady=3)
            
            lbl_h = ctk.CTkLabel(f, text=h, width=90, height=45, fg_color="#eff6ff", text_color="#3a86ff", corner_radius=8, font=("Segoe UI", 14, "bold"))
            lbl_h.pack(side="left", padx=10, pady=8)

            if h in agendados:
                d = agendados[h]
                info = f"👤 {d[3].upper()}  |  🎂 {d[4]}  |  🦷 {d[6]}"
                ctk.CTkLabel(f, text=info, font=("Segoe UI", 13), text_color="#334155").pack(side="left", padx=20)
                
                btn_c = ctk.CTkFrame(f, fg_color="transparent")
                btn_c.pack(side="right", padx=15)
                
                ctk.CTkButton(btn_c, text="📝", width=35, fg_color="#fef3c7", text_color="#92400e", hover_color="#fde68a", 
                             command=lambda data=data_f, pac=d: self.abrir_formulario(data, pac)).pack(side="left", padx=5)
                
                ctk.CTkButton(btn_c, text="🗑️", width=35, fg_color="#fee2e2", text_color="#991b1b", hover_color="#fecaca", 
                             command=lambda id_a=d[0]: self.excluir_reg(id_a)).pack(side="left", padx=5)
            else:
                ctk.CTkLabel(f, text="--- Horário Disponível ---", text_color="#94a3b8", font=("Segoe UI", 12, "italic")).pack(side="left", padx=20)

    def abrir_formulario(self, data, editar_p=None):
        ocupados = [h for h in self.db.buscar_no_dia(data).keys()]
        dt = datetime.strptime(data, "%d/%m/%Y")
        horarios = [f"{h:02d}:{m:02d}" for h in range(8, 12) for m in (0, 30)] + ["12:00"] if dt.weekday() == 5 else self.horarios_semana
        
        livres = [h for h in horarios if h not in ocupados]
        if editar_p: 
            if editar_p[2] not in livres: 
                livres.append(editar_p[2])
            livres.sort()

        janela = ctk.CTkToplevel(self)
        janela.geometry("450x650")
        janela.attributes("-topmost", True)
        janela.title("Ficha do Paciente" if not editar_p else "Editar Ficha")

        ctk.CTkLabel(janela, text="NOME COMPLETO *", font=("Segoe UI", 12, "bold")).pack(pady=(20,0))
        en_nome = ctk.CTkEntry(janela, width=350, corner_radius=8)
        en_nome.pack(pady=5)
        if editar_p: 
            en_nome.insert(0, editar_p[3])

        ctk.CTkLabel(janela, text="NASCIMENTO (DD/MM/AAAA) *", font=("Segoe UI", 12, "bold")).pack(pady=(10,0))
        en_nasc = ctk.CTkEntry(janela, width=350, corner_radius=8)
        en_nasc.pack(pady=5)
        if editar_p: 
            en_nasc.insert(0, editar_p[4])

        ctk.CTkLabel(janela, text="CONVÊNIO *", font=("Segoe UI", 12, "bold")).pack(pady=(10,0))
        en_conv = ctk.CTkEntry(janela, width=350, corner_radius=8)
        en_conv.pack(pady=5)
        if editar_p: 
            en_conv.insert(0, editar_p[5])

        ctk.CTkLabel(janela, text="PROCEDIMENTO", font=("Segoe UI", 12, "bold")).pack(pady=(10,0))
        self.cursor = self.db.cursor
        self.cursor.execute("SELECT servico, preco FROM tabela_precos")
        precos = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        en_proc = ctk.CTkComboBox(janela, values=list(precos.keys()), width=350, corner_radius=8)
        en_proc.pack(pady=5)
        if editar_p: 
            en_proc.set(editar_p[6])

        ctk.CTkLabel(janela, text="HORÁRIO", font=("Segoe UI", 12, "bold")).pack(pady=(10,0))
        en_hora = ctk.CTkComboBox(janela, values=livres, width=350, corner_radius=8)
        en_hora.pack(pady=5)
        if editar_p: 
            en_hora.set(editar_p[2])

        def salvar():
            nome_val = en_nome.get().strip()
            nasc_val = en_nasc.get().strip()
            conv_val = en_conv.get().strip()
            proc_val = en_proc.get()
            hora_val = en_hora.get()
            
            # VALIDAÇÃO DE CAMPOS VAZIOS
            if not nome_val or not nasc_val or not conv_val:
                messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha NOME, NASCIMENTO e CONVÊNIO.")
                return

            sucesso, mensagem = self.db.salvar((data, hora_val, nome_val.upper(), nasc_val, conv_val.upper(), proc_val, precos[proc_val]))
            
            if sucesso:
                janela.destroy()
                self.atualizar_interface()
            else: 
                messagebox.showerror("Erro ao Salvar", mensagem)

        ctk.CTkButton(janela, text="CONFIRMAR AGENDAMENTO", fg_color="#10b981", hover_color="#059669", 
                     height=45, corner_radius=10, font=("Segoe UI", 13, "bold"), command=salvar).pack(pady=35)

    def executar_busca_global(self):
        nome = self.ent_busca_global.get()
        if not nome: 
            return
            
        res = self.db.busca_global(nome)
        if not res: 
            messagebox.showinfo("Busca", "Nenhum paciente encontrado.")
            return
        
        win = ctk.CTkToplevel(self)
        win.title(f"Histórico: {nome}")
        win.geometry("900x500")
        win.attributes("-topmost", True)
        
        cols = ('ID', 'Data', 'Hora', 'Paciente', 'Procedimento', 'Valor')
        tree = ttk.Treeview(win, columns=cols, show='headings')
        for c in cols: 
            tree.heading(c, text=c)
            
        for r in res: 
            tree.insert('', 'end', values=(r[0], r[1], r[2], r[3], r[6], f"R$ {r[7]:.2f}"))
        tree.pack(expand=True, fill='both', padx=20, pady=20)

        def acao(tipo):
            sel = tree.selection()
            if not sel: 
                messagebox.showwarning("Aviso", "Selecione um registro primeiro.")
                return
                
            item = tree.item(sel[0])['values']
            if tipo == "EDITAR":
                win.destroy()
                self.lbl_data_topo.configure(text=item[1])
                self.atualizar_interface()
                dados_completos = next(x for x in res if x[0] == item[0])
                self.abrir_formulario(item[1], dados_completos)
                
            elif tipo == "EXCLUIR":
                if messagebox.askyesno("Confirmar", "Eliminar registro de forma definitiva?"):
                    self.db.excluir(item[0])
                    tree.delete(sel[0])
                    self.atualizar_interface()

        f_btn = ctk.CTkFrame(win, fg_color="transparent")
        f_btn.pack(pady=10)
        ctk.CTkButton(f_btn, text="IR PARA DATA / EDITAR", fg_color="#f39c12", hover_color="#d68910", command=lambda: acao("EDITAR")).pack(side="left", padx=10)
        ctk.CTkButton(f_btn, text="EXCLUIR", fg_color="#f87171", hover_color="#dc2626", command=lambda: acao("EXCLUIR")).pack(side="left", padx=10)

    def excluir_reg(self, id_a):
        if messagebox.askyesno("Confirmar", "Deseja excluir este agendamento?"): 
            self.db.excluir(id_a)
            self.atualizar_interface()

if __name__ == "__main__":
    app = AgendaApp()
    app.mainloop()
