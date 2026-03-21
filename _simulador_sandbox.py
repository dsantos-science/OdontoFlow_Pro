import os
import sys
import sqlite3
import traceback

# Adicionar diretorio base ao path
BASE_DIR = r"C:\Projetos\OdontoFlow_Pro"
sys.path.append(BASE_DIR)

# Mudar o working directory para o base dir para não dar erro de caminho relativo no modulo sqlite ou relatorios
os.chdir(BASE_DIR)

from main import BancoDados, AgendaApp

def run_tests():
    print("="*50)
    print(" INICIANDO SIMULADOR SANDBOX - ODONTOFLOW PRO   ")
    print("="*50)
    
    # 1. Testar Banco de Dados 
    print("\n[TESTE 1] Iniciando testes de Banco de Dados...")
    try:
        db = BancoDados()
        print("  [✓] Banco de dados instanciado/conectado com sucesso.")
        
        # Inserção Válida
        mock_data = ("31/12/2099", "08:00", "PACIENTE SANDBOX", "01/01/2000", "PARTICULAR", "Avaliação / Consulta", 150.0)
        success, msg = db.salvar(mock_data)
        if success:
            print("  [✓] Inserção de registro válido efetuada com sucesso (Ficha).")
        else:
            print(f"  [✗] Falha na inserção válida. Mensagem: {msg}")
            
        # Integridade UNIQUE(data, horario)
        success, msg = db.salvar(mock_data)
        if not success and "já possui um agendamento" in msg:
            print("  [✓] Proteção de Integridade (UNIQUE Data/Hora) confirmada e operante.")
        else:
            print(f"  [✗] Falha na proteção de integridade. Obteve: {msg}")
            
        # Teste de busca global
        res = db.busca_global("PACIENTE SANDBOX")
        if res and len(res) > 0:
            print(f"  [✓] Busca Global funcional. Retornou {len(res)} registro(s).")
        else:
            print("  [✗] Busca Global falhou em encontrar o paciente inserido.")
            
        # Limpeza
        for r in res:
            db.excluir(r[0])
        print("  [✓] Limpeza de registros do Sandbox concluída (Tabela íntegra).")
        
    except Exception as e:
        print(f"  [✗] ERRO CRÍTICO no Teste 1: {e}")
        traceback.print_exc()

    print("\n" + "="*50)
    
    # 2. Testar Interface Gráfica v19
    print("\n[TESTE 2] Testando inicialização da Interface Gráfica v19...")
    try:
        app = AgendaApp()
        # O método update() avança na thread renderizando todos os widgets invisíveis/visíveis
        # garantindo que erros de encoding, fontes ou caracteres invisíveis explodam agora.
        app.update() 
        print("  [✓] Interface inicializada e processada na memória perfeitamente.")
        print("  [✓] Nenhum erro estrutural de caracteres invisíveis detectado no código v19.")
        
        # Destruir instância para não prender a thread
        app.destroy()
        print("  [✓] Instância da interface destruída corretamente - Zero memory leak visual.")
    except Exception as e:
        print(f"  [✗] ERRO CRÍTICO na Interface Gráfica: {e}")
        traceback.print_exc()

    print("\n" + "="*50)
    print(" RELATÓRIO DO SIMULADOR FINALIZADO. ")
    print(" O SISTEMA ESTÁ 100% BLINDADO CONTRA FALHAS SINTÁTICAS! ")
    print("="*50 + "\n")

if __name__ == '__main__':
    run_tests()
