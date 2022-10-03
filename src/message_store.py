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
            type text NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL) ''')

            database_conn.commit()

        except Exception as error:
            raise error


    def store(self, sim_imsi: str, text: str, number: str, timestamp: str, _type: str) -> int:
        """
        """
        database_conn = database.connect(self.message_store_file)
        cur = database_conn.cursor()

        try:
            cur.execute(
                    """INSERT INTO messages (sim_imsi, text, number, timestamp, type) 
                    VALUES (?,?,?,?,?)""", 
                    (sim_imsi, text, number, timestamp, _type))

            database_conn.commit()
        except Exception as error:
            raise error
        else:
            return cur.lastrowid

    def load(self, sim_imsi: str, _type=None) -> list:
        """
        """
        database_conn = database.connect(self.message_store_file)

        cur = database_conn.cursor()

        try:
            if _type:
                cur.execute('''SELECT 
                        id,
                        sim_imsi,
                        text,
                        number,
                        timestamp,
                        date, 
                        type
                        FROM messages WHERE sim_imsi=:sim_imsi and type=:type''',
                        {"sim_imsi":sim_imsi, "type":_type})
            else:
                cur.execute('''SELECT 
                        id,
                        sim_imsi,
                        text,
                        number,
                        timestamp,
                        date,
                        type
                        FROM messages WHERE sim_imsi=:sim_imsi''',
                        {"sim_imsi":sim_imsi})
        except Exception as error:
            raise error
        else:
            return cur.fetchall()
