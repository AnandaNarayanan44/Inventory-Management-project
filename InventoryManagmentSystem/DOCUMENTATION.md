# Inventory Management System - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Installation & Setup](#installation--setup)
5. [Database Models](#database-models)
6. [User Roles & Permissions](#user-roles--permissions)
7. [API Endpoints](#api-endpoints)
8. [Machine Learning Features](#machine-learning-features)
9. [Project Structure](#project-structure)
10. [Usage Guide](#usage-guide)
11. [Barcode Scanning Feature](#barcode-scanning-feature)
12. [Development Notes](#development-notes)

---

## Project Overview

The **Inventory Management System** is a comprehensive Django-based web application designed for managing inventory, sales, billing, and business operations. It provides a complete Point of Sale (POS) system with advanced features including machine learning predictions, role-based access control, and automated reporting.

### Key Highlights
- **Full-featured POS System**: Complete billing with GST calculation and PDF invoice generation
- **Multi-warehouse Support**: Manage inventory across multiple warehouse locations
- **Machine Learning Integration**: Sales prediction and product demand forecasting
- **Role-based Access Control**: Admin and Staff roles with different permission levels
- **Barcode Scanning**: Auto-fill product details using barcode scanning in billing
- **Comprehensive Reporting**: Inventory reports, sales analytics, and downloadable reports

---

## Features

### 1. **Product Management**
- Create, edit, and delete products
- Product attributes: name, category, price, GST, barcode, description, image
- Product activation/deactivation
- Bulk product import via CSV
- Product export to CSV
- Product image upload

### 2. **Inventory Management**
- Real-time inventory tracking across multiple warehouses
- Stock level monitoring with low stock alerts
- Expiry date tracking
- Batch number management
- Stock entry and reduction tracking
- Inventory item editing and deletion
- Stock threshold configuration

### 3. **Warehouse Management**
- Multiple warehouse support
- Warehouse details: name, location, contact person, phone, notes
- Warehouse-specific inventory tracking

### 4. **Supplier Management**
- Supplier information management
- Contact details and address tracking
- Supplier association with inventory items

### 5. **Billing & POS System**
- **Barcode Scanning**: Scan or enter barcode to auto-fill product details
- Manual product selection (dropdown)
- Multi-item billing with line items
- Real-time stock availability checking
- GST calculation per product
- Automatic invoice number generation
- Customer information capture (name, phone, email)
- Staff assignment
- Sale date selection
- Notes/remarks field
- Automatic inventory decrement on sale
- PDF invoice generation
- Invoice viewing and printing

### 6. **Sales Management**
- Complete sales history
- Sales analytics with charts (Chart.js)
- Daily sales aggregation
- Sales filtering and search
- Sales detail view

### 7. **Stock Operations**
- **Stock Addition**: Add stock with supplier, warehouse, batch number, expiry date
- **Stock Reduction**: Reduce stock with reasons (Sale, Damage, Expired, Theft, Return, Other)
- Stock entry history tracking
- Stock reduction history

### 8. **Reports & Analytics**
- Inventory reports with filters
- Low stock alerts
- Out of stock products
- Category-wise inventory
- Report export functionality
- Sales reports and charts

### 9. **Machine Learning Features**
- **Sales Prediction**: Predict future sales using linear regression
- **Product Demand Forecasting**: Predict product demand for next 7 days
- **Expiry Risk Prediction**: Predict expiry risk for inventory items
- Model artifact storage and management

### 10. **Staff Management** (Admin Only)
- Create and manage staff accounts
- Activate/deactivate staff accounts
- Password reset functionality
- Role assignment (Admin/Staff)
- Staff activity tracking

### 11. **User Authentication**
- Login/logout functionality
- Auto-creation of default admin and staff accounts
- Session management
- Role-based access control

---

## Technology Stack

### Backend
- **Django 5.2.7**: Web framework
- **Python**: Programming language
- **SQLite**: Database (default, can be changed to PostgreSQL/MySQL)

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript**: Client-side interactivity
- **Chart.js**: Sales charts and analytics
- **Font Awesome**: Icons

### Machine Learning
- **scikit-learn 1.8.0**: ML algorithms (Linear Regression, Decision Tree)
- **numpy 1.26.4**: Numerical computations
- **joblib 1.5.2**: Model serialization

### Additional Libraries
- **Pillow 12.0.0**: Image processing
- **xhtml2pdf 0.2.17**: PDF generation for invoices

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step-by-Step Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd Inventory-Management-project/InventoryManagmentSystem
   ```

2. **Create and activate virtual environment** (if not using included `env_IMS`)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

   Or use the included virtual environment:
   ```bash
   # Windows
   env_IMS\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser** (optional, default accounts auto-create)
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Open browser and navigate to: `http://127.0.0.1:8000/`
   - Login with default credentials (see below)

### Default Credentials

The system auto-creates default accounts on first login:

- **Admin Account**:
  - Email/Username: `admin@example.com`
  - Password: `Admin@123`

- **Staff Account**:
  - Email/Username: `staff@example.com`
  - Password: `Staff@123`

### Running Tests

```bash
python manage.py test InventoryApp
```

---

## Database Models

### 1. **Product**
Stores product information.

**Fields:**
- `name` (CharField, max_length=100): Product name
- `category` (CharField, max_length=50): Product category
- `price` (DecimalField): Product price
- `gst` (DecimalField): GST percentage (default: 0.00)
- `barcode` (CharField, max_length=64, unique, nullable): Product barcode
- `description` (TextField, nullable): Product description
- `date_added` (DateTimeField, auto_now_add): Creation timestamp
- `image` (ImageField, nullable): Product image
- `active` (BooleanField, default=True): Product active status

### 2. **Supplier**
Stores supplier information.

**Fields:**
- `name` (CharField, max_length=100): Supplier name
- `contact_number` (CharField, max_length=20, blank): Contact number
- `email` (EmailField, blank): Email address
- `address` (TextField, nullable): Physical address

### 3. **Warehouse**
Stores warehouse information.

**Fields:**
- `name` (CharField, max_length=120, unique): Warehouse name
- `location` (CharField, max_length=255, blank): Warehouse location
- `contact_person` (CharField, max_length=120, blank): Contact person
- `phone` (CharField, max_length=30, blank): Phone number
- `notes` (TextField, blank): Additional notes
- `created_at` (DateTimeField, auto_now_add): Creation timestamp

### 4. **InventoryItem**
Tracks inventory for products in warehouses.

**Fields:**
- `product` (ForeignKey to Product): Associated product
- `warehouse` (ForeignKey to Warehouse): Associated warehouse
- `supplier` (ForeignKey to Supplier, nullable): Associated supplier
- `quantity_on_hand` (PositiveIntegerField, default=0): Current stock quantity
- `low_stock_threshold` (PositiveIntegerField, default=10): Low stock alert threshold
- `expiry_date` (DateField, nullable): Product expiry date
- `last_restocked` (DateTimeField, auto_now): Last restock timestamp

**Unique Constraint:** (product, warehouse)

**Properties:**
- `is_expired`: Returns True if expiry_date has passed

### 5. **StockEntry**
Records stock additions.

**Fields:**
- `product` (ForeignKey to Product): Product added
- `supplier` (ForeignKey to Supplier, nullable): Supplier
- `warehouse` (ForeignKey to Warehouse, nullable): Warehouse
- `inventory_item` (ForeignKey to InventoryItem, nullable): Related inventory item
- `quantity_added` (PositiveIntegerField): Quantity added
- `expiry_date` (DateField, nullable): Expiry date
- `batch_number` (CharField, max_length=50, blank): Batch number
- `barcode` (CharField, max_length=100, unique): Entry barcode
- `notes` (TextField, nullable): Additional notes
- `date_added` (DateTimeField, auto_now_add): Entry timestamp

### 6. **StockReduction**
Records stock reductions.

**Fields:**
- `product` (ForeignKey to Product): Product reduced
- `warehouse` (ForeignKey to Warehouse): Warehouse
- `inventory_item` (ForeignKey to InventoryItem, nullable): Related inventory item
- `sale` (ForeignKey to Sale, nullable): Related sale (if applicable)
- `quantity_removed` (PositiveIntegerField): Quantity removed
- `sale_price` (DecimalField, nullable): Sale price (if applicable)
- `customer_name` (CharField, max_length=120, blank): Customer name
- `sale_date` (DateField, default=timezone.now): Sale date
- `reason` (CharField, choices): Reduction reason (Sale, Damage, Expired, Theft, Return, Other)
- `notes` (TextField, blank): Additional notes
- `created_at` (DateTimeField, auto_now_add): Creation timestamp

### 7. **Sale**
Stores sale/invoice information.

**Fields:**
- `invoice_number` (CharField, max_length=30, unique): Invoice number
- `customer_name` (CharField, max_length=120, blank): Customer name
- `staff_name` (CharField, max_length=120, blank): Staff member name
- `sale_date` (DateField, default=timezone.now): Sale date
- `notes` (TextField, blank): Additional notes
- `subtotal` (DecimalField, default=0): Subtotal amount
- `tax_amount` (DecimalField, default=0): Tax amount
- `total_amount` (DecimalField, default=0): Total amount
- `created_at` (DateTimeField, auto_now_add): Creation timestamp
- `created_by` (ForeignKey to User, nullable): User who created the sale
- `pdf_file` (FileField, nullable): Generated PDF invoice

### 8. **SaleItem**
Stores individual line items in a sale.

**Fields:**
- `sale` (ForeignKey to Sale): Parent sale
- `product` (ForeignKey to Product): Product sold
- `warehouse` (ForeignKey to Warehouse): Warehouse
- `quantity` (PositiveIntegerField): Quantity sold
- `unit_price` (DecimalField): Unit price
- `gst_percent` (DecimalField, default=0): GST percentage
- `line_total` (DecimalField): Line total (quantity × unit_price)

### 9. **StaffProfile**
Extends User model with role and status.

**Fields:**
- `user` (OneToOneField to User): Associated user
- `role` (CharField, choices): Role (Admin or Staff)
- `active` (BooleanField, default=True): Account active status
- `last_login_at` (DateTimeField, nullable): Last login timestamp

### 10. **MLModelArtifact**
Stores machine learning model files.

**Fields:**
- `name` (CharField, max_length=100, unique): Model name
- `model_file` (FileField): Model file path
- `created_at` (DateTimeField, auto_now_add): Creation timestamp
- `trained_on_rows` (PositiveIntegerField, default=0): Number of training rows
- `notes` (TextField, blank): Model notes

---

## User Roles & Permissions

### Admin Role
**Full access to all features:**
- Product management (CRUD)
- Inventory management
- Stock operations (add/reduce)
- Billing and POS
- Sales management
- Reports and analytics
- Staff management
- Warehouse management
- Supplier management
- ML predictions
- CSV import/export

### Staff Role
**Limited access:**
- View products
- View inventory
- Billing and POS (create sales)
- View sales (own sales)
- View reports
- View ML predictions
- View warehouses

**Restricted:**
- Cannot add/edit/delete products
- Cannot add/reduce stock
- Cannot manage staff
- Cannot manage warehouses
- Cannot import/export CSV

---

## API Endpoints

### Authentication
- `GET/POST /login/` - User login
- `GET /logout/` - User logout

### Product Management
- `GET /productIndexPage` - List all products
- `GET/POST /productCreation` - Create new product
- `GET/POST /productEdit/<int:pk>` - Edit product
- `POST /productDelete/<int:pk>/` - Delete product
- `GET/POST /uplodeCsv` - Import products from CSV
- `GET /exportCsv` - Export products to CSV

### Inventory Management
- `GET /inventory` - Inventory overview
- `GET/POST /addStock` - Add stock
- `GET/POST /reduceStock` - Reduce stock
- `GET/POST /inventory/item/<int:pk>/edit` - Edit inventory item
- `POST /inventory/item/<int:pk>/delete` - Delete inventory item
- `GET /inventory/stock-level/` - Stock level API (JSON)

### Warehouse Management
- `GET /warehouses` - List warehouses
- `POST /warehouses` - Create warehouse
- `POST /warehouses/<int:pk>/edit` - Edit warehouse
- `POST /warehouses/<int:pk>/delete` - Delete warehouse

### Supplier Management
- `GET/POST /addSupplier` - Add supplier

### Billing & Sales
- `GET/POST /billing` - Billing/POS page
- `GET /invoice/<int:pk>` - View invoice details
- `GET /invoice/<int:pk>/pdf` - Download PDF invoice
- `GET /sales` - Sales page with analytics

### Reports
- `GET /inventory/reports` - Inventory reports

### Machine Learning
- `GET /predict-expiry/` - Expiry risk prediction page
- `GET /ml/` - ML predictions page (sales & demand)

### Staff Management (Admin Only)
- `GET /staff` - Staff management page
- `POST /staff` - Create/edit staff
- `POST /staff/<int:pk>/activate` - Activate/deactivate staff
- `POST /staff/<int:pk>/reset-password` - Reset staff password

### Dashboard
- `GET /` - Index/home page
- `GET /dashboard/` - Admin dashboard

### API Endpoints (JSON)
- `GET /api/product-by-barcode/?barcode=<barcode>` - Get product by barcode
  - **Response**: `{"id": 1, "name": "Product Name", "price": "100.00", "gst": "18.00", "category": "Category"}`
  - **Error Response**: `{"error": "Product not found with this barcode"}` (404)

---

## Machine Learning Features

### 1. Sales Prediction
- **Algorithm**: Linear Regression
- **Purpose**: Predict future sales based on historical sales data
- **Location**: `/ml/` page
- **How it works**:
  - Uses daily sales totals from historical data
  - Trains a linear regression model
  - Predicts sales for the next day
  - Stores model artifact in `media/ml_models/`

### 2. Product Demand Forecasting
- **Algorithm**: Linear Regression
- **Purpose**: Predict product demand for next 7 days
- **Location**: `/ml/` page
- **How it works**:
  - Analyzes historical sales for each product
  - Trains individual models per product
  - Predicts demand with confidence levels (low/medium/high)
  - Identifies trends (increasing/decreasing/stable)
  - Requires minimum 3 sales records for prediction

**Prediction Output:**
```python
{
    'predicted_demand': 15.5,  # Units predicted for next 7 days
    'confidence': 'high',      # low/medium/high
    'trend': 'increasing',     # increasing/decreasing/stable
    'current_avg': 12.3,      # Current average sales
    'message': None            # Error message if any
}
```

### 3. Expiry Risk Prediction
- **Algorithm**: Decision Tree Classifier
- **Purpose**: Predict expiry risk for inventory items
- **Location**: `/predict-expiry/` page
- **How it works**:
  - Calculates days until expiry
  - Uses trained Decision Tree model
  - Classifies risk as: Low, Medium, High
  - Model file: `ml/expiry_model.pkl`

**Risk Levels:**
- **Low**: More than 30 days until expiry
- **Medium**: 7-30 days until expiry
- **High**: Less than 7 days until expiry or expired

### Model Training
- Sales prediction model: Auto-trained on sales data
- Demand prediction models: Auto-trained per product
- Expiry model: Pre-trained, can be retrained using `ml/expiry_model_train.py`

---

## Project Structure

```
InventoryManagmentSystem/
├── InventoryApp/                 # Main Django app
│   ├── __init__.py
│   ├── admin.py                  # Django admin configuration
│   ├── apps.py
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions
│   ├── urls.py                   # URL routing
│   ├── tests.py                  # Unit tests
│   ├── migrations/               # Database migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_supplier.py
│   │   ├── 0003_stockentry.py
│   │   ├── 0004_sale_warehouse_inventoryitem_and_more.py
│   │   └── 0005_mlmodelartifact_product_active_product_barcode_and_more.py
│   ├── static/                   # Static files (CSS, JS, images)
│   │   └── css/
│   └── templates/                # HTML templates
│       ├── base.html
│       ├── index.html
│       ├── auth_login.html
│       ├── admin_dashboard.html
│       ├── productIndex.html
│       ├── productCreation.html
│       ├── editProduct.html
│       ├── csvUplode.html
│       ├── inventory.html
│       ├── addStock.html
│       ├── reduceStock.html
│       ├── addSupplier.html
│       ├── billing.html          # Billing page with barcode scanning
│       ├── invoice_detail.html
│       ├── invoice_print.html
│       ├── sales.html
│       ├── reports.html
│       ├── staff_management.html
│       ├── warehouse_manager.html
│       ├── ml_page.html
│       └── expiry_predict.html
├── InventoryManagmentSystem/     # Django project settings
│   ├── __init__.py
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI configuration
│   └── asgi.py                  # ASGI configuration
├── ml/                          # Machine learning modules
│   ├── __init__.py
│   ├── demand_predict.py        # Product demand prediction
│   ├── expiry_predict.py        # Expiry risk prediction
│   └── expiry_model_train.py    # Expiry model training script
├── media/                       # User-uploaded files
│   ├── invoices/               # Generated PDF invoices
│   ├── ml_models/              # Saved ML models
│   └── product_images/         # Product images
├── manage.py                    # Django management script
├── db.sqlite3                   # SQLite database (default)
├── requirements.txt             # Python dependencies
├── README.md                    # Quick start guide
└── DOCUMENTATION.md             # This file
```

---

## Usage Guide

### Adding Products

1. Navigate to **Products** page
2. Click **"Add Product"** or go to `/productCreation`
3. Fill in product details:
   - Name, Category, Price, GST
   - **Barcode** (optional but recommended for barcode scanning)
   - Description, Image
4. Check **"Active"** checkbox to make product sellable
5. Click **"Create Product"**

### Adding Stock

1. Navigate to **Inventory** page
2. Click **"Add Stock"**
3. Select:
   - Product
   - Warehouse
   - Supplier (optional)
   - Quantity
   - Expiry Date (optional)
   - Batch Number (optional)
4. Click **"Add Stock"**

### Creating a Sale (Billing)

1. Navigate to **Billing** page (`/billing`)
2. Fill customer information (optional)
3. Add line items:
   - **Option 1 - Barcode Scanning**:
     - Enter or scan barcode in the barcode field
     - Product details auto-fill
   - **Option 2 - Manual Selection**:
     - Select product from dropdown
     - Barcode field auto-fills if product has barcode
4. Select warehouse for each item
5. Enter quantity (default: 1)
6. Price auto-fills from product, can be edited
7. Click **"Add Item"** for more products
8. Review totals (Subtotal, Tax, Total)
9. Click **"Complete Billing"**
10. Invoice is generated and inventory is automatically decremented

### Viewing Sales

1. Navigate to **Sales** page (`/sales`)
2. View sales list with filters
3. Click on invoice number to view details
4. Download PDF invoice from detail page

### Generating Reports

1. Navigate to **Reports** (`/inventory/reports`)
2. Apply filters (product, warehouse, category)
3. View filtered results
4. Export reports if needed

### Using ML Predictions

1. Navigate to **ML Predictions** (`/ml/`)
2. View:
   - **Sales Prediction**: Next day sales forecast
   - **Product Demand**: Demand forecast for all products
3. Navigate to **Expiry Prediction** (`/predict-expiry/`)
4. View expiry risk for inventory items

### Managing Staff (Admin Only)

1. Navigate to **Staff Management** (`/staff`)
2. View all staff accounts
3. Create new staff: Click **"Add Staff"**
4. Activate/Deactivate: Toggle active status
5. Reset Password: Click reset button

---

## Barcode Scanning Feature

### Overview
The billing page includes a barcode scanning feature that automatically fills product details when a barcode is scanned or entered.

### How It Works

1. **Barcode Input Field**: Each billing row has a barcode input field (first column)
2. **Auto-fill on Scan**: When a barcode is entered:
   - System calls API: `/api/product-by-barcode/?barcode=<barcode>`
   - If product found, automatically:
     - Selects product in dropdown
     - Fills price
     - Fills GST
     - Updates line total
3. **Manual Entry Support**: Users can still manually select products from dropdown
4. **Two-way Sync**: 
   - Selecting product manually updates barcode field
   - Scanning barcode selects product in dropdown

### Features

- **Debounced Input**: 500ms delay for manual typing
- **Enter Key Support**: Immediate lookup on Enter (barcode scanner friendly)
- **Visual Feedback**: Red border if barcode not found
- **Error Handling**: Graceful handling of invalid/missing barcodes

### API Endpoint

**GET** `/api/product-by-barcode/?barcode=<barcode>`

**Success Response (200):**
```json
{
    "id": 1,
    "name": "Product Name",
    "price": "100.00",
    "gst": "18.00",
    "category": "Electronics"
}
```

**Error Response (404):**
```json
{
    "error": "Product not found with this barcode"
}
```

### Usage Tips

1. **For Barcode Scanners**: 
   - Point scanner at barcode field
   - Scanner automatically sends Enter key after scanning
   - Product details auto-fill immediately

2. **For Manual Entry**:
   - Type barcode in field
   - Wait 500ms or press Enter
   - Product details auto-fill

3. **Product Must Have Barcode**:
   - Ensure product has barcode set in product management
   - Barcode must be unique

---

## Development Notes

### Database
- Default: SQLite (`db.sqlite3`)
- Can be changed to PostgreSQL/MySQL in `settings.py`
- Run migrations after model changes: `python manage.py makemigrations && python manage.py migrate`

### Static Files
- Static files in `InventoryApp/static/`
- Collect static files for production: `python manage.py collectstatic`

### Media Files
- Media files stored in `media/` directory
- Configured in `settings.py`:
  - `MEDIA_ROOT = BASE_DIR / 'media'`
  - `MEDIA_URL = '/media/'`

### Security Considerations
- Change `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` properly
- Use HTTPS in production
- Implement proper password policies
- Regular database backups

### Performance Optimization
- Use database indexing for frequently queried fields
- Consider caching for reports and analytics
- Optimize queries with `select_related()` and `prefetch_related()`
- Use pagination for large datasets

### Testing
- Run tests: `python manage.py test InventoryApp`
- Test files: `InventoryApp/tests.py`
- Coverage includes authentication and billing tests

### Customization
- Modify templates in `InventoryApp/templates/`
- Update CSS in `InventoryApp/static/css/`
- Add new features in `views.py`
- Extend models in `models.py`

### Deployment
1. Set `DEBUG = False`
2. Configure production database
3. Set up static file serving
4. Configure media file serving
5. Set up web server (Nginx + Gunicorn recommended)
6. Configure domain and SSL
7. Set up backup system

---

## Troubleshooting

### Common Issues

1. **Migration Errors**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Static Files Not Loading**:
   ```bash
   python manage.py collectstatic
   ```

3. **Permission Errors**:
   - Check file permissions on `media/` directory
   - Ensure write permissions for PDF generation

4. **Barcode Not Working**:
   - Verify product has barcode set
   - Check barcode is unique
   - Verify API endpoint is accessible
   - Check browser console for errors

5. **ML Predictions Not Working**:
   - Ensure sufficient sales data (minimum 2-3 records)
   - Check `ml_models/` directory exists
   - Verify scikit-learn is installed

---

## Support & Contribution

### Getting Help
- Check this documentation first
- Review Django documentation: https://docs.djangoproject.com/
- Check error logs in console/terminal

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## License

This project is provided as-is for educational and commercial use.

---

## Version History

### Current Version
- Django 5.2.7
- Full POS system with barcode scanning
- ML predictions (sales, demand, expiry)
- Multi-warehouse support
- Role-based access control
- PDF invoice generation

---

**Last Updated**: December 2024

**Documentation Version**: 1.0

