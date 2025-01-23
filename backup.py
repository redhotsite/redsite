import os
import shutil
import datetime
import subprocess
import logging
from git import Repo
import json

# Configuração do logging
logging.basicConfig(
    filename='backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configurações
BACKUP_DIR = 'backups'
MAX_BACKUPS = 5
DB_FILE = 'users.db'
GITHUB_CONFIG_FILE = 'github_config.json'

def setup_github():
    """Configura as credenciais do GitHub se não estiverem configuradas"""
    if not os.path.exists(GITHUB_CONFIG_FILE):
        print("\nConfiguração do GitHub necessária:")
        repo_url = input("Digite a URL do repositório GitHub: ")
        username = input("Digite seu nome de usuário GitHub: ")
        token = input("Digite seu token de acesso GitHub: ")
        
        config = {
            'repo_url': repo_url,
            'username': username,
            'token': token
        }
        
        with open(GITHUB_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        
        print("✓ Configuração do GitHub salva!")
    
    return load_github_config()

def load_github_config():
    """Carrega as configurações do GitHub"""
    if os.path.exists(GITHUB_CONFIG_FILE):
        with open(GITHUB_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def create_backup():
    """Cria um backup do banco de dados e envia para o GitHub"""
    try:
        # Cria diretório de backup se não existir
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        # Verifica se o banco de dados existe
        if not os.path.exists(DB_FILE):
            logging.warning(f"Arquivo {DB_FILE} não encontrado!")
            return False
        
        # Gera nome do arquivo de backup com timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'users_backup_{timestamp}.db'
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        
        # Cria o backup
        shutil.copy2(DB_FILE, backup_path)
        logging.info(f"Backup criado: {backup_file}")
        
        # Remove backups antigos se exceder o limite
        cleanup_old_backups()
        
        # Tenta fazer backup no GitHub
        try:
            github_backup(backup_file)
        except Exception as e:
            logging.error(f"Erro no backup do GitHub: {str(e)}")
        
        return True
    
    except Exception as e:
        logging.error(f"Erro ao criar backup: {str(e)}")
        return False

def cleanup_old_backups():
    """Remove backups antigos mantendo apenas os MAX_BACKUPS mais recentes"""
    try:
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('users_backup_')])
        while len(backups) > MAX_BACKUPS:
            oldest = os.path.join(BACKUP_DIR, backups.pop(0))
            os.remove(oldest)
            logging.info(f"Backup antigo removido: {oldest}")
    except Exception as e:
        logging.error(f"Erro ao limpar backups antigos: {str(e)}")

def github_backup(backup_file):
    """Envia o backup para o GitHub"""
    config = load_github_config()
    if not config:
        config = setup_github()
    
    if not config:
        logging.error("Configuração do GitHub não encontrada")
        return
    
    try:
        # Configura o repositório
        if not os.path.exists('.git'):
            repo = Repo.init()
            origin = repo.create_remote('origin', config['repo_url'])
        else:
            repo = Repo('.')
        
        # Configura credenciais
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', config['username'])
            git_config.set_value('credential', 'helper', 'store')
        
        # Cria/atualiza .gitignore
        gitignore = """
users.db
__pycache__/
*.pyc
static/uploads/
backups/
*.log
github_config.json
"""
        with open('.gitignore', 'w') as f:
            f.write(gitignore)
        
        # Adiciona arquivos e faz commit
        repo.index.add(['.gitignore'])
        repo.index.commit(f"Backup automático - {datetime.datetime.now()}")
        
        # Push para o GitHub
        origin = repo.remote('origin')
        origin.push()
        
        logging.info("Backup enviado para o GitHub com sucesso!")
        return True
    
    except Exception as e:
        logging.error(f"Erro ao fazer backup no GitHub: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando backup...")
    if create_backup():
        print("✓ Backup concluído com sucesso!")
    else:
        print("✗ Erro ao criar backup. Verifique o arquivo backup.log para mais detalhes.") 