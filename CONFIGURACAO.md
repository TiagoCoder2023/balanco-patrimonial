# 🔐 Guia de Configuração Segura

## ⚠️ **IMPORTANTE: Segurança**

**NUNCA commite chaves API ou senhas no GitHub!** Isso pode resultar em:
- Uso não autorizado da sua conta
- Custos inesperados
- Comprometimento da segurança
- Bloqueio do push pelo GitHub

## 🚀 **Configuração Rápida**

### **1. Configure a Chave da OpenAI**

#### **Opção A: Pasta _config_api (Recomendado para desenvolvimento)**
```bash
# Copie o arquivo de exemplo para a pasta privada
cp config.example.py _config_api/config.py

# Edite _config_api/config.py com suas chaves reais
# NUNCA commite esta pasta!
```

#### **Opção B: Variáveis de Ambiente (Recomendado para produção)**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sua-chave-aqui"

# Windows CMD
set OPENAI_API_KEY=sua-chave-aqui

# Linux/Mac
export OPENAI_API_KEY="sua-chave-aqui"
```

### **2. Configure a Chave Secreta**
```python
# Em config.py ou variável de ambiente
SECRET_KEY = "chave-secreta-forte-e-aleatoria"
```

## 🔑 **Obtendo a Chave da OpenAI**

1. Acesse [OpenAI Platform](https://platform.openai.com/)
2. Faça login ou crie uma conta
3. Vá para "API Keys"
4. Clique em "Create new secret key"
5. Copie a chave (formato: `sk-...`)
6. **Guarde com segurança!**

## 📁 **Estrutura de Arquivos**

```
balanco_patrimonial/
├── config.example.py     # ✅ Pode ser commitado
├── _config_api/         # ❌ NUNCA commite (pasta privada com chaves)
│   ├── __init__.py      # ❌ NUNCA commite
│   └── config.py        # ❌ NUNCA commite (contém chaves reais)
├── .env                 # ❌ NUNCA commite (contém chaves reais)
├── .gitignore          # ✅ Protege arquivos sensíveis
└── CONFIGURACAO.md     # ✅ Este guia
```

## 🚨 **Arquivos que NUNCA devem ser commitados**

- ❌ `_config_api/` (pasta inteira com chaves)
- ❌ `config.py` (com chaves reais)
- ❌ `.env`
- ❌ Qualquer arquivo com chaves API
- ❌ Senhas ou tokens de acesso

## ✅ **Arquivos que DEVEM ser commitados**

- ✅ `config.example.py`
- ✅ `.gitignore`
- ✅ `CONFIGURACAO.md`
- ✅ Código da aplicação
- ✅ Templates e estilos

## 🔧 **Verificação de Segurança**

### **Antes de fazer commit:**
```bash
# Verifique se não há chaves expostas
git diff --cached | grep -i "sk-"

# Verifique se config.py não está sendo commitado
git status
```

### **Se encontrar chaves expostas:**
1. **IMMEDIATAMENTE** revogue a chave na OpenAI
2. Gere uma nova chave
3. Remova a chave do código
4. Faça novo commit limpo

## 🚀 **Deploy Seguro**

### **Render/Heroku:**
Configure as variáveis de ambiente no painel de controle:
- `OPENAI_API_KEY`
- `SECRET_KEY`

### **VPS/Servidor:**
```bash
# Crie arquivo .env no servidor
nano .env

# Adicione suas chaves
OPENAI_API_KEY=sua-chave-aqui
SECRET_KEY=sua-chave-secreta
```

## 📞 **Suporte**

Se você acidentalmente expôs uma chave:
1. **REVOQUE IMEDIATAMENTE** na OpenAI
2. Gere uma nova chave
3. Atualize sua configuração
4. **NUNCA** use a chave exposta novamente

---

**🔒 Lembre-se: Segurança em primeiro lugar!**
