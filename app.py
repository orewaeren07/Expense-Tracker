"""Pocket Ledger - simple expense tracker (Streamlit + SQLite + Plotly)."""
from datetime import date
from html import escape

import streamlit as st

import calculations as calc
import charts
import database as db

st.set_page_config(page_title="Pocket Ledger", page_icon="💰", layout="centered")

PAGES = ["Dashboard", "Add Income", "Add Expense", "Reports"]

CSS = """
<style>
.block-container{max-width:860px;padding-top:1.5rem;padding-bottom:4rem}
footer{visibility:hidden}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:12px 0 22px}
.card{border-radius:18px;padding:18px 20px;border:1px solid rgba(128,128,128,.18);
      box-shadow:0 2px 12px rgba(0,0,0,.10)}
.card .lbl{font-size:.85rem;opacity:.8;margin-bottom:6px}
.card .val{font-size:1.65rem;font-weight:700;letter-spacing:-.01em;word-break:break-word}
.card.balance{background:#0f766e;color:#fff;border-color:transparent}
.card.income{background:rgba(22,163,74,.12)} .card.income .val{color:#16a34a}
.card.expense{background:rgba(220,38,38,.10)} .card.expense .val{color:#dc2626}
.panel{border-radius:18px;padding:18px 20px;border:1px solid rgba(128,128,128,.2);
       background:rgba(128,128,128,.06);box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:18px}
.big{font-size:1.9rem;font-weight:700;color:#dc2626}
.muted{opacity:.7;font-size:.85rem}
.row{margin-top:14px}
.row .top{display:flex;justify-content:space-between;gap:8px;font-size:.95rem}
.bar{height:8px;border-radius:99px;background:rgba(128,128,128,.2);margin-top:6px;overflow:hidden}
.bar>span{display:block;height:100%;border-radius:99px;background:#dc2626}
.stButton>button,.stFormSubmitButton>button{border-radius:12px;font-weight:600}
div[data-testid="stForm"],div[data-testid="stExpander"]{border-radius:16px}
@media(max-width:640px){.card .val{font-size:1.4rem}.big{font-size:1.6rem}.block-container{padding-left:1rem;padding-right:1rem;padding-top:1rem}.card{padding:14px 16px}.cards{gap:10px}}
</style>
"""


# ---------- helpers ----------
def run(fn, *args):
    """Call a database function; show a friendly error and stop on failure."""
    try:
        return fn(*args)
    except db.DatabaseError as exc:
        st.error(str(exc))
        st.stop()


def flash(msg, icon="✅"):
    st.session_state["flash"] = (msg, icon)


def md_escape(text):
    for ch in "\\`*_[]$~<>#":
        text = text.replace(ch, "\\" + ch)
    return text


def card(label, value, tone):
    return (f'<div class="card {tone}"><div class="lbl">{label}</div>'
            f'<div class="val">{value}</div></div>')


def cards_html(*items):
    return '<div class="cards">' + "".join(card(*i) for i in items) + "</div>"


def breakdown_html(breakdown, limit=None):
    total = sum(breakdown.values()) or 1
    out = ""
    for cat, amt in list(breakdown.items())[:limit]:
        pct = amt / total * 100
        out += (f'<div class="row"><div class="top"><span>{calc.CATEGORY_ICONS.get(cat, "")} '
                f'{escape(cat)}</span><span><b>{calc.money(amt)}</b> '
                f'<span class="muted">{pct:.0f}%</span></span></div>'
                f'<div class="bar"><span style="width:{pct:.1f}%"></span></div></div>')
    return out


