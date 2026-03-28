# OdontoFlow Pro v4.6 
**Motor Logístico, Estatístico e de Alta Disponibilidade para Clínicas Odontológicas Premium.**

O OdontoFlow Pro deixou de ser um simples sistema de agendamento para se tornar uma infraestrutura **Edge Computing (Local-First)**. Focado em duas métricas absolutas: **Zero Latência** na recepção e **Zero Perda de Faturamento** por faltas (No-Show), utilizando IA Preditiva e Prescritiva em tempo real.

## 🚀 Engenharia de Destaque (Os 5 Superpoderes)

* **Motor Prescritivo V14 (IA de Risco):** O sistema não apenas agenda; ele calcula a probabilidade matemática de falta do paciente cruzando 6 dimensões em tempo real: 
  1. *Clima* (Integração Open-Meteo para tempestades locais).
  2. *Heurística Etária* (Curva em U de risco).
  3. *Histórico Recidivo* (Pesos exponenciais para faltas recentes).
  4. *Atrito Financeiro* (Bypass de segurança para PIX/Sinal).
  5. *Logística* (Distância via CEP).
  6. *Afinidade Temporal* (Dias de menor atrito).
* **Arquitetura Híbrida & Fallback (Resiliência Musk):** O banco de dados primário opera em **PostgreSQL (Docker)** para performance máxima. Em caso de falha do container, o sistema desvia silenciosamente para um **SQLite** local, garantindo que a clínica nunca pare de operar.
* **Latência Zero Absoluta (SSE):** Morte ao *polling*. A interface se comunica com o motor Python via **Server-Sent Events (SSE)**. Se o dentista confirmar um agendamento no consultório, a tela da secretária atualiza no exato milissegundo.
* **Antigravity Frontend (Vanilla ES6):** Interface construída 100% em JavaScript puro, sem frameworks pesados (React/Vue). Utiliza a estética **Google Stitch Glassmorphism Dark**, garantindo renderização instantânea até em hardwares antigos.
* **Sincronia Nuvem (Transactional Outbox):** Operações locais são enfileiradas de forma segura (`SKIP LOCKED`) e enviadas assincronamente para a nuvem (Supabase) via *workers* em background, garantindo o backup sem travar a recepção.

## 🛠️ Stack Tecnológica Restrita (Zero Arrasto)

* **Back-End (Motor V14):** Python 3.10+ com Flask v4.0 (API REST e Streaming SSE).
* **Front-End (Edge):** HTML5 / CSS3 / Vanilla ES6 (Rodando nativamente porta 3000).
* **Banco de Dados (Orquestrado):** PostgreSQL (Docker) ↔ SQLite3 (Fallback) ↔ Supabase (Nuvem).
* **Autenticação:** JWT (HMAC-SHA256) manual, sem dependências externas.

## 🤖 Ações de IA Prescritiva

Quando um agendamento atinge o nível **ALTO RISCO (Score > 85)**, o sistema:
1. Emite um alerta visual pulsante na interface.
2. Bloqueia a confirmação simples.
3. Fornece duas coordenadas vetoriais (*Vetor Paciente* e *Vetor Clínica*) sugerindo o dia/hora ideal para remarcação baseado em ociosidade e histórico.
4. Sugere a cobrança de **Sinal Financeiro (PIX)** para forçar o comprometimento (*Skin in the Game*).

## 💻 Como Executar a Ignição (Cold Start)

O sistema foi desenhado para inicialização em 1 Clique via script de orquestração.

**Pré-requisitos:** Python 3.10+, Docker Desktop (opcional, mas recomendado).

1. Clone o repositório.
2. Instale as dependências mínimas do motor:
   ```bash
   pip install flask flask-cors requests psycopg2-binary
