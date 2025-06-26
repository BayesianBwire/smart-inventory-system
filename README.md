Smart Inventory & Sales System
A Flask-based inventory, sales, and HR management platform tailored for small businesses such as mini-marts, agro-vets, and retail outlets.

Key Features
User Authentication & Role Management
Secure login system with hashed passwords

Role-based access control (Super Admin, Admin, HR, Sales, Finance, etc.)

Dashboard customization based on role

HR-specific tools restricted to HR only

Inventory Management
Add, edit, delete products

Live product search and low stock detection

Product image support

Product import via cleaned CSV (e.g., Adidas products)

Export full inventory to Excel

Sales & Checkout
Shopping cart with subtotal and total calculations

Stock auto-adjusts after sales

Persistent sales records with timestamps

HR & Payroll Tools
Staff overview with filtering by role or search

Add new salary records (gross, deductions, net pay)

Loan and bonus tracking

View full payroll history

Visual Analytics
Bar charts for product quantities

Pie charts for category-wise sales

Highlights for most valuable or low-stock products

Technologies Used
Backend: Flask (Python)

Frontend: HTML, Bootstrap 5, Jinja2

Database: SQLite (via SQLAlchemy)

Libraries: pandas, numpy, werkzeug

Folder Structure
csharp
Copy
Edit
smartshop/
│
├── app.py
├── create_admin.py
├── cleaned_adidas_products.csv
├── shop.db
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── product.py
│   ├── sale.py
│   ├── login_log.py
│   └── payroll.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── inventory.html
│   ├── cart.html
│   ├── checkout.html
│   ├── sales.html
│   ├── hr.html
│   └── new_payroll.html
├── static/
│   ├── css/
│   ├── js/
│   └── rahasoft-logo.png
Setup Instructions
Clone the Repository

bash
Copy
Edit
git clone https://github.com/BayesianBwire/smart-inventory-system.git
cd smart-inventory-system
Create Virtual Environment and Install Dependencies

bash
Copy
Edit
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
Create Admin User

bash
Copy
Edit
python create_admin.py
Run the Application

bash
Copy
Edit
python app.py
Access the System

Open your browser at: http://localhost:5000

Login credentials:

Username: admin

Password: admin

License
This project is open-source under the MIT License.
