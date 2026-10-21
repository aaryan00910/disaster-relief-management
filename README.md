# 🚨 Disaster Relief & Resource Management System

A modern, responsive full-stack web application designed for emergency crisis response, inventory stockpiling, disaster zone tracking, and automated relief aid allocation.

Built with **Python Flask**, **SQLite3**, **HTML5**, **CSS3**, and **Vanilla JavaScript**. Perfect for second-year engineering college projects, demonstrations, and emergency response operations.

---

## 📸 Key Features

1. **Situational Operations Dashboard**:
   - Live metrics: Total Resources Available, Active Disaster Zones, Pending Relief Requests, and Total Distributed Aid.
   - Low-stock warning panel with visual threshold progress bars.
   - Quick activity feeds for active incidents and recent relief requests.
2. **Resource Inventory Management**:
   - Full lifecycle management for **Food, Water, Medicines, Clothes, Blankets, and Shelter Tools**.
   - Category filtering and search.
   - Low-stock safety buffer alerts (`quantity <= threshold`).
   - Add, edit, and delete supply items.
3. **Disaster Zones Management**:
   - Register and monitor disaster incidents (Flood, Earthquake, Cyclone, Fire, Landslide, etc.).
   - Severity categorization (Critical, High, Medium, Low) and affected population estimation.
   - Status updates (Active Emergency vs. Resolved / Stabilized).
4. **Relief Requests & Automated Resource Allocation**:
   - Field volunteers and camp leaders can submit specific aid requests with urgency ratings.
   - **Automated Stock Deduction**: Allocating aid verifies warehouse stock, subtracts the dispatched quantity, generates an audit entry, and updates the ticket status.
   - Built-in deficit protection prevents dispatching unavailable stock.
5. **Distribution History & Strategic Reports**:
   - Verified ledger of every dispatched consignment with date, officer name, and recipient camp.
   - Direct field dispatch recording without prior requests.
   - **One-click CSV Export** of distribution logs.
   - **Printable Executive Report View** styled for clean college report submissions.

---

## 🎨 Design Theme

- **Background**: Deep Navy (`#0a0e17`) and Obsidian Slate (`#0f172a`).
- **Highlights & Accents**: Crimson Emergency Red (`#ef4444`) with subtle red glow effects.
- **Typography**: Clean high-contrast white text (`#f8fafc`) with muted slate metadata (`#94a3b8`).
- **Responsive Elements**: Mobile slide-out drawer, elevated glass-style cards, clean tables, and accessible modals.

---

## 🗄️ Database Architecture (SQLite3)

The application uses an SQLite database named `disaster_relief.db`. All tables are created automatically on the first launch and seeded with realistic sample data:

```
+--------------------+        +---------------------+
|     disasters      |        |      inventory      |
+--------------------+        +---------------------+
| id (PK)            |<---+   | id (PK)             |<---+
| title              |    |   | item_name           |    |
| type               |    |   | category            |    |
| location           |    |   | quantity            |    |
| severity           |    |   | unit                |    |
| affected_pop       |    |   | threshold           |    |
| status             |    |   | storage_location    |    |
| date_reported      |    |   | last_updated        |    |
+--------------------+    |   +---------------------+    |
                          |                              |
                          |                              |
+--------------------+    |   +---------------------+    |
|  relief_requests   |    |   |    distributions    |    |
+--------------------+    |   +---------------------+    |
| id (PK)            |    |   | id (PK)             |    |
| requester_name     |    |   | request_id (FK)     |    |
| contact_number     |    |   | disaster_id (FK)----+----+
| disaster_id (FK)---+----+   | item_id (FK)--------+----+
| location           |        | item_name           |
| item_id (FK)-------+--------| quantity            |
| quantity           |        | unit                |
| urgency            |        | recipient_area      |
| status             |        | officer_name        |
| request_date       |        | distribution_date   |
| notes              |        | remarks             |
+--------------------+        +---------------------+
```

---

## 🚀 How to Run the Application

### Option A: The Easiest Way (Single Click on Windows)
Simply double-click the **`run.bat`** file located in this project folder.
It will automatically:
1. Verify Python and install required packages.
2. Launch the Flask web server.
3. Automatically open your default web browser to `http://127.0.0.1:5000`.

