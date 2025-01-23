# RED HOT - Sistema de Gerenciamento

Sistema web desenvolvido em Flask para gerenciamento de áreas, usuários e conteúdo.

## Funcionalidades

- Sistema de login e registro
- Painel administrativo
- Gerenciamento de usuários e cargos
- Áreas específicas com posts
- Área +18 com verificação de idade
- Sistema de destaques e notícias
- Upload de fotos e vídeos

## Requisitos

- Python 3.8+
- Flask
- SQLAlchemy
- Werkzeug
- Outras dependências em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/redsite.git
cd redsite
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o servidor:
```bash
python app.py
```

O site estará disponível em `http://127.0.0.1:5000`

## Backup

Para fazer backup do sistema:

1. Commit das alterações:
```bash
git add .
git commit -m "Descrição das alterações"
```

2. Envie para o GitHub:
```bash
git push origin main
```

## Restauração

Para restaurar o sistema:

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/redsite.git
```

2. Siga os passos de instalação acima

## Estrutura de Arquivos

```
redsite/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências
├── static/            # Arquivos estáticos
│   ├── css/          # Estilos
│   ├── js/           # Scripts
│   └── uploads/      # Uploads de usuários
└── templates/        # Templates HTML
```

## Segurança

- Backup automático diário no GitHub
- Senhas criptografadas
- Verificação de permissões
- Proteção contra uploads maliciosos
- Sistema de logs 