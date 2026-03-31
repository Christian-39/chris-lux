# Chris-Lux Hair E-Commerce Platform

A complete, production-ready Django e-commerce application for a premium hair business. Built with Django, MySQL, HTML, CSS, and Vanilla JavaScript.

## Features

### Core E-Commerce Features

- **Product Management**: Wigs, bundles, closures, frontals, and accessories
- **Multiple Images & Videos**: Support for multiple product images and videos
- **Shopping Cart**: Add, update, remove items with quantity controls
- **Checkout System**: Complete checkout flow with shipping options
- **Order Management**: Full order lifecycle from placement to delivery

### Payment System (Bank Transfer)

- **Bank Details Display**: Show business bank account information
- **Receipt Upload**: Customers upload payment receipts (image/PDF)
- **Verification Workflow**: Admin can approve or reject receipts
- **Order Status Tracking**: Pending Payment → Payment Uploaded → Verified → Processing → Delivered

### Notifications System

- **Real-time Notifications**: Order updates, payment verification, shipping alerts
- **Notification Badge**: Visual indicator for unread notifications
- **Notification Preferences**: Users can customize notification settings

### Admin Dashboard

- **Powerful Dashboard**: Custom admin UI with analytics and statistics
- **Order Management**: View, filter, update order status
- **Product Management**: CRUD operations for products with images/videos
- **Receipt Verification**: Approve/reject payment receipts
- **Customer Management**: View customer details and order history
- **Sales Analytics**: Charts and reports for sales data
- **Activity Logs**: Track admin actions

### User Management

- **Authentication**: Register, login, logout
- **Profile Management**: Edit profile, upload avatar, manage addresses
- **Order History**: View past orders and track current orders
- **Wishlist**: Save favorite products

### Settings System

- **Site Settings**: Branding, contact info, social media links
- **Bank Account Management**: Multiple bank accounts for payments
- **Currency Settings**: Support for multiple currencies
- **Shipping Settings**: Configure shipping costs and thresholds
- **Theme Customization**: Colors and styling options

### Additional Features

- **Search & Filter**: Product search with auto-suggestions
- **SEO Optimized**: Meta tags, clean URLs, structured data
- **Responsive Design**: Desktop sidebar, mobile bottom navigation
- **Dark Mode Support**: Toggle between light and dark themes
- **Newsletter Subscription**: Email marketing integration

## Tech Stack

- **Backend**: Django 6.0.3, Python 3.12
- **Database**: MySQL (with SQLite fallback for development)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Custom CSS with CSS Variables
- **Icons**: Font Awesome 6.4.0
- **Fonts**: Google Fonts (Playfair Display, Inter)

## Project Structure

```
chris_lux/
├── chris_lux/              # Main project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # URL configuration
│   ├── wsgi.py             # WSGI application
│   ├── context_processors.py # Template context processors
│   └── middleware.py       # Custom middleware
├── core/                   # Core app (home, pages, contact)
├── users/                  # User authentication and profiles
├── products/               # Product catalog
├── orders/                 # Shopping cart and orders
├── payments/               # Payment receipts and verification
├── notifications/          # User notifications
├── dashboard/              # Admin dashboard
├── settings_app/           # Site settings
├── templates/              # Global templates
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User-uploaded files
└── manage.py               # Django management script
```

## Installation

### Prerequisites

- Python 3.12+
- MySQL 8.0+ (or SQLite for development)
- pip

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd chris_lux
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install django mysqlclient pillow python-dotenv
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (MySQL)
DB_NAME=chris_lux
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

# For development with SQLite
USE_SQLITE=True

# Email Settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Step 5: Create Database

```bash
# For MySQL
mysql -u root -p
CREATE DATABASE chris_lux CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# Or use SQLite (set USE_SQLITE=True in .env)
```

### Step 6: Run Migrations

```bash
python manage.py migrate
```

### Step 7: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 8: Collect Static Files

```bash
python manage.py collectstatic
```

### Step 9: Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the application.

## Deployment on Render

### Step 1: Create a Render Account

Sign up at [render.com](https://render.com)

### Step 2: Create a New Web Service

1. Connect your GitHub/GitLab repository
2. Select the repository containing this project

### Step 3: Configure Build Settings

- **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start Command**: `gunicorn chris_lux.wsgi:application`

### Step 4: Environment Variables

Add these environment variables in Render dashboard:

```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=your-postgres-database-url
```

### Step 5: Create PostgreSQL Database

1. Create a new PostgreSQL database on Render
2. Copy the internal database URL
3. Add it as `DATABASE_URL` environment variable

### Step 6: Deploy

Click "Create Web Service" and wait for deployment.

## Usage

### Admin Access

- URL: `/admin/`
- Login with superuser credentials

### Custom Dashboard

- URL: `/dashboard/`
- Features: Orders, Products, Customers, Analytics, Receipts

### Managing Products

1. Go to Dashboard → Products
2. Click "Add Product" to create new products
3. Upload multiple images and videos
4. Set inventory tracking

### Processing Orders

1. Go to Dashboard → Orders
2. View order details
3. Update order status
4. Track shipments

### Verifying Payments

1. Go to Dashboard → Pending Receipts
2. View uploaded receipts
3. Approve or reject with reason
4. Customer receives notification

## API Endpoints

### Products

- `GET /products/` - Product list with filters
- `GET /products/<slug>/` - Product detail
- `GET /products/search/suggestions/?q=<query>` - Search suggestions

### Cart & Orders

- `POST /orders/cart/add/<slug>/` - Add to cart
- `GET /orders/cart/` - View cart
- `POST /orders/place-order/` - Place order
- `GET /orders/my-orders/` - Order history

### Payments

- `POST /payments/upload/<order_id>/` - Upload receipt
- `GET /payments/receipts/` - List receipts

### Notifications

- `GET /notifications/` - List notifications
- `GET /notifications/ajax/` - AJAX notifications
- `POST /notifications/mark-read/<id>/` - Mark as read

## Customization

### Changing Colors

Edit `static/css/main.css` CSS variables:

```css
:root {
  --primary: #6b21a8; /* Main brand color */
  --secondary: #1f2937; /* Secondary color */
  --accent: #f59e0b; /* Accent/highlight color */
}
```

### Adding New Product Types

Edit `products/models.py`:

```python
PRODUCT_TYPES = [
    ('wig', 'Wig'),
    ('bundle', 'Bundle'),
    # Add new types here
]
```

### Customizing Email Templates

1. Go to Admin → Settings → Email Templates
2. Edit templates for order confirmations, etc.

## Security Considerations

- Keep `SECRET_KEY` secret and unique for production
- Set `DEBUG=False` in production
- Use HTTPS in production
- Regularly update dependencies
- Enable Django's security middleware

## License

This project is proprietary software for Chris-Lux Hair Business.

## Support

For support and inquiries:

- Email: support@chris-lux.com
- Website: https://chris-lux.com

---

Built with love by the Chris-Lux Team.
