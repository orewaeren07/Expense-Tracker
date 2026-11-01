# Pocket Ledger – Simple Expense Tracker

Python · Streamlit · SQLite · Plotly. No login, no accounts, no cloud services.

## Features
- **Dashboard**: total balance, income, expenses, this month's expense summary, and a *Manage entries* section to edit or delete any entry (with delete confirmation).
- **Add Income / Add Expense**: amount, description, date (and category for expenses). Categories: Food, Travel, Shopping, Education, Entertainment, Bills, Healthcare, Other.
- **Reports**: pick any month; see income, expenses, remaining balance, category breakdown, and a pie or bar chart.
- Amounts must be a number greater than zero (max 1,000,000,000); descriptions are required; dates cannot be in the future. The database also enforces `amount > 0`.
- Light and dark mode follow your device/browser setting (Streamlit menu → Settings can override).
- Currency symbol is `CURRENCY = "₹"` at the top of `calculations.py`.

## Project structure
```
app.py            Streamlit UI and navigation
database.py       All SQLite code (schema, CRUD, sample data)
calculations.py   Totals, breakdowns, formatting, input validation
charts.py         Plotly pie / bar charts
requirements.txt  Dependencies
android/          WebView wrapper source (see below)
```
Data is stored in `expenses.db` next to `app.py` (override with the `EXPENSE_DB` environment variable). It persists across restarts.

## Run the web app
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501. To use it from a phone on the same Wi-Fi: `streamlit run app.py --server.address 0.0.0.0` and open `http://<your-PC-IP>:8501`.

## Sample data
- Easiest: on an empty Dashboard, click **Load sample data** (adds ~36 entries over 3 months).
- Or from the terminal: `python database.py --seed` (does nothing if data already exists).
- To start fresh, stop the app and delete `expenses.db`.

## Android (WebView wrapper)
Streamlit does **not** produce a native APK. It is a Python server that renders a web page. The Android app here is a thin shell that displays that page in a `WebView`. Same Python code and same SQLite logic on every platform. The Python server must be running somewhere the phone can reach. I have not built or run the Android project in this environment, so treat it as a starting point.

### 1. Create the wrapper app
1. In Android Studio: **New Project → Empty Views Activity**, language **Kotlin**, package `com.example.pocketledger`, min SDK 24+.
2. Copy over the files from this repo's `android/` folder:
   - `MainActivity.kt` → `app/src/main/java/com/example/pocketledger/`
   - `AndroidManifest.xml` → replace the generated one
   - `network_security_config.xml` → `app/src/main/res/xml/` (create the `xml` folder)
3. Make sure `androidx.appcompat:appcompat` is in `app/build.gradle` dependencies (the template includes it).
4. Edit `appUrl` in `MainActivity.kt` (see the options below).
5. **Build → Build APK(s)** (or **Run** on a device/emulator). For a Play Store release you also need a signed release build.

### 2. Choose where the Python server runs
| Option | `appUrl` | Where data lives | Notes |
|---|---|---|---|
| Emulator + PC | `http://10.0.2.2:8501` | PC (`expenses.db`) | Best for testing. Run Streamlit with `--server.address 0.0.0.0`. |
| Phone + PC on same Wi-Fi | `http://<PC-LAN-IP>:8501` | PC | Add the IP to `network_security_config.xml`. PC must stay on. |
| Hosted server (VPS, etc.) | `https://your-domain` | Server | Use HTTPS. The app has no login, so protect it (VPN or reverse-proxy password) if it's public. |
| On the phone via Termux (advanced, experimental) | `http://127.0.0.1:8501` | Phone | Install Termux, then `pkg install python python-pip python-pyarrow`, copy the project, `pip install streamlit plotly`, run `streamlit run app.py`. Keep Termux running. Package builds on Android can be fiddly. |

Fully embedding Python + Streamlit inside the APK (e.g. with Chaquopy) is not something I'd recommend for this stack: Streamlit's dependencies (pandas, pyarrow) make it heavy and unreliable on-device.

## Troubleshooting
- *"Can't reach the server" in the app*: Streamlit isn't running, wrong `appUrl`, or a firewall blocks port 8501.
- *Blank page / cleartext error*: the host isn't listed in `network_security_config.xml` (or use HTTPS).
- *Database error message*: the folder must be writable; set `EXPENSE_DB` to a writable path.
