import os
import sqlite3 as database

class MessageStore:
    message_store_file = os.path.join(
            os.path.dirname(__file__), '.db', f"message_store.db")

    @staticmethod
    def has_store() -> bool:
        """Checks if ledger file exist.
        """
        try:
            database_conn = database.connect(
                    f"file:{MessageStore.message_store_file}?mode=rw", uri=True)
        except database.OperationalError as error:
            return False
        except Exception as error:
            raise error

        return True

    @staticmethod
    def create_store() -> None:
        """
        """
        database_conn = database.connect(MessageStore.message_store_file)
        cur = database_conn.cursor()

        try:
            cur.execute( f'''
            CREATE TABLE messages
            (id integer PRIMARY KEY,
            sim_imsi text NOT NULL,
            text text NOT NULL,
            number text NOT NULL, 
            timestamp text NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL) ''')

            database_conn.commit()

        except Exception as error:
            raise error


    def store(self, sim_imsi: str, text: str, number: str, timestamp: str) -> int:
        """
        """
        database_conn = database.connect(self.message_store_file)
        cur = database_conn.cursor()

        try:
            cur.execute(
                    """INSERT INTO messages (sim_imsi, text, number, timestamp) VALUES (?,?,?,?)""", 
                    (sim_imsi, text, number, timestamp))

            database_conn.commit()
        except Exception as error:
            raise error
        else:
            return cur.lastrowid

    def load_all(self, sim_imsi: str) -> list:
        """
        """
        database_conn = database.connect(self.message_store_file)

        cur = database_conn.cursor()

        try:
            cur.execute('''SELECT 
                    id,
                    sim_imsi,
                    text,
                    number,
                    timestamp,
                    date 
                    FROM messages WHERE sim_imsi=:sim_imsi''',
                    {"sim_imsi":sim_imsi})
        except Exception as error:
            raise error
        else:
            return cur.fetchall()
