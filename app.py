import io
import re
import os
import base64
from typing import Dict, Optional, Tuple

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

import pdfplumber
import PyPDF2
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Importa configurações
try:
    from _config_api.config import OPENAI_API_KEY, MAX_FILE_SIZE, SECRET_KEY
except ImportError:
    # Fallback para variáveis de ambiente
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MAX_FILE_SIZE = 16 * 1024 * 1024
    SECRET_KEY = "change-this-secret-key"

client = OpenAI(api_key=OPENAI_API_KEY)


app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


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
	"""
	Converte uma série para valores numéricos, lidando com formatos brasileiros.
	"""
	# Primeiro tenta conversão direta
	numeric = pd.to_numeric(series, errors="coerce")
	
	# Se todos os valores são NaN, tenta limpar o formato
	if numeric.isna().all():
		# Remove caracteres não numéricos exceto vírgula e ponto
		cleaned = series.astype(str).str.replace(r'[^\d,.-]', '', regex=True)
		# Substitui vírgula por ponto para decimais
		cleaned = cleaned.str.replace(',', '.')
		# Remove pontos de milhares (mantém apenas o último ponto)
		cleaned = cleaned.str.replace(r'\.(?=.*\.)', '', regex=True)
		# Converte para numérico
		numeric = pd.to_numeric(cleaned, errors="coerce")
	
	return numeric


def _sum_numeric(series: pd.Series) -> float:
	"""
	Soma valores numéricos de uma série, ignorando valores NaN.
	"""
	numeric = _coerce_numeric(series)
	print(f"DEBUG: Série original: {series.tolist()}")
	print(f"DEBUG: Série numérica: {numeric.tolist()}")
	print(f"DEBUG: Valores não-NaN: {numeric.dropna().tolist()}")
	
	sum_result = float(pd.Series(numeric).fillna(0).sum())
	print(f"DEBUG: Soma calculada: {sum_result}")
	return sum_result


def calculate_balance_from_df(df: pd.DataFrame) -> Tuple[Dict, Optional[str]]:
	"""
	Tenta identificar Ativo e Passivo em um DataFrame e calcula o Patrimônio Líquido.

	Retorna:
		(result_dict, error_message)
	"""
	if df is None or df.empty:
		return {}, "Planilha vazia ou inválida."

	# Debug: Mostra informações sobre o DataFrame
	print(f"DEBUG: DataFrame shape: {df.shape}")
	print(f"DEBUG: Colunas: {list(df.columns)}")
	print(f"DEBUG: Primeiras 5 linhas:")
	print(df.head())
	print(f"DEBUG: Tipos de dados:")
	print(df.dtypes)

	# Padroniza nomes de colunas
	columns_lower = {col: _normalize_string(str(col)) for col in df.columns}
	print(f"DEBUG: Colunas normalizadas: {columns_lower}")

	# 0) Caso especial: dados da visão computacional (formato padronizado)
	if set(df.columns) == {"classificacao", "descricao", "valor"}:
		print("DEBUG: Detectado formato da visão computacional")
		df_copy = df.copy()
		df_copy["valor"] = _coerce_numeric(df_copy["valor"])
		
		# Agrupa por classificação
		agrupado = df_copy.groupby("classificacao")["valor"].sum()
		total_ativos = float(agrupado.get("ativo", 0.0))
		total_passivos = float(agrupado.get("passivo", 0.0))
		
		if total_ativos != 0.0 or total_passivos != 0.0:
			pl = total_ativos - total_passivos
			detalhes = df_copy.to_dict(orient="records")
			return (
				{
					"metodo": "visao_computacional",
					"total_ativos": total_ativos,
					"total_passivos": total_passivos,
					"patrimonio_liquido": pl,
					"detalhes": detalhes,
					"aviso": "Análise realizada com inteligência artificial da OpenAI (GPT-4o-mini)."
				},
				None,
			)

	# 1) Caso com colunas separadas para Ativo e Passivo
	ativo_col = None
	passivo_col = None
	for original, lowered in columns_lower.items():
		if "ativo" in lowered or "asset" in lowered:
			ativo_col = original
		if "passivo" in lowered or "liab" in lowered or "obrig" in lowered:
			passivo_col = original
	
	print(f"DEBUG: Coluna ativo encontrada: {ativo_col}")
	print(f"DEBUG: Coluna passivo encontrada: {passivo_col}")
	
	if ativo_col and passivo_col:
		print(f"DEBUG: Valores da coluna ativo: {df[ativo_col].tolist()}")
		print(f"DEBUG: Valores da coluna passivo: {df[passivo_col].tolist()}")
		
		total_ativos = _sum_numeric(df[ativo_col])
		total_passivos = _sum_numeric(df[passivo_col])
		
		print(f"DEBUG: Total ativos calculado: {total_ativos}")
		print(f"DEBUG: Total passivos calculado: {total_passivos}")
		
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


