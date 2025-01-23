import schedule
import time
from backup import create_backup
import logging

# Configuração do logging
logging.basicConfig(
    filename='backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def scheduled_backup():
    try:
        logging.info("Iniciando backup agendado...")
        create_backup()
        logging.info("Backup concluído com sucesso!")
    except Exception as e:
        logging.error(f"Erro durante o backup: {str(e)}")

def main():
    print("Iniciando sistema de backup automático...")
    logging.info("Sistema de backup automático iniciado")
    
    # Agenda backup diário às 23:59
    schedule.every().day.at("23:59").do(scheduled_backup)
    
    # Também faz backup a cada 6 horas
    schedule.every(6).hours.do(scheduled_backup)
    
    print("Backup agendado para rodar:")
    print("- Diariamente às 23:59")
    print("- A cada 6 horas")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto

if __name__ == "__main__":
    main() 