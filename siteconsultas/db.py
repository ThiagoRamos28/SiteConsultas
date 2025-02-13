import cx_Oracle

def conectar_oracle():
    """
    Função para conectar no banco de dados
    """
    dsn = cx_Oracle.makedsn("192.168.4.19", 1521, service_name="TESTE")
    try:
        conexao = cx_Oracle.connect(user="HOMOLOGA", password="HOMOLOGA", dsn=dsn)
        return conexao
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        raise Exception(f'Erro ao conectar no banco de dados: {error.message}')
