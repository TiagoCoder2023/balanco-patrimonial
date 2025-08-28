import io
import re
from typing import Dict, Optional, Tuple

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

import pdfplumber
import PyPDF2


app = Flask(__name__)
app.secret_key = "change-this-secret-key"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


def _normalize_string(value: str) -> str:
	"""Normaliza strings para comparação robusta (minúsculas, sem múltiplos espaços)."""
	if not isinstance(value, str):
		return ""
	return re.sub(r"\s+", " ", value.strip().lower())


def _find_column(candidates, columns_lower):
	for pattern in candidates:
		for original, lowered in columns_lower.items():
			if pattern in lowered:
				return original
	return None


def _coerce_numeric(series: pd.Series) -> pd.Series:
	return pd.to_numeric(series, errors="coerce")


def _sum_numeric(series: pd.Series) -> float:
	numeric = _coerce_numeric(series)
	return float(pd.Series(numeric).fillna(0).sum())


def calculate_balance_from_df(df: pd.DataFrame) -> Tuple[Dict, Optional[str]]:
	"""
	Tenta identificar Ativo e Passivo em um DataFrame e calcula o Patrimônio Líquido.

	Retorna:
		(result_dict, error_message)
	"""
	if df is None or df.empty:
		return {}, "Planilha vazia ou inválida."

	# Padroniza nomes de colunas
	columns_lower = {col: _normalize_string(str(col)) for col in df.columns}

	# 1) Caso com colunas separadas para Ativo e Passivo
	ativo_col = None
	passivo_col = None
	for original, lowered in columns_lower.items():
		if "ativo" in lowered or "asset" in lowered:
			ativo_col = original
		if "passivo" in lowered or "liab" in lowered or "obrig" in lowered:
			passivo_col = original
	if ativo_col and passivo_col:
		total_ativos = _sum_numeric(df[ativo_col])
		total_passivos = _sum_numeric(df[passivo_col])
		pl = total_ativos - total_passivos
		return (
			{
				"metodo": "colunas_separadas",
				"coluna_ativo": ativo_col,
				"coluna_passivo": passivo_col,
				"total_ativos": total_ativos,
				"total_passivos": total_passivos,
				"patrimonio_liquido": pl,
				"detalhes": None,
			},
			None,
		)

	# 2) Coluna de classificação + coluna de valor
	classificacao_candidates = [
		"classificacao",
		"classificação",
		"tipo",
		"grupo",
		"classe",
		"categoria",
		"natureza",
		"tipo de conta",
	]
	valor_candidates = [
		"valor",
		"value",
		"amount",
		"montante",
		"saldo",
		"total",
	]

	classificacao_col = _find_column(classificacao_candidates, columns_lower)
	valor_col = _find_column(valor_candidates, columns_lower)

	if classificacao_col and valor_col:
		tmp = df[[classificacao_col, valor_col]].copy()
		tmp[classificacao_col] = tmp[classificacao_col].map(_normalize_string)
		tmp[valor_col] = _coerce_numeric(tmp[valor_col])
		# Mapeia valores para 'ativo' e 'passivo'
		def map_class(value: str) -> Optional[str]:
			v = value or ""
			if "ativo" in v or "asset" in v:
				return "ativo"
			if "passivo" in v or "liab" in v:
				return "passivo"
			return None

		tmp["__classe__"] = tmp[classificacao_col].map(map_class)
		filtered = tmp.dropna(subset=["__classe__", valor_col])
		agrupado = filtered.groupby("__classe__")[valor_col].sum()
		total_ativos = float(agrupado.get("ativo", 0.0))
		total_passivos = float(agrupado.get("passivo", 0.0))
		if total_ativos != 0.0 or total_passivos != 0.0:
			pl = total_ativos - total_passivos
			detalhes = (
				filtered[["__classe__", valor_col]]
				.rename(columns={"__classe__": "classe", valor_col: "valor"})
				.to_dict(orient="records")
			)
			return (
				{
					"metodo": "classificacao_e_valor",
					"coluna_classificacao": classificacao_col,
					"coluna_valor": valor_col,
					"total_ativos": total_ativos,
					"total_passivos": total_passivos,
					"patrimonio_liquido": pl,
					"detalhes": detalhes,
				},
				None,
			)

	# 3) Usar coluna de descrição para buscar palavras-chave com coluna de valor
	descricao_candidates = [
		"descricao",
		"descrição",
		"conta",
		"historico",
		"histórico",
		"nome",
		"detalhe",
		"linha",
	]
	descricao_col = _find_column(descricao_candidates, columns_lower)
	valor_col_alt = valor_col or _find_column(valor_candidates, columns_lower)

	if descricao_col and valor_col_alt:
		tmp = df[[descricao_col, valor_col_alt]].copy()
		tmp[descricao_col] = tmp[descricao_col].map(_normalize_string)
		tmp[valor_col_alt] = _coerce_numeric(tmp[valor_col_alt])
		tmp["__classe__"] = tmp[descricao_col].apply(
			lambda x: "ativo" if "ativo" in (x or "") or "asset" in (x or "") else ("passivo" if "passivo" in (x or "") or "liab" in (x or "") else None)
		)
		filtered = tmp.dropna(subset=["__classe__", valor_col_alt])
		agrupado = filtered.groupby("__classe__")[valor_col_alt].sum()
		total_ativos = float(agrupado.get("ativo", 0.0))
		total_passivos = float(agrupado.get("passivo", 0.0))
		if total_ativos != 0.0 or total_passivos != 0.0:
			pl = total_ativos - total_passivos
			detalhes = (
				filtered[["__classe__", valor_col_alt]]
				.rename(columns={"__classe__": "classe", valor_col_alt: "valor"})
				.to_dict(orient="records")
			)
			return (
				{
					"metodo": "descricao_e_valor",
					"coluna_descricao": descricao_col,
					"coluna_valor": valor_col_alt,
					"total_ativos": total_ativos,
					"total_passivos": total_passivos,
					"patrimonio_liquido": pl,
					"detalhes": detalhes,
				},
				None,
			)

	# 4) Heurística de sinais (fallback): positivos = ativos, negativos = passivos
	# Procura primeira coluna numérica como 'valor'
	numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
	if not numeric_cols and len(df.columns) > 0:
		# tenta converter a primeira coluna que pareça 'valor'
		candidate = valor_col or df.columns[-1]
		try:
			df[candidate] = _coerce_numeric(df[candidate])
			numeric_cols = [candidate]
		except Exception:
			pass

	if numeric_cols:
		valor_col_last = numeric_cols[0]
		numbers = _coerce_numeric(df[valor_col_last]).fillna(0)
		total_ativos = float(numbers[numbers > 0].sum())
		total_passivos = float((-numbers[numbers < 0]).sum())
		if total_ativos != 0.0 or total_passivos != 0.0:
			pl = total_ativos - total_passivos
			return (
				{
					"metodo": "heuristica_sinal",
					"coluna_valor": valor_col_last,
					"aviso": "Classificação por sinal utilizada (positivos=Ativo, negativos=Passivo). Verifique os resultados.",
					"total_ativos": total_ativos,
					"total_passivos": total_passivos,
					"patrimonio_liquido": pl,
					"detalhes": None,
				},
				None,
			)

	return {}, "Não foi possível identificar colunas de Ativo e Passivo automaticamente."


