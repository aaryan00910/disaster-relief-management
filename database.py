import sqlite3
import os
from datetime import datetime

DATABASE_NAME = 'disaster_relief.db'

def get_db_path():
    """Returns absolute path to the SQLite database file in the project folder."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_NAME)

def get_db_connection():
    """Establishes and returns a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes tables and populates sample data if tables are empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Disasters Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disasters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            location TEXT NOT NULL,
            severity TEXT NOT NULL,
            affected_population INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Active',
            date_reported TEXT NOT NULL,
            notes TEXT
        )
    ''')

    # 2. Inventory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT NOT NULL,
            threshold INTEGER NOT NULL DEFAULT 50,
            storage_location TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    ''')

    # 3. Relief Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relief_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            disaster_id INTEGER,
            location TEXT NOT NULL,
            item_id INTEGER,
            quantity INTEGER NOT NULL,
            urgency TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            request_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (disaster_id) REFERENCES disasters(id) ON DELETE SET NULL,
            FOREIGN KEY (item_id) REFERENCES inventory(id) ON DELETE SET NULL
        )
    ''')

    # 4. Distribution History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            disaster_id INTEGER,
            item_id INTEGER,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL,
            recipient_area TEXT NOT NULL,
            officer_name TEXT NOT NULL,
            distribution_date TEXT NOT NULL,
            remarks TEXT,
            FOREIGN KEY (request_id) REFERENCES relief_requests(id) ON DELETE SET NULL,
            FOREIGN KEY (disaster_id) REFERENCES disasters(id) ON DELETE SET NULL,
            FOREIGN KEY (item_id) REFERENCES inventory(id) ON DELETE SET NULL
        )
    ''')

    conn.commit()

    # Seed initial data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM inventory')
    if cursor.fetchone()[0] == 0:
        seed_sample_data(conn)

    conn.close()

def seed_sample_data(conn):
    """Inserts realistic sample records for demonstration and college evaluation."""
    cursor = conn.cursor()
    today_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Sample Disasters
    disasters_data = [
        ('Riverfront Flash Flood', 'Flood', 'Eastern River Basin, Sector 4', 'Critical', 14500, 'Active', today_str, 'Heavy rainfall breached local barriers. Immediate food and shelter required.'),
        ('Seismic Tremor & Landslide', 'Earthquake', 'Northern Hill District', 'High', 8200, 'Active', today_str, 'Roadways blocked, 150 homes damaged. Blankets and medical supplies needed.'),
        ('Coastal Cyclone Warning', 'Cyclone', 'Southern Coastal Bay', 'High', 26000, 'Active', today_str, 'Evacuation centers active. Safe drinking water in high demand.'),
        ('Industrial Suburb Fire Outbreak', 'Fire', 'Western Industrial Zone', 'Medium', 1200, 'Resolved', today_str, 'Contained by emergency services. Emergency burn kits provided.')
    ]
    cursor.executemany('''
        INSERT INTO disasters (title, type, location, severity, affected_population, status, date_reported, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', disasters_data)

    # Sample Inventory
    inventory_data = [
        ('Dry Ration Food Packets', 'Food', 2400, 'Packets', 300, 'Warehouse Alpha - Bay 1', today_str),
        ('Purified Drinking Water Bottles', 'Water', 4800, 'Liters', 600, 'Central Logistics Hub', today_str),
        ('Emergency First-Aid Kits', 'Medicines', 350, 'Kits', 100, 'Medical Depot Station', today_str),
        ('Paracetamol & Antibiotic Packs', 'Medicines', 80, 'Packs', 150, 'Medical Depot Station', today_str), # Low stock alert example
        ('Thermal Woolen Blankets', 'Blankets', 1200, 'Pieces', 200, 'Warehouse Beta - Rack 4', today_str),
        ('Clean Adult & Children Clothes', 'Clothes', 1600, 'Sets', 250, 'Relief Depot South', today_str),
        ('Tarpaulin & Tent Sheets', 'Shelter/Tools', 420, 'Sheets', 100, 'Warehouse Alpha - Bay 3', today_str),
        ('Water Purification Tablets', 'Water', 6000, 'Packs', 500, 'Central Logistics Hub', today_str)
    ]
    cursor.executemany('''
        INSERT INTO inventory (item_name, category, quantity, unit, threshold, storage_location, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', inventory_data)

    # Sample Relief Requests
    requests_data = [
        ('Community Center Shelter Team', '+91 98765 43210', 1, 'Eastern River Basin Shelter #2', 1, 500, 'Critical', 'Pending', today_str, 'For 500 stranded flood victims.'),
        ('Volunteer Red Cross Unit', '+91 98111 22334', 2, 'Northern Hill Camp Alpha', 5, 300, 'High', 'Approved', today_str, 'Freezing night temperatures expected in hill camp.'),
        ('District Medical Officer', '+91 94222 33445', 1, 'Riverfront Medical Outpost', 3, 100, 'Critical', 'Allocated', today_str, 'Urgent supplies for injury treatments.'),
        ('Local Panchayat Representative', '+91 97333 44556', 3, 'Southern Coastal Evac Center', 2, 800, 'High', 'Pending', today_str, 'Drinking water pipeline damaged by cyclonic winds.'),
        ('Urban Rescue Team', '+91 99444 55667', 4, 'Western Sector Aid Post', 6, 200, 'Normal', 'Allocated', today_str, 'Replacement clothing for fire victims.')
    ]
    cursor.executemany('''
        INSERT INTO relief_requests (requester_name, contact_number, disaster_id, location, item_id, quantity, urgency, status, request_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', requests_data)

    # Sample Distributions (already completed for initial reports)
    distributions_data = [
        (3, 1, 3, 'Emergency First-Aid Kits', 100, 'Kits', 'Riverfront Medical Outpost', 'Officer R. Sharma', today_str, 'Delivered via emergency rescue boat.'),
        (5, 4, 6, 'Clean Adult & Children Clothes', 200, 'Sets', 'Western Sector Aid Post', 'Coordinator A. Verma', today_str, 'Handed over to community shelter head.')
    ]
    cursor.executemany('''
        INSERT INTO distributions (request_id, disaster_id, item_id, item_name, quantity, unit, recipient_area, officer_name, distribution_date, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', distributions_data)

    conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with sample data.")
