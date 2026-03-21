# OdontoFlow Pro

Sistema premium de gestão clínica odontológica, desenvolvido inteiramente em Python. Utiliza uma interface gráfica moderna (CustomTkinter v19) acoplada a um banco de dados relacional robusto (SQLite3), focado na produtividade, prevenção de erros e relatórios dinâmicos empresariais.

## 🚀 Principais Funcionalidades

- **Agendamento Inteligente:** Prevenção sistêmica de duplicidade (Unique Constraints SQL). Bloqueio automático de marcações em dias não úteis (ex: Domingos).
- **Validação de Formulários em Tempo Real:** Checagem rigorosa de campos vitais antes da persistência de dados.
- **Geração de PDF Diário:** Motor `ReportLab` embutido para criar fichas elegantes em formato A4, com cálculos instantâneos de todo o faturamento previsto do dia.
- **UI/UX Moderna:** Construído com `CustomTkinter` no estilo "v19", garantindo estética limpa, cores harmoniosas (Slate/Blue) e zero gargalos de renderização (Sandbox testado).
- **Gestão Ágil:** Dashboard analítico superior com os quadros: Ocupação, Quantidade de Cadastros e Previsão de Entradas Financeiras.

## 🛠️ Stack Tecnológica

- **Front-End:** Python 3 + CustomTkinter + tkcalendar
- **Back-End:** Python Genérico + Estrutura Modular
- **Banco de Dados:** SQLite3 nativo
- **Geração de Arquivos:** ReportLab (Exportações estruturadas)

## 🤖 Roadmap Futuro

- Expansão do Front-End e Back-End em Microsserviços
- **Integração com Inteligência Artificial (IA)**: Ferramentas de suporte preditivas ao diagnóstico e gestão automática de comunicação com o paciente (Chatbot integrado / Lembretes).

## 💻 Para Executar o Projeto

Certifique-se de estar com o ambiente Python ativado e instalar as bibliotecas necessárias:

```cmd
pip install customtkinter tkcalendar reportlab
python main.py
```

*OdontoFlow Pro - Tecnologias Inteligentes para Odontologia Premium.*
