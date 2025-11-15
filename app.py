# Importação dos bibliotecas
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# Configuração da aplicação e do banco do dados
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    # Observar esta linha que pede login, senha e banco de dados
    'mysql+pymysql://root:root@localhost:3306/espetinho?charset=utf8mb4')
db = SQLAlchemy(app)


# Modelagem das classes
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(14), unique=True)
    email = db.Column(db.String(255))
    telefone = db.Column(db.String(20))

class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)


# Função que ativa o login da aplicação
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper



@app.route('/index')
@login_required
def index():
    return render_template('index.html', show_menu=True)

# Cadastro do clietes
@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes_view():
    if request.method == 'POST':
        # Recuperando os dados do formulário
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        # Validação do nome do usuário
        if not nome:
            flash('Informe o nome do cliente.', 'danger')
        else:
            try:
                # Criação do objeto c, para inserção no banco de dados
                c = Cliente(nome=nome, cpf=cpf or None, email=email or None, telefone=telefone or None)
                db.session.add(c)
                db.session.commit()
                flash('Cliente cadastrado.', 'success')
                return redirect(url_for('clientes_view'))
            except IntegrityError:
                db.session.rollback()
                flash('Erro ao cadastrar cliente.', 'danger')
    # Recupera os dados do cliente para exibir na tabela abaixo do formulário
    clientes = db.session.execute(db.select(Cliente).order_by(Cliente.id.desc())).scalars().all()
    return render_template('clientes.html', show_menu=True, clientes=clientes)


# Cadastro do usuário - Funcionário do espetinho
@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios_view():
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password_val = request.form.get('password', '')
        if not login_val or not password_val:
            flash('Informe login e senha.', 'danger')
        else:
            exists = db.session.execute(db.select(Usuario).filter_by(login=login_val)).scalar_one_or_none()
            if exists:
                flash('Login já utilizado.', 'warning')
            else:
                try:
                    u = Usuario(login=login_val, password=password_val)
                    db.session.add(u)
                    db.session.commit()
                    flash('Usuário cadastrado.', 'success')
                    return redirect(url_for('usuarios_view'))
                except IntegrityError:
                    db.session.rollback()
                    flash('Erro ao cadastrar usuário.', 'danger')
    # Recupera os dados do usuário para login
    usuarios = db.session.execute(db.select(Usuario).order_by(Usuario.id.desc())).scalars().all()
    return render_template('usuarios.html', show_menu=True, usuarios=usuarios)

# Cadastro do espetinho
@app.route('/produtos', methods=['GET', 'POST'])
@login_required
def produtos_view():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        preco_raw = request.form.get('preco', '').strip()
        if not nome or not preco_raw:
            flash('Informe nome e preço do espetinho.', 'danger')
        else:
            try:
                preco_val = float(preco_raw)
                p = Produto(nome=nome, preco=preco_val)
                db.session.add(p)
                db.session.commit()
                flash('Espetinho cadastrado.', 'success')
                return redirect(url_for('produtos_view'))
            except ValueError:
                flash('Preço inválido.', 'danger')
            except IntegrityError:
                db.session.rollback()
                flash('Erro ao cadastrar espetinho.', 'danger')
    # Recupera os dados do espetinho para mostrar na tabela abaixo do formulário
    produtos = db.session.execute(db.select(Produto).order_by(Produto.id.desc())).scalars().all()
    return render_template('produtos.html', show_menu=True, produtos=produtos)


@app.route('/bebidas', methods=['GET', 'POST'])
@login_required
def bebidas_view():
    return render_template('bebidas.html', show_menu=True)


@app.route('/pedidos', methods=['GET', 'POST'])
@login_required
def pedidos_view():
    return render_template('pedidos.html', show_menu=True)


# Rota de login, que valida as credenciais do usuário
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password_val = request.form.get('password', '')
        if not login_val or not password_val:
            flash('Informe login e senha.', 'danger')
            return render_template('login.html', show_menu=False)
        row = db.session.execute(db.select(Usuario).filter_by(login=login_val)).scalar_one_or_none()
        if not row or row.password != password_val:
            flash('Credenciais inválidas.', 'danger')
            return render_template('login.html', show_menu=False)
        session['user_id'] = row.id
        session['user_login'] = row.login
        flash('Login efetuado.', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', show_menu=False)

# Logout da aplicação
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    flash('Sessão encerrada.', 'success')
    return redirect(url_for('login'))

# Cadastro do usuário do espetinho
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password_val = request.form.get('password', '')
        if not login_val or not password_val:
            flash('Informe login e senha.', 'danger')
            return render_template('registro.html', show_menu=False)
        exists = db.session.execute(db.select(Usuario).filter_by(login=login_val)).scalar_one_or_none()
        if exists:
            flash('Login já utilizado.', 'warning')
            return render_template('registro.html', show_menu=False)
        u = Usuario(login=login_val, password=password_val)
        db.session.add(u)
        db.session.commit()
        flash('Usuário cadastrado. Faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html', show_menu=False)

# Verifica se o arquivo é o principal do projeto
if __name__ == '__main__':
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5600'))
    app.run(host=host, port=port, debug=True)
