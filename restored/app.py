from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sys
import os
from enum import IntEnum
from datetime import datetime
import subprocess
from PIL import Image
import io

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class CargoNivel(IntEnum):
    DEV = 1
    ADMIN = 2
    SECRETARIO = 3
    ADM_GERAL = 4
    RED_LIDER = 5
    BRACO_DIREITO = 6
    SUPERVISOR = 7
    OFICIAL = 8
    MEMBRO = 9

print("=== Iniciando Sistema de Login ===")
print(f"Python versão: {sys.version}")
print(f"Diretório atual: {os.getcwd()}")

# Configura o caminho do banco de dados
db_path = os.path.join(os.getcwd(), 'users.db')
print(f"Configurando banco de dados em: {db_path}")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov', 'avi'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB para suportar vídeos

# Criar pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adiciona timestamp para evitar nomes duplicados
        filename = f"{int(datetime.now().timestamp())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'/static/uploads/{filename}'
    return None

print(f"Configurando banco de dados em: {db_path}")
db = SQLAlchemy(app)

# Tabela de associação entre usuários e áreas
user_areas = db.Table('user_areas',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('area_id', db.Integer, db.ForeignKey('area.id'), primary_key=True)
)

class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    nivel = db.Column(db.Integer, nullable=False)

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(200))

class Destaque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # 'semana' ou 'mes'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    foto = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # 'aviso' ou 'noticia'
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(200))
    autor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AreaPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'))
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(200))
    autor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    area = db.relationship('Area')

class PendingUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Gema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Integer, nullable=False)
    icone = db.Column(db.String(200))  # URL do ícone da gema
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)

class CargoGema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    min_gemas = db.Column(db.Integer, nullable=False)  # Mínimo de gemas necessário
    max_gemas = db.Column(db.Integer, nullable=False)  # Máximo de gemas permitido
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    users = db.relationship('User', backref='cargo_gema', foreign_keys='User.cargo_gema_id')
    criador = db.relationship('User', backref='cargos_gemas_criados', foreign_keys=[created_by])

class CargoConfianca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    nivel = db.Column(db.Integer, nullable=False)  # 1 a 5, onde 1 é o mais alto
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    criador = db.relationship('User', backref='cargos_confianca_criados', foreign_keys=[created_by])

class UserGema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gema_id = db.Column(db.Integer, db.ForeignKey('gema.id'))
    quantidade = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='gemas')
    gema = db.relationship('Gema')

