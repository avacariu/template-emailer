import sqlite3

class DBManager(object):
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.c = self.conn.cursor()

    def insert(self, email, subject, body, time, template):
        self.c.execute("""INSERT INTO emails (email, subject, body, time, template) VALUES (?, ?, ?, ?, ?)""", (email, subject, body, time, template))
        self.conn.commit()

    def retrieve_all(self):
        result = self.c.execute('SELECT * FROM emails ORDER BY time')
        return result

    def retrieve_next(self):
        result = self.c.execute('SELECT * FROM emails ORDER BY time LIMIT 1')
        return result

    def delete(self, id):
        self.c.execute('''DELETE FROM emails WHERE id=%d''' % (id))
        self.conn.commit()

    def create_new(self):
        self.c.execute('''CREATE TABLE emails
                     (id integer primary key autoincrement, 
                     email text, subject text, body text, time integer, template text)''')
        self.conn.commit()

