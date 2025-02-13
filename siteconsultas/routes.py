from flask import render_template, request, redirect, url_for, session, flash
from siteconsultas import app
from siteconsultas.db import conectar_oracle

def consulta_usuario(matricula):
    """
    Função para realizar consulta no banco de dados com base na matrícula do colaborador
    """
    try:
        conexao = conectar_oracle()
        with conexao.cursor() as cursor:
            cursor.execute("SELECT usuariobd, nome_guerra FROM pcempr WHERE matricula = :matricula", {'matricula': matricula})
            result = cursor.fetchone()
            return result
    except Exception as e:
        return str(e)

def validar_usuario(username, password):
    """
    Função para validar o usuário no banco de dados.
    """
    try:
        conexao = conectar_oracle()
        with conexao.cursor() as cursor:
            cursor.execute("SELECT usuariobd, senhabd FROM pcempr WHERE usuariobd = :username", {'username': username})
            result = cursor.fetchone()
            if result:
                usuariobd, senhabd = result
                print(f"Usuário encontrado: {usuariobd}")
                # Certifique-se de que a função decrypt está definida corretamente no banco de dados
                cursor.execute("SELECT decrypt(:senhabd, :usuariobd) FROM dual", {'senhabd': senhabd, 'usuariobd': usuariobd})
                senha_decrypt = cursor.fetchone()[0]
                print(f"Senha descriptografada: {senha_decrypt}")
                if password == senha_decrypt:
                    return True, result
                else:
                    print("Senha incorreta!")
            else:
                print("Usuário não encontrado")
        return False, None
    except Exception as e:
        print(f"Erro ao validar usuário: {e}")
        return False, None
    
@app.route('/consulta_pedidos', methods=['POST'])
def consulta_pedidos():
    num_ped_rca = request.form['num_ped_rca']
    num_ped_winthor = request.form['num_ped_winthor']
    cod_cliente = request.form['cod_cliente']
    
    query = "SELECT data, numpedrca, numped, codcli, numnota, vltotal FROM pcpedc WHERE 1=1"
    params = {}
    
    if num_ped_rca:
        query += " AND numpedrca = :num_ped_rca"
        params['num_ped_rca'] = num_ped_rca
    if num_ped_winthor:
        query += " AND numped = :num_ped_winthor"
        params['num_ped_winthor'] = num_ped_winthor
    if cod_cliente:
        query += " AND codcli = :cod_cliente"
        params['cod_cliente'] = cod_cliente
    
    try:
        conexao = conectar_oracle()
        with conexao.cursor() as cursor:
            cursor.execute(query,params)
            result = cursor.fetchall()
            return render_template('resultado_consulta.html', result=result)
    except Exception as e:
        return str(e)
    
@app.route('/consulta_form')
def consulta_form():
    return render_template('consulta_form.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    result = None
    if request.method == 'POST':
        matricula = request.form['matricula']
        result = consulta_usuario(matricula)
    return render_template('home.html', result=result)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    username = ''
    password = ''
    result = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Lógica de autenticação
        is_valid, result = validar_usuario(username, password)
        if is_valid:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = f'Credenciais inválidas. Tente novamente. Usuário: {username}, Senha: {password}'
    return render_template('login.html', error=error, username=username, password=password, result=result)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))