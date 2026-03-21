"""
Gerenciador de Banco de Dados - Padrão Singleton Blindado
Aplica threading.Lock para garantir concorrência segura na UI.
Proteção integral com blocos genéricos de try/except.
"""
import sqlite3
import os
from datetime import datetime
import threading

class DBManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path="database/clinic_data.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DBManager, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.initialize_db()
        return cls._instance

    def _connect(self):
        """Conexão centralizada permissiva com múltiplas threads."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def initialize_db(self):
        """Prepara o arquivo do banco de dados e a tabela principal de agendamentos."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS appointments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        birth_date TEXT NOT NULL,
                        insurance TEXT NOT NULL,
                        procedure TEXT NOT NULL,
                        value REAL NOT NULL,
                        appointment_datetime TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"[FATAL] Falha de leitura/escrita inicializadora (DB): {e}")

    def add_appointment(self, name, birth_date, insurance, procedure, value, appointment_datetime):
        """Adiciona novo registro aplicando transformação auto-upper para o nome."""
        try:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO appointments (name, birth_date, insurance, procedure, value, appointment_datetime, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (str(name).upper().strip(), birth_date, insurance, procedure, float(value), appointment_datetime, created_at))
                conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Não foi possível persistir agendamento: {e}")
            return False

    def update_appointment(self, appt_id, name, birth_date, insurance, procedure, value, appointment_datetime):
        """Atualiza a integridade dos dados de um cliente já registrado."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE appointments
                    SET name=?, birth_date=?, insurance=?, procedure=?, value=?, appointment_datetime=?
                    WHERE id=?
                ''', (str(name).upper().strip(), birth_date, insurance, procedure, float(value), appointment_datetime, appt_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Impedimento na atualização de ficha: {e}")
            return False

    def delete_appointment(self, appt_id):
        """Expurga permanentemente o agendamento através do ID."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM appointments WHERE id=?', (appt_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Remoção negada ou falha SQL: {e}")
            return False

    def get_appointments_by_date(self, date_str):
        """Retorna uma lista serializada do dia especificado (YYYY-MM-DD)."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM appointments 
                    WHERE appointment_datetime LIKE ? 
                    ORDER BY appointment_datetime ASC
                ''', (f'{date_str}%',))
                return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Operação de busca diária rejeitada: {e}")
            return []

    def search_appointments(self, query):
        """Motor de busca global aplicando wildcard."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM appointments 
                    WHERE name LIKE ? OR procedure LIKE ? OR insurance LIKE ?
                    ORDER BY appointment_datetime DESC
                ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
                return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Falha generalizada no buscador: {e}")
            return []

    def get_dashboard_stats(self, date_str):
        """Processa estatísticas base matemáticas para montagem do Dashboard UI."""
        try:
            appointments = self.get_appointments_by_date(date_str)
            occupancy = len(appointments)
            billing = sum(float(row[5]) for row in appointments)
            
            month_str = date_str[:7]
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM appointments WHERE appointment_datetime LIKE ?', (f'{month_str}%',))
                month_billing = sum(float(row[0]) for row in cursor.fetchall())
                
            return {
                'daily_occupancy': occupancy,
                'daily_billing': billing,
                'monthly_billing': month_billing
            }
        except Exception as e:
            print(f"[ERROR] Interrupção no cálculo estatístico: {e}")
            return {'daily_occupancy': 0, 'daily_billing': 0, 'monthly_billing': 0}

    def ping(self):
        """Teste de conectividade de infraestrutura (Ping DB)."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except Exception:
            return False

# Ponto de entrada padrão Singleton
def init_db(db_path="database/clinic_data.db"):
    return DBManager(db_path)
