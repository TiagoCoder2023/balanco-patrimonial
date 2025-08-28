# Como Fazer Deploy Online

## Opção 1: GitHub + Render (Recomendado)

### 1. Instalar Git
- Baixe e instale o Git: https://git-scm.com/download/win
- Ou use o GitHub Desktop: https://desktop.github.com/

### 2. Criar Repositório no GitHub
1. Acesse https://github.com
2. Clique em "New repository"
3. Nome: `balanco-patrimonial`
4. Descrição: "Aplicação web para cálculo de balanço patrimonial"
5. Público ou privado (sua escolha)
6. Clique "Create repository"

### 3. Subir Código para GitHub
```bash
# No PowerShell, com Git instalado:
git init
git add .
git commit -m "Primeira versão: aplicação de balanço patrimonial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/balanco-patrimonial.git
git push -u origin main
```

### 4. Deploy no Render (Gratuito)
1. Acesse https://render.com
2. Faça login com sua conta GitHub
3. Clique "New +" → "Web Service"
4. Conecte seu repositório GitHub
5. Configurações:
   - **Name**: balanco-patrimonial
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free
6. Clique "Create Web Service"

## Opção 2: Heroku (Alternativa)

### 1. Criar Conta Heroku
- Acesse https://heroku.com
- Crie uma conta gratuita

### 2. Instalar Heroku CLI
```bash
# No PowerShell como administrador:
winget install --id=Heroku.HerokuCLI
```

### 3. Deploy
```bash
heroku login
heroku create balanco-patrimonial
git add .
git commit -m "Deploy para Heroku"
git push heroku main
```

## Opção 3: PythonAnywhere (Mais Simples)

### 1. Criar Conta
- Acesse https://www.pythonanywhere.com
- Crie uma conta gratuita

### 2. Upload dos Arquivos
1. No dashboard, vá em "Files"
2. Crie uma pasta `balanco-patrimonial`
3. Faça upload de todos os arquivos do projeto

### 3. Configurar Web App
1. Vá em "Web" → "Add a new web app"
2. Escolha "Flask" e Python 3.9
3. Configure o caminho: `/home/SEU_USUARIO/balanco-patrimonial/app.py`
4. Clique "Reload"

## Arquivos de Configuração

Este projeto já inclui:
- `requirements.txt` - Dependências Python
- `Procfile` - Para Heroku
- `runtime.txt` - Versão Python
- `.gitignore` - Arquivos a ignorar no Git

## Testando Online

Após o deploy, você poderá:
1. Acessar a aplicação pelo navegador
2. Testar no iPhone/Safari
3. Fazer upload de planilhas Excel/CSV
4. Ver os cálculos de Ativo, Passivo e Patrimônio Líquido

## Suporte

Se encontrar problemas:
1. Verifique os logs da plataforma de deploy
2. Confirme que todas as dependências estão em `requirements.txt`
3. Teste localmente primeiro com `python app.py`