def extract_tables_from_pdf(content: bytes) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
	"""
	Extrai tabelas de um PDF usando pdfplumber e PyPDF2 como fallback.
	
	Retorna:
		(DataFrame, error_message)
	"""
	try:
		# Tenta primeiro com pdfplumber (melhor para tabelas estruturadas)
		pdf_buffer = io.BytesIO(content)
		with pdfplumber.open(pdf_buffer) as pdf:
			all_tables = []
			for page in pdf.pages:
				tables = page.extract_tables()
				if tables:
					all_tables.extend(tables)
			
			if all_tables:
				# Concatena todas as tabelas encontradas
				dfs = []
				for table in all_tables:
					if table and len(table) > 1:  # Pula tabelas vazias ou com apenas cabeçalho
						# Remove linhas vazias
						table = [row for row in table if any(cell and str(cell).strip() for cell in row)]
						if table:
							df = pd.DataFrame(table[1:], columns=table[0])
							dfs.append(df)
				
				if dfs:
					# Combina todas as tabelas
					result_df = pd.concat(dfs, ignore_index=True)
					# Remove colunas completamente vazias
					result_df = result_df.dropna(how='all', axis=1)
					# Remove linhas completamente vazias
					result_df = result_df.dropna(how='all', axis=0)
					
					if not result_df.empty:
						return result_df, None
		
		# Fallback para PyPDF2 (extração de texto simples)
		pdf_buffer.seek(0)
		reader = PyPDF2.PdfReader(pdf_buffer)
		text_content = ""
		for page in reader.pages:
			text_content += page.extract_text() + "\n"
		
		# Tenta extrair dados estruturados do texto
		lines = text_content.split('\n')
		data_rows = []
		for line in lines:
			line = line.strip()
			if line and len(line.split()) > 1:
				# Tenta dividir por espaços múltiplos ou caracteres especiais
				parts = re.split(r'\s{2,}|\t', line)
				if len(parts) >= 2:
					data_rows.append(parts)
		
		if data_rows and len(data_rows) > 1:
			# Cria DataFrame do texto extraído
			df = pd.DataFrame(data_rows[1:], columns=data_rows[0])
			return df, None
		
		return None, "Não foi possível extrair tabelas estruturadas do PDF."
		
	except Exception as exc:
		return None, f"Erro ao processar PDF: {exc}"


