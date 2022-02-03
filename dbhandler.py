import sqlite3
from datetime import datetime
import os


class DbHandler:
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(filename):
            self._create_tables()

    def _handle(self, query: str, commit=False):
        try:
            connection = sqlite3.connect(self.filename)
            cursor = connection.cursor()
            cursor.execute(query)
            record = cursor.fetchall()
            if commit:
                connection.commit()
            cursor.close()
            connection.close()
            return record
        except sqlite3.Error as error:
            print("Ошибка при подключении к sqlite", error)

    def _create_tables(self):
        self._handle("CREATE TABLE balance (id INTEGER PRIMARY KEY AUTOINCREMENT, account VARCHAR (255), value BIGINT);", commit=True)
        self._handle("INSERT INTO balance (account, value) VALUES ('Tim', 0);", commit=True)
        self._handle("CREATE TABLE earn_log (id INTEGER PRIMARY KEY AUTOINCREMENT, value INT, description VARCHAR (255), user VARCHAR (128), datetime DATETIME);", commit=True)
        self._handle("CREATE TABLE expence_log (id INTEGER PRIMARY KEY AUTOINCREMENT, value INT, description VARCHAR (255), user VARCHAR (128), datetime DATETIME);", commit=True)

    def _drop_tables(self):
        self._handle("DROP TABLE balance;", commit=True)
        self._handle("DROP TABLE earn_log;", commit=True)
        self._handle("DROP TABLE expence_log;", commit=True)

    def reset_db(self):
        self._drop_tables()
        self._create_tables()

    def _set_total(self, value: int):
        self._handle(f"UPDATE balance SET value = {value} WHERE id = 1;", commit=True)

    def get_total(self):
        return int(self._handle("SELECT value FROM balance WHERE id = 1;")[0][0])

    def add_money(self, value: int, total: int, descr='Разное', user=325802019,):
        self._handle(f"INSERT INTO earn_log (value, description, user, datetime) VALUES ({value}, '{descr}', '{user}', '{datetime.now()}');", commit=True)
        self._set_total(total+value)

    def spend_money(self, value: int, total: int, descr='Разное', user=325802019,):
        self._handle(f"INSERT INTO expence_log (value, description, user, datetime) VALUES ({value}, '{descr}', '{user}', '{datetime.now()}');", commit=True)
        self._set_total(total-value)

    def get_summary(self, limit='0', header=""):
        limit = str(limit)
        incomes = self._handle(f"SELECT description, SUM(value) FROM earn_log WHERE datetime > '{limit}' GROUP BY description;")
        expences = self._handle(f"SELECT description, SUM(value) FROM expence_log WHERE datetime > '{limit}' GROUP BY description;")
        totalincome = sum([x[1] for x in incomes])
        totalspent = sum([x[1] for x in expences])
        message = f"""    КРАТКАЯ ДЕТАЛИЗАЦИЯ ЗА {header}
В копилке {self.get_total()} рублей.
Всего получено: {totalincome} р.
Всего потрачено: {totalspent} р.

ПРИХОД:
"""
        for entry in sorted(incomes, key=lambda x: -x[1]):
            message += f"    {entry[0]}: {entry[1]}\n"
        message += "РАСХОДЫ:\n"
        for entry in sorted(expences, key=lambda x: -x[1]):
            message += f"    {entry[0]}: {entry[1]}\n"
        return message

    def get_detail(self, limit='0', header=""):
        limit = str(limit)
        incomes = self._handle(
            f"SELECT * FROM earn_log WHERE datetime > '{limit}';")
        expences = self._handle(
            f"SELECT * FROM expence_log WHERE datetime > '{limit}';")
        totalincome = sum([x[1] for x in incomes])
        totalspent = sum([x[1] for x in expences])
        incomes = [['+'] + list(x[1:]) for x in incomes]
        expences = [['-'] + list(x[1:]) for x in expences]
        fullog = sorted(incomes + expences, key=lambda x: x[4], reverse=True)
        message = f"""    ПОЛНАЯ ДЕТАЛИЗАЦИЯ ЗА {header}
В копилке {self.get_total()} рублей.
Всего получено: {totalincome} р.
Всего потрачено: {totalspent} р.

ОПЕРАЦИИ:
"""
        for entry in fullog:
            message += f"    {datetime.strftime(datetime.strptime(entry[4], '%Y-%m-%d %H:%M:%S.%f'), '%d-%m-%Y %H:%M')}  {entry[0]}{entry[1]} {entry[2]} ({entry[3]})\n"
        return message
