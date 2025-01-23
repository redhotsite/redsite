from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Olá! O servidor está funcionando!'

if __name__ == '__main__':
    print("Iniciando servidor de teste...")
    app.run(debug=False, port=5000) 