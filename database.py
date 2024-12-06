# database.py
import sqlite3

class Database:
    def __init__(self, db_name="finance.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()
        self.create_regular_expenses_table()
        # Вызовите этот метод в конструкторе `Database`
        self.create_table_categories()
        self.update_records_table()  # Обновление структуры таблицы


    def create_table(self):
        # Создаем таблицу для записей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.connection.commit()

    def add_record(self, category, amount, record_type='expense'):
        self.cursor.execute('''
            INSERT INTO records (category, amount, type)
            VALUES (?, ?, ?)
        ''', (category, amount, record_type))
        self.connection.commit()


    def get_all_records(self):
        # Получаем все записи
        self.cursor.execute('SELECT * FROM records')
        return self.cursor.fetchall()

    def close(self):
        # Закрываем соединение
        self.connection.close()

    def delete_record(self, record_id):
        # Удаление записи по ID
        self.cursor.execute('DELETE FROM records WHERE id = ?', (record_id,))
        self.connection.commit()
    
    def get_categories(self):
        self.cursor.execute("SELECT DISTINCT category FROM records")
        return [row[0] for row in self.cursor.fetchall()]


    def load_categories(self):
        categories = self.db.get_categories()
        self.category_filter.addItems(categories)

    def get_filtered_records(self, category_filter=None, start_date=None, end_date=None):
        query = "SELECT * FROM records WHERE 1=1"
        params = []

        if category_filter and category_filter != "Все категории":
            query += " AND category = ?"
            params.append(category_filter)

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def create_table_categories(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        self.connection.commit()

    def get_all_categories(self):
        self.cursor.execute("SELECT * FROM categories")
        return self.cursor.fetchall()

    def add_category(self, name):
        self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        self.connection.commit()

    def delete_category(self, category_id):
        self.cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.connection.commit()

    def update_category(self, category_id, new_name):
        self.cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
        self.connection.commit()

    def create_regular_expenses_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS regular_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                interval TEXT NOT NULL, -- daily, weekly, monthly
                next_payment_date DATE NOT NULL
            )
        ''')
        self.connection.commit()
    
    def add_regular_expense(self, category, amount, interval, next_payment_date):
        self.cursor.execute('''
            INSERT INTO regular_expenses (category, amount, interval, next_payment_date)
            VALUES (?, ?, ?, ?)
        ''', (category, amount, interval, next_payment_date))
        self.connection.commit()

    def get_regular_expenses(self):
        self.cursor.execute("SELECT * FROM regular_expenses")
        return self.cursor.fetchall()

    def update_next_payment_date(self, expense_id, next_payment_date):
        self.cursor.execute('''
            UPDATE regular_expenses
            SET next_payment_date = ?
            WHERE id = ?
        ''', (next_payment_date, expense_id))
        self.connection.commit()
    
    def get_due_regular_expenses(self, current_date):
        self.cursor.execute('''
            SELECT * FROM regular_expenses
            WHERE next_payment_date <= ?
        ''', (current_date,))
        return self.cursor.fetchall()

    def get_records_by_period(self, start_date, end_date):
        query = "SELECT * FROM records WHERE date >= ? AND date <= ?"
        self.cursor.execute(query, (start_date, end_date))
        return self.cursor.fetchall()

    def search_records(self, search_term):
        query = '''
            SELECT * FROM records 
            WHERE category LIKE ? OR 
                CAST(amount AS TEXT) LIKE ? OR 
                date LIKE ?
        '''
        wildcard_term = f"%{search_term}%"
        self.cursor.execute(query, (wildcard_term, wildcard_term, wildcard_term))
        return self.cursor.fetchall()

    def update_records_table(self):
        # Проверяем, есть ли столбец 'type' в таблице records
        self.cursor.execute("PRAGMA table_info(records)")
        columns = [column[1] for column in self.cursor.fetchall()]

        if 'type' not in columns:
            # Если столбца нет, добавляем его
            self.cursor.execute('''
                ALTER TABLE records 
                ADD COLUMN type TEXT DEFAULT 'expense'
            ''')
            self.connection.commit()
        else:
            print("Столбец 'type' уже существует в таблице 'records'")