def analyze_with_vision_computer(file_content: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
	"""
	Analisa arquivos usando a API de visão computacional da OpenAI.
	
	Args:
		file_content: Conteúdo do arquivo em bytes
		filename: Nome do arquivo para identificação do tipo
		
	Returns:
		(DataFrame, error_message)
	"""
	try:
		# Converte o arquivo para base64
		file_base64 = base64.b64encode(file_content).decode('utf-8')
		
		# Determina o tipo MIME baseado na extensão
		mime_type = "application/pdf"
		if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
			mime_type = "image/jpeg"
		elif filename.lower().endswith('.pdf'):
			mime_type = "application/pdf"
		
		# Prompt para análise de balanço patrimonial
		system_prompt = """Você é um especialista em contabilidade e análise financeira. 
		Analise o documento fornecido e extraia as informações de balanço patrimonial.
		
		INSTRUÇÕES:
		1. Identifique todos os ativos e passivos
		2. Classifique cada item corretamente
		3. Extraia os valores numéricos
		4. Retorne os dados em formato JSON estruturado
		
		FORMATO DE RESPOSTA:
		{
			"ativos": [
				{"descricao": "Nome do ativo", "valor": 1000.00},
				{"descricao": "Outro ativo", "valor": 500.00}
			],
			"passivos": [
				{"descricao": "Nome do passivo", "valor": 300.00},
				{"descricao": "Outro passivo", "valor": 200.00}
			],
			"observacoes": "Qualquer observação relevante sobre o documento"
		}
		
		IMPORTANTE: Retorne APENAS o JSON, sem texto adicional."""
		
		# Chama a API da OpenAI com visão computacional
		response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{
					"role": "system",
					"content": system_prompt
				},
				{
					"role": "user",
					"content": [
						{
							"type": "text",
							"text": "Analise este documento e extraia as informações de balanço patrimonial. Retorne apenas o JSON conforme especificado."
						},
						{
							"type": "image_url",
							"image_url": {
								"url": f"data:{mime_type};base64,{file_base64}"
							}
						}
					]
				}
			],
			max_tokens=2000,
			temperature=0.1
		)
		
		# Extrai a resposta
		content = response.choices[0].message.content
		
		# Tenta extrair JSON da resposta
		import json
		try:
			# Remove possíveis marcadores de código
			if "```json" in content:
				content = content.split("```json")[1].split("```")[0]
			elif "```" in content:
				content = content.split("```")[1]
			
			data = json.loads(content.strip())
			
			# Converte para DataFrame
			rows = []
			
			# Adiciona ativos
			for ativo in data.get("ativos", []):
				rows.append({
					"classificacao": "ativo",
					"descricao": ativo.get("descricao", ""),
					"valor": ativo.get("valor", 0.0)
				})
			
			# Adiciona passivos
			for passivo in data.get("passivos", []):
				rows.append({
					"classificacao": "passivo",
					"descricao": passivo.get("descricao", ""),
					"valor": passivo.get("valor", 0.0)
				})
			
			if rows:
				df = pd.DataFrame(rows)
				return df, None
			else:
				return None, "Nenhum dado extraído da análise de visão computacional."
				
		except json.JSONDecodeError as e:
			return None, f"Erro ao processar resposta da API: {e}. Resposta: {content[:200]}..."
		except Exception as e:
			return None, f"Erro ao processar dados extraídos: {e}"
			
	except Exception as e:
		return None, f"Erro na análise com visão computacional: {e}"


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

	print(f"DEBUG: Tentando ler arquivo: {filename}")
	print(f"DEBUG: Tamanho do arquivo: {len(content)} bytes")

	# Primeiro tenta análise com visão computacional para imagens e PDFs
	if filename.endswith(('.png', '.jpg', '.jpeg', '.pdf')):
		print("DEBUG: Tentando análise com visão computacional")
		vision_result, vision_error = analyze_with_vision_computer(content, filename)
		if vision_result is not None and not vision_result.empty:
			print("DEBUG: Visão computacional bem-sucedida")
			return vision_result, None
		else:
			print(f"DEBUG: Visão computacional falhou: {vision_error}")
			# Continua com métodos tradicionais para PDFs

	# Tenta por extensão primeiro
	try:
		if filename.endswith(".pdf"):
			print("DEBUG: Processando como PDF")
			return extract_tables_from_pdf(content)
		if filename.endswith(".xlsx") or filename.endswith(".xlsm"):
			print("DEBUG: Processando como Excel (.xlsx/.xlsm)")
			buffer.seek(0)
			df = pd.read_excel(buffer, engine="openpyxl", header=0)
			print(f"DEBUG: Excel lido com sucesso. Shape: {df.shape}")
			return df, None
		if filename.endswith(".xls"):
			print("DEBUG: Processando como Excel (.xls)")
			buffer.seek(0)
			df = pd.read_excel(buffer, engine="xlrd", header=0)
			print(f"DEBUG: Excel lido com sucesso. Shape: {df.shape}")
			return df, None
		if filename.endswith(".csv"):
			print("DEBUG: Processando como CSV")
			buffer.seek(0)
			df = pd.read_csv(buffer, sep=None, engine="python", header=0)
			print(f"DEBUG: CSV lido com sucesso. Shape: {df.shape}")
			return df, None
	except Exception as exc:
		print(f"DEBUG: Erro ao ler arquivo: {exc}")
		return None, f"Erro ao ler arquivo: {exc}"

	# Se extensão desconhecida, tenta PDF, Excel e depois CSV
	print("DEBUG: Extensão desconhecida, tentando diferentes formatos...")
	try:
		return extract_tables_from_pdf(content)
	except Exception as e:
		print(f"DEBUG: Falha ao processar como PDF: {e}")
		pass
	try:
		buffer.seek(0)
		df = pd.read_excel(buffer, engine="openpyxl", header=0)
		print(f"DEBUG: Excel lido com sucesso (fallback). Shape: {df.shape}")
		return df, None
	except Exception as e:
		print(f"DEBUG: Falha ao processar como Excel: {e}")
		pass
	try:
		buffer.seek(0)
		df = pd.read_csv(buffer, sep=None, engine="python", header=0)
		print(f"DEBUG: CSV lido com sucesso (fallback). Shape: {df.shape}")
		return df, None
	except Exception as exc:
		print(f"DEBUG: Falha ao processar como CSV: {exc}")
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
