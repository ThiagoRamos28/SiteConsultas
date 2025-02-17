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

def consultar_filiais():
    """
    Aqui é pra consultar as filiais que utilizam o Vocollect sem ser tão manual
    """
    try:
        conexao = conectar_oracle()
        with conexao.cursor() as cursor:
            query = """
            SELECT codigo, fantasia 
            FROM pcfilial 
            WHERE usawms = 'S' 
            AND codigo IN (
                SELECT codfilial 
                FROM pcparametrowms 
                WHERE valor = 'S' 
                AND nome = 'USAVOCOLLECT'
            )
            """
            cursor.execute(query)
            result = cursor.fetchall()
            return result
    except Exception as e:
        return str(e)
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

@app.route('/verificar_integracao', methods=['GET', 'POST'])
def verificar_integracao():
    conexao = conectar_oracle()
    cursor = conexao.cursor()
    query_status = """
    SELECT 
        sess.program,
        CASE 
            WHEN PCI.DATA_IMPORTACAO IS NOT NULL AND PCI.DATA_IMPORTACAO = (
                SELECT MAX(DATA_IMPORTACAO) FROM PCINTEGRACAOWMS
                WHERE DATA_IMPORTACAO IS NOT NULL
            ) THEN 'Integração em andamento'
            ELSE 'Integração em andamento'
        END AS STATUS_INTEGRACAO,
        (SELECT MAX(DATA_IMPORTACAO) FROM PCINTEGRACAOWMS WHERE DATA_IMPORTACAO IS NOT NULL) AS ULTIMA_DATA_IMPORTACAO
    FROM 
        sys.v_$sess_info sess
    LEFT JOIN 
        PCINTEGRACAOWMS PCI ON 1=1
    WHERE     
        sess.program LIKE '%1742%'
        AND sess.status <> 'KILLED'
        AND sess.action <> '2ª Sessão'
        AND sess.username = SYS_CONTEXT('USERENV', 'CURRENT_USER')
        AND INSTR(NVL(sess.client_info, ' '), ':') > 0
    FETCH FIRST 1 ROWS ONLY
    """
    cursor.execute(query_status)
    result_status = cursor.fetchone()
    
    """
    em cima ela pegua o status da integração e a última data de importação com base na sessão da rotina, se estiver aberta ou não
    e embaixo valida as carga integradas no dia atual fazendo a quantidade do winthor que é a tabela primaria no caso aonde gerado primeiro com a pcintegracaowms que é aonde sobre pro kairos
    """
    status_integracao = result_status[1] if result_status else 'Rotina Fechada'
    ultima_data_importacao = result_status[2] if result_status else 'N/A'
    
    filiais = consultar_filiais()
    
    resultados = []
    filial_selecionada = None
    if request.method == 'POST':
        filial_selecionada = request.form['filial']
        query_resultados = """
        SELECT 
            pmp.data as "Data geração",
            pmp.numcar AS Carga,  
            COUNT(DISTINCT pmp.numos) AS Winthor_Contagem,
            (SELECT COUNT(DISTINCT numos) 
             FROM pcintegracaowms 
             WHERE dsc_lote = pmp.numcar) AS Kairos_Contagem
        FROM pcmovendpend pmp
        LEFT JOIN pcintegracaowms piw 
        ON piw.dsc_lote = pmp.numcar
            WHERE 
        pmp.data BETWEEN SYSDATE - 1 AND SYSDATE
        AND pmp.numcar IS NOT NULL
        AND pmp.codfilial = :filial
        GROUP BY pmp.data,pmp.numcar
        ORDER BY MAX(pmp.data) DESC
        """
        cursor.execute(query_resultados, {'filial': filial_selecionada})
        resultados = cursor.fetchall()
    
    cursor.close()
    conexao.close()
    
    return render_template('kairos_form.html', status_integracao=status_integracao, ultima_data_importacao=ultima_data_importacao, filiais=filiais, resultados=resultados, filial_selecionada=filial_selecionada)

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