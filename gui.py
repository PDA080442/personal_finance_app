# gui.py
import sys
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox, QDateEdit
from database import Database
from utils.export_to_csv import export_to_csv
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Инициализация базы данных
        self.db = Database()
        
        self.set_light_theme()

        # Настройка главного окна
        self.setWindowTitle("Программа для учета личных финансов")
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет и компоновка
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Кнопка для экспорта данных в CSV
        self.export_button = QPushButton("Экспортировать в CSV", self)
        self.export_button.clicked.connect(self.export_records)
        self.layout.addWidget(self.export_button)

        # Поля для ввода категории
        self.category_input = QLineEdit(self)
        self.category_input.setPlaceholderText("Введите категорию (например, 'Еда')")
        self.layout.addWidget(self.category_input)

        # Поля для ввода суммы
        self.amount_input = QLineEdit(self)
        self.amount_input.setPlaceholderText("Введите сумму")
        self.layout.addWidget(self.amount_input)

        self.type_selector = QComboBox(self)
        self.type_selector.addItems(["Расход", "Доход"])
        self.layout.addWidget(self.type_selector)
        
        # Кнопка для добавления записи
        self.add_button = QPushButton("Добавить запись", self)
        self.add_button.clicked.connect(self.add_record)
        self.layout.addWidget(self.add_button)

        # Таблица для отображения записей
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)  # 5 столбца: ID, Категория, Сумма, Дата
        self.table.setHorizontalHeaderLabels(["ID", "Категория", "Сумма", "Дата", "Тип"])
        self.layout.addWidget(self.table)

        # Кнопка для удаления записи
        self.delete_button = QPushButton("Удалить запись", self)
        self.delete_button.clicked.connect(self.delete_record)
        self.layout.addWidget(self.delete_button)

        # Поле для выбора категории
        self.category_filter = QComboBox(self)
        self.category_filter.addItem("Все категории")
        self.layout.addWidget(self.category_filter)

        # Поля для выбора диапазона дат
        self.start_date_filter = QDateEdit(self)
        self.start_date_filter.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_filter.setCalendarPopup(True)
        self.layout.addWidget(self.start_date_filter)

        self.end_date_filter = QDateEdit(self)
        self.end_date_filter.setDate(QDate.currentDate())
        self.end_date_filter.setCalendarPopup(True)
        self.layout.addWidget(self.end_date_filter)

        # Кнопка для применения фильтра
        self.filter_button = QPushButton("Применить фильтр", self)
        self.filter_button.clicked.connect(self.filter_records)
        self.layout.addWidget(self.filter_button)

        self.chart_button = QPushButton("Показать диаграмму расходов", self)
        self.chart_button.clicked.connect(self.show_chart)
        self.layout.addWidget(self.chart_button)

        self.line_chart_button = QPushButton("Показать график расходов по времени", self)
        self.line_chart_button.clicked.connect(self.show_line_chart)
        self.layout.addWidget(self.line_chart_button)
        
        self.regular_expenses_button = QPushButton("Настроить регулярные расходы", self)
        self.regular_expenses_button.clicked.connect(self.open_regular_expenses_window)
        self.layout.addWidget(self.regular_expenses_button)
        
        self.check_regular_expenses()
        
        self.report_button = QPushButton("Создать отчет", self)
        self.report_button.clicked.connect(self.open_report_window)
        self.layout.addWidget(self.report_button)
        
        # Загрузка категорий и данных в таблицу
        self.load_categories()
        self.load_records()
        
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введите категорию, сумму или дату")
        self.layout.addWidget(self.search_input)

        self.search_button = QPushButton("Найти", self)
        self.search_button.clicked.connect(self.search_records)
        self.layout.addWidget(self.search_button)


        self.type_filter = QComboBox(self)
        self.type_filter.addItems(["Все записи", "Только доходы", "Только расходы"])
        self.type_filter.currentTextChanged.connect(self.filter_records)
        self.layout.addWidget(self.type_filter)

        self.export_pdf_button = QPushButton("Экспортировать в PDF", self)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.layout.addWidget(self.export_pdf_button)
        
        self.theme_selector = QComboBox(self)
        self.theme_selector.addItems([
            "Светлая тема", 
            "Темная тема", 
            "Зеленая тема", 
            "Синяя тема", 
            "Красная тема"
        ])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        self.layout.addWidget(self.theme_selector)

        
        
    def load_categories(self):
        try:
            categories = self.db.get_categories()
            if categories:
                self.category_filter.addItems(categories)
        except Exception as e:
            print("Ошибка при загрузке категорий:", e)

    def add_record(self):
        category = self.category_input.text()
        amount = self.amount_input.text()
        record_type = self.type_selector.currentText().lower()  # "expense" или "income"
        
        if not category or not amount.isdigit():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректные данные!")
            return
        
        record_type_db = "expense" if record_type == "расход" else "income"

        # Сохраняем данные в базу
        self.db.add_record(category, float(amount), record_type)

        # Обновляем таблицу
        self.load_records()

        # Очистка полей ввода
        self.category_input.clear()
        self.amount_input.clear()

    def load_records(self, category_filter=None, start_date=None, end_date=None):
        query = "SELECT id, category, amount, date, type FROM records WHERE 1=1"
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

        if hasattr(self, 'type_filter') and self.type_filter.currentText() == "Только доходы": query += " AND type = 'income'"
        elif hasattr(self, 'type_filter') and self.type_filter.currentText() == "Только расходы": query += " AND type = 'expense'"

        self.db.cursor.execute(query, params)
        records = self.db.cursor.fetchall()

        # Устанавливаем количество строк в таблице
        self.table.setRowCount(len(records))

        for row_index, row_data in enumerate(records):
            # row_data: (id, category, amount, date, type)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row_data[0])))  # ID
            self.table.setItem(row_index, 1, QTableWidgetItem(row_data[1]))  # Категория
            self.table.setItem(row_index, 2, QTableWidgetItem(f"{row_data[2]:.2f}"))  # Сумма
            self.table.setItem(row_index, 3, QTableWidgetItem(row_data[3]))  # Дата

            # Обработка типа записи, если он существует
            record_type = row_data[4] if len(row_data) > 4 else "N/A"
            self.table.setItem(row_index, 4, QTableWidgetItem(record_type.capitalize()))  # Тип

        self.table.setColumnHidden(0, True)  # Скрыть колонку ID


    def filter_records(self):
        category = self.category_filter.currentText()
        start_date = self.start_date_filter.date().toString("yyyy-MM-dd")
        end_date = self.end_date_filter.date().toString("yyyy-MM-dd")

        self.load_records(category_filter=category, start_date=start_date, end_date=end_date)

    def delete_record(self):
        # Получаем текущую строку
        selected_row = self.table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите запись для удаления!")
            return

        # Получаем ID записи из первой колонки (скрытый идентификатор)
        record_id = int(self.table.item(selected_row, 0).text())

        # Удаляем запись из базы данных
        self.db.delete_record(record_id)

        # Обновляем таблицу
        self.load_records()

    def export_records(self):
        records = self.db.get_all_records()

        if not records:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта!")
            return

        # Экспорт данных
        export_to_csv(records)
        QMessageBox.information(self, "Успех", "Данные успешно экспортированы в 'finance_records.csv'!")

    def show_chart(self):
        records = self.db.get_all_records()

        if not records:
            QMessageBox.warning(self, "Ошибка", "Нет данных для построения диаграммы!")
            return

        # Группируем данные по категориям
        categories = {}
        for record in records:
            category = record[1]  # Категория
            amount = record[2]    # Сумма
            if category in categories:
                categories[category] += amount
            else:
                categories[category] = amount

        # Построение диаграммы
        labels = list(categories.keys())
        sizes = list(categories.values())

        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')  # Делает круговой график кругом

        # Отображение диаграммы в новом окне
        chart_window = QMainWindow(self)
        chart_window.setWindowTitle("Диаграмма расходов")
        chart_layout = QVBoxLayout()
        chart_widget = QWidget()
        chart_widget.setLayout(chart_layout)
        chart_layout.addWidget(canvas)
        chart_window.setCentralWidget(chart_widget)
        chart_window.resize(600, 400)
        chart_window.show()

    def show_line_chart(self):
        records = self.db.get_all_records()

        if not records:
            QMessageBox.warning(self, "Ошибка", "Нет данных для построения графика!")
            return

        # Группируем данные по датам
        dates = {}
        for record in records:
            date = record[3].split(" ")[0]  # Учитываем только дату, без времени
            amount = record[2]             # Сумма
            if date in dates:
                dates[date] += amount
            else:
                dates[date] = amount

        # Сортируем данные по дате
        sorted_dates = sorted(dates.items())

        # Данные для графика
        x_data = [date for date, _ in sorted_dates]
        y_data = [amount for _, amount in sorted_dates]

        # Построение графика
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot(x_data, y_data, marker="o")
        ax.set_title("Расходы по времени")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Сумма")
        ax.grid(True)
        fig.autofmt_xdate()

        # Отображение графика в новом окне
        chart_window = QMainWindow(self)
        chart_window.setWindowTitle("График расходов по времени")
        chart_layout = QVBoxLayout()
        chart_widget = QWidget()
        chart_widget.setLayout(chart_layout)
        chart_layout.addWidget(canvas)
        chart_window.setCentralWidget(chart_widget)
        chart_window.resize(800, 600)
        chart_window.show()

    def open_regular_expenses_window(self):
        self.regular_expenses_window = QMainWindow(self)
        self.regular_expenses_window.setWindowTitle("Настройка регулярных расходов")
        self.regular_expenses_window.resize(400, 400)

        layout = QVBoxLayout()
    
        # Таблица для отображения регулярных расходов
        self.regular_expenses_table = QTableWidget()
        self.regular_expenses_table.setColumnCount(4)
        self.regular_expenses_table.setHorizontalHeaderLabels(["ID", "Категория", "Сумма", "Следующий платеж"])
        self.load_regular_expenses()
        layout.addWidget(self.regular_expenses_table)

        # Поле для ввода категории
        category_input = QLineEdit()
        category_input.setPlaceholderText("Категория (например, 'Аренда')")
        layout.addWidget(category_input)

        # Поле для ввода суммы
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("Сумма")
        layout.addWidget(amount_input)

        # Поле для выбора интервала
        interval_input = QComboBox()
        interval_input.addItems(["Ежедневно", "Еженедельно", "Ежемесячно"])
        layout.addWidget(interval_input)

        # Поле для выбора следующей даты платежа
        next_date_input = QDateEdit()
        next_date_input.setDate(QDate.currentDate())
        next_date_input.setCalendarPopup(True)
        layout.addWidget(next_date_input)

        # Кнопка для добавления регулярного расхода
        add_button = QPushButton("Добавить регулярный расход")
        layout.addWidget(add_button)

        # Кнопка для удаления регулярного расхода
        delete_button = QPushButton("Удалить выбранный расход")
        layout.addWidget(delete_button)

        # Функция для добавления регулярного расхода
        def add_regular_expense():
            category = category_input.text()
            amount = amount_input.text()
            interval = interval_input.currentText().lower()  # Преобразуем в "daily", "weekly", "monthly"
            next_payment_date = next_date_input.date().toString("yyyy-MM-dd")

            if not category or not amount.isdigit():
                QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректные данные!")
                return

            self.db.add_regular_expense(category, float(amount), interval, next_payment_date)
            QMessageBox.information(self, "Успех", "Регулярный расход добавлен!")
            self.load_regular_expenses()
            category_input.clear()
            amount_input.clear()

        add_button.clicked.connect(add_regular_expense)

        # Связываем кнопку удаления с методом
        delete_button.clicked.connect(self.delete_regular_expense)

        # Устанавливаем виджет и компоновку
        widget = QWidget()
        widget.setLayout(layout)
        self.regular_expenses_window.setCentralWidget(widget)
        self.regular_expenses_window.show()


    def check_regular_expenses(self):

        today = datetime.now().strftime("%Y-%m-%d")
        due_expenses = self.db.get_due_regular_expenses(today)

        for expense in due_expenses:
            expense_id, category, amount, interval, next_payment_date = expense

            # Добавляем расход в основную таблицу
            self.db.add_record(category, amount)

            # Рассчитываем новую дату платежа
            if interval == "ежедневно":
                new_date = datetime.strptime(next_payment_date, "%Y-%m-%d") + timedelta(days=1)
            elif interval == "еженедельно":
                new_date = datetime.strptime(next_payment_date, "%Y-%m-%d") + timedelta(weeks=1)
            elif interval == "ежемесячно":
                new_date = datetime.strptime(next_payment_date, "%Y-%m-%d").replace(day=1) + timedelta(days=31)
                new_date = new_date.replace(day=1)

            self.db.update_next_payment_date(expense_id, new_date.strftime("%Y-%m-%d"))

        self.load_records()
        
    def delete_regular_expense(self):
        # Получаем выбранную строку
        selected_row = self.regular_expenses_table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите запись для удаления!")
            return

        # Получаем ID выбранного расхода
        expense_id = int(self.regular_expenses_table.item(selected_row, 0).text())

        # Удаляем запись из базы данных
        self.db.cursor.execute("DELETE FROM regular_expenses WHERE id = ?", (expense_id,))
        self.db.connection.commit()

        # Обновляем таблицу
        self.load_regular_expenses()
        QMessageBox.information(self, "Успех", "Регулярный расход удален!")


    def load_regular_expenses(self):
        # Получаем данные из базы
        regular_expenses = self.db.get_regular_expenses()

        # Устанавливаем количество строк в таблице
        self.regular_expenses_table.setRowCount(len(regular_expenses))

        # Заполняем таблицу данными
        for row_index, expense in enumerate(regular_expenses):
            expense_id, category, amount, interval, next_payment_date = expense
            self.regular_expenses_table.setItem(row_index, 0, QTableWidgetItem(str(expense_id)))  # ID
            self.regular_expenses_table.setItem(row_index, 1, QTableWidgetItem(category))        # Категория
            self.regular_expenses_table.setItem(row_index, 2, QTableWidgetItem(f"{amount:.2f}")) # Сумма
            self.regular_expenses_table.setItem(row_index, 3, QTableWidgetItem(next_payment_date))  # Следующий платеж

    def open_report_window(self):
        self.report_window = QMainWindow(self)
        self.report_window.setWindowTitle("Генерация отчета")
        self.report_window.resize(400, 300)

        layout = QVBoxLayout()

        # Поле для выбора периода
        period_input = QComboBox()
        period_input.addItems(["Сегодня", "Последняя неделя", "Последний месяц", "Последний год"])
        layout.addWidget(period_input)

        # Кнопка для генерации отчета
        generate_button = QPushButton("Сгенерировать отчет")
        layout.addWidget(generate_button)

        # Поле для отображения отчета
        report_area = QTableWidget()
        report_area.setColumnCount(3)
        report_area.setHorizontalHeaderLabels(["Категория", "Сумма", "Процент"])
        layout.addWidget(report_area)

        # Функция генерации отчета
        def generate_report():
            period = period_input.currentText()
            records = self.get_records_by_period(period)

            if not records:
                QMessageBox.warning(self, "Ошибка", "Нет данных за выбранный период!")
                return

            # Группируем данные по категориям
            categories = {}
            total = 0
            for record in records:
                category = record[1]  # Категория
                amount = record[2]    # Сумма
                total += amount
                if category in categories:
                    categories[category] += amount
                else:
                    categories[category] = amount

            # Заполняем таблицу отчетов
            report_area.setRowCount(len(categories))
            for row_index, (category, amount) in enumerate(categories.items()):
                report_area.setItem(row_index, 0, QTableWidgetItem(category))         # Категория
                report_area.setItem(row_index, 1, QTableWidgetItem(f"{amount:.2f}"))  # Сумма
            report_area.setItem(row_index, 2, QTableWidgetItem(f"{(amount / total) * 100:.2f}%"))  # Процент

        generate_button.clicked.connect(generate_report)

        # Устанавливаем виджет и компоновку
        widget = QWidget()
        widget.setLayout(layout)
        self.report_window.setCentralWidget(widget)
        self.report_window.show()

    def get_records_by_period(self, period):
        today = datetime.now().strftime("%Y-%m-%d")
        if period == "Сегодня":
            start_date = end_date = today
        elif period == "Последняя неделя":
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today
        elif period == "Последний месяц":
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = today
        elif period == "Последний год":
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            end_date = today
        else:
            start_date = end_date = today  # Default case

        return self.db.get_records_by_period(start_date, end_date)
    
    def set_light_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QPushButton {
                background-color: #E0E0E0;
                color: #000000;
                border: 1px solid #CCCCCC;
                padding: 5px;
            }   
            QLineEdit, QComboBox, QTableWidget {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
            }
            QLabel {
                color: #000000;
            }
        """)
        
    def set_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2B2B2B;
            }
            QPushButton {
                background-color: #555555;
                color: #FFFFFF;
                border: 1px solid #444444;
                padding: 5px;
            }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

    def set_colorful_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFE4B5;
            }
            QPushButton {
                background-color: #FFB6C1;
                color: #000000;
                border: 1px solid #FF69B4;
                padding: 5px;
            }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #FFF8DC;
                color: #000000;
                border: 1px solid #FFD700;
            }
            QLabel {
                color: #8B4513;
            }
        """)
    
    def set_green_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8F5E9;
            }
            QPushButton {
                background-color: #81C784;
                color: #000000;
                border: 1px solid #66BB6A;
                padding: 5px;
            }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #C8E6C9;
                color: #000000;
                border: 1px solid #81C784;
            }
            QLabel {
                color: #2E7D32;
            }
        """)
        
    def set_blue_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E3F2FD;
            }
            QPushButton {
                background-color: #64B5F6;
                color: #000000;
                border: 1px solid #42A5F5;
                padding: 5px;
            }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #BBDEFB;
                color: #000000;
                border: 1px solid #64B5F6;
            }
            QLabel {
                color: #1E88E5;
            }
        """)

    def set_red_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFEBEE;
            }
            QPushButton {
                background-color: #EF9A9A;
                color: #000000;
                border: 1px solid #E57373;
                padding: 5px;
            }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #FFCDD2;
                color: #000000;
                border: 1px solid #EF9A9A;
            }
            QLabel {
                color: #C62828;
            }
        """)


    def change_theme(self, theme):
        if theme == "Светлая тема": self.set_light_theme()
        elif theme == "Темная тема": self.set_dark_theme()
        elif theme == "Зеленая тема": self.set_green_theme()
        elif theme == "Синяя тема": self.set_blue_theme()
        elif theme == "Красная тема": self.set_red_theme()

    def search_records(self):
        search_term = self.search_input.text().strip()

        if not search_term:
            QMessageBox.warning(self, "Ошибка", "Введите критерий для поиска!")
            return

        # Выполняем поиск в базе данных
        records = self.db.search_records(search_term)

        if not records:
            QMessageBox.information(self, "Результат поиска", "Записи не найдены.")
            self.load_records()  # Загружаем все записи
            return

        # Отображаем результаты в таблице
        self.table.setRowCount(len(records))
        for row_index, row_data in enumerate(records):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row_data[0])))  # ID
            self.table.setItem(row_index, 1, QTableWidgetItem(row_data[1]))  # Категория
            self.table.setItem(row_index, 2, QTableWidgetItem(f"{row_data[2]:.2f}"))  # Сумма
            self.table.setItem(row_index, 3, QTableWidgetItem(row_data[3]))  # Дата

    def export_to_pdf(self):
        # Получаем данные из таблицы
        row_count = self.table.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта!")
            return

        # Создаем PDF-файл
        file_name = "finance_report.pdf"
        pdf = canvas.Canvas(file_name, pagesize=letter)
        pdf.setTitle("Отчет по финансам")

        # Заголовок
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 750, "Отчет по финансам")

        # Таблица
        pdf.setFont("Helvetica", 10)
        start_y = 700
        x_offsets = [50, 150, 250, 350, 450]  # Колонки: Категория, Сумма, Дата, Тип
        headers = ["Категория", "Сумма", "Дата", "Тип"]
    
        # Рисуем заголовки
        for i, header in enumerate(headers): pdf.drawString(x_offsets[i], start_y, header)

        # Рисуем строки данных
        y = start_y - 20
        for row in range(row_count):
            if y < 50:  # Если место на странице закончилось, создаем новую
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = 750

            for col in range(1, 5):  # Пропускаем скрытый ID
                item = self.table.item(row, col)
                if item:
                    pdf.drawString(x_offsets[col - 1], y, item.text())

            y -= 20

        pdf.save()

        QMessageBox.information(self, "Успех", f"Отчет успешно экспортирован в {file_name}!")
        
        
    def closeEvent(self, event):
        self.db.close()
        event.accept()


def start_app():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
