import os
import csv
import io
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, Response
)
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = 'disaster-relief-secret-key-college-project'

# Ensure database and tables exist at startup
init_db()

# -------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------
def get_now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def get_dashboard_metrics():
    """Calculates all key statistics required by the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total available resources count
    cursor.execute('SELECT COALESCE(SUM(quantity), 0) FROM inventory')
    total_resources = cursor.fetchone()[0]

    # Total active disasters
    cursor.execute("SELECT COUNT(*) FROM disasters WHERE status = 'Active'")
    active_disasters = cursor.fetchone()[0]

    # Total pending relief requests
    cursor.execute("SELECT COUNT(*) FROM relief_requests WHERE status = 'Pending'")
    pending_requests = cursor.fetchone()[0]

    # Total distributed resources
    cursor.execute('SELECT COALESCE(SUM(quantity), 0) FROM distributions')
    total_distributed = cursor.fetchone()[0]

    # Total affected population
    cursor.execute("SELECT COALESCE(SUM(affected_population), 0) FROM disasters WHERE status = 'Active'")
    total_affected_population = cursor.fetchone()[0]

    # Critical / Low stock alert items count
    cursor.execute('SELECT COUNT(*) FROM inventory WHERE quantity <= threshold')
    low_stock_count = cursor.fetchone()[0]

    conn.close()

    return {
        'total_resources': total_resources,
        'active_disasters': active_disasters,
        'pending_requests': pending_requests,
        'total_distributed': total_distributed,
        'total_affected_population': total_affected_population,
        'low_stock_count': low_stock_count
    }

# -------------------------------------------------------------
# WEB ROUTES
# -------------------------------------------------------------

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Main system dashboard showing metrics, active alerts, and recent activities."""
    metrics = get_dashboard_metrics()
    conn = get_db_connection()

    # Recent active disasters
    disasters = conn.execute('''
        SELECT * FROM disasters 
        ORDER BY CASE severity 
            WHEN 'Critical' THEN 1 
            WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 
            ELSE 4 END, id DESC 
        LIMIT 5
    ''').fetchall()

    # Recent relief requests
    requests_list = conn.execute('''
        SELECT r.*, d.title AS disaster_title, i.item_name, i.unit
        FROM relief_requests r
        LEFT JOIN disasters d ON r.disaster_id = d.id
        LEFT JOIN inventory i ON r.item_id = i.id
        ORDER BY r.id DESC 
        LIMIT 6
    ''').fetchall()

    # Low stock inventory items
    low_stock_items = conn.execute('''
        SELECT * FROM inventory 
        WHERE quantity <= threshold 
        ORDER BY quantity ASC
    ''').fetchall()

    # Inventory category breakdown
    category_summary = conn.execute('''
        SELECT category, SUM(quantity) as total_qty, COUNT(*) as item_count 
        FROM inventory 
        GROUP BY category
    ''').fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        metrics=metrics,
        disasters=disasters,
        requests=requests_list,
        low_stock_items=low_stock_items,
        category_summary=category_summary,
        page='dashboard'
    )

# -------------------------------------------------------------
# INVENTORY MANAGEMENT
# -------------------------------------------------------------

@app.route('/inventory')
def inventory():
    """List of all supplies with category filter and search."""
    category_filter = request.args.get('category', 'All')
    search_query = request.args.get('search', '').strip()

    conn = get_db_connection()
    query = 'SELECT * FROM inventory WHERE 1=1'
    params = []

    if category_filter and category_filter != 'All':
        query += ' AND category = ?'
        params.append(category_filter)

    if search_query:
        query += ' AND (item_name LIKE ? OR storage_location LIKE ?)'
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard])

    query += ' ORDER BY category, item_name'
    items = conn.execute(query, params).fetchall()

    # Summary metrics for inventory page
    total_items_count = conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]
    low_stock_count = conn.execute('SELECT COUNT(*) FROM inventory WHERE quantity <= threshold').fetchone()[0]
    total_units_sum = conn.execute('SELECT COALESCE(SUM(quantity), 0) FROM inventory').fetchone()[0]

    conn.close()

    return render_template(
        'inventory.html',
        items=items,
        selected_category=category_filter,
        search_query=search_query,
        total_items_count=total_items_count,
        low_stock_count=low_stock_count,
        total_units_sum=total_units_sum,
        page='inventory'
    )

@app.route('/inventory/add', methods=['POST'])
def add_inventory():
    """Adds a new resource supply to the inventory database."""
    item_name = request.form.get('item_name', '').strip()
    category = request.form.get('category', '').strip()
    quantity = int(request.form.get('quantity', 0))
    unit = request.form.get('unit', '').strip()
    threshold = int(request.form.get('threshold', 50))
    storage_location = request.form.get('storage_location', '').strip()

    if not item_name or not category or not unit:
        flash('Item name, category, and unit are required!', 'danger')
        return redirect(url_for('inventory'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO inventory (item_name, category, quantity, unit, threshold, storage_location, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (item_name, category, quantity, unit, threshold, storage_location, get_now_str()))
    conn.commit()
    conn.close()

    flash(f'Resource "{item_name}" successfully added to inventory!', 'success')
    return redirect(url_for('inventory'))

@app.route('/inventory/edit/<int:item_id>', methods=['POST'])
def edit_inventory(item_id):
    """Updates an existing inventory item."""
    item_name = request.form.get('item_name', '').strip()
    category = request.form.get('category', '').strip()
    quantity = int(request.form.get('quantity', 0))
    unit = request.form.get('unit', '').strip()
    threshold = int(request.form.get('threshold', 50))
    storage_location = request.form.get('storage_location', '').strip()

    conn = get_db_connection()
    conn.execute('''
        UPDATE inventory 
        SET item_name = ?, category = ?, quantity = ?, unit = ?, threshold = ?, storage_location = ?, last_updated = ?
        WHERE id = ?
    ''', (item_name, category, quantity, unit, threshold, storage_location, get_now_str(), item_id))
    conn.commit()
    conn.close()

    flash(f'Inventory item "{item_name}" updated successfully.', 'success')
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:item_id>', methods=['POST'])
def delete_inventory(item_id):
    """Deletes an item from inventory."""
    conn = get_db_connection()
    conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

    flash('Inventory item removed successfully.', 'info')
    return redirect(url_for('inventory'))

# -------------------------------------------------------------
# DISASTER AREAS MANAGEMENT
# -------------------------------------------------------------

@app.route('/disasters')
def disasters():
    """List of all registered disaster zones and affected areas."""
    status_filter = request.args.get('status', 'All')
    severity_filter = request.args.get('severity', 'All')

    conn = get_db_connection()
    query = 'SELECT * FROM disasters WHERE 1=1'
    params = []

    if status_filter and status_filter != 'All':
        query += ' AND status = ?'
        params.append(status_filter)

    if severity_filter and severity_filter != 'All':
        query += ' AND severity = ?'
        params.append(severity_filter)

    query += ' ORDER BY id DESC'
    disaster_list = conn.execute(query, params).fetchall()

    active_count = conn.execute("SELECT COUNT(*) FROM disasters WHERE status = 'Active'").fetchone()[0]
    total_pop = conn.execute("SELECT COALESCE(SUM(affected_population), 0) FROM disasters WHERE status = 'Active'").fetchone()[0]
    resolved_count = conn.execute("SELECT COUNT(*) FROM disasters WHERE status = 'Resolved'").fetchone()[0]

    conn.close()

    return render_template(
        'disasters.html',
        disasters=disaster_list,
        selected_status=status_filter,
        selected_severity=severity_filter,
        active_count=active_count,
        total_pop=total_pop,
        resolved_count=resolved_count,
        page='disasters'
    )

@app.route('/disasters/add', methods=['POST'])
def add_disaster():
    """Registers a new disaster incident area."""
    title = request.form.get('title', '').strip()
    disaster_type = request.form.get('type', '').strip()
    location = request.form.get('location', '').strip()
    severity = request.form.get('severity', 'High').strip()
    affected_population = int(request.form.get('affected_population', 0))
    status = request.form.get('status', 'Active').strip()
    notes = request.form.get('notes', '').strip()

    if not title or not location or not disaster_type:
        flash('Title, disaster type, and location are mandatory fields.', 'danger')
        return redirect(url_for('disasters'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO disasters (title, type, location, severity, affected_population, status, date_reported, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, disaster_type, location, severity, affected_population, status, get_now_str(), notes))
    conn.commit()
    conn.close()

    flash(f'Disaster incident "{title}" registered successfully.', 'success')
    return redirect(url_for('disasters'))

@app.route('/disasters/edit/<int:disaster_id>', methods=['POST'])
def edit_disaster(disaster_id):
    """Updates disaster area details and status."""
    title = request.form.get('title', '').strip()
    disaster_type = request.form.get('type', '').strip()
    location = request.form.get('location', '').strip()
    severity = request.form.get('severity', 'High').strip()
    affected_population = int(request.form.get('affected_population', 0))
    status = request.form.get('status', 'Active').strip()
    notes = request.form.get('notes', '').strip()

    conn = get_db_connection()
    conn.execute('''
        UPDATE disasters 
        SET title = ?, type = ?, location = ?, severity = ?, affected_population = ?, status = ?, notes = ?
        WHERE id = ?
    ''', (title, disaster_type, location, severity, affected_population, status, notes, disaster_id))
    conn.commit()
    conn.close()

    flash(f'Disaster record "{title}" updated.', 'success')
    return redirect(url_for('disasters'))

@app.route('/disasters/delete/<int:disaster_id>', methods=['POST'])
def delete_disaster(disaster_id):
    """Deletes a disaster entry."""
    conn = get_db_connection()
    conn.execute('DELETE FROM disasters WHERE id = ?', (disaster_id,))
    conn.commit()
    conn.close()

    flash('Disaster record deleted.', 'info')
    return redirect(url_for('disasters'))

# -------------------------------------------------------------
# RELIEF REQUESTS & RESOURCE ALLOCATION
# -------------------------------------------------------------

@app.route('/requests')
def relief_requests():
    """List of incoming relief requests and status management."""
    status_filter = request.args.get('status', 'All')

    conn = get_db_connection()
    query = '''
        SELECT r.*, d.title AS disaster_title, i.item_name, i.unit, i.quantity AS stock_available
        FROM relief_requests r
        LEFT JOIN disasters d ON r.disaster_id = d.id
        LEFT JOIN inventory i ON r.item_id = i.id
        WHERE 1=1
    '''
    params = []

    if status_filter and status_filter != 'All':
        query += ' AND r.status = ?'
        params.append(status_filter)

    query += ' ORDER BY CASE r.urgency WHEN "Critical" THEN 1 WHEN "High" THEN 2 ELSE 3 END, r.id DESC'
    requests_list = conn.execute(query, params).fetchall()

    # Dropdowns data for the request form
    active_disasters = conn.execute("SELECT id, title, location FROM disasters ORDER BY title").fetchall()
    inventory_items = conn.execute("SELECT id, item_name, unit, quantity FROM inventory ORDER BY item_name").fetchall()

    pending_count = conn.execute("SELECT COUNT(*) FROM relief_requests WHERE status = 'Pending'").fetchone()[0]
    allocated_count = conn.execute("SELECT COUNT(*) FROM relief_requests WHERE status = 'Allocated'").fetchone()[0]

    conn.close()

    return render_template(
        'requests.html',
        requests=requests_list,
        active_disasters=active_disasters,
        inventory_items=inventory_items,
        selected_status=status_filter,
        pending_count=pending_count,
        allocated_count=allocated_count,
        page='requests'
    )

@app.route('/requests/add', methods=['POST'])
def add_request():
    """Creates a new relief request from ground teams or affected communities."""
    requester_name = request.form.get('requester_name', '').strip()
    contact_number = request.form.get('contact_number', '').strip()
    disaster_id = request.form.get('disaster_id')
    location = request.form.get('location', '').strip()
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))
    urgency = request.form.get('urgency', 'Normal').strip()
    notes = request.form.get('notes', '').strip()

    if not requester_name or not contact_number or not location or not item_id:
        flash('Requester name, contact, location, and requested item are mandatory.', 'danger')
        return redirect(url_for('relief_requests'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO relief_requests (
            requester_name, contact_number, disaster_id, location, item_id, quantity, urgency, status, request_date, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
    ''', (requester_name, contact_number, disaster_id if disaster_id else None, location, item_id, quantity, urgency, get_now_str(), notes))
    conn.commit()
    conn.close()

    flash(f'Relief request from "{requester_name}" logged successfully with Pending status.', 'success')
    return redirect(url_for('relief_requests'))

@app.route('/requests/status/<int:req_id>/<string:new_status>', methods=['POST'])
def update_request_status(req_id, new_status):
    """Directly updates request status to Approved or Rejected."""
    if new_status not in ['Pending', 'Approved', 'Rejected']:
        flash('Invalid status operation.', 'danger')
        return redirect(url_for('relief_requests'))

    conn = get_db_connection()
    conn.execute('UPDATE relief_requests SET status = ? WHERE id = ?', (new_status, req_id))
    conn.commit()
    conn.close()

    flash(f'Request #{req_id} marked as {new_status}.', 'info')
    return redirect(url_for('relief_requests'))

@app.route('/requests/allocate/<int:req_id>', methods=['POST'])
def allocate_resources(req_id):
    """
    CRITICAL FEATURE:
    Fulfills a relief request by deducting required supplies from inventory,
    recording an official distribution audit log, and marking request as 'Allocated'.
    """
    officer_name = request.form.get('officer_name', 'Relief Logistics Officer').strip()
    remarks = request.form.get('remarks', 'Allocated and dispatched from central depot.').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch request and linked item
    req = cursor.execute('''
        SELECT r.*, i.item_name, i.unit, i.quantity AS stock_available, i.threshold
        FROM relief_requests r
        JOIN inventory i ON r.item_id = i.id
        WHERE r.id = ?
    ''', (req_id,)).fetchone()

    if not req:
        conn.close()
        flash('Request not found or inventory item was unlinked.', 'danger')
        return redirect(url_for('relief_requests'))

    if req['status'] == 'Allocated':
        conn.close()
        flash(f'Request #{req_id} is already marked as Allocated.', 'warning')
        return redirect(url_for('relief_requests'))

    requested_qty = req['quantity']
    available_qty = req['stock_available']

    # Stock availability verification
    if available_qty < requested_qty:
        conn.close()
        flash(
            f'Insufficient stock! Requested: {requested_qty} {req["unit"]}, but only {available_qty} {req["unit"]} available in inventory. Please restock first.',
            'danger'
        )
        return redirect(url_for('relief_requests'))

    try:
        # 1. Deduct quantity from inventory
        new_quantity = available_qty - requested_qty
        cursor.execute('''
            UPDATE inventory 
            SET quantity = ?, last_updated = ? 
            WHERE id = ?
        ''', (new_quantity, get_now_str(), req['item_id']))

        # 2. Update request status to 'Allocated'
        cursor.execute('''
            UPDATE relief_requests 
            SET status = 'Allocated' 
            WHERE id = ?
        ''', (req_id,))

        # 3. Create Distribution Audit Log
        cursor.execute('''
            INSERT INTO distributions (
                request_id, disaster_id, item_id, item_name, quantity, unit, recipient_area, officer_name, distribution_date, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            req_id,
            req['disaster_id'],
            req['item_id'],
            req['item_name'],
            requested_qty,
            req['unit'],
            req['location'],
            officer_name,
            get_now_str(),
            remarks
        ))

        conn.commit()
        flash(
            f'Success! Allocated {requested_qty} {req["unit"]} of "{req["item_name"]}". Inventory updated (remaining: {new_quantity} {req["unit"]}).',
            'success'
        )
    except Exception as e:
        conn.rollback()
        flash(f'Allocation failed: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('relief_requests'))

# -------------------------------------------------------------
# DISTRIBUTION HISTORY & REPORTS
# -------------------------------------------------------------

@app.route('/distribution')
def distribution():
    """Audit log of all relief supplies distributed to affected areas."""
    search_query = request.args.get('search', '').strip()

    conn = get_db_connection()
    query = '''
        SELECT dist.*, d.title AS disaster_title
        FROM distributions dist
        LEFT JOIN disasters d ON dist.disaster_id = d.id
        WHERE 1=1
    '''
    params = []

    if search_query:
        query += ' AND (dist.item_name LIKE ? OR dist.recipient_area LIKE ? OR dist.officer_name LIKE ?)'
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard, wildcard])

    query += ' ORDER BY dist.id DESC'
    distribution_list = conn.execute(query, params).fetchall()

    # Form dropdown data for manual direct distribution
    inventory_items = conn.execute('SELECT id, item_name, unit, quantity FROM inventory ORDER BY item_name').fetchall()
    disasters_list = conn.execute('SELECT id, title, location FROM disasters ORDER BY title').fetchall()

    total_distributions = len(distribution_list)
    total_items_distributed = conn.execute('SELECT COALESCE(SUM(quantity), 0) FROM distributions').fetchone()[0]

    conn.close()

    return render_template(
        'distribution.html',
        distributions=distribution_list,
        inventory_items=inventory_items,
        disasters=disasters_list,
        search_query=search_query,
        total_distributions=total_distributions,
        total_items_distributed=total_items_distributed,
        page='distribution'
    )

@app.route('/distribution/add', methods=['POST'])
def add_distribution():
    """Allows direct relief dispatch logging (without pre-existing request)."""
    item_id = request.form.get('item_id')
    disaster_id = request.form.get('disaster_id')
    recipient_area = request.form.get('recipient_area', '').strip()
    quantity = int(request.form.get('quantity', 1))
    officer_name = request.form.get('officer_name', '').strip()
    remarks = request.form.get('remarks', '').strip()

    if not item_id or not recipient_area or not officer_name or quantity <= 0:
        flash('Item, recipient location, officer name, and positive quantity are required.', 'danger')
        return redirect(url_for('distribution'))

    conn = get_db_connection()
    cursor = conn.cursor()

    item = cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
    if not item:
        conn.close()
        flash('Selected inventory item does not exist.', 'danger')
        return redirect(url_for('distribution'))

    if item['quantity'] < quantity:
        conn.close()
        flash(f'Cannot distribute: Requested {quantity} {item["unit"]}, but only {item["quantity"]} available in stock.', 'danger')
        return redirect(url_for('distribution'))

    try:
        # Deduct from inventory
        new_quantity = item['quantity'] - quantity
        cursor.execute('UPDATE inventory SET quantity = ?, last_updated = ? WHERE id = ?', (new_quantity, get_now_str(), item_id))

        # Log distribution
        cursor.execute('''
            INSERT INTO distributions (
                request_id, disaster_id, item_id, item_name, quantity, unit, recipient_area, officer_name, distribution_date, remarks
            ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            disaster_id if disaster_id else None,
            item_id,
            item['item_name'],
            quantity,
            item['unit'],
            recipient_area,
            officer_name,
            get_now_str(),
            remarks
        ))

        conn.commit()
        flash(f'Dispatched {quantity} {item["unit"]} of "{item["item_name"]}". Updated inventory balance: {new_quantity}.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Distribution failed: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('distribution'))

@app.route('/reports')
def reports():
    """Generates analytics, category summaries, and printable reports."""
    conn = get_db_connection()
    metrics = get_dashboard_metrics()

    # Category-wise supply breakdown
    category_data = conn.execute('''
        SELECT category, 
               COUNT(*) as item_types, 
               SUM(quantity) as total_units,
               SUM(CASE WHEN quantity <= threshold THEN 1 ELSE 0 END) as low_stock_items
        FROM inventory 
        GROUP BY category
    ''').fetchall()

    # Distribution by item
    item_distributions = conn.execute('''
        SELECT item_name, unit, SUM(quantity) as total_distributed, COUNT(*) as delivery_count
        FROM distributions
        GROUP BY item_name, unit
        ORDER BY total_distributed DESC
    ''').fetchall()

    # Disasters summary with affected population
    disasters_summary = conn.execute('''
        SELECT title, type, location, severity, status, affected_population,
               (SELECT COUNT(*) FROM relief_requests WHERE disaster_id = disasters.id) as request_count
        FROM disasters
        ORDER BY status, severity
    ''').fetchall()

    conn.close()

    return render_template(
        'reports.html',
        metrics=metrics,
        category_data=category_data,
        item_distributions=item_distributions,
        disasters_summary=disasters_summary,
        generated_at=get_now_str(),
        page='reports'
    )

@app.route('/api/export-distribution-csv')
def export_distribution_csv():
    """Exports distribution history as a downloadable CSV spreadsheet."""
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT dist.id, dist.distribution_date, dist.item_name, dist.quantity, dist.unit,
               dist.recipient_area, dist.officer_name, COALESCE(d.title, 'Direct Dispatch') AS disaster_event,
               dist.remarks
        FROM distributions dist
        LEFT JOIN disasters d ON dist.disaster_id = d.id
        ORDER BY dist.id DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Distribution ID', 'Date & Time', 'Item Name', 'Quantity', 'Unit',
        'Recipient Area / Camp', 'Dispatched By (Officer)', 'Disaster Event', 'Remarks'
    ])

    for row in rows:
        writer.writerow([
            row['id'], row['distribution_date'], row['item_name'], row['quantity'],
            row['unit'], row['recipient_area'], row['officer_name'], row['disaster_event'],
            row['remarks'] or 'N/A'
        ])

    output.seek(0)
    filename = f"disaster_distribution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# -------------------------------------------------------------
# JSON API ENDPOINTS (For AJAX or external clients)
# -------------------------------------------------------------

@app.route('/api/stats')
def api_stats():
    """Returns key metrics in JSON format."""
    return jsonify(get_dashboard_metrics())

# -------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -------------------------------------------------------------
if __name__ == '__main__':
    # Running locally on port 5000 with debug enabled for easy student development
    print("===============================================================")
    print("  DISASTER RELIEF AND RESOURCE MANAGEMENT SYSTEM (FLASK)")
    print("  Server is starting up...")
    print("  Open your browser and navigate to: http://127.0.0.1:5000")
    print("===============================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
