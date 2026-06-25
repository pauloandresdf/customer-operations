# 🎯 Projeto: Dashboard de Performance e Chamados — CEX Multi

## Contexto do Projeto
Dashboard analítico e preditivo de monitoramento de ocorrências de transporte, estadias e recusas logísticas no Power BI usando Antigravity IDE + Power BI Modeling MCP (27 tools ativas). 
A solução cruza a volumetria operacional de atendimento com o cadastro mestre de clientes para identificar gargalos geográficos, ofensores por cliente e balanceamento de carga de trabalho na equipe de Customer Execution (CEX).

- **Base Fato:** `data/raw/RELATORIO CHAMADOS.xlsx` (Sheet1) — 65.535 linhas de registros operacionais.
- **Base Dimensão:** `data/raw/BASE CLIENTES MULTI.xlsx` (Planilha1) — Cadastro mestre de carteiras, analistas e coordenadores.

## 🤖 Modelo e Comportamento da IA
- **Modelo Sugerido:** Gemini 1.5 Pro ou 3.1 Pro (Medium/High) para processamento robusto de contexto extenso de dados.
- **Idioma:** Sempre responder e documentar em português do Brasil (PT-BR).
- **Ordem de Execução:** Sempre ler a skill correspondente contida na pasta `docs/` ANTES de gerar ou injetar códigos no modelo.
- **Processo de Mudança:** Validar expressões DAX com `EVALUATE` antes de consolidar medidas e confirmar cada etapa com o usuário antes de avançar.

## 🗂️ Matriz de Skills Disponíveis (`docs/`)
| Escopo da Tarefa | Arquivo de Skill Referência |
|------------------|-----------------------------|
| Limpeza de dados, modelagem Star Schema, Power Query (M) | `docs/01-limpeza-dados.md` |
| Métricas de Supply Chain/CEX, KPIs de volumetria, frameworks | `docs/02-analise-dados.md` |
| Engenharia de Medidas DAX, contexto de filtro, uso do MCP | `docs/03-dax-powerbi.md` |
| Interface Visual HTML Premium, Injeção JSON, Chart.js Dark | `docs/04-visualizacao.md` |

## 🔌 Protocolo de Conexão MCP (Antigravity)
O MCP está ativo via executável nativo conectado à instância local do Power BI Desktop.
Toda sessão de desenvolvimento com a IA deve obrigatoriamente iniciar com o comando:
*"Connect to the Power BI model that is currently open"*

Ferramentas mandatórias por etapa:
- `connection_operations`: Mapeamento estrutural, conferência de metadados e listagem de tabelas.
- `named_expression_operations`: Gravação de etapas de transformação e higienização no Power Query (M).
- `measure_operations`: Criação, modificação e deploy de medidas DAX no modelo.
- `dax_query_operations`: Execução de queries de validação via `EVALUATE` (obrigatório antes de salvar medidas).
- `database_operations`: Geração de tabelas calculadas físicas (como a dCalendario).

## 📊 Arquitetura de Dados e Chaves de Integração
Para garantir a integridade referencial do modelo Star Schema, a modelagem deve seguir estritamente as especificações abaixo:

1. **Chave Primária/Estrangeira (PK/FK):**
   - Conectar a tabela de Clientes à tabela de Chamados em um relacionamento **1 para Muitos (1:N)**, com direção única de filtro.
   - Chave na Fato: `RELATORIO CHAMADOS[Código Integração Cliente]`
   - Chave na Dimensão: `BASE CLIENTES MULTI[Destino ID.1]` (Coluna de texto contendo o prefixo "C").
   - **Regra Crítica:** Forçar o tipo de dados dessas colunas para **Texto** no Power Query para evitar que o Power BI trunque ou descarte os zeros à esquerda dos códigos.

2. **Distorções de Cadastro a Tratar no Pipeline:**
   - **Chamados órfãos:** Tratar via `LEFT JOIN` no Power Query ou Python e assinalar clientes não encontrados na base Multi como `"Cliente Não Cadastrado"`.
   - **Campos de Texto:** Aplicar `Text.Trim` e `Text.Proper` na coluna `RELATORIO CHAMADOS[Situação Chamado]` para unificar registros como "Aberto", "Finalizado" e "Rejeitado".

## 📐 Padronização de Nomenclatura de Medidas DAX
O projeto exige consistência absoluta na criação de métricas. Nunca altere o padrão estabelecido:
- `[Total Chamados]` — Contagem implícita de linhas da tabela fato (`COUNTROWS`).
- `[Total Chamados Finalizados]` — Chamados com status igual a "Finalizado".
- `[Total Chamados Abertos]` — Chamados com status igual a "Aberto".
- `[Taxa de Eficiência CEX]` — Proporção de chamados finalizados sobre o total bruto.
- `[Índice de Avaria]` — Percentual de chamados abertos pelo motivo "23 - MAU ESTADO DA MERCADORIA".
- `[Índice de Excesso de Veículo]` — Percentual de chamados pelo motivo "10 - EXCESSO DE VEICULO NO CLIENTE".
- `[Visual Dashboard]` — Medida mestre que armazena a string e o template HTML do painel.

## 🎯 Alvo Final de Entrega (Milestones)
1. **ETL Automatizado:** Script M ou Python validando o pareamento de códigos integradores de clientes.
2. **Modelagem Eficiente:** Modelo relacional performático minimizando colunas desnecessárias na Fato para otimizar compressão xVelocity.
3. **Métricas DAX Homologadas:** Criação do grupo de medidas de controle logístico e produtividade de carteira.
4. **Painel HTML Content Dark:** Construção de uma interface futurista (Exo 2 + Share Tech Mono), com gráficos responsivos de linha (evolução diária) e rosca (share de ofensores por cliente/região) processados em memória pelo client-side (JS).
5. **Módulo IA Insight:** Inclusão de um rodapé interativo conectado à API da OpenAI (`gpt-4o-mini`) para leitura contextualizada da matriz condensada de chamados do analista selecionado.

## ⚠️ Regras de Ouro Inegociáveis
1. **Regra das Aspas em HTML:** O template visual dentro da medida DAX deve utilizar **EXCLUSIVAMENTE aspas simples ('')** para marcação de atributos, CSS inline e scripts. Aspas duplas quebrará o motor de renderização da string DAX.
2. **Prevenção de Erros de Linhagem:** Para cálculos tabulares ou ordenações de rankings por analista/região utilizando medidas, use **SEMPRE** a combinação `ADDCOLUMNS(VALUES('Tabela'[Coluna]), "Nome", [Medida])`. **NUNCA** adicione colunas calculadas baseadas em medidas diretamente em uma função `SUMMARIZE`.
3. **Payload Econômico:** O JSON gerado dinamicamente via `CONCATENATEX` e `UNICHAR(34)` na medida do painel não pode exceder o limite de **30KB**. Use chaves compactas de uma ou duas letras (`a` para Analista, `r` para Região, `tc` para Total Chamados).
