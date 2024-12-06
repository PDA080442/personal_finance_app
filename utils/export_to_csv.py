import csv

def export_to_csv(data, filename="finance_records.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Записываем заголовки
        writer.writerow(["Категория", "Сумма", "Дата"])

        # Записываем данные
        for record in data:
            writer.writerow([record[1], f"{record[2]:.2f}", record[3]])

    print(f"Данные успешно экспортированы в {filename}")
