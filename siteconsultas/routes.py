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
            cursor.execute("SELECT usuariobd, senhabd FROM pcempr WHERE usuariobd = upper(:username)", {'username': username}) ## Alterado para upper
            result = cursor.fetchone()
            if result:
                usuariobd, senhabd = result
                print(f"Usuário encontrado: {usuariobd}")
                # Certifique-se de que a função decrypt está definida corretamente no banco de dados
                cursor.execute("SELECT decrypt (:senhabd, :usuariobd) FROM dual", {'senhabd': senhabd, 'usuariobd': usuariobd})
                senha_decrypt = cursor.fetchone()[0]
                if password.upper() == senha_decrypt:
                    return True, result
                else:
                    print("Senha incorreta!")
            else:
                print("Usuário não encontrado")
        return False, None
    except Exception as e:
        print(f"Erro ao validar usuário: {e}")
        return False, None
    finally:
        if conexao:
            conexao.close()
    
@app.route('/consulta_pedidos', methods=['POST'])
def consulta_pedidos():
    num_ped_rca = request.form['num_ped_rca']
    num_ped_winthor = request.form['num_ped_winthor']
    cod_cliente = request.form['cod_cliente']
    
    query1 = "SELECT a.data,a.numpedrca,a.numped,a.codcli,c.cliente,a.codusur,d.nome,a.numcar,a.numnota,a.numtransvenda,a.vltotal,b.situacaonfe,'PCNFSAID' AS TABELA_ORIGEM FROM pcpedc a JOIN pcnfsaid b ON a.numped = b.numped JOIN pcclient c ON a.codcli = c.codcli JOIN pcusuari d ON a.codusur = d.codusur WHERE 1=1"
    query2 = "SELECT a.data,a.numpedrca,a.numped,a.codcli,c.cliente,a.codusur,d.nome,a.numcar,a.numnota,a.numtransvenda,a.vltotal,b.situacaonfe,'PCNFSAIDPREFAT' AS TABELA_ORIGEM FROM pcpedc a JOIN pcnfsaidprefat b ON a.numped = b.numped JOIN pcclient c ON a.codcli = c.codcli JOIN pcusuari d ON a.codusur = d.codusur WHERE 1=1"
    params = {}
    
    if num_ped_rca:
        query1 += " AND a.numpedrca = :num_ped_rca and a.data >= TRUNC(SYSDATE) - interval '24' hour"
        query2 += " AND a.numpedrca = :num_ped_rca and a.data >= TRUNC(SYSDATE) - interval '24' hour"
        params['num_ped_rca'] = num_ped_rca
    if num_ped_winthor:
        query1 += " AND a.numped = :num_ped_winthor and a.data >= TRUNC(SYSDATE) - interval '24' hour"
        query2 += " AND a.numped = :num_ped_winthor and a.data >= TRUNC(SYSDATE) - interval '24' hour"
        params['num_ped_winthor'] = num_ped_winthor
    if cod_cliente:
        query1 += " AND a.codcli = :cod_cliente and a.data >= TRUNC(SYSDATE) - interval '24' hour"
        query2 += " AND a.codcli = :cod_cliente and a.data >= TRUNC(SYSDATE) - interval '24' hour"
        params['cod_cliente'] = cod_cliente
        
    consulta = f"({query1}) UNION ALL ({query2})"
    
    try:
        conexao = conectar_oracle()
        with conexao.cursor() as cursor:
            cursor.execute(consulta,params)
            result = cursor.fetchall()
            return render_template('resultado_consulta.html', result=result)
    except Exception as e:
        return str(e)
    finally:
        if conexao:
            conexao.close()
    
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
            error = f'Credenciais inválidas. Tente novamente.'
    return render_template('login.html', error=error, result=result)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))