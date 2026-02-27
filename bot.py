"""
Фінансовий трекер студента (консольний чат-бот)
Зберігання даних: JSON файл (budget + список витрат)
Автор: (Катункін Дмитро Євгенович 472)
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional


DATA_FILE = "finance_data.json"


# ---------------------------
# Робота з даними (файл JSON)
# ---------------------------

def default_state() -> Dict[str, Any]:
    """Початковий стан, якщо файлу ще немає або він порожній/пошкоджений."""
    return {
        "budget": 0.0,
        "expenses": []  # список словників: {amount, category, date, comment}
    }


def load_state(filename: str = DATA_FILE) -> Dict[str, Any]:
    """Зчитує дані з JSON. Якщо файлу немає або помилка — повертає default_state()."""
    if not os.path.exists(filename):
        return default_state()

    try:
        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)
        # базова валідація структури
        if "budget" not in state or "expenses" not in state or not isinstance(state["expenses"], list):
            return default_state()
        return state
    except (json.JSONDecodeError, OSError):
        return default_state()


def save_state(state: Dict[str, Any], filename: str = DATA_FILE) -> None:
    """Записує дані у JSON (автооновлення після кожної зміни)."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------------------
# Допоміжні функції
# ---------------------------

def parse_float(prompt: str) -> float:
    """Безпечне зчитування числа (суми)."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
            if value < 0:
                print("❌ Сума не може бути від'ємною. Спробуй ще раз.")
                continue
            return value
        except ValueError:
            print("❌ Некоректне число. Приклад: 120 або 120.50")


def parse_date(prompt: str) -> str:
    """
    Зчитує дату у форматі YYYY-MM-DD.
    Повертає рядок (так зручніше зберігати в JSON).
    """
    while True:
        raw = input(prompt).strip()
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d").date()
            return dt.isoformat()
        except ValueError:
            print("❌ Некоректна дата. Формат має бути YYYY-MM-DD, наприклад 2026-02-27")


def normalize_category(cat: str) -> str:
    """Нормалізує категорію (прибирає зайві пробіли)."""
    cat = cat.strip()
    return cat if cat else "Без категорії"


def total_expenses(expenses: List[Dict[str, Any]]) -> float:
    """Підрахунок загальної суми витрат."""
    return sum(float(e.get("amount", 0)) for e in expenses)


def calculate_balance(budget: float, expenses: List[Dict[str, Any]]) -> float:
    """Залишок бюджету."""
    return float(budget) - total_expenses(expenses)


def print_expenses(expenses: List[Dict[str, Any]]) -> None:
    """Красивий вивід списку витрат."""
    if not expenses:
        print("ℹ️ Витрат поки немає.")
        return

    print("\n📌 Список витрат:")
    print("-" * 72)
    print(f"{'#':<3} {'Дата':<12} {'Категорія':<18} {'Сума':>10}  Коментар")
    print("-" * 72)

    for i, e in enumerate(expenses, start=1):
        d = str(e.get("date", "----"))
        c = str(e.get("category", ""))
        a = float(e.get("amount", 0))
        com = str(e.get("comment", "")).strip()
        print(f"{i:<3} {d:<12} {c:<18} {a:>10.2f}  {com}")

    print("-" * 72)
    print(f"Разом витрат: {total_expenses(expenses):.2f}\n")


def filter_by_date(expenses: List[Dict[str, Any]], target_date: str) -> List[Dict[str, Any]]:
    return [e for e in expenses if str(e.get("date")) == target_date]


def filter_by_period(expenses: List[Dict[str, Any]], start: str, end: str) -> List[Dict[str, Any]]:
    """
    Фільтр між двома датами включно.
    Дати зберігаються як YYYY-MM-DD, тому порівняння рядків теж працює,
    але робимо через date для надійності.
    """
    start_d = datetime.strptime(start, "%Y-%m-%d").date()
    end_d = datetime.strptime(end, "%Y-%m-%d").date()
    if end_d < start_d:
        start_d, end_d = end_d, start_d

    result = []
    for e in expenses:
        try:
            d = datetime.strptime(str(e.get("date")), "%Y-%m-%d").date()
            if start_d <= d <= end_d:
                result.append(e)
        except ValueError:
            continue
    return result


def filter_by_category(expenses: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    category_norm = category.strip().lower()
    return [e for e in expenses if str(e.get("category", "")).strip().lower() == category_norm]


def report_by_categories(expenses: List[Dict[str, Any]]) -> Dict[str, float]:
    """Повертає словник: категорія -> сума."""
    report: Dict[str, float] = {}
    for e in expenses:
        cat = str(e.get("category", "Без категорії")).strip()
        amount = float(e.get("amount", 0))
        report[cat] = report.get(cat, 0.0) + amount
    return report


# ---------------------------
# Команди бота
# ---------------------------

def cmd_help() -> None:
    print("""