# Tabela de associação entre User e CargoConfianca
user_cargos_confianca = db.Table('user_cargos_confianca',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('cargo_confianca_id', db.Integer, db.ForeignKey('cargo_confianca.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    discord = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargo.id'))
    cargo_gema_id = db.Column(db.Integer, db.ForeignKey('cargo_gema.id'))
    cargo = db.relationship('Cargo', backref='users')
    areas = db.relationship('Area', secondary=user_areas, backref='users')
    is_active = db.Column(db.Boolean, default=True)
    destaques_recebidos = db.relationship('Destaque', backref='user', foreign_keys=[Destaque.user_id])
    destaques_dados = db.relationship('Destaque', backref='autor', foreign_keys=[Destaque.created_by])
    noticias = db.relationship('Noticia', backref='autor')
    area_posts = db.relationship('AreaPost', backref='autor')
    pending_approvals = db.relationship('PendingUser', backref='approver')
    gemas_criadas = db.relationship('Gema', backref='criador', foreign_keys=[Gema.created_by])
    total_gemas = db.Column(db.Integer, default=0)  # Total de gemas do usuário
    cargos_confianca = db.relationship('CargoConfianca', secondary=user_cargos_confianca, backref=db.backref('usuarios', lazy='dynamic'))

    def atualizar_cargo_por_gemas(self):
        """Atualiza o cargo do usuário baseado no total de gemas"""
        cargo_atual = CargoGema.query.filter(
            CargoGema.min_gemas <= self.total_gemas,
            CargoGema.max_gemas >= self.total_gemas
        ).first()
        
        if cargo_atual and self.cargo_gema_id != cargo_atual.id:
            self.cargo_gema_id = cargo_atual.id
            db.session.commit()
            return True
        return False

def is_dev_or_admin(user):
    return user and user.cargo and user.cargo.nivel <= CargoNivel.ADMIN

def is_admin_or_above(user):
    """Verifica se o usuário é ADMIN ou superior"""
    return user and user.cargo and user.cargo.nivel <= CargoNivel.ADMIN

def is_red_lider_or_above(user):
    """Verifica se o usuário é RED_LIDER ou superior"""
    return user and user.cargo and user.cargo.nivel <= CargoNivel.RED_LIDER

def has_admin_access(user):
    """Verifica se o usuário tem acesso ao painel administrativo"""
    return user and user.cargo and user.cargo.nivel < CargoNivel.MEMBRO

def can_manage_cargo(admin_user, target_nivel):
    # DEV pode gerenciar qualquer nível
    if admin_user.cargo.nivel == CargoNivel.DEV:
        return True
    # ADMIN só não pode gerenciar DEV
    elif admin_user.cargo.nivel == CargoNivel.ADMIN:
        return target_nivel > CargoNivel.DEV
    return False

def init_db():
    with app.app_context():
        print("Verificando banco de dados...")
        
        # Cria as tabelas apenas se não existirem
        db.create_all()
        
        # Verifica se já existem cargos
        if not Cargo.query.first():
            print("Criando cargos iniciais...")
            cargos = [
                ('DEVS', CargoNivel.DEV),
                ('ADMIN', CargoNivel.ADMIN),
                ('Secretario', CargoNivel.SECRETARIO),
                ('ADM Geral', CargoNivel.ADM_GERAL),
                ('Red Lider', CargoNivel.RED_LIDER),
                ('Braço Direito', CargoNivel.BRACO_DIREITO),
                ('Supervisor', CargoNivel.SUPERVISOR),
                ('Oficial', CargoNivel.OFICIAL),
                ('Membro Normal', CargoNivel.MEMBRO),
                ('Premium', CargoNivel.MEMBRO),
                ('Atiz +18', CargoNivel.MEMBRO)
            ]
            
            for nome, nivel in cargos:
                cargo = Cargo(nome=nome, nivel=nivel)
                db.session.add(cargo)
            
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise
        
        # Verifica se já existem áreas
        if not Area.query.first():
            print("Criando áreas iniciais...")
            areas = [
                'Area +18', 'Eventos', 'Games', 'Marketing', 'Migração',
                'Moderação', 'Monitoramento', 'Mov Call', 'Mov Chat',
                'Mov Sex', 'Perfil', 'Recrutamento', 'Registro', 'Social'
            ]
            
            for nome in areas:
                area = Area(nome=nome)
                db.session.add(area)

        # Verifica se já existem cargos de confiança
        if not CargoConfianca.query.first():
            print("Criando cargos de confiança iniciais...")
            cargos_confianca = [
                ('01', 1),
                ('02', 2),
                ('03', 3),
                ('04', 4),
                ('05', 5)
            ]
            
            for nome, nivel in cargos_confianca:
                cargo = CargoConfianca(nome=nome, nivel=nivel)
                db.session.add(cargo)

        # Criar usuário admin inicial se não existir
        if not User.query.filter_by(username='allef').first():
            print("Criando usuário admin inicial...")
            cargo_dev = Cargo.query.filter_by(nivel=CargoNivel.DEV).first()
            if cargo_dev:
                admin_user = User(
                    username='allef',
                    email='admin@redhot.com',
                    discord='allef#0001',
                    password=generate_password_hash('123'),
                    cargo_id=cargo_dev.id,
                    is_active=True
                )
                db.session.add(admin_user)

        try:
            db.session.commit()
            print("✓ Dados iniciais verificados/criados com sucesso")
        except Exception as e:
            print(f"Erro ao criar dados iniciais: {e}")
            db.session.rollback()
            return

def generate_video_thumbnail(video_path):
    try:
        # Gera o nome do arquivo da thumbnail
        thumbnail_filename = f"thumb_{os.path.basename(video_path).rsplit('.', 1)[0]}.jpg"
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
        
        # Comando FFmpeg para extrair um frame do vídeo (no segundo 1)
        command = [
            'ffmpeg', '-i', video_path,
            '-ss', '00:00:01.000',
            '-vframes', '1',
            thumbnail_path
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        
        # Retorna o caminho relativo da thumbnail
        return f'/static/uploads/{thumbnail_filename}'
    except Exception as e:
        print(f"Erro ao gerar thumbnail: {e}")
        return None

def get_current_user():
    if 'username' not in session:
        return None
    return User.query.filter_by(username=session['username']).first()

@app.route('/')
def home():
    # Buscar destaques
    destaque_semana = Destaque.query.filter_by(tipo='semana').order_by(Destaque.created_at.desc()).first()
    destaque_mes = Destaque.query.filter_by(tipo='mes').order_by(Destaque.created_at.desc()).first()
    
    # Buscar notícias e avisos
    noticias = Noticia.query.order_by(Noticia.created_at.desc()).all()
    
    # Buscar áreas
    areas = Area.query.all()
    
    return render_template('index.html',
                         destaque_semana=destaque_semana,
                         destaque_mes=destaque_mes,
                         noticias=noticias,
                         areas=areas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            session['user_id'] = user.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Usuário ou senha inválidos!', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        discord = request.form.get('discord')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validações
        if not all([username, email, discord, password, confirm_password]):
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('register'))

        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já está em uso.', 'error')
            return redirect(url_for('register'))

        # Verificar se email já existe
        if User.query.filter_by(email=email).first():
            flash('E-mail já está em uso.', 'error')
            return redirect(url_for('register'))

        # Verificar se discord já existe
        if User.query.filter_by(discord=discord).first():
            flash('Discord já está em uso.', 'error')
            return redirect(url_for('register'))

        # Criar novo usuário
        try:
            # Pegar o cargo de Membro Normal
            cargo_membro = Cargo.query.filter_by(nome='Membro Normal').first()
            
            new_user = User(
                username=username,
                email=email,
                discord=discord,
                password=generate_password_hash(password),
                cargo_id=cargo_membro.id if cargo_membro else None,
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {str(e)}', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.clear()
            return redirect(url_for('login'))
        return render_template('dashboard.html', user=user)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        session.clear()
        return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    current_user = get_current_user()
    if not has_admin_access(current_user):
        flash('Você não tem permissão para acessar o painel administrativo.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('admin_dashboard.html', user=current_user)

@app.route('/admin/users')
@login_required
def admin_users():
    current_user = get_current_user()
    if not has_admin_access(current_user):
        flash('Acesso negado', 'error')
        return redirect(url_for('home'))

    # Obter parâmetros de filtro
    username = request.args.get('username', '')
    cargo_id = request.args.get('cargo', type=int)
    cargo_gema_id = request.args.get('cargo_gema', type=int)
    cargo_confianca_id = request.args.get('cargo_confianca', type=int)

    # Query base
    query = User.query

    # Aplicar filtros
    if username:
        query = query.filter(User.username.ilike(f'%{username}%'))
    if cargo_id:
        query = query.filter(User.cargo_id == cargo_id)
    if cargo_gema_id:
        query = query.filter(User.cargo_gema_id == cargo_gema_id)
    if cargo_confianca_id:
        query = query.join(user_cargos_confianca).filter(
            user_cargos_confianca.c.cargo_confianca_id == cargo_confianca_id
        )

    # Ordenar por username
    users = query.order_by(User.username).all()
    
    return render_template('admin_users.html',
        user=current_user,
        users=users,
        cargos=Cargo.query.order_by(Cargo.nivel).all(),
        cargos_gemas=CargoGema.query.filter_by(is_active=True).all(),
        cargos_confianca=CargoConfianca.query.filter_by(is_active=True).all(),
        areas=Area.query.all()
    )

@app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
def admin_edit_user(user_id):
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    target_user = User.query.get_or_404(user_id)
    
    # DEV pode editar qualquer usuário
    if current_user.cargo.nivel == CargoNivel.DEV:
        pass
    # ADMIN só não pode editar DEV
    elif current_user.cargo.nivel == CargoNivel.ADMIN and target_user.cargo.nivel == CargoNivel.DEV:
        flash('Você não tem permissão para editar este usuário!', 'error')
        return redirect(url_for('admin_users'))
    
    # Atualiza cargo hierárquico
    cargo_id = request.form.get('cargo')
    if cargo_id:
        new_cargo = Cargo.query.get(cargo_id)
        if new_cargo and can_manage_cargo(current_user, new_cargo.nivel):
            target_user.cargo_id = cargo_id
    
    # Atualiza cargo de confiança
    cargo_confianca_id = request.form.get('cargo_confianca')
    if cargo_confianca_id:
        target_user.cargo_confianca_id = cargo_confianca_id
    
    # Atualiza áreas
    area_ids = request.form.getlist('areas')
    if area_ids:
        target_user.areas = Area.query.filter(Area.id.in_(area_ids)).all()
    
    # Atualiza senha se fornecida
    new_password = request.form.get('password')
    if new_password:
        target_user.password = generate_password_hash(new_password)
    
    target_user.is_active = 'is_active' in request.form
    
    try:
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/make_dev/<username>')
def make_dev(username):
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            cargo_dev = Cargo.query.filter_by(nivel=CargoNivel.DEV).first()
            if cargo_dev:
                user.cargo = cargo_dev
                db.session.commit()
                flash('Usuário promovido a DEV com sucesso!', 'success')
            else:
                flash('Cargo DEV não encontrado!', 'error')
        else:
            flash('Usuário não encontrado!', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao promover usuário: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/dev_allef')
def dev_allef():
    try:
        user = User.query.filter_by(username='allef').first()
        if user:
            cargo_dev = Cargo.query.filter_by(nivel=CargoNivel.DEV).first()
            if cargo_dev:
                user.cargo = cargo_dev
                db.session.commit()
                flash('Conta promovida para DEV com sucesso!', 'success')
            else:
                flash('Cargo DEV não encontrado!', 'error')
        else:
            flash('Usuário não encontrado!', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao promover usuário: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

# Gerenciamento de Aprovações
@app.route('/admin/approvals')
def admin_approvals():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    pending_users = PendingUser.query.filter_by(status='pending').all()
    return render_template('admin_approvals.html', user=current_user, pending_users=pending_users)

@app.route('/admin/approve_user/<int:user_id>/<action>')
def approve_user(user_id, action):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    pending_user = PendingUser.query.get_or_404(user_id)
    
    if action == 'approve':
        new_user = User(
            username=pending_user.username,
            password=pending_user.password,
            cargo=Cargo.query.filter_by(nivel=CargoNivel.MEMBRO).first()
        )
        db.session.add(new_user)
        pending_user.status = 'approved'
        pending_user.approved_by = current_user.id
        flash('Usuário aprovado com sucesso!', 'success')
    else:
        pending_user.status = 'rejected'
        pending_user.approved_by = current_user.id
        flash('Usuário rejeitado!', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_approvals'))

# Gerenciamento de Destaques
@app.route('/admin/destaques')
def admin_destaques():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    destaques_semana = Destaque.query.filter_by(tipo='semana').order_by(Destaque.created_at.desc()).first()
    destaques_mes = Destaque.query.filter_by(tipo='mes').order_by(Destaque.created_at.desc()).first()
    users = User.query.all()
    
    return render_template('admin_destaques.html', 
                         user=current_user,
                         destaque_semana=destaques_semana,
                         destaque_mes=destaques_mes,
                         users=users)

@app.route('/admin/add_destaque', methods=['POST'])
def add_destaque():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    tipo = request.form.get('tipo')
    user_id = request.form.get('user_id')
    
    # Processar upload da foto
    foto_path = None
    if 'foto' in request.files:
        foto = request.files['foto']
        foto_path = save_file(foto)
    
    destaque = Destaque(
        tipo=tipo,
        user_id=user_id,
        foto=foto_path,
        created_by=current_user.id
    )
    
    db.session.add(destaque)
    db.session.commit()
    
    flash('Destaque adicionado com sucesso!', 'success')
    return redirect(url_for('admin_destaques'))

# Gerenciamento de Notícias
@app.route('/admin/noticias')
def admin_noticias():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    noticias = Noticia.query.order_by(Noticia.created_at.desc()).all()
    return render_template('admin_noticias.html', user=current_user, noticias=noticias)

@app.route('/admin/add_noticia', methods=['POST'])
def add_noticia():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Processar upload da foto
    foto_path = None
    if 'foto' in request.files:
        foto = request.files['foto']
        foto_path = save_file(foto)
    
    noticia = Noticia(
        tipo=request.form.get('tipo'),
        titulo=request.form.get('titulo'),
        descricao=request.form.get('descricao'),
        foto=foto_path,
        autor_id=current_user.id
    )
    
    db.session.add(noticia)
    db.session.commit()
    
    flash('Notícia/Aviso adicionado com sucesso!', 'success')
    return redirect(url_for('admin_noticias'))

# Gerenciamento de Áreas
@app.route('/admin/areas')
def admin_areas():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    areas = Area.query.all()
    return render_template('admin_areas.html', user=current_user, areas=areas)

@app.route('/admin/area/<int:area_id>')
def admin_area(area_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    area = Area.query.get_or_404(area_id)
    
    return render_template('admin_area_detail.html', user=current_user, area=area)

# Rota para gerenciar membros da área (apenas RED_LIDER ou superior)
@app.route('/admin/area/members/<int:area_id>', methods=['POST'])
def manage_area_members(area_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if current_user.cargo.nivel > 5:  # Se não for RED_LIDER ou superior
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_areas'))

    area = Area.query.get_or_404(area_id)
    action = request.form.get('action')
    member_id = request.form.get('member_id')

    if not action or not member_id:
        flash('Dados inválidos.', 'error')
        return redirect(url_for('admin_area_members', area_id=area.id))

    user = User.query.get_or_404(member_id)

    if action == 'add':
        if user not in area.users:
            area.users.append(user)
            db.session.commit()
            flash(f'{user.username} adicionado à área com sucesso!', 'success')
        else:
            flash(f'{user.username} já é membro desta área.', 'error')

    elif action == 'remove':
        if user in area.users:
            area.users.remove(user)
            db.session.commit()
            flash(f'{user.username} removido da área com sucesso!', 'success')
        else:
            flash(f'{user.username} não é membro desta área.', 'error')

    return redirect(url_for('admin_area_members', area_id=area.id))

@app.route('/admin/area/<int:area_id>/post', methods=['POST'])
def add_area_post(area_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not is_red_lider_or_above(user):
        abort(403)
    
    # Processar upload da foto
    foto_path = None
    if 'foto' in request.files:
        foto = request.files['foto']
        foto_path = save_file(foto)
    
    post = AreaPost(
        area_id=area_id,
        titulo=request.form.get('titulo'),
        descricao=request.form.get('descricao'),
        foto=foto_path,
        autor_id=user.id
    )
    
    db.session.add(post)
    db.session.commit()
    
    flash('Post adicionado com sucesso!', 'success')
    return redirect(url_for('admin_area', area_id=area_id))

@app.route('/admin/remove_destaque/<int:destaque_id>')
def remove_destaque(destaque_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    destaque = Destaque.query.get_or_404(destaque_id)
    
    # Remover foto se existir
    if destaque.foto and os.path.exists(os.path.join('static', destaque.foto.lstrip('/'))):
        os.remove(os.path.join('static', destaque.foto.lstrip('/')))
    
    db.session.delete(destaque)
    db.session.commit()
    
    flash('Destaque removido com sucesso!', 'success')
    return redirect(url_for('admin_destaques'))

@app.route('/admin/remove_noticia/<int:noticia_id>')
def remove_noticia(noticia_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    noticia = Noticia.query.get_or_404(noticia_id)
    
    # Remover foto se existir
    if noticia.foto and os.path.exists(os.path.join('static', noticia.foto.lstrip('/'))):
        os.remove(os.path.join('static', noticia.foto.lstrip('/')))
    
    db.session.delete(noticia)
    db.session.commit()
    
    flash('Notícia/Aviso removido com sucesso!', 'success')
    return redirect(url_for('admin_noticias'))

# Rota para visualizar membros da área
@app.route('/admin/area/<int:area_id>/members')
def admin_area_members(area_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    area = Area.query.get_or_404(area_id)
    users = User.query.all()
    return render_template('admin_area_members.html', user=current_user, area=area, users=users)

# Rota para visualizar posts da área
@app.route('/admin/area/<int:area_id>/posts')
def admin_area_posts(area_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if current_user.cargo.nivel > 5:  # Se não for RED_LIDER ou superior
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_areas'))
    
    area = Area.query.get_or_404(area_id)
    users = User.query.all()  # Para o select de adicionar membros
    posts = AreaPost.query.filter_by(area_id=area_id).order_by(AreaPost.created_at.desc()).all()
    
    return render_template('admin_area_posts.html', user=current_user, area=area, users=users, posts=posts)

# Rota para adicionar post na área (apenas RED_LIDER ou superior)
@app.route('/admin/area/<int:area_id>/add_post/<tipo>', methods=['GET', 'POST'])
def add_area_post_new(area_id, tipo):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if current_user.cargo.nivel > 5:  # Se não for RED_LIDER ou superior
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_areas'))

    area = Area.query.get_or_404(area_id)
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        foto = request.files.get('foto')
        video = request.files.get('video') if tipo in ['videos', 'premium'] else None

        if not titulo or not descricao:
            flash('Título e descrição são obrigatórios.', 'error')
            return redirect(url_for('add_area_post_new', area_id=area.id, tipo=tipo))

        # Processar upload de vídeo e gerar thumbnail
        video_url = None
        foto_url = None
        if video and video.filename != '':
            video_url = save_file(video)
            if not video_url:
                flash('Erro ao fazer upload do vídeo. Verifique o formato e tamanho.', 'error')
                return redirect(url_for('add_area_post_new', area_id=area.id, tipo=tipo))
                
            # Gera thumbnail do vídeo se não foi fornecida uma foto
            if not foto or foto.filename == '':
                video_path = os.path.join(os.getcwd(), video_url.lstrip('/'))
                foto_url = generate_video_thumbnail(video_path)
        
        # Se foi enviada uma foto, usa ela ao invés da thumbnail gerada
        if foto and foto.filename != '':
            foto_url = save_file(foto)
            if not foto_url:
                flash('Erro ao fazer upload da imagem. Verifique o formato e tamanho.', 'error')
                return redirect(url_for('add_area_post_new', area_id=area.id, tipo=tipo))

        # Adiciona informação do tipo no título se for área +18
        if area.nome == 'Area +18':
            titulo_completo = f"[{tipo.upper()}] {titulo}"
        else:
            titulo_completo = titulo
        
        # Adiciona link do vídeo na descrição se for um post de vídeo
        if video_url:
            descricao = f"{descricao}\n\nVídeo: {video_url}"

        post = AreaPost(
            area_id=area.id,
            titulo=titulo_completo,
            descricao=descricao,
            foto=foto_url,
            autor_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post adicionado com sucesso!', 'success')
        
        # Redireciona para a página correta baseado na área
        if area.nome == 'Area +18':
            return redirect(url_for('area_18'))
        else:
            return redirect(url_for('area_posts', area_id=area.id))

    return render_template('add_area_post_new.html', area=area, tipo=tipo, user=current_user)

# Rota para remover post da área (apenas RED_LIDER ou superior)
@app.route('/admin/area/post/<int:post_id>/remove', methods=['POST'])
def remove_area_post(post_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if current_user.cargo.nivel > 5:  # Se não for RED_LIDER ou superior
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_areas'))

    post = AreaPost.query.get_or_404(post_id)
    area_id = post.area_id

    # Remove a foto se existir
    if post.foto:
        try:
            filename = post.foto.split('/')[-1]
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        except:
            pass  # Se houver erro ao remover o arquivo, apenas ignora

    db.session.delete(post)
    db.session.commit()

    flash('Post removido com sucesso!', 'success')
    return redirect(url_for('admin_area_posts', area_id=area_id))

@app.route('/admin/user/<int:user_id>/areas', methods=['POST'])
def admin_edit_user_areas(user_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user or current_user.cargo.nivel > 2:  # Apenas DEV e ADMIN podem editar
        flash('Você não tem permissão para editar usuários.', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    areas_ids = request.form.getlist('areas[]', type=int)
    
    # Remove todas as áreas atuais
    user.areas = []
    
    # Adiciona as áreas selecionadas
    if areas_ids:
        areas = Area.query.filter(Area.id.in_(areas_ids)).all()
        user.areas.extend(areas)
    
    db.session.commit()
    flash('Áreas do usuário atualizadas com sucesso!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/profile', methods=['POST'])
def admin_edit_user_profile(user_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user or current_user.cargo.nivel > 2:  # Apenas DEV e ADMIN podem editar
        flash('Você não tem permissão para editar usuários.', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    new_username = request.form.get('username')
    new_password = request.form.get('password')
    
    # Verifica se o novo username já existe
    if new_username != user.username and User.query.filter_by(username=new_username).first():
        flash('Este nome de usuário já está em uso.', 'error')
        return redirect(url_for('admin_users'))
    
    user.username = new_username
    if new_password:  # Só atualiza a senha se uma nova foi fornecida
        user.password = generate_password_hash(new_password)
    
    db.session.commit()
    flash('Perfil do usuário atualizado com sucesso!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/area/<int:area_id>/remove', methods=['POST'])
def remove_area(area_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user or user.cargo.nivel > 2:
        flash('Apenas usuários DEV podem remover áreas.', 'error')
        return redirect(url_for('admin_areas'))
    
    area = Area.query.get_or_404(area_id)
    
    # Remove todos os usuários da área
    for user in area.users:
        area.users.remove(user)
    
    # Remove todos os posts da área e suas fotos/vídeos
    posts = AreaPost.query.filter_by(area_id=area_id).all()
    for post in posts:
        if post.foto:
            try:
                filename = post.foto.split('/')[-1]
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except:
                pass
    AreaPost.query.filter_by(area_id=area_id).delete()
    
    # Remove a área
    db.session.delete(area)
    db.session.commit()
    
    flash('Área removida com sucesso!', 'success')
    return redirect(url_for('admin_areas'))

@app.route('/admin/area/add', methods=['POST'])
def add_area():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user or current_user.cargo.nivel > 2:  # Apenas DEV pode adicionar
        flash('Você não tem permissão para adicionar áreas.', 'error')
        return redirect(url_for('admin_areas'))
    
    nome = request.form.get('nome')
    if not nome:
        flash('Nome da área é obrigatório.', 'error')
        return redirect(url_for('admin_areas'))
    
    # Criar a área
    area = Area(nome=nome)
    db.session.add(area)
    
    # Criar o cargo correspondente à área
    cargo_nome = f"RED {nome}"  # Ex: "RED Games", "RED Marketing", etc.
    if not Cargo.query.filter_by(nome=cargo_nome).first():
        cargo = Cargo(nome=cargo_nome, nivel=5)  # Nível 5 = RED_LIDER
        db.session.add(cargo)
    
    try:
        db.session.commit()
        flash('Área e cargo criados com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao criar área e cargo. Verifique se já não existem.', 'error')
    
    return redirect(url_for('admin_areas'))

@app.route('/age-verification', methods=['GET', 'POST'])
def age_verification():
    if request.method == 'POST':
        session['age_verified'] = True
        return redirect(url_for('area_18'))
    return render_template('age_verification.html')

@app.route('/area-18')
def area_18():
    if 'age_verified' not in session:
        return redirect(url_for('age_verification'))
        
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta área.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    # Buscar todos os posts da área +18
    area = Area.query.filter_by(nome='Area +18').first()
    if not area:
        flash('Área +18 não encontrada.', 'error')
        return redirect(url_for('home'))
    
    posts = AreaPost.query.filter_by(area_id=area.id).order_by(AreaPost.created_at.desc()).all()
    
    return render_template('area_18.html', user=user, posts=posts)

@app.route('/area-18/fotos')
def area_18_fotos():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta área.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    # Verificar se o usuário tem permissão (Premium ou Atiz +18)
    if not user.cargo or user.cargo.nome not in ['Premium', 'Atiz +18', 'DEVS', 'ADMIN']:
        flash('Você não tem permissão para acessar esta área.', 'error')
        return redirect(url_for('home'))
    
    area = Area.query.filter_by(nome='Area +18').first()
    if not area:
        flash('Área +18 não encontrada.', 'error')
        return redirect(url_for('home'))
    
    posts = AreaPost.query.filter(
        AreaPost.area_id == area.id,
        AreaPost.titulo.like('[FOTOS]%')
    ).order_by(AreaPost.created_at.desc()).all()
    
    return render_template('area_18_fotos.html', user=user, posts=posts)

@app.route('/area-18/videos')
def area_18_videos():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta área.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    # Verificar se o usuário tem permissão (Premium ou Atiz +18)
    if not user.cargo or user.cargo.nome not in ['Premium', 'Atiz +18', 'DEVS', 'ADMIN']:
        flash('Você não tem permissão para acessar esta área.', 'error')
        return redirect(url_for('home'))
    
    area = Area.query.filter_by(nome='Area +18').first()
    if not area:
        flash('Área +18 não encontrada.', 'error')
        return redirect(url_for('home'))
    
    posts = AreaPost.query.filter(
        AreaPost.area_id == area.id,
        AreaPost.titulo.like('[VIDEOS]%')
    ).order_by(AreaPost.created_at.desc()).all()
    
    return render_template('area_18_videos.html', user=user, posts=posts)

@app.route('/area-18/comunidade')
def area_18_comunidade():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta área.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    # Verificar se o usuário tem permissão (Premium ou Atiz +18)
    if not user.cargo or user.cargo.nome not in ['Premium', 'Atiz +18', 'DEVS', 'ADMIN']:
        flash('Você não tem permissão para acessar esta área.', 'error')
        return redirect(url_for('home'))
    
    area = Area.query.filter_by(nome='Area +18').first()
    if not area:
        flash('Área +18 não encontrada.', 'error')
        return redirect(url_for('home'))
    
    posts = AreaPost.query.filter(
        AreaPost.area_id == area.id,
        AreaPost.titulo.like('[COMUNIDADE]%')
    ).order_by(AreaPost.created_at.desc()).all()
    
    return render_template('area_18_comunidade.html', user=user, posts=posts)

@app.route('/area-18/premium')
def area_18_premium():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta área.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    # Verificar se o usuário tem permissão (Premium ou Atiz +18)
    if not user.cargo or user.cargo.nome not in ['Premium', 'Atiz +18', 'DEVS', 'ADMIN']:
        flash('Você precisa ter a tag Premium ou Atriz +18 para acessar esta área.', 'error')
        return redirect(url_for('area_18'))
    
    area = Area.query.filter_by(nome='Area +18').first()
    if not area:
        flash('Área +18 não encontrada.', 'error')
        return redirect(url_for('home'))
    
    posts = AreaPost.query.filter(
        AreaPost.area_id == area.id,
        AreaPost.titulo.like('[PREMIUM]%')
    ).order_by(AreaPost.created_at.desc()).all()
    
    return render_template('area_18_premium.html', user=user, posts=posts)

@app.route('/area/<int:area_id>/posts')
def area_posts(area_id):
    area = Area.query.get_or_404(area_id)
    posts = AreaPost.query.filter_by(area_id=area_id).order_by(AreaPost.created_at.desc()).all()
    return render_template('area_posts.html', area=area, posts=posts)

@app.route('/admin/area/<int:area_id>/clear_posts', methods=['POST'])
def clear_area_posts(area_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    if not current_user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
    
    if current_user.cargo.nivel > 5:  # Se não for RED_LIDER ou superior
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_areas'))

    area = Area.query.get_or_404(area_id)
    
    # Não permitir limpar a Área +18
    if area.nome == 'Area +18':
        flash('Não é permitido limpar a Área +18.', 'error')
        return redirect(url_for('admin_area_posts', area_id=area_id))
    
    # Remove todos os posts e suas fotos
    posts = AreaPost.query.filter_by(area_id=area_id).all()
    for post in posts:
        if post.foto:
            try:
                filename = post.foto.split('/')[-1]
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except:
                pass  # Se houver erro ao remover arquivo, apenas ignora
    
    # Remove todos os posts da área
    AreaPost.query.filter_by(area_id=area_id).delete()
    db.session.commit()
    
    flash('Todos os posts foram removidos com sucesso!', 'success')
    return redirect(url_for('admin_area_posts', area_id=area_id))

@app.route('/admin/area/<int:area_id>/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_area_post(area_id, post_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        session.clear()
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('login'))
        
    area = Area.query.get_or_404(area_id)
    post = AreaPost.query.get_or_404(post_id)
    
    # Verifica se o usuário tem cargo de Red Lider ou superior (nível <= 5)
    if not user.cargo or user.cargo.nivel > CargoNivel.RED_LIDER:
        flash('Você precisa ter cargo de Red Lider ou superior para editar posts.', 'error')
        return redirect(url_for('admin_area_posts', area_id=area_id))
        
    if request.method == 'POST':
        post.titulo = request.form.get('titulo')
        post.descricao = request.form.get('descricao')
        
        nova_foto = request.files.get('nova_foto')
        if nova_foto and allowed_file(nova_foto.filename):
            # Se houver uma foto antiga, exclui
            if post.foto:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.foto))
                except:
                    pass
                    
            # Salva a nova foto
            filename = secure_filename(nova_foto.filename)
            nova_foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post.foto = filename
            
        db.session.commit()
        flash('Post atualizado com sucesso!', 'success')
        return redirect(url_for('admin_area_posts', area_id=area_id))
        
    return render_template('edit_area_post.html', user=user, area=area, post=post)

@app.route('/admin/area/<int:area_id>/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_area_post(area_id, post_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Você precisa estar logado.'})
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'})

    if not user.cargo or user.cargo.nivel > CargoNivel.ADMIN:
        return jsonify({'success': False, 'message': 'Você não tem permissão para excluir posts.'})
        
    post = AreaPost.query.get_or_404(post_id)
    
    # Exclui a foto se existir
    if post.foto:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post.foto))
        except:
            pass
            
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'success': True})

# Gerenciamento de Gemas
@app.route('/admin/gemas')
@login_required
def admin_gemas():
    current_user = get_current_user()
    if not is_red_lider_or_above(current_user):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    users = User.query.all()
    return render_template('admin_gemas_usuarios.html', user=current_user, users=users)

@app.route('/admin/gema/add', methods=['POST'])
@login_required
def add_gema():
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para realizar esta ação.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    valor = request.form.get('valor')
    
    if not nome or not valor:
        flash('Nome e valor são obrigatórios.', 'error')
        return redirect(url_for('admin_gemas'))
    
    # Processar upload do ícone
    icone_path = None
    if 'icone' in request.files:
        icone = request.files['icone']
        icone_path = save_file(icone)
    
    gema = Gema(
        nome=nome,
        descricao=descricao,
        valor=valor,
        icone=icone_path,
        created_by=current_user.id
    )
    
    db.session.add(gema)
    db.session.commit()
    
    flash('Gema adicionada com sucesso!', 'success')
    return redirect(url_for('admin_gemas'))

@app.route('/admin/gema/<int:gema_id>/delete', methods=['POST'])
@login_required
def delete_gema(gema_id):
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão'})
    
    gema = Gema.query.get_or_404(gema_id)
    
    # Remover ícone se existir
    if gema.icone and os.path.exists(os.path.join('static', gema.icone.lstrip('/'))):
        os.remove(os.path.join('static', gema.icone.lstrip('/')))
    
    db.session.delete(gema)
    db.session.commit()
    
    return jsonify({'success': True})

# Rotas para Gerenciamento de Cargos por Gemas
@app.route('/admin/cargos_gemas')
@login_required
def admin_cargos_gemas():
    current_user = get_current_user()
    if not is_admin_or_above(current_user):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    cargos = CargoGema.query.order_by(CargoGema.min_gemas).all()
    return render_template('admin_cargos_gemas.html', user=current_user, cargos=cargos)

@app.route('/admin/cargo_gema/add', methods=['POST'])
@login_required
def add_cargo_gema():
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão'})
    
    nome = request.form.get('nome')
    min_gemas = request.form.get('min_gemas', type=int)
    max_gemas = request.form.get('max_gemas', type=int)
    
    if not nome or min_gemas is None or max_gemas is None:
        return jsonify({'success': False, 'message': 'Dados incompletos'})
    
    cargo = CargoGema(
        nome=nome,
        min_gemas=min_gemas,
        max_gemas=max_gemas,
        created_by=current_user.id
    )
    
    db.session.add(cargo)
    db.session.commit()
    
    # Atualiza os cargos dos usuários
    users = User.query.filter(
        User.total_gemas >= min_gemas,
        User.total_gemas <= max_gemas
    ).all()
    
    for user in users:
        user.atualizar_cargo_por_gemas()
    
    return jsonify({'success': True})

@app.route('/admin/cargo_gema/<int:cargo_id>/delete', methods=['POST'])
@login_required
def delete_cargo_gema(cargo_id):
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão'})
    
    cargo = CargoGema.query.get_or_404(cargo_id)
    
    # Remove o cargo dos usuários
    User.query.filter_by(cargo_gema_id=cargo_id).update({User.cargo_gema_id: None})
    
    db.session.delete(cargo)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/cargo_gema/<int:cargo_id>/edit', methods=['POST'])
@login_required
def edit_cargo_gema(cargo_id):
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão'})
    
    cargo = CargoGema.query.get_or_404(cargo_id)
    
    nome = request.form.get('nome')
    min_gemas = request.form.get('min_gemas', type=int)
    max_gemas = request.form.get('max_gemas', type=int)
    
    if not nome or min_gemas is None or max_gemas is None:
        return jsonify({'success': False, 'message': 'Dados incompletos'})
    
    if min_gemas > max_gemas:
        return jsonify({'success': False, 'message': 'O mínimo de gemas não pode ser maior que o máximo'})
    
    cargo.nome = nome
    cargo.min_gemas = min_gemas
    cargo.max_gemas = max_gemas
    
    try:
        db.session.commit()
        
        # Atualiza os cargos dos usuários afetados pela mudança
        users = User.query.filter(
            (User.total_gemas >= min_gemas) & (User.total_gemas <= max_gemas) |
            (User.cargo_gema_id == cargo_id)
        ).all()
        
        for user in users:
            user.atualizar_cargo_por_gemas()
        
        return jsonify({
            'success': True,
            'message': 'Cargo atualizado com sucesso',
            'cargo': {
                'id': cargo.id,
                'nome': cargo.nome,
                'min_gemas': cargo.min_gemas,
                'max_gemas': cargo.max_gemas
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Rotas para Gerenciamento de Cargos de Confiança
@app.route('/admin/cargos_confianca')
@login_required
def admin_cargos_confianca():
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    cargos = CargoConfianca.query.order_by(CargoConfianca.nivel).all()
    return render_template('admin_cargos_confianca.html', user=current_user, cargos=cargos)

@app.route('/admin/cargo_confianca/add', methods=['POST'])
@login_required
def add_cargo_confianca():
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão'})
    
    nome = request.form.get('nome')
    nivel = request.form.get('nivel', type=int)
    
    if not nome or nivel is None or nivel < 1 or nivel > 5:
        return jsonify({'success': False, 'message': 'Dados inválidos'})
    
    cargo = CargoConfianca(
        nome=nome,
        nivel=nivel,
        created_by=current_user.id
    )
    
    db.session.add(cargo)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/cargo_confianca/<int:cargo_id>/delete', methods=['POST'])
@login_required
def delete_cargo_confianca(cargo_id):
    current_user = get_current_user()
    if not is_dev_or_admin(current_user):
        return jsonify({'success': False, 'message': 'Sem permissão'})
    
    cargo = CargoConfianca.query.get_or_404(cargo_id)
    
    # Remove o cargo dos usuários
    User.query.filter_by(cargo_confianca_id=cargo_id).update({User.cargo_confianca_id: None})
    
    db.session.delete(cargo)
    db.session.commit()
    
    return jsonify({'success': True})

# Rotas para Gerenciamento de Gemas dos Usuários
@app.route('/admin/user/<int:user_id>/add_gemas', methods=['POST'])
@login_required
def add_user_gemas(user_id):
    current_user = get_current_user()
    if not has_admin_access(current_user):
        return jsonify({'success': False, 'message': 'Acesso negado'})

    user = User.query.get_or_404(user_id)
    try:
        # Tentar pegar quantidade do JSON ou do form data
        if request.is_json:
            quantidade = request.json.get('quantidade', 1)
        else:
            quantidade = request.form.get('quantidade', 1, type=int)

        if not isinstance(quantidade, int) or quantidade < 1:
            return jsonify({'success': False, 'message': 'Quantidade inválida'})

        user.total_gemas += quantidade
        user.atualizar_cargo_por_gemas()
        db.session.commit()
        return jsonify({'success': True, 'total_gemas': user.total_gemas})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/user/<int:user_id>/remove_gemas', methods=['POST'])
@login_required
def remove_user_gemas(user_id):
    current_user = get_current_user()
    if not has_admin_access(current_user):
        return jsonify({'success': False, 'message': 'Acesso negado'})

    user = User.query.get_or_404(user_id)
    try:
        # Tentar pegar quantidade do JSON ou do form data
        if request.is_json:
            quantidade = request.json.get('quantidade', 1)
        else:
            quantidade = request.form.get('quantidade', 1, type=int)

        if not isinstance(quantidade, int) or quantidade < 1:
            return jsonify({'success': False, 'message': 'Quantidade inválida'})

        if user.total_gemas >= quantidade:
            user.total_gemas -= quantidade
            user.atualizar_cargo_por_gemas()
            db.session.commit()
            return jsonify({'success': True, 'total_gemas': user.total_gemas})
        else:
            return jsonify({'success': False, 'message': f'Usuário possui apenas {user.total_gemas} gemas'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/user/<int:user_id>/toggle_status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    current_user = get_current_user()
    if not has_admin_access(current_user):
        return jsonify({'success': False, 'message': 'Acesso negado'})

    user = User.query.get_or_404(user_id)
    try:
        data = request.get_json()
        user.is_active = data.get('is_active', True)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/get_user/<int:user_id>')
@login_required
def get_user(user_id):
    current_user = get_current_user()
    if not has_admin_access(current_user):
        return jsonify({'success': False, 'message': 'Acesso negado'})

    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'cargo_id': user.cargo_id,
        'cargo_gema_id': user.cargo_gema_id,
        'cargos_confianca': [cargo.id for cargo in user.cargos_confianca],
        'total_gemas': user.total_gemas,
        'areas': [area.id for area in user.areas],
        'is_active': user.is_active
    })

@app.route('/admin/user/<int:user_id>/update_cargo', methods=['POST'])
@login_required
def update_user_cargo(user_id):
    current_user = get_current_user()
    if not has_admin_access(current_user):
        return jsonify({'success': False, 'message': 'Acesso negado'})

    user = User.query.get_or_404(user_id)
    
    # Verificar se o usuário atual pode gerenciar o cargo do usuário alvo
    if not can_manage_cargo(current_user, user.cargo.nivel if user.cargo else 999):
        return jsonify({'success': False, 'message': 'Você não tem permissão para gerenciar este usuário'})

    try:
        # Atualizar cargo hierárquico
        cargo_id = request.form.get('cargo_id', type=int)
        if cargo_id:
            cargo = Cargo.query.get(cargo_id)
            if not cargo:
                return jsonify({'success': False, 'message': 'Cargo inválido'})
            user.cargo_id = cargo_id

        # Atualizar cargo por gemas
        cargo_gema_id = request.form.get('cargo_gema_id', type=int)
        if cargo_gema_id:
            cargo_gema = CargoGema.query.get(cargo_gema_id)
            if not cargo_gema:
                return jsonify({'success': False, 'message': 'Cargo por gemas inválido'})
            user.cargo_gema_id = cargo_gema_id

        # Atualizar cargos de confiança
        cargos_confianca_ids = request.form.getlist('cargos_confianca')
        if cargos_confianca_ids:
            cargos_confianca = CargoConfianca.query.filter(
                CargoConfianca.id.in_(cargos_confianca_ids),
                CargoConfianca.is_active == True
            ).all()
            user.cargos_confianca = cargos_confianca

        # Atualizar áreas
        areas = request.form.getlist('areas')
        if areas:
            user.areas = Area.query.filter(Area.id.in_(areas)).all()

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Registrar funções auxiliares para os templates
@app.context_processor
def utility_processor():
    return {
        'is_red_lider_or_above': is_red_lider_or_above,
        'is_dev_or_admin': is_dev_or_admin,
        'has_admin_access': has_admin_access,
        'can_manage_cargo': can_manage_cargo,
        'is_admin_or_above': is_admin_or_above  # Adicionando a função is_admin_or_above
    }

# Inicialização do banco de dados
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("\n=== Servidor Pronto ===")
    print("Iniciando na porta 5000...")
    print("Acesse: http://127.0.0.1:5000")
    print("Pressione CTRL+C para parar o servidor")
    print("===============================")
    app.run(host='0.0.0.0', port=5000, debug=True)



