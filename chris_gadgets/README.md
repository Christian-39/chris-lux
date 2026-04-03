# Gadgets Store - Premium E-commerce Platform

A fully functional, production-ready Gadgets & Accessories E-commerce Website built with Django, designed specifically for the Nigerian market.

## Features

### Core Business Structure
- **Product Categories**: Phones & Tablets, Accessories, Computers, Smart Gadgets, Power Solutions, Repairs & Services
- **Dynamic Sections**: Hot Deals, New Arrivals, Featured Products, Related Products, Frequently Bought Together, Recently Viewed
- **Product Details**: Multiple images, videos, specifications, reviews, wishlist, cart functionality

### UI/UX & Design
- **Responsive Navigation**: Desktop sidebar, Mobile bottom navigation
- **Theme Modes**: Dark Mode, Light Mode, System Default
- **Mobile App-like Experience**: Smooth transitions, touch-friendly interactions
- **Modern UI Components**: Cards, animated elements, notifications

### Technology Stack
- **Backend**: Django 5.0+
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: SQLite (development), MySQL (production)
- **Static Files**: Well-structured CSS/JS

### Authentication & Security
- User registration with email verification
- Login/logout with session management
- Password reset functionality
- CSRF protection, input validation
- Secure file uploads

### Admin System
- Full CRUD operations
- Analytics dashboard
- User management
- Order management
- Payment verification
- Content management

### Order & Payment System
- Shopping cart with session persistence
- Checkout with address selection
- **Bank Transfer Payment** with receipt upload
- QR code generation for payments
- Manual payment verification by admin
- Order tracking

### Additional Features
- Smart search with filters
- Coupon/Discount system
- Flash sales with countdown
- Customer reviews
- Wishlist functionality
- Notification system
- Messaging/support system
- Newsletter subscription
- SEO optimization
- WhatsApp integration

## Installation

### Prerequisites
- Python 3.10+
- pip
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gadgets_store
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt 
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load initial data (optional)**
   ```bash
   python manage.py shell
   # Then run setup commands
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Website: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Project Structure

```
gadgets_store/
├── accounts/          # User authentication & profiles
├── core/              # Main app (home, about, contact, etc.)
├── messaging/         # Support messaging system
├── notifications/     # User notifications
├── orders/            # Shopping cart & orders
├── payments/          # Payment processing
├── products/          # Product catalog
├── static/            # CSS, JS, images
├── templates/         # HTML templates
├── media/             # User-uploaded files
├── gadgets_store/     # Project settings
├── manage.py
├── requirements.txt
└── README.md
```

## Configuration

### Database
For production, configure MySQL in `.env`:
```
DB_ENGINE=django.db.backends.mysql
DB_NAME=gadgets_store
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### Email
Configure SMTP for email notifications:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Payment
Update bank details in `.env`:
```
BANK_NAME=Your Bank
BANK_ACCOUNT_NAME=Your Account Name
BANK_ACCOUNT_NUMBER=Your Account Number
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up MySQL database
- [ ] Configure email SMTP
- [ ] Set up static files serving (Whitenoise or CDN)
- [ ] Configure media files storage
- [ ] Set up SSL certificate
- [ ] Configure web server (Nginx/Apache)
- [ ] Set up WSGI server (Gunicorn/uWSGI)

### Collect Static Files
```bash
python manage.py collectstatic
```

## Usage

### Admin Dashboard
1. Login at `/admin/`
2. Manage products, categories, brands
3. Process orders and verify payments
4. View analytics and reports
5. Manage users and content

### Customer Flow
1. Browse products by category
2. Add items to cart
3. Proceed to checkout
4. Select delivery address
5. Choose bank transfer payment
6. Upload payment receipt
7. Track order status

## Customization

### Theme Colors
Edit CSS variables in `static/css/main.css`:
```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --accent-color: #f59e0b;
}
```

### Site Settings
Access via Admin > Core > Site Settings to update:
- Site name and logo
- Contact information
- Social media links
- Shipping and tax settings
- Feature toggles

## Support

For support and inquiries:
- Email: support@gadgetsstore.com
- WhatsApp: +2348012345678

## License

This project is proprietary software. All rights reserved.

## Credits

Built with ❤️ for the Nigerian market.