🧾 Доступні команди:
- допомога                 : показати список команд
- встановити бюджет        : задати суму бюджету
- додати витрату           : додати нову витрату (сума, категорія, дата, коментар)
- показати витрати         : показати всі витрати
- витрати за дату          : фільтр витрат за конкретну дату
- витрати за період        : фільтр витрат між двома датами
- витрати за категорією    : фільтр витрат за категорією
- залишок                  : показати залишок бюджету
- звіт за категоріями      : підсумок витрат по категоріях
- вийти                    : завершити роботу
""".strip())


def cmd_set_budget(state: Dict[str, Any]) -> None:
    budget = parse_float("Введи суму бюджету: ")
    state["budget"] = float(budget)
    save_state(state)
    print(f"✅ Бюджет встановлено: {state['budget']:.2f}")


def cmd_add_expense(state: Dict[str, Any]) -> None:
    amount = parse_float("Сума витрати: ")
    category = normalize_category(input("Категорія: "))
    exp_date = parse_date("Дата (YYYY-MM-DD): ")
    comment = input("Коментар (необов'язково): ").strip()

    expense = {
        "amount": float(amount),
        "category": category,
        "date": exp_date,
        "comment": comment
    }

    state["expenses"].append(expense)
    save_state(state)

    print("✅ Витрату додано.")
    # Перевірка бюджету
    budget = float(state.get("budget", 0.0))
    balance = calculate_balance(budget, state["expenses"])
    if budget > 0 and balance < 0:
        print(f"⚠️ УВАГА: Бюджет перевищено на {abs(balance):.2f}!")
    elif budget > 0:
        print(f"💰 Залишок бюджету: {balance:.2f}")


def cmd_show_expenses(state: Dict[str, Any]) -> None:
    print_expenses(state["expenses"])


def cmd_expenses_by_date(state: Dict[str, Any]) -> None:
    d = parse_date("Введи дату (YYYY-MM-DD): ")
    filtered = filter_by_date(state["expenses"], d)
    print_expenses(filtered)


def cmd_expenses_by_period(state: Dict[str, Any]) -> None:
    start = parse_date("Початкова дата (YYYY-MM-DD): ")
    end = parse_date("Кінцева дата (YYYY-MM-DD): ")
    filtered = filter_by_period(state["expenses"], start, end)
    print_expenses(filtered)


def cmd_expenses_by_category(state: Dict[str, Any]) -> None:
    cat = input("Введи категорію: ").strip()
    if not cat:
        print("❌ Категорія не може бути порожньою.")
        return
    filtered = filter_by_category(state["expenses"], cat)
    print_expenses(filtered)


def cmd_balance(state: Dict[str, Any]) -> None:
    budget = float(state.get("budget", 0.0))
    spent = total_expenses(state["expenses"])
    balance = budget - spent

    print(f"Бюджет: {budget:.2f}")
    print(f"Витрати: {spent:.2f}")
    print(f"Залишок: {balance:.2f}")

    if budget > 0 and balance < 0:
        print(f"⚠️ Бюджет перевищено на {abs(balance):.2f}!")


def cmd_report_categories(state: Dict[str, Any]) -> None:
    rep = report_by_categories(state["expenses"])
    if not rep:
        print("ℹ️ Немає витрат для звіту.")
        return

    print("\n📊 Звіт за категоріями:")
    print("-" * 40)
    total = 0.0
    for cat, amount in sorted(rep.items(), key=lambda x: x[0].lower()):
        print(f"{cat:<22} {amount:>10.2f}")
        total += amount
    print("-" * 40)
    print(f"{'Разом':<22} {total:>10.2f}\n")


# ---------------------------
# Головний цикл
# ---------------------------

def greet() -> None:
    print("👋 Привіт! Я бот «Фінансовий трекер студента».")
    print("Напиши 'допомога', щоб побачити команди.\n")


def handle_command(command: str, state: Dict[str, Any]) -> bool:
    """
    Обробляє команду користувача.
    Повертає False, якщо треба завершити роботу.
    """
    cmd = command.strip().lower()

    if cmd in ("допомога", "help", "?"):
        cmd_help()
    elif cmd == "встановити бюджет":
        cmd_set_budget(state)
    elif cmd == "додати витрату":
        cmd_add_expense(state)
    elif cmd == "показати витрати":
        cmd_show_expenses(state)
    elif cmd == "витрати за дату":
        cmd_expenses_by_date(state)
    elif cmd == "витрати за період":
        cmd_expenses_by_period(state)
    elif cmd == "витрати за категорією":
        cmd_expenses_by_category(state)
    elif cmd == "залишок":
        cmd_balance(state)
    elif cmd == "звіт за категоріями":
        cmd_report_categories(state)
    elif cmd in ("вийти", "exit", "quit"):
        print("👋 До зустрічі! Бережи бюджет 🙂")
        return False
    else:
        print("❌ Не розпізнав команду. Напиши 'допомога'.")

    return True


def main() -> None:
    state = load_state(DATA_FILE)
    greet()

    while True:
        user_input = input("👉 Команда: ")
        if not handle_command(user_input, state):
            break


if __name__ == "__main__":
    main()