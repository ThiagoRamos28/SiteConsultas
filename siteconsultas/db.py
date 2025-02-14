import cx_Oracle

def conectar_oracle():
    """
    Função para conectar no banco de dados
    """
    dsn = cx_Oracle.makedsn("192.168.4.9", 1521, service_name="WINT")
    try:
        conexao = cx_Oracle.connect(user="DISDAL", password="di203alfor", dsn=dsn)
        return conexao
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        raise Exception(f'Erro ao conectar no banco de dados: {error.message}')
