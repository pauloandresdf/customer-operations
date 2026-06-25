# Skill 01 — Limpeza de Dados e Modelagem CEX (Power Query / M Language)

## Quando usar esta skill
Sempre que precisar importar, higienizar ou transformar os dados operacionais de atendimento e cadastro de clientes no Power Query via Antigravity IDE.
Usar a ferramenta `named_expression_operations` para persistir o código M.

## Ordem de Limpeza e Relacionamento — Projeto Chamados CEX

### 1. Tratamento da Tabela Dimensão (BASE CLIENTES MULTI)
- **Ajuste de Colunas Duplicadas:** Manter a coluna `Destino ID.1` como a chave mestre oficial, pois ela preserva o prefixo "C" (ex: `C0030570571`).
- **Definição de Tipo:** Forçar explicitamente a coluna `Destino ID.1` como **Texto**. Isso evita que o Power BI elimine os zeros à esquerda dos códigos.
- **Remoção de Duplicadas:** Aplicar a remoção de linhas duplicadas baseada na chave `Destino ID.1` para garantir a integridade de dimensão (1:N).

### 2. Tratamento da Tabela Fato (RELATORIO CHAMADOS)
- **Definição de Tipo da Chave:** Forçar a coluna `Código Integração Cliente` como **Texto**.
- **Higienização de Texto:** Aplicar `Text.Trim` e `Text.Proper` na coluna `Situação Chamado` para garantir a unificação dos status (`Aberto`, `Finalizado`, `Rejeitado`).
- **Preenchimento de Nulos:** Na coluna `Chave NFD`, substituir valores nulos/blank por `"Sem Nota de Devolução"`.

### 3. Código M de Padronização da Chave de Integração
```m
let
    Fonte = Excel.Workbook(File.Contents("C:\projeto-chamados-cex\data\raw\RELATORIO CHAMADOS.xlsx"), null, true),
    Sheet1_sheet = Fonte{[Item="Sheet1",Kind="Sheet"]}[Data],
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(Sheet1_sheet, [PromoteAllScalars=true]),
    #"Tipo Alterado Chave" = Table.TransformColumnTypes(#"Cabeçalhos Promovidos",{{"Código Integração Cliente", type text}}),
    #"Texto Trimado" = Table.TransformColumns(#"Tipo Alterado Chave",{{"Situação Chamado", Text.Trim, type text}, {"Código Integração Cliente", Text.Trim, type text}}),
    #"Status Padronizado" = Table.TransformColumns(#"Texto Trimado",{{"Situação Chamado", Text.Proper, type text}})
in
    #"Status Padronizado"


    Nomes de Colunas Finais (Fato)
Nº Atendimento | Nº Carga | Código Grupo Motivo | Grupo Motivo | Motivo | 
Situação Chamado | Código Filial | Código Integração Cliente | Cliente | NFes