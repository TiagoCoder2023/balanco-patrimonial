# Exemplo de Uso da Nova Funcionalidade de Visão Computacional

## 🚀 O que foi implementado

A aplicação agora possui **inteligência artificial integrada** para analisar documentos contábeis usando a API de visão computacional da OpenAI (GPT-4o-mini).

## 📁 Formatos Suportados

### **Antes (apenas processamento tradicional)**
- ✅ Excel (.xlsx, .xls, .xlsm)
- ✅ CSV
- ✅ PDF (extração de tabelas)

### **Agora (com IA)**
- ✅ Excel (.xlsx, .xls, .xlsm)
- ✅ CSV
- ✅ PDF (extração de tabelas + IA como backup)
- 🆕 **PNG, JPG, JPEG** (análise completa com IA)

## 🔍 Como Funciona

### **1. Upload de Imagem**
```
Usuário envia: balanco_patrimonial.jpg
↓
IA analisa a imagem
↓
Extrai ativos e passivos
↓
Retorna dados estruturados
↓
Calcula Patrimônio Líquido
```

### **2. Upload de PDF**
```
Usuário envia: relatorio.pdf
↓
Tenta extração tradicional primeiro
↓
Se falhar, usa IA como backup
↓
Análise completa do documento
```

## 📊 Exemplo de Resposta da IA

Quando você envia uma imagem ou PDF, a IA retorna:

```json
{
  "ativos": [
    {"descricao": "Caixa e Bancos", "valor": 50000.00},
    {"descricao": "Contas a Receber", "valor": 150000.00},
    {"descricao": "Estoques", "valor": 200000.00}
  ],
  "passivos": [
    {"descricao": "Fornecedores", "valor": 80000.00},
    {"descricao": "Empréstimos", "valor": 100000.00}
  ],
  "observacoes": "Documento bem estruturado com balanço patrimonial completo"
}
```

## 🎯 Casos de Uso Reais

### **Cenário 1: Foto de Balanço Impresso**
- Contador tira foto do balanço
- Upload na aplicação
- IA identifica automaticamente ativos/passivos
- Resultado em segundos

### **Cenário 2: PDF Escaneado**
- Documento antigo escaneado
- Extração tradicional falha
- IA analisa o conteúdo visual
- Dados extraídos com precisão

### **Cenário 3: Relatório Complexo**
- Múltiplas páginas
- Formatação irregular
- IA interpreta o contexto
- Resultado estruturado

## 🔧 Configuração

### **1. Arquivo config.py**
```python
OPENAI_API_KEY = "sua-chave-api-aqui"
```

### **2. Variáveis de Ambiente**
```bash
OPENAI_API_KEY=sk-proj-...
```

## 💰 Custos da API

- **GPT-4o-mini**: ~$0.00015 por 1K tokens (muito mais econômico)
- **Visão computacional**: Incluída no modelo
- **Depende do tamanho** e complexidade
- **Cobrança por uso** (não mensal)
- **Teste gratuito** disponível

## 🚨 Limitações

- **Tamanho máximo**: 16 MB
- **Qualidade da imagem**: Afeta precisão
- **Idioma**: Melhor em português/inglês
- **Formato**: PNG, JPG, JPEG

## 🧪 Testando

### **1. Execute a aplicação**
```bash
python app.py
```

### **2. Acesse no navegador**
```
http://localhost:5000
```

### **3. Teste com diferentes arquivos**
- Planilha Excel
- Imagem de balanço
- PDF escaneado
- CSV simples

## 📈 Benefícios

### **Para Usuários**
- ✅ Análise de qualquer documento
- ✅ Não precisa formatar dados
- ✅ Resultados instantâneos
- ✅ Interface intuitiva

### **Para Desenvolvedores**
- ✅ Código modular
- ✅ Fallback inteligente
- ✅ Logs detalhados
- ✅ Fácil manutenção

## 🔮 Próximos Passos

1. **Teste com documentos reais**
2. **Ajuste prompts da IA**
3. **Implemente cache de resultados**
4. **Adicione mais formatos**
5. **Melhore tratamento de erros**

---

**A funcionalidade está pronta para uso! 🎉**
