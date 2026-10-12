# ShopEase — E-Commerce Website (Flask + MySQL)

Modern responsive online shopping site: register/login, browse, search, product details,
cart, checkout with payment options, order tracking + admin CRUD dashboard.

## Quick start (no MySQL needed)

```bash
cd project3
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

- User: register a new account, or login
- Admin: `admin@shop.com` / `admin123` → **Admin** link → add / edit / delete / search products, update order status

## Use with MySQL

1. Install & start MySQL, create nothing manually (app auto-creates DB).
2. Set env vars then run:
```bash
# Windows PowerShell
$env:USE_MYSQL="1"; $env:MYSQL_USER="root"; $env:MYSQL_PASSWORD="yourpw"; $env:MYSQL_DB="shopease"
python app.py
# Linux/Mac
USE_MYSQL=1 MYSQL_USER=root MYSQL_PASSWORD=yourpw MYSQL_DB=shopease python app.py
```
Schema: `schema_mysql.sql` (auto-applied on first run).

## Features
- Auth (hashed passwords, sessions), Categories, Search + live suggestions, Sort, Offers
- Product detail + related items, Cart (add/update/remove), Bill with savings
- Checkout: name/phone/address + COD / UPI / Card / NetBanking (mock)
- Orders list + tracking timeline (Placed→Packed→Shipped→Out for Delivery→Delivered)
- Admin: stats (products/orders/users/revenue), product CRUD + search, order status updates
- Responsive CSS (mobile-friendly), Font Awesome icons

## Project structure
```
app.py  config.py  requirements.txt  schema_mysql.sql
templates/base.html index.html card.html product_detail.html cart.html
  checkout.html orders.html order_detail.html login.html register.html
  admin/dashboard.html admin/product_form.html
static/css/style.css  static/js/main.js
```

## CRUD demo (admin)
Add → /admin/product/new • Edit → /admin/product/<id>/edit • Delete → /admin/product/<id>/delete • Search → /admin?q=
