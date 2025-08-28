# Balanço Patrimonial com IA

Aplicação web para cálculo automático de Patrimônio Líquido a partir de planilhas, PDFs e imagens, utilizando inteligência artificial da OpenAI.

## 🚀 Funcionalidades

### **Processamento Inteligente de Documentos**
- **Planilhas Excel/CSV**: Análise automática de colunas e valores
- **PDFs**: Extração de tabelas com pdfplumber e PyPDF2
- **Imagens**: Análise com visão computacional da OpenAI (GPT-4 Vision)
- **Fallback Inteligente**: Múltiplos algoritmos de análise para máxima precisão

### **Algoritmos de Análise**
1. **Visão Computacional**: IA analisa imagens e PDFs para extrair dados estruturados
2. **Colunas Separadas**: Identifica colunas específicas de ativo e passivo
3. **Classificação + Valor**: Mapeia classificações para categorias
4. **Descrição + Valor**: Análise de texto para classificação automática
5. **Heurística de Sinais**: Positivos = Ativos, Negativos = Passivos

### **Formatos Suportados**
- 📊 **Excel**: .xlsx, .xls, .xlsm
- 📄 **CSV**: Arquivos de texto separados por vírgula
- 📋 **PDF**: Documentos com tabelas estruturadas
- 🖼️ **Imagens**: .png, .jpg, .jpeg (análise com IA)

## 🛠️ Tecnologias

- **Backend**: Flask (Python)
- **Processamento**: Pandas, OpenPyXL, xlrd
- **PDFs**: pdfplumber, PyPDF2
- **IA**: OpenAI GPT-4o-mini API (visão computacional)
- **Frontend**: HTML5, CSS3 (Responsivo)
- **Deploy**: Render, Heroku

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd balanco_patrimonial
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure a API da OpenAI
Crie um arquivo `config.py` com sua chave:
```python
OPENAI_API_KEY = "sua-chave-api-aqui"
```

### 4. Execute a aplicação
```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

## 🔑 Configuração da API OpenAI

1. Acesse [OpenAI Platform](https://platform.openai.com/)
2. Crie uma conta e gere uma chave API
3. Adicione a chave no arquivo `config.py`
4. A funcionalidade de visão computacional estará disponível

## 📱 Como Usar

### **Upload de Arquivo**
1. Acesse a aplicação no navegador
2. Clique em "Escolher arquivo"
3. Selecione seu documento (planilha, PDF ou imagem)
4. Clique em "Calcular"

### **Análise Automática**
- **Planilhas**: Análise direta das colunas
- **PDFs**: Extração de tabelas + IA como backup
- **Imagens**: Análise completa com visão computacional

### **Resultados**
- Total de Ativos
- Total de Passivos
- Patrimônio Líquido calculado
- Detalhes do processamento
- Método utilizado (incluindo IA quando aplicável)

## 🏗️ Arquitetura

```
app.py                 # Aplicação principal Flask
├── analyze_with_vision_computer()  # Análise com IA
├── extract_tables_from_pdf()       # Extração de PDFs
├── calculate_balance_from_df()     # Cálculos de balanço
└── read_table_from_file_storage()  # Leitura de arquivos

templates/             # Interface HTML
├── index.html         # Página de upload
└── result.html        # Página de resultados

static/                # Estilos CSS
└── style.css          # Design responsivo
```

## 🔍 Casos de Uso

### **Contadores e Contadores**
- Análise de balanços patrimoniais
- Verificação de demonstrações financeiras
- Auditoria de documentos contábeis

### **Empresas**
- Análise de relatórios financeiros
- Verificação de balanços
- Processamento de documentos em lote

### **Educação**
- Estudos de casos contábeis
- Análise de demonstrações financeiras
- Exercícios práticos de contabilidade

## 🚀 Deploy

### **Render**
1. Conecte seu repositório GitHub
2. Configure as variáveis de ambiente
3. Deploy automático a cada push

### **Heroku**
1. Crie um app no Heroku
2. Configure as variáveis de ambiente
3. Deploy via Git

## 📊 Limitações e Considerações

- **Tamanho máximo**: 16 MB por arquivo
- **Formato de imagem**: PNG, JPG, JPEG
- **Custo da API**: OpenAI cobra por uso da API Vision
- **Precisão**: Depende da qualidade do documento enviado

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para dúvidas ou problemas:
1. Abra uma issue no GitHub
2. Verifique a documentação
3. Consulte os logs de debug da aplicação

---

**Desenvolvido com ❤️ para facilitar a análise contábil**