# ---------- Dashboard ----------
def page_dashboard():
    rows = run(db.get_transactions)
    income, expense, balance = calc.totals(rows)

    if not rows:
        st.info("No entries yet. Add income or an expense, or load sample data to try the app.")
        if st.button("Load sample data"):
            run(db.seed_sample_data)
            flash("Sample data loaded", "🧪")
            st.rerun()

    st.markdown(cards_html(("Total Balance", calc.money(balance), "balance"),
                           ("Total Income", calc.money(income), "income"),
                           ("Total Expenses", calc.money(expense), "expense")),
                unsafe_allow_html=True)

    ym = date.today().strftime("%Y-%m")
    this_m = [r for r in rows if r["date"].startswith(ym)]
    prev_m = [r for r in rows if r["date"].startswith(calc.previous_month(ym))]
    m_exp = calc.totals(this_m)[1]
    p_exp = calc.totals(prev_m)[1]
    if p_exp == 0:
        change = "No spending recorded last month"
    else:
        diff = (m_exp - p_exp) / p_exp * 100
        change = f"{abs(diff):.0f}% {'more' if diff > 0 else 'less'} than last month"
    top = calc.category_breakdown(this_m)
    body = breakdown_html(top, limit=4) if top else '<div class="muted row">No expenses this month yet.</div>'
    st.markdown(f'<div class="panel"><div class="muted">Monthly expense summary: '
                f'{calc.month_label(ym)}</div><div class="big">{calc.money(m_exp)}</div>'
                f'<div class="muted">{change}</div>{body}</div>', unsafe_allow_html=True)

    if rows:
        manage_entries(rows)


def manage_entries(rows):
    st.subheader("Manage entries")
    months = sorted({r["date"][:7] for r in rows}, reverse=True)
    c1, c2 = st.columns(2)
    month = c1.selectbox("Month", ["All time"] + months,
                         format_func=lambda m: m if m == "All time" else calc.month_label(m))
    kind = c2.selectbox("Type", ["All", "Income", "Expense"])
    shown = [r for r in rows
             if (month == "All time" or r["date"].startswith(month))
             and (kind == "All" or r["type"] == kind)]
    if not shown:
        st.info("No entries match these filters.")
        return
    limit = st.session_state.setdefault("limit", 10)
    for r in shown[:limit]:
        entry_editor(r)
    if len(shown) > limit and st.button(f"Show more ({len(shown) - limit} more)"):
        st.session_state["limit"] += 10
        st.rerun()


def entry_editor(r):
    rid, is_income = r["id"], r["type"] == "Income"
    label = (f"{'🟢 +' if is_income else '🔴 -'}{calc.money(r['amount'])}  "
             f"{md_escape(r['description'])}  ({r['date']})")
    with st.expander(label):
        if st.session_state.get("confirm_delete") == rid:
            st.warning("Delete this entry permanently?")
            a, b = st.columns(2)
            if a.button("Yes, delete", key=f"yes_{rid}", type="primary"):
                run(db.delete_transaction, rid)
                st.session_state.pop("confirm_delete", None)
                flash("Entry deleted", "🗑️")
                st.rerun()
            if b.button("Cancel", key=f"no_{rid}"):
                st.session_state.pop("confirm_delete", None)
                st.rerun()
            return
        row_date = date.fromisoformat(r["date"])
        cats = db.EXPENSE_CATEGORIES
        with st.form(f"edit_{rid}"):
            amount = st.number_input(f"Amount ({calc.CURRENCY})", min_value=0.01,
                                     max_value=calc.MAX_AMOUNT, value=float(r["amount"]),
                                     step=1.0, format="%.2f", key=f"amt_{rid}")
            if is_income:
                category = db.INCOME_CATEGORY
            else:
                idx = cats.index(r["category"]) if r["category"] in cats else len(cats) - 1
                category = st.selectbox("Category", cats, index=idx, key=f"cat_{rid}")
            desc = st.text_input("Description", value=r["description"],
                                 max_chars=calc.MAX_DESC, key=f"desc_{rid}")
            day = st.date_input("Date", value=row_date,
                                max_value=max(date.today(), row_date), key=f"day_{rid}")
            s, d = st.columns(2)
            save = s.form_submit_button("Save changes", type="primary", use_container_width=True)
            delete = d.form_submit_button("Delete", use_container_width=True)
        if delete:
            st.session_state["confirm_delete"] = rid
            st.rerun()
        if save:
            clean, errors = calc.validate_entry(r["type"], amount, category, desc, day,
                                                cats if not is_income else [])
            if errors:
                for e in errors:
                    st.error(e)
            else:
                run(db.update_transaction, rid, clean["amount"], clean["category"],
                    clean["description"], clean["day"])
                flash("Changes saved")
                st.rerun()


