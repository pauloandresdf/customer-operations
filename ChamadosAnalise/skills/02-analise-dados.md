Regra Crítica de Modelagem: Direção do Filtro
O relacionamento no modelo deve ser feito de BASE CLIENTES MULTI[Destino ID.1] (1) para RELATORIO CHAMADOS[Código Integração Cliente] (N). A direção do filtro deve ser estritamente Única (Dimensão filtra Fato) para preservar a performance do motor xVelocity.


---

### 📂 2. Conteúdo para `docs/02-analise-dados.md`

```md
# Skill 02 — Análise de Dados e Indicadores de Logística/CEX

## KPIs Essenciais do Projeto CEX Multi

| KPI | Fórmula Conceitual | Meta / Benchmark Operational |
|-----|--------------------|------------------------------|
| **Total Chamados** | Contagem total de ocorrências abertas | Monitorar picos de gargalos na malha |
| **Taxa de Eficiência CEX** | Chamados Finalizados / Total Chamados | Mínimo de **85%** de resolução de carteira |
| **Backlog Ativo (Abertos)**| Contagem de chamados com status "Aberto" | Menor e melhor (indica gargalo de atendimento) |
| **Volumetria Excesso Veículo**| Total de chamados pelo Motivo 10 | Mede problemas de agendamento/janela no cliente |
| **Índice de Avaria/Mau Estado**| Total de chamados pelo Motivo 23 | Mede sinistros e problemas com a transportadora |

## Volumetria de Ofensores (Pareto CEX)

Total Chamados → Identificar Maiores Clientes → Identificar Principais Motivos (10, 23 ou 01)
└─ Cruzar com Analista CEX Responsável por destravar a operação


## Segmentações Críticas para o Negócio
- **Por Região:** Nordeste (NE), Centro-Norte (CN), Centro-Oeste, etc. (Foco em identificar eficiência regional).
- **Por Analista CEX:** Marcela Roskosz, Cynthia Brito, Fernanda Soares, etc. (Avaliação de balanceamento de carga).
- **Por Visão de Situação:** Aberto, Finalizado, Rejeitado.

## Perguntas de Negócio para Destravar com o Dashboard
1. Qual região (ex: NE ou CN) apresenta maior concentração de mercadorias em mau estado?
2. O volume de chamados de "Excesso de Veículo" está concentrado em quais clientes específicos?
3. Como está a distribuição de chamados por coordenador e analista CEX? Há sobrecarga na carteira de algum profissional?
4. Quais ocorrências estão abertas há mais tempo sem resolução operacional (Gargalo de SLA)?