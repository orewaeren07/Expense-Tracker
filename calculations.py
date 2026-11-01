"""Pure functions: totals, breakdowns, formatting and input validation."""
import math
from datetime import date, datetime

CURRENCY = "₹"          # change to "$", "€", ... if you like
MAX_AMOUNT = 1_000_000_000.0
MAX_DESC = 100
CATEGORY_ICONS = {"Food": "🍽️", "Travel": "🚌", "Shopping": "🛍️", "Education": "📚",
                  "Entertainment": "🎬", "Bills": "💡", "Healthcare": "💊", "Other": "📦"}


def money(value):
    sign = "-" if value < 0 else ""
    return f"{sign}{CURRENCY}{abs(value):,.2f}"


def totals(rows):
    income = round(sum(r["amount"] for r in rows if r["type"] == "Income"), 2)
    expense = round(sum(r["amount"] for r in rows if r["type"] == "Expense"), 2)
    return income, expense, round(income - expense, 2)


def category_breakdown(rows):
    """{category: total} for expenses, largest first."""
    out = {}
    for r in rows:
        if r["type"] == "Expense":
            out[r["category"]] = round(out.get(r["category"], 0) + r["amount"], 2)
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def month_label(ym):
    return datetime.strptime(ym, "%Y-%m").strftime("%B %Y")


def previous_month(ym):
    y, m = map(int, ym.split("-"))
    y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return f"{y:04d}-{m:02d}"


def validate_entry(kind, amount, category, description, day, categories):
    """Return (clean_values, errors). clean_values is None when errors exist."""
    errors = []
    if amount is None or isinstance(amount, bool):
        errors.append("Enter an amount.")
    else:
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = None
            errors.append("Amount must be a number.")
        else:
            if not math.isfinite(amount):
                errors.append("Amount must be a valid number.")
            elif amount <= 0:
                errors.append("Amount must be greater than zero.")
            elif amount > MAX_AMOUNT:
                errors.append(f"Amount cannot exceed {money(MAX_AMOUNT)}.")
    if kind == "Expense" and category not in categories:
        errors.append("Choose a category.")
    description = (description or "").strip()
    if not description:
        errors.append("Enter a short description.")
    elif len(description) > MAX_DESC:
        errors.append(f"Description must be {MAX_DESC} characters or fewer.")
    if not isinstance(day, date):
        errors.append("Choose a valid date.")
    elif day > date.today():
        errors.append("Date cannot be in the future.")
    if errors:
        return None, errors
    return {"amount": round(amount, 2), "category": category,
            "description": description, "day": day.isoformat()}, []