# ---------- Add income / expense ----------
def page_add(kind):
    is_income = kind == "Income"
    n = st.session_state.setdefault(f"n_{kind}", 0)   # bumping n resets the form
    k = f"{kind}_{n}"
    st.subheader("Add income" if is_income else "Add expense")
    cats = db.EXPENSE_CATEGORIES
    with st.form(f"add_{k}"):
        amount = st.number_input(f"Amount ({calc.CURRENCY})", min_value=0.01,
                                 max_value=calc.MAX_AMOUNT, value=None, step=1.0,
                                 format="%.2f", placeholder="0.00", key=f"amt_{k}")
        category = db.INCOME_CATEGORY if is_income else st.selectbox("Category", cats, key=f"cat_{k}")
        desc = st.text_input("Description", max_chars=calc.MAX_DESC, key=f"desc_{k}",
                             placeholder="e.g. Salary" if is_income else "e.g. Groceries")
        day = st.date_input("Date", value=date.today(), max_value=date.today(), key=f"day_{k}")
        submitted = st.form_submit_button("Save income" if is_income else "Save expense",
                                          type="primary", use_container_width=True)
    if submitted:
        clean, errors = calc.validate_entry(kind, amount, category, desc, day,
                                            [] if is_income else cats)
        if errors:
            for e in errors:
                st.error(e)
            return
        run(db.add_transaction, kind, clean["amount"], clean["category"],
            clean["description"], clean["day"])
        st.session_state[f"n_{kind}"] += 1
        flash(f"{kind} of {calc.money(clean['amount'])} saved")
        st.rerun()


# ---------- Reports ----------
def page_reports():
    rows_all = run(db.get_transactions)
    months = sorted({r["date"][:7] for r in rows_all} | {date.today().strftime("%Y-%m")},
                    reverse=True)
    ym = st.selectbox("Month", months, format_func=calc.month_label)
    rows = [r for r in rows_all if r["date"].startswith(ym)]
    income, expense, balance = calc.totals(rows)
    st.markdown(cards_html(("Income", calc.money(income), "income"),
                           ("Expenses", calc.money(expense), "expense"),
                           ("Remaining balance", calc.money(balance), "balance")),
                unsafe_allow_html=True)
    breakdown = calc.category_breakdown(rows)
    if not breakdown:
        st.info(f"No expenses recorded for {calc.month_label(ym)}.")
        return
    st.subheader("Where the money went")
    view = st.segmented_control("Chart type", ["Pie", "Bar"], default="Pie",
                                key="chart_type", label_visibility="collapsed") or "Pie"
    st.plotly_chart(charts.category_pie(breakdown) if view == "Pie"
                    else charts.category_bar(breakdown))
    st.markdown(f'<div class="panel">{breakdown_html(breakdown)}</div>', unsafe_allow_html=True)


# ---------- main ----------
def main():
    st.markdown(CSS, unsafe_allow_html=True)
    msg = st.session_state.pop("flash", None)
    if msg:
        st.toast(msg[0], icon=msg[1])
    try:
        db.init_db()
    except db.DatabaseError as exc:
        st.error(f"Could not open the database. {exc}")
        st.stop()

    st.title("💰 Pocket Ledger")
    # st.pills wraps onto a second line on narrow screens (segmented_control does not)
    page = st.pills("Navigate", PAGES, selection_mode="single", default="Dashboard",
                    key="page", label_visibility="collapsed") or "Dashboard"
    if page == "Dashboard":
        page_dashboard()
    elif page == "Add Income":
        page_add("Income")
    elif page == "Add Expense":
        page_add("Expense")
    else:
        page_reports()


main()
