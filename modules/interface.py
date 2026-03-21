"""
Interface minimalista "OdontoFlow Pro".
S.O.L.I.D. Pattern para UI com validações em tempo real e formulários acoplados.
"""
import customtkinter as ctk
import tkinter.messagebox as messagebox
from datetime import datetime, timedelta
import re
from modules import db_manager, reports_engine

class AppointmentForm(ctk.CTkToplevel):
    def __init__(self, parent, db, current_date, appt=None, callback=None):
        super().__init__(parent)
        self.db = db
        self.current_date = current_date
        self.appt = appt
        self.callback = callback
        
        self.title("Ficha do Paciente" if appt else "Novo Agendamento")
        self.geometry("450x700")
        self.grab_set()
        self.attributes('-topmost', True)
        
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # NOME COMPLETO - Bloqueia Especiais/Números e Força Maiúsculo
        ctk.CTkLabel(self.scroll, text="NOME COMPLETO:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.v_name = ctk.StringVar(value=appt[1] if appt else "")
        def to_up(*args):
            v = self.v_name.get().upper()
            # Regex permitindo apenas Letras Latinas Espaços
            v = re.sub(r'[^A-ZÀ-Ÿ\s]', '', v)
            if self.v_name.get() != v:
                self.v_name.set(v)
        self.v_name.trace_add("write", to_up)
        self.e_name = ctk.CTkEntry(self.scroll, textvariable=self.v_name, width=300)
        self.e_name.pack(fill="x")
        
        # DATA DE NASCIMENTO - Máscara Dinâmica
        ctk.CTkLabel(self.scroll, text="DATA DE NASCIMENTO:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.v_bd = ctk.StringVar(value=appt[2] if appt else "")
        def to_mask(*args):
            raw = self.v_bd.get().replace("/", "")
            if len(raw) > 8: raw = raw[:8]
            out = ""
            for i, c in enumerate(raw):
                if c.isdigit():
                    if i in (2, 4): out += "/"
                    out += c
            if self.v_bd.get() != out: self.v_bd.set(out)
        self.v_bd.trace_add("write", to_mask)
        self.e_bd = ctk.CTkEntry(self.scroll, textvariable=self.v_bd, width=300)
        self.e_bd.pack(fill="x")

        # CONVÊNIO
        ctk.CTkLabel(self.scroll, text="CONVÊNIO:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        self.e_ins = ctk.CTkEntry(self.scroll, width=300)
        self.e_ins.insert(0, appt[3] if appt else "")
        self.e_ins.pack(fill="x")
        
        # PROCEDIMENTO - ComboBox
        ctk.CTkLabel(self.scroll, text="PROCEDIMENTO:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        procs = ["Consulta de Rotina", "Avaliação Inicial", "Limpeza (Profilaxia)", "Restauração", "Extração", "Clareamento Clínico", "Manutenção Ortodôntica"]
        self.cb_proc = ctk.CTkComboBox(self.scroll, values=procs, width=300)
        self.cb_proc.set(appt[4] if appt else procs[0])
        self.cb_proc.pack(fill="x", pady=(0, 10))

        # VALOR BASE MANTIDO PARA OPERAÇÕES
        ctk.CTkLabel(self.scroll, text="VALOR REFERÊNCIA (R$):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5,0))
        self.e_val = ctk.CTkEntry(self.scroll, width=300)
        self.e_val.insert(0, str(appt[5]) if appt else "0.00")
        self.e_val.pack(fill="x")
        
        # HORÁRIO - ComboBox
        ctk.CTkLabel(self.scroll, text="HORÁRIO:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10,0))
        times = [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(8, 19) for m in (0, 30)]
        self.cb_time = ctk.CTkComboBox(self.scroll, values=times, width=300)
        self.cb_time.set(appt[6].split(' ')[1] if appt and ' ' in appt[6] else "09:00")
        self.cb_time.pack(fill="x", pady=(0, 10))
        
        # CONFIRMAR
        self.btn_confirm = ctk.CTkButton(self.scroll, text="CONFIRMAR", fg_color="#28a745", hover_color="#218838", font=ctk.CTkFont(weight="bold", size=15), height=45, command=self.save)
        self.btn_confirm.pack(pady=30)
        
        # Botão Extra para Deletar caso seja Edit
        if appt:
            ctk.CTkButton(self.scroll, text="Excluir", fg_color="#A83232", hover_color="#8B0000", command=self.delete_me).pack(pady=0)

    def delete_me(self):
        if messagebox.askyesno("Confirmar Remoção", "Confirma a exclusão permanentede deste registro?"):
            if self.db.delete_appointment(self.appt[0]):
                self.destroy()
                if self.callback: self.callback()
            else:
                messagebox.showerror("Bloqueio", "Não foi possível remover o registro do banco.")

    def save(self):
        n = self.v_name.get().strip()
        b = self.v_bd.get().strip()
        i = self.e_ins.get().strip()
        p = self.cb_proc.get().strip()
        v = self.e_val.get().strip()
        t = self.cb_time.get().strip()
        
        if not all([n, b, i, p, v, t]):
            return messagebox.showerror("Campos", "Por favor, preencha todos os campos corretamente.")
            
        try:
            val_f = float(v)
        except:
            return messagebox.showerror("Tipagem", "A estrutura de 'Valor (R$)' deve ser numérica plana contendo somente dígito ou ponto (Ex: 150.00).")
            
        # >> REGRA DE NEGÓCIOS - VALIDAÇÕES RÍGIDAS (DIRETAS NO BOTÃO) <<
        
        # Impede Retroativos
        if self.current_date < datetime.now().date():
            return messagebox.showerror("Bloqueio Temporal", "Não é permitido confirmar novos agendamentos para datas retroativas do passado.")
            
        # Bloqueio de Domingos
        if self.current_date.weekday() == 6:
            return messagebox.showerror("Clínica Fechada", "Domingos não são homologados para a base de agendamentos ativa nas configurações atuais.")
            
        # Pós validações, constrói string e salva.
        dt_time = f"{self.current_date.strftime('%Y-%m-%d')} {t}"
        local_id = self.appt[0] if self.appt else None
        
        success = False
        if local_id:
            success = self.db.update_appointment(local_id, n, b, i, p, val_f, dt_time)
        else:
            success = self.db.add_appointment(n, b, i, p, val_f, dt_time)
            
        if success:
            self.destroy()
            if self.callback: self.callback()
        else:
            messagebox.showerror("Integridade", "Erro severo ao registrar os dados operacionais no núcleo SQL.")


class OdontoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = db_manager.init_db()
        self._cfg()
        self.calendar_cursor = self._smart_date()
        self._construct()
        self.refresh()

    def _cfg(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.title("OdontoFlow Pro v1.0")
        self.geometry("1150x750")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _smart_date(self):
        """Pulo Inteligente - Finais de semana mortos não travam a UI na data corrente"""
        n = datetime.now()
        if n.weekday() == 5 and n.hour >= 11:
            n += timedelta(days=2)
        if n.weekday() == 6:
            n += timedelta(days=1)
        return n.date()

    def _construct(self):
        nav = ctk.CTkFrame(self, width=220, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsew")
        nav.grid_rowconfigure(5, weight=1)
        
        ctk.CTkLabel(nav, text="OdontoFlow\nPRO", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))
        
        ctk.CTkButton(nav, text="Nova Ficha", command=self.open_new).grid(row=1, column=0, padx=20, pady=10)
        ctk.CTkButton(nav, text="Pesquisar (Geral)", command=self.open_search).grid(row=2, column=0, padx=20, pady=10)
        ctk.CTkButton(nav, text="Gerar PDF Relatório do Dia", command=self.print_pdf).grid(row=3, column=0, padx=20, pady=10)
        
        self.hud_date = ctk.CTkLabel(nav, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.hud_date.grid(row=4, column=0, padx=20, pady=(30, 0))
        
        ctk.CTkButton(nav, text="<< Dia Anterior", command=lambda: self.shift_d(-1)).grid(row=5, column=0, padx=20, pady=5, sticky="s")
        ctk.CTkButton(nav, text="Dia Incomum >>", command=lambda: self.shift_d(1)).grid(row=6, column=0, padx=20, pady=30)
        
        core = ctk.CTkFrame(self, corner_radius=10)
        core.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        core.grid_rowconfigure(1, weight=1)
        core.grid_columnconfigure(0, weight=1)
        
        card = ctk.CTkFrame(core, height=90)
        card.grid(row=0, column=0, padx=20, pady=20, sticky="new")
        card.grid_columnconfigure((0,1), weight=1)
        
        self.h_occ = ctk.CTkLabel(card, text="Pacientes: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.h_occ.grid(row=0, column=0, padx=20, pady=25)
        
        self.h_bil = ctk.CTkLabel(card, text="Referência (R$): 0.00", font=ctk.CTkFont(size=14, weight="bold"))
        self.h_bil.grid(row=0, column=1, padx=20, pady=25)
        
        self.h_ping = ctk.CTkLabel(card, text="DB: Conectando...", font=ctk.CTkFont(size=13, weight="bold"))
        self.h_ping.grid(row=0, column=2, padx=20, pady=25)
        
        self.gr = ctk.CTkScrollableFrame(core, label_text="Tabela Diária")
        self.gr.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def shift_d(self, x):
        self.calendar_cursor += timedelta(days=x)
        self.refresh()

    def refresh(self):
        try:
            d = self.calendar_cursor.strftime('%Y-%m-%d')
            self.hud_date.configure(text=f"Filtrado: {self.calendar_cursor.strftime('%d/%m/%Y')}")
            
            s = self.db.get_dashboard_stats(d)
            self.h_occ.configure(text=f"Pacientes: {s['daily_occupancy']}")
            self.h_bil.configure(text=f"Agregado Inicial (R$): {s['daily_billing']:.2f}")
            
            ok = self.db.ping()
            self.h_ping.configure(text=f"Status: {'SISTEMA OPERACIONAL' if ok else 'OFFLINE'}", text_color="#32CD32" if ok else "#FF0000")
            
            for c in self.gr.winfo_children(): c.destroy()
            for a in self.db.get_appointments_by_date(d):
                r = ctk.CTkFrame(self.gr, fg_color=("gray80", "gray16"))
                r.pack(fill="x", padx=5, pady=4)
                
                t = a[6].split(' ')[1] if ' ' in a[6] else a[6]
                ctk.CTkLabel(r, text=f"{t} • {a[1]} • {a[4]}", anchor="w", font=ctk.CTkFont(size=14)).pack(side="left", padx=15, pady=12, fill="x", expand=True)
                
                ctk.CTkButton(r, text="Editar 📝", width=85, command=lambda x=a: self.open_new(x)).pack(side="right", padx=5)
                ctk.CTkButton(r, text="Guia PDF", width=65, fg_color="#1F6B45", hover_color="#144C30", command=lambda x=a: self.gen_rec(x)).pack(side="right", padx=5)
        except Exception as e:
            messagebox.showerror("Fatal", f"Crash na camada UI: {e}")

    def open_new(self, a=None):
        AppointmentForm(self, self.db, self.calendar_cursor, a, self.refresh)

    def open_search(self):
        w = ctk.CTkToplevel(self)
        w.title("Central de Busca")
        w.geometry("750x500")
        w.grab_set()
        w.attributes('-topmost', True)
        
        t = ctk.CTkFrame(w)
        t.pack(fill="x", padx=10, pady=10)
        e = ctk.CTkEntry(t, width=500, placeholder_text="Termo...")
        e.pack(side="left", padx=10)
        
        s = ctk.CTkScrollableFrame(w)
        s.pack(fill="both", expand=True, padx=10, pady=10)
        
        def run():
            for c in s.winfo_children(): c.destroy()
            for a in self.db.search_appointments(e.get()):
                r = ctk.CTkFrame(s)
                r.pack(fill="x", pady=4)
                ctk.CTkLabel(r, text=f"{a[6]} | {a[1]} | {a[4]}", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
                ctk.CTkButton(r, text="Editar 📝", width=100, command=lambda x=a: goto(x, w)).pack(side="right", padx=10, pady=5)
                
        def goto(a, win):
            win.destroy()
            self.calendar_cursor = datetime.strptime(a[6].split(' ')[0], "%Y-%m-%d").date()
            self.refresh()
            self.open_new(a)

        ctk.CTkButton(t, text="PESQUISAR", command=run).pack(side="left")

    def print_pdf(self):
        d = self.calendar_cursor.strftime('%Y-%m-%d')
        ds = self.db.get_appointments_by_date(d)
        if not ds: return messagebox.showwarning("Vazio", "Grade vazia para exportação.")
        p, s = reports_engine.generate_daily_report(d, ds, self.db.get_dashboard_stats(d))
        if s: messagebox.showinfo("PDF Gerado Exclusivo", f"PDF emitido em:\n{p}")

    def gen_rec(self, u):
        p, s = reports_engine.generate_patient_receipt(u)
        if s: messagebox.showinfo("Guia Emitida Limpa", f"Paciente processado: {p}")

def start_ui():
    app = OdontoApp()
    app.mainloop()
