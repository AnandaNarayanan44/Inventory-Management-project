# Inventory Management System

Fully functional Django Inventory + Billing with roles, billing, reports, ML prediction and PDF invoices.

## Setup
1. Create/activate venv or use the included `env_IMS`:
   ```
   env_IMS\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```
   python manage.py migrate
   ```
4. Start server:
   ```
   python manage.py runserver
   ```

## Default credentials
- Admin: `admin@example.com` / `Admin@123`
- Staff: `staff@example.com` / `Staff@123`

Accounts auto-create on first visit to `/login/`.

## Key features
- Role-based access (Admin vs Staff)
- POS billing with inventory decrement, GST and invoice PDF
- Inventory, stock in/out, suppliers, warehouses
- Reports with filters & downloads
- Staff management (activate/deactivate, reset password)
- Sales charts (Chart.js) and ML sales prediction

## Tests
```
python manage.py test InventoryApp
```

