# Balanço Patrimonial

Aplicação web em Flask para calcular Ativo, Passivo e Patrimônio Líquido a partir de uma planilha Excel/CSV.

## Requisitos
- Python 3.10+
- Pip

## Instalação
```bash
# No diretório do projeto
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Executando
```bash
# Ambiente ativado
python app.py
```
Acesse `http://127.0.0.1:5000` no navegador.

## Uso
1. Envie um arquivo `.xlsx`, `.xls` ou `.csv` contendo colunas que indiquem Ativo e Passivo, ou uma coluna de classificação e uma coluna de valor.
2. A aplicação tenta identificar automaticamente as colunas e calcular:
   - Total de Ativos
   - Total de Passivos
   - Patrimônio Líquido (Ativos - Passivos)

Se não houver colunas explícitas, é usada uma heurística por sinal (valores positivos como ativos e negativos como passivos).

## iOS (Safari)
- Interface responsiva e com suporte a `viewport-fit=cover` e safe-areas.
- Você pode adicionar à tela inicial no iPhone e usar em modo web-app.

## Observações
- Nenhum dado é persistido.
- Compatível com `.xlsx`, `.xls` (via xlrd) e `.csv`.
