
# 🛒 Smart Inventory & Sales System

A Flask-based inventory management and sales tracking system designed for small businesses like mini-marts, retail shops, and agro-vets.

## 🚀 Features

- 🔐 **Admin Login System** (with hashed passwords)
- 📦 **Inventory Dashboard**
  - Product categories
  - Low stock filtering
  - Pagination and live product search
  - Product image support
- 📊 **Visual Analytics**
  - Quantity bar chart
  - Category-wise sales pie chart
  - Most valuable product highlight
- 🛍️ **Shopping Cart and Checkout**
  - Add to cart functionality
  - Total cost calculation
  - Reduces quantity after checkout
  - Sales records saved automatically
- 📂 **Product Import**
  - Import real product data from `cleaned_adidas_products.csv`
- 📥 **Excel Export**
  - Download entire inventory as an Excel file
- 🧾 **Sales History**
  - View all completed sales with quantities, totals, and timestamps

## 🧱 Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, Bootstrap, Jinja2
- **Database**: SQLite (via SQLAlchemy)
- **Libraries**: pandas, numpy, werkzeug

## 📁 Folder Structure

```
smartshop/
│
├── app.py
├── create_admin.py
├── cleaned_adidas_products.csv
├── shop.db
├── models/
│   ├── __init__.py
│   ├── product.py
│   ├── user.py
│   └── sale.py
├── templates/
│   ├── login.html
│   ├── inventory.html
│   ├── edit_product.html
│   ├── cart.html
│   ├── checkout.html
│   └── sales.html
├── static/
│   └── (optional CSS/JS/image files)
```

## 🛠️ Setup Instructions

1. **Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/smart-inventory-system.git
cd smart-inventory-system
```

2. **Create a virtual environment & install dependencies**
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

3. **Create admin user**
```bash
python create_admin.py
```

4. **Run the application**
```bash
python app.py
```

5. **Access the system**
- Visit: `http://localhost:5000`
- Login: `admin` / `admin`

## 📸 Screenshots

(Add screenshots of your dashboard, cart, and sales history here)

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

Developed by [Bilford Bwire]  
