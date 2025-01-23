from waitress import serve
from app import app
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    try:
        logging.info("=== Iniciando servidor em http://localhost:8080 ===")
        serve(app, host='0.0.0.0', port=8080)
    except Exception as e:
        logging.error(f"Erro ao iniciar o servidor: {str(e)}") 