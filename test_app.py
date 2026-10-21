import unittest
from app import app
from database import init_db, get_db_connection

class DisasterReliefTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()

    def test_dashboard_route(self):
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Operations Dashboard', response.data)
        self.assertIn(b'Total Resources', response.data)

    def test_inventory_routes(self):
        # 1. View Inventory
        response = self.client.get('/inventory')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Resource Inventory Management', response.data)

        # 2. Add Item
        add_resp = self.client.post('/inventory/add', data={
            'item_name': 'Solar LED Flashlights',
            'category': 'Shelter/Tools',
            'quantity': 150,
            'unit': 'Units',
            'threshold': 30,
            'storage_location': 'Warehouse Test Bay 9'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)
        self.assertIn(b'Solar LED Flashlights', add_resp.data)

        # Check DB
        conn = get_db_connection()
        item = conn.execute("SELECT * FROM inventory WHERE item_name = 'Solar LED Flashlights'").fetchone()
        self.assertIsNotNone(item)
        item_id = item['id']

        # 3. Edit Item
        edit_resp = self.client.post(f'/inventory/edit/{item_id}', data={
            'item_name': 'Solar LED Flashlights (Pro)',
            'category': 'Shelter/Tools',
            'quantity': 180,
            'unit': 'Units',
            'threshold': 35,
            'storage_location': 'Warehouse Test Bay 9'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)
        self.assertIn(b'Solar LED Flashlights (Pro)', edit_resp.data)

        # 4. Delete Item
        del_resp = self.client.post(f'/inventory/delete/{item_id}', follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        conn.close()

    def test_disasters_routes(self):
        # 1. View Disasters
        response = self.client.get('/disasters')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Disaster-Affected Areas Management', response.data)

        # 2. Add Disaster
        add_resp = self.client.post('/disasters/add', data={
            'title': 'Test Monsoon Flash Flood',
            'type': 'Flood',
            'location': 'Sub-district North Delta',
            'severity': 'Critical',
            'affected_population': 4500,
            'status': 'Active',
            'notes': 'Test simulation disaster'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)
        self.assertIn(b'Test Monsoon Flash Flood', add_resp.data)

        # Check DB
        conn = get_db_connection()
        d = conn.execute("SELECT * FROM disasters WHERE title = 'Test Monsoon Flash Flood'").fetchone()
        self.assertIsNotNone(d)
        d_id = d['id']

        # 3. Edit Disaster
        edit_resp = self.client.post(f'/disasters/edit/{d_id}', data={
            'title': 'Test Monsoon Flash Flood (Contained)',
            'type': 'Flood',
            'location': 'Sub-district North Delta',
            'severity': 'Medium',
            'affected_population': 4000,
            'status': 'Resolved',
            'notes': 'Contained successfully'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)
        self.assertIn(b'Resolved', edit_resp.data)

        # 4. Delete Disaster
        del_resp = self.client.post(f'/disasters/delete/{d_id}', follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        conn.close()

    def test_requests_and_stock_allocation(self):
        # 1. View Requests
        response = self.client.get('/requests')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Relief Requests & Resource Allocation', response.data)

        # 2. Add Request for food packets
        conn = get_db_connection()
        food_item = conn.execute("SELECT * FROM inventory WHERE item_name = 'Dry Ration Food Packets'").fetchone()
        initial_stock = food_item['quantity']
        item_id = food_item['id']

        add_resp = self.client.post('/requests/add', data={
            'requester_name': 'Test Volunteer Captain',
            'contact_number': '+91 99999 88888',
            'disaster_id': 1,
            'location': 'Test Camp Zone 5',
            'item_id': item_id,
            'quantity': 50,
            'urgency': 'High',
            'notes': 'Urgent food test'
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)
        self.assertIn(b'Test Volunteer Captain', add_resp.data)

        req = conn.execute("SELECT * FROM relief_requests WHERE requester_name = 'Test Volunteer Captain'").fetchone()
        req_id = req['id']

        # 3. Test Allocate
        alloc_resp = self.client.post(f'/requests/allocate/{req_id}', data={
            'officer_name': 'Test Officer S. Rao',
            'remarks': 'Testing stock deduction'
        }, follow_redirects=True)
        self.assertEqual(alloc_resp.status_code, 200)
        self.assertIn(b'Allocated', alloc_resp.data)

        # Verify stock was deducted
        updated_food = conn.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()
        self.assertEqual(updated_food['quantity'], initial_stock - 50)

        # Verify distribution log was created
        dist = conn.execute("SELECT * FROM distributions WHERE request_id = ?", (req_id,)).fetchone()
        self.assertIsNotNone(dist)
        self.assertEqual(dist['quantity'], 50)
        self.assertEqual(dist['officer_name'], 'Test Officer S. Rao')
        conn.close()

    def test_distribution_and_reports(self):
        # 1. View Distribution
        dist_resp = self.client.get('/distribution')
        self.assertEqual(dist_resp.status_code, 200)
        self.assertIn(b'Distribution History & Audit Trail', dist_resp.data)

        # 2. View Reports
        rep_resp = self.client.get('/reports')
        self.assertEqual(rep_resp.status_code, 200)
        self.assertIn(b'Strategic Reports & Impact Analytics', rep_resp.data)

        # 3. CSV Export
        csv_resp = self.client.get('/api/export-distribution-csv')
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Distribution ID', csv_resp.data)

        # 4. JSON API Stats
        stats_resp = self.client.get('/api/stats')
        self.assertEqual(stats_resp.status_code, 200)
        data = stats_resp.get_json()
        self.assertIn('total_resources', data)
        self.assertIn('active_disasters', data)

if __name__ == '__main__':
    unittest.main()
