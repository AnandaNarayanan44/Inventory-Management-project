# Inventory Management System

Fully functional Django Inventory + Billing with roles, billing, reports, ML prediction and PDF invoices.

## Quick Start

### Setup
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

### Default credentials
- Admin: `admin@example.com` / `Admin@123`
- Staff: `staff@example.com` / `Staff@123`

Accounts auto-create on first visit to `/login/`.

## Key Features
- **Role-based access control** (Admin vs Staff)
- **POS Billing System** with barcode scanning, inventory decrement, GST calculation, and PDF invoice generation
- **Inventory Management** with multi-warehouse support, stock tracking, expiry management
- **Stock Operations** (add/reduce stock with batch tracking)
- **Reports & Analytics** with filters and exports
- **Staff Management** (activate/deactivate, reset password)
- **Sales Analytics** with Chart.js visualizations
- **Machine Learning** predictions (sales forecast, product demand, expiry risk)
- **Barcode Scanning** - Auto-fill product details in billing
- **CSV Import/Export** for bulk product management

## Documentation

For complete documentation, see **[DOCUMENTATION.md](DOCUMENTATION.md)**

The documentation includes:
- Complete feature list
- Database model reference
- API endpoints
- Usage guides
- Machine learning details
- Barcode scanning guide
- Development notes
- Troubleshooting

## Tests
```
python manage.py test InventoryApp
```

## Project Structure
```
InventoryManagmentSystem/
├── InventoryApp/          # Main Django application
├── ml/                    # Machine learning modules
├── media/                 # User uploads (invoices, images, models)
├── manage.py             # Django management script
└── requirements.txt      # Dependencies
```

