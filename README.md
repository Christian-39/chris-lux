# Chris Lux and Accessories

A complete, production-ready luxury hair e-commerce website built with Django.

## Features

- **Product Catalog**: Human hair wigs, bundles, frontals, closures, and accessories
- **Shopping Cart**: AJAX-powered cart with coupon support
- **Checkout**: Secure payment integration with Paystack
- **User Accounts**: Registration, login, profile management, wishlist, order history
- **Reviews**: Product reviews with ratings and images
- **Admin Panel**: Customized Django admin for easy management
- **SEO Optimized**: Sitemaps, meta tags, clean URLs
- **Mobile Responsive**: Fully responsive design

## Tech Stack

- **Backend**: Django 5.0+
- **Frontend**: HTML5, CSS3, Bootstrap 5, Vanilla JavaScript
- **Database**: PostgreSQL (production), SQLite (development)
- **Payment**: Paystack
- **Deployment**: Heroku-ready configuration

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd chris_lux_ecommerce
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Project Structure

```
chris_lux_ecommerce/
├── chris_lux/              # Main project directory
│   ├── settings/           # Settings modules
│   ├── core/              # Core app (home, about, contact)
│   ├── accounts/          # User authentication
│   ├── products/          # Product catalog
│   ├── cart/              # Shopping cart
│   ├── orders/            # Orders and checkout
│   └── reviews/           # Product reviews
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── media/                 # User-uploaded files
├── requirements.txt       # Python dependencies
└── manage.py             # Django management script
```

## Configuration

### Paystack Payment Setup

1. Create a Paystack account at https://paystack.com
2. Get your API keys from the dashboard
3. Add to `.env`:
   ```
   PAYSTACK_PUBLIC_KEY=pk_test_...
   PAYSTACK_SECRET_KEY=sk_test_...
   ```

### Email Configuration

For production, configure SMTP settings in `.env`:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration

For production with PostgreSQL:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
```

## Deployment

### Heroku Deployment

1. Install Heroku CLI and login
2. Create Heroku app:
   ```bash
   heroku create your-app-name
   ```
3. Add PostgreSQL addon:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```
4. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   # ... other variables
   ```
5. Deploy:
   ```bash
   git push heroku main
   ```
6. Run migrations:
   ```bash
   heroku run python manage.py migrate
   ```

## Admin Panel

Access the admin panel at `/admin/`

Default superuser credentials are created during setup.

## Customization

### Colors

Edit `static/css/style.css` to customize:
- Primary color: `--color-gold: #C5A059`
- Secondary color: `--color-black: #000000`

### Logo

Replace `static/images/logo.png` with your logo.

## License

This project is proprietary software. All rights reserved.

## Support

For support, email info@chrislux.com or call +234 800 000 0000.
