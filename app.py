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

class Bebida(db.Model):
    __tablename__ = 'bebida'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    tamanho = db.Column(db.String(50))
    preco = db.Column(db.Numeric(10, 2), nullable=False)

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    # Integração das tabelas - Campo id da tabela Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    criado_em = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP'))

class PedidoItem(db.Model):
    __tablename__ = 'pedido_item'
    id = db.Column(db.Integer, primary_key=True)
    # Integração das tabelas - Campo id da tabela Pedido
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    tipo = db.Column(db.Enum('espetinho', 'bebida'), nullable=False)
    referencia_id = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    tamanho = db.Column(db.String(50))
    qtd = db.Column(db.Integer, nullable=False)
    preco_unit = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)


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

# Rota que realiza o cadastro das bebidas
@app.route('/bebidas', methods=['GET', 'POST'])
@login_required
def bebidas_view():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        tamanho = request.form.get('tamanho', '').strip()
        preco_raw = request.form.get('preco', '').strip()
        if not nome or not preco_raw:
            flash('Informe nome e preço da bebida.', 'danger')
        else:
            try:
                preco_val = float(preco_raw)
                b = Bebida(nome=nome, tamanho=tamanho or None, preco=preco_val)
                db.session.add(b)
                db.session.commit()
                flash('Bebida cadastrada.', 'success')
                return redirect(url_for('bebidas_view'))
            except ValueError:
                flash('Preço inválido.', 'danger')
            except IntegrityError:
                db.session.rollback()
                flash('Erro ao cadastrar bebida.', 'danger')
    bebidas = db.session.execute(db.select(Bebida).order_by(Bebida.id.desc())).scalars().all()
    return render_template('bebidas.html', show_menu=True, bebidas=bebidas)

# Rota para realizar um pedido
@app.route('/pedidos', methods=['GET', 'POST'])
@login_required
def pedidos_view():
    # POST: cria o pedido e seus itens
    if request.method == 'POST':
        # Recupera e valida o cliente selecionado
        cliente_id_raw = request.form.get('cliente_id', '').strip()
        if not cliente_id_raw:
            flash('Informe o cliente.', 'danger')
        else:
            try:
                # Cria o cabeçalho do pedido a partir do cliente selecionado
                cliente_id = int(cliente_id_raw)
                pedido = Pedido(cliente_id=cliente_id)
                db.session.add(pedido)
                # Garante que o ID do pedido esteja disponível
                db.session.flush()

                # Quantifica os itens de espetinho do formulário
                prod_ids = request.form.getlist('item_produto_id')
                prod_qtds = request.form.getlist('item_produto_qtd')
                for idx, pid_raw in enumerate(prod_ids):
                    pid = (pid_raw or '').strip()
                    qtd_raw = prod_qtds[idx] if idx < len(prod_qtds) else ''
                    if not pid or not qtd_raw:
                        continue
                    try:
                        prod_id = int(pid)
                        qtd = int(qtd_raw)
                    except ValueError:
                        continue
                    # Busca o produto selecionado pelo ID informado
                    prod = db.session.execute(db.select(Produto).filter_by(id=prod_id)).scalar_one_or_none()
                    # Valida se o produto existe e se a quantidade é positiva
                    if not prod or qtd <= 0:
                        continue
                    # Converte o preço unitário para float e calcula o total do item
                    preco_unit = float(prod.preco)
                    total_val = preco_unit * qtd
                    # Monta o objeto PedidoItem com dados do produto no momento do pedido
                    item = PedidoItem(
                        pedido_id=pedido.id,
                        tipo='espetinho',
                        referencia_id=prod.id,
                        nome=prod.nome,
                        tamanho=None,
                        qtd=qtd,
                        preco_unit=preco_unit,
                        total=total_val
                    )
                    # Adiciona o item à sessão para persistir junto com o pedido
                    db.session.add(item)

                # Quantifica os itens de bebida do formulário
                beb_ids = request.form.getlist('item_bebida_id')
                beb_qtds = request.form.getlist('item_bebida_qtd')
                for idx, bid_raw in enumerate(beb_ids):
                    bid = (bid_raw or '').strip()
                    qtd_raw = beb_qtds[idx] if idx < len(beb_qtds) else ''
                    if not bid or not qtd_raw:
                        continue
                    try:
                        bebida_id = int(bid)
                        qtd = int(qtd_raw)
                    except ValueError:
                        continue
                    # Busca a bebida selecionada pelo ID informado
                    beb = db.session.execute(db.select(Bebida).filter_by(id=bebida_id)).scalar_one_or_none()
                    # Valida se a bebida existe e se a quantidade é positiva
                    if not beb or qtd <= 0:
                        continue
                    # Converte o preço unitário para float e calcula o total do item
                    preco_unit = float(beb.preco)
                    total_val = preco_unit * qtd
                    # Monta o objeto PedidoItem com dados da bebida no momento do pedido
                    item = PedidoItem(
                        pedido_id=pedido.id,
                        tipo='bebida',
                        referencia_id=beb.id,
                        nome=beb.nome,
                        tamanho=beb.tamanho,
                        qtd=qtd,
                        preco_unit=preco_unit,
                        total=total_val
                    )
                    # Adiciona o item à sessão para persistir junto com o pedido
                    db.session.add(item)

                # Confirma transação
                db.session.commit()
                flash('Pedido salvo.', 'success')
                return redirect(url_for('pedidos_view'))
            except IntegrityError:
                db.session.rollback()
                flash('Erro ao salvar pedido.', 'danger')
            except ValueError:
                flash('Dados inválidos.', 'danger')

    # GET: prepara dados para o formulário e a listagem
    # Carrega clientes, produtos e bebidas para preencher os selects
    clientes_objs = db.session.execute(db.select(Cliente).order_by(Cliente.nome.asc())).scalars().all()
    clientes = [{'id': c.id, 'nome': c.nome} for c in clientes_objs]
    produtos_objs = db.session.execute(db.select(Produto).order_by(Produto.nome.asc())).scalars().all()
    produtos = [{'id': p.id, 'nome': p.nome, 'preco': float(p.preco)} for p in produtos_objs]
    bebidas_objs = db.session.execute(db.select(Bebida).order_by(Bebida.nome.asc())).scalars().all()
    bebidas = [{'id': b.id, 'nome': b.nome, 'tamanho': b.tamanho or None, 'preco': float(b.preco)} for b in bebidas_objs]

    # Monta lista de pedidos com seus itens e totais
    pedidos = []
    pedidos_objs = db.session.execute(db.select(Pedido).order_by(Pedido.id.desc())).scalars().all()
    for ped in pedidos_objs:
        itens = db.session.execute(db.select(PedidoItem).filter_by(pedido_id=ped.id)).scalars().all()
        esp = []
        beb = []
        total = 0.0
        for it in itens:
            total += float(it.total)
            if it.tipo == 'espetinho':
                esp.append({'nome': it.nome, 'qtd': it.qtd, 'total': float(it.total)})
            else:
                beb.append({'nome': it.nome, 'tamanho': it.tamanho, 'qtd': it.qtd, 'total': float(it.total)})
        cli = db.session.execute(db.select(Cliente).filter_by(id=ped.cliente_id)).scalar_one_or_none()
        pedidos.append({'id': ped.id, 'cliente_nome': cli.nome if cli else '-', 'espetinhos': esp, 'bebidas': beb, 'total': total})

    # Renderiza a página com formulário e listagem
    return render_template('pedidos.html', show_menu=True, clientes=clientes, produtos=produtos, bebidas=bebidas, pedidos=pedidos)


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
