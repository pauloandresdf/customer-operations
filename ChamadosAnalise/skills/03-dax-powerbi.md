# Skill 03 — Engenharia de Métricas DAX via MCP

## Fluxo de Trabalho com MCP no Antigravity
1. Conectar ao modelo aberto usando `connection_operations`.
2. Validar a sintaxe e o resultado do DAX com `dax_query_operations` (usando `EVALUATE`) antes de criar fisicamente a medida.
3. Criar a medida com `measure_operations` (Operation=Create).

## REGRA CRÍTICA — Nomes Padronizados das Medidas
Sempre referenciar as medidas rigorosamente por estes nomes:
- `[Total Chamados]` — NUNCA "Contagem de Chamados"
- `[Total Chamados Finalizados]`
- `[Total Chamados Abertos]`
- `[Taxa de Eficiência CEX]`
- `[Índice de Excesso de Veículo]`
- `[Índice de Avaria]`

## REGRA CRÍTICA — ADDCOLUMNS vs SUMMARIZE
Para criar tabelas calculadas ou rankings de analistas que utilizam medidas dinâmicas, **SEMPRE** usar `ADDCOLUMNS(VALUES())`. NUNCA aninhar medidas diretamente dentro do `SUMMARIZE`.

## Medidas DAX Homologadas para o Projeto

### Grupo 1: Volumetria de Atendimento
```dax
Total Chamados = COUNTROWS('RELATORIO CHAMADOS')

Total Chamados Abertos = 
CALCULATE(
    [Total Chamados],
    'RELATORIO CHAMADOS'[Situação Chamado] = "Aberto"
)

Total Chamados Finalizados = 
CALCULATE(
    [Total Chamados],
    'RELATORIO CHAMADOS'[Situação Chamado] = "Finalizado"
)


Taxa de Eficiência CEX = DIVIDE([Total Chamados Finalizados], [Total Chamados], 0)

Índice de Excesso de Veículo = 
DIVIDE(
    CALCULATE([Total Chamados], 'RELATORIO CHAMADOS'[Motivo] = "10 - EXCESSO DE VEICULO NO CLIENTE"),
    [Total Chamados],
    0
)

Índice de Avaria = 
DIVIDE(
    CALCULATE([Total Chamados], 'RELATORIO CHAMADOS'[Motivo] = "23 - MAU ESTADO DA MERCADORIA"),
    [Total Chamados],
    0
)

EVALUATE
TOPN(
    5,
    ADDCOLUMNS(
        VALUES('BASE CLIENTES MULTI'[Analista CEX]),
        "_Chamados", [Total Chamados]
    ),
    [_Chamados], DESC
)