---

### Option B: Using the Terminal / Command Prompt

1. Open **Command Prompt** or **PowerShell** in this project folder:
   ```bash
   cd "c:\Users\naren\OneDrive\Documents\disaster relif system"
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask application:
   ```bash
   python app.py
   ```

5. Open your web browser and go to:
   ```
   http://127.0.0.1:5000
   ```

---

## 📁 Project Structure

```
disaster relif system/
│
├── app.py                     # Main Flask application with routing & business logic
├── database.py                # Database connection, schema setup & seed data
├── requirements.txt           # Python dependencies (Flask)
├── run.bat                    # One-click Windows starter script
├── .gitignore                 # Files excluded from Git version control
├── README.md                  # Complete project documentation
│
├── static/
│   ├── css/
│   │   └── style.css          # Dark navy & red responsive CSS stylesheet
│   └── js/
│       └── app.js             # Client-side modals, search, and dynamic forms
│
└── templates/
    ├── base.html              # Core navigation layout and sidebar
    ├── dashboard.html         # Main metrics & situational overview
    ├── inventory.html         # Supplies directory & add/edit modals
    ├── disasters.html         # Crisis zones and incident tracking
    ├── requests.html          # Relief aid queue & allocation engine
    ├── distribution.html      # Dispatched aid ledger & direct logging
    └── reports.html           # Strategic reports & printable analytics
```

---

## 🌐 Step-by-Step: How to Upload to GitHub

Follow these simple commands to push your project to your GitHub profile:

1. Create a new repository on [GitHub](https://github.com/new) (e.g., named `disaster-relief-system`). Leave "Add a README" **unchecked**.
2. In your project folder terminal, run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Disaster Relief & Resource Management System"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/disaster-relief-system.git
   git push -u origin main
   ```
*(Replace `YOUR_USERNAME` with your actual GitHub username).*

---

## ☁️ Step-by-Step: How to Deploy Online for Free

### Method 1: Deploy on Render.com (Recommended)
1. Sign up for free at [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Select **New Web Service**.
4. Configure:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app` (or add `gunicorn` to `requirements.txt`)
5. Click **Deploy Web Service** — Render will give you a live HTTPS public link!

### Method 2: Deploy on PythonAnywhere.com
1. Register for a free Beginner account on [PythonAnywhere.com](https://www.pythonanywhere.com).
2. Go to the **Web** tab and click **Add a new web app**.
3. Choose **Flask** and select **Python 3.10+**.
4. Upload your files or clone from GitHub.
5. Reload the web app and view it live at `yourusername.pythonanywhere.com`.

---

## 🎓 College Viva / Project Presentation Questions & Answers

**Q1: Why did you choose SQLite over MySQL or PostgreSQL?**  
*Answer:* SQLite is serverless, zero-configuration, and file-based. It requires no background database daemon, making it exceptionally lightweight, reliable, and easily portable for a standalone disaster relief management node that can run locally on field laptops without internet connectivity.

**Q2: How does the system prevent allocating resources that do not exist?**  
*Answer:* In `app.py`, the `allocate_resources()` route queries the current warehouse stock of the linked item before executing the transaction. If `available_quantity < requested_quantity`, the transaction is aborted and a warning notification is displayed. If sufficient, the deduction and distribution log are executed within a database transaction to ensure atomicity.

**Q3: What design pattern did you follow?**  
*Answer:* We followed the standard Model-View-Controller (MVC) architectural pattern:
- **Model**: `database.py` and SQLite schema representing relief data entities.
- **View**: Jinja2 HTML templates in `templates/` and styling in `static/css/style.css`.
- **Controller**: Flask route handlers in `app.py` controlling the application logic.

**Q4: Is the system responsive on mobile devices?**  
*Answer:* Yes. The CSS incorporates media queries (`@media (max-width: 768px)`), a collapsable hamburger sidebar drawer, responsive table horizontal scrolling, and flexible CSS grid layouts.

---

## 📄 License
This project is open-source and free to use for educational and academic purposes.
