import psycopg2

conn = psycopg2.connect(host="localhost", database="postgres", user="postgres",
                        password="instancemanager", port="5433")


def input_server(id, active):
    cur = conn.cursor()

    sql = """INSERT INTO server_instance(id, active)
             VALUES(%s, %s)"""

    cur.execute(sql, (id, active))
    conn.commit()
    cur.close()


def input_group(id, created_by):
    cur = conn.cursor()

    sql = """INSERT INTO group_instance(id, created_by)
             VALUES(%s, %s)"""

    cur.execute(sql, (id, created_by))
    conn.commit()
    cur.close()


def input_group_server(group_id, server_id):
    cur = conn.cursor()

    sql = """INSERT INTO group_server(group_id, server_id)
                 VALUES(%s, %s)"""

    cur.execute(sql, (group_id, server_id))
    conn.commit()
    cur.close()


def input_user_server(user_id, server_id):
    cur = conn.cursor()

    sql = """INSERT INTO user_server(group_id, server_id)
                     VALUES(%s, %s)"""

    cur.execute(sql, (user_id, server_id))
    conn.commit()
    cur.close()


def input_command(id, body, type, running, user_id, server_id):
    cur = conn.cursor()

    sql = """INSERT INTO command(id, body, type, running, user_id, server_id)
                     VALUES(%s, %s, %s, %s, %s, %s)"""

    cur.execute(sql, (id, body, type, running, user_id, server_id))
    conn.commit()
    cur.close()
