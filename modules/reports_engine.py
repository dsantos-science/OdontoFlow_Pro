"""
Motor de Geração PDF (Reports Engine).
Usa ReportLab e encapsula geração em try/except robustos prevenindo travamento caso arquivo aberto.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

class PDFEngine:
    def __init__(self, export_dir="exports"):
        self.export_dir = export_dir
        try:
            os.makedirs(self.export_dir, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Criação de diretório de relatórios falhou: {e}")

    def _draw_header(self, c, title):
        """Cabecalho corporativo isolado."""
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(A4[0] / 2.0, A4[1] - 2 * cm, "Agendamento Clínico Premium - Relatórios")
        c.setFont("Helvetica", 14)
        c.drawCentredString(A4[0] / 2.0, A4[1] - 3 * cm, title)
        c.line(2 * cm, A4[1] - 3.5 * cm, A4[0] - 2 * cm, A4[1] - 3.5 * cm)

    def generate_daily_report(self, date_str, appointments, stats):
        try:
            filename = os.path.join(self.export_dir, f'relatorio_diario_{date_str}.pdf')
            c = canvas.Canvas(filename, pagesize=A4)
            
            self._draw_header(c, f"Relatório de Atendimentos: {date_str}")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2 * cm, A4[1] - 4.5 * cm, f"Ocupação Geral: {stats['daily_occupancy']} paciente(s)")
            c.drawString(2 * cm, A4[1] - 5.5 * cm, f"Rendimentos Diários Realizados: R$ {stats['daily_billing']:.2f}")
            
            y = A4[1] - 7 * cm
            c.setFont("Helvetica-Bold", 10)
            headers = [("Hora", 2), ("Paciente", 4.5), ("Procedimento", 11), ("Plano", 15), ("Ref(R$)", 18)]
            for title, pos in headers:
                c.drawString(pos * cm, y, title)
            
            c.line(2 * cm, y - 0.2 * cm, A4[0] - 2 * cm, y - 0.2 * cm)
            y -= 0.8 * cm
            
            c.setFont("Helvetica", 10)
            for appt in appointments:
                # appt: id, name, birth, ins, proc, val, datetime, created_at
                time_f = appt[6].split(' ')[1] if ' ' in appt[6] else appt[6]
                c.drawString(2 * cm, y, time_f)
                c.drawString(4.5 * cm, y, str(appt[1])[:25])
                c.drawString(11 * cm, y, str(appt[4])[:20])
                c.drawString(15 * cm, y, str(appt[3])[:15])
                c.drawString(18 * cm, y, f"{float(appt[5]):.2f}")
                y -= 0.6 * cm
            
            c.save()
            return filename, True
        except Exception as e:
            print(f"[ERROR] Arquivo ocupado ou falha de escrita PDF (Diário): {e}")
            return "", False

    def generate_patient_receipt(self, appointment):
        try:
            safe = str(appointment[1]).replace(' ', '_').lower()
            ds = str(appointment[6]).replace(':', '')[:10]
            filename = os.path.join(self.export_dir, f'extrato_paciente_{safe}_{ds}.pdf')
            
            c = canvas.Canvas(filename, pagesize=A4)
            self._draw_header(c, "Recibo e Comprovante de Atendimento Oficial")
            
            c.setFont("Helvetica", 12)
            y = A4[1] - 5 * cm
            
            lines = [
                f"Títular / Paciente: {appointment[1]}",
                f"Data de Nascimento: {appointment[2]}",
                f"Modalidade (Convênio): {appointment[3]}",
                f"Ato Clínico: {appointment[4]}",
                f"Realizado Em: {appointment[6]}",
                f"Custo Oficial: R$ {float(appointment[5]):.2f}"
            ]
            
            for index, line in enumerate(lines):
                c.drawString(2 * cm, y - (index * cm), line)
            
            c.save()
            return filename, True
        except Exception as e:
            print(f"[ERROR] Impedimento na compilação do Recibo: {e}")
            return "", False

engine = PDFEngine()

def generate_daily_report(date_str, appointments, stats):
    return engine.generate_daily_report(date_str, appointments, stats)

def generate_patient_receipt(appointment):
    return engine.generate_patient_receipt(appointment)
