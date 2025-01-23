import os
import sys
import shutil
import threading
from app import app, init_db
from backup import create_backup
import schedule
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("\n" + "="*50)
    print("RED HOT - Painel de Controle do Servidor")
    print("="*50 + "\n")

def print_menu():
    print("1. Iniciar Servidor")
    print("2. Reiniciar Banco de Dados")
    print("3. Sair")
    print("\n" + "="*50)

def backup_database():
    """Faz backup do banco de dados atual se existir"""
    if os.path.exists('users.db'):
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Encontra o próximo número de backup disponível
        i = 1
        while os.path.exists(f'{backup_dir}/users_backup_{i}.db'):
            i += 1
        
        backup_path = f'{backup_dir}/users_backup_{i}.db'
        shutil.copy2('users.db', backup_path)
        print(f"\n✓ Backup do banco de dados criado: {backup_path}")

def reset_database():
    """Reinicia o banco de dados"""
    try:
        print("\nReiniciando banco de dados...")
        
        # Faz backup do banco atual
        backup_database()
        
        # Remove o banco atual
        if os.path.exists('users.db'):
            os.remove('users.db')
            print("✓ Banco de dados atual removido")
        
        # Inicializa novo banco
        with app.app_context():
            init_db()
        
        print("\n✓ Banco de dados reiniciado com sucesso!")
        input("\nPressione ENTER para continuar...")
        
    except Exception as e:
        print(f"\nErro ao reiniciar banco de dados: {e}")
        input("\nPressione ENTER para continuar...")

def start_backup_scheduler():
    """Inicia o agendador de backups em uma thread separada"""
    def run_scheduler():
        # Agenda backup a cada 6 horas
        schedule.every(6).hours.do(create_backup)
        
        # Agenda backup diário às 23:59
        schedule.every().day.at("23:59").do(create_backup)
        
        print("\n✓ Backup automático configurado:")
        print("  - A cada 6 horas")
        print("  - Diariamente às 23:59")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    # Inicia o agendador em uma thread separada
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

def main():
    clear_screen()
    print_header()
    
    # Inicia o agendador de backups
    start_backup_scheduler()
    
    print("\n=== Servidor Pronto ===")
    print("Iniciando na porta 5000...")
    print("Acesse: http://127.0.0.1:5000")
    print("Pressione CTRL+C para parar o servidor")
    print("===============================")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário")
        print("Fazendo backup final...")
        create_backup()
        print("Backup concluído. Encerrando...")
    except Exception as e:
        print(f"\nErro ao iniciar servidor: {e}")
        input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    main() 