def read_table_from_file_storage(file_storage) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
	filename = (file_storage.filename or "").lower()
	content = file_storage.read()
	buffer = io.BytesIO(content)

	# Tenta por extensão primeiro
	try:
		if filename.endswith(".pdf"):
			return extract_tables_from_pdf(content)
		if filename.endswith(".xlsx") or filename.endswith(".xlsm"):
			df = pd.read_excel(buffer, engine="openpyxl")
			return df, None
		if filename.endswith(".xls"):
			df = pd.read_excel(buffer, engine="xlrd")
			return df, None
		if filename.endswith(".csv"):
			buffer.seek(0)
			df = pd.read_csv(buffer, sep=None, engine="python")
			return df, None
	except Exception as exc:
		return None, f"Erro ao ler arquivo: {exc}"

	# Se extensão desconhecida, tenta PDF, Excel e depois CSV
	try:
		return extract_tables_from_pdf(content)
	except Exception:
		pass
	try:
		buffer.seek(0)
		df = pd.read_excel(buffer, engine="openpyxl")
		return df, None
	except Exception:
		pass
	try:
		buffer.seek(0)
		df = pd.read_csv(buffer, sep=None, engine="python")
		return df, None
	except Exception as exc:
		return None, f"Formato não suportado ou arquivo inválido: {exc}"


@app.route("/", methods=["GET"])
def index():
	return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
	if "file" not in request.files:
		flash("Nenhum arquivo enviado.", "error")
		return redirect(url_for("index"))

	file = request.files["file"]
	if file.filename == "":
		flash("Selecione um arquivo.", "error")
		return redirect(url_for("index"))

	df, read_err = read_table_from_file_storage(file)
	if read_err:
		flash(read_err, "error")
		return redirect(url_for("index"))

	result, calc_err = calculate_balance_from_df(df)
	if calc_err:
		flash(calc_err, "error")
		return redirect(url_for("index"))

	return render_template("result.html", result=result)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)
