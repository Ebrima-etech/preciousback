# Plasticprecious Backend

Django REST API for the Plasticprecious eCommerce platform.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis (for Celery tasks)

### Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file with your configuration:
```bash
cp .env .env.local
# Edit .env.local with your settings
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run development server:
```bash
python manage.py runserver
```

## Project Structure

```
preciousback/
├── config/                 # Project settings
├── products/              # Products app (models, serializers, views)
├── orders/                # Orders & cart management
├── accounts/              # User authentication
├── payments/              # Payment processing
└── manage.py
```

## API Endpoints

### Products
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Get product details
- `GET /api/categories/` - List categories

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/refresh/` - Refresh JWT token

### Orders
- `GET /api/orders/` - List user orders
- `POST /api/orders/` - Create new order
- `GET /api/orders/{id}/` - Get order details

### Cart
- `GET /api/cart/` - Get user cart
- `POST /api/cart/items/` - Add item to cart
- `PATCH /api/cart/items/{id}/` - Update cart item
- `DELETE /api/cart/items/{id}/` - Remove item from cart

### Payments
- `POST /api/payments/` - Create payment
- `GET /api/payments/{id}/` - Get payment status

## Database Models

### Products
- Category
- Product
- ProductReview

### Orders
- Order
- OrderItem
- Cart
- CartItem

### Accounts
- User (custom)
- Address

### Payments
- Payment

## Authentication

Uses JWT (JSON Web Tokens) for authentication. Include token in request headers:
```
Authorization: Bearer <your_access_token>
```

## Development

### Run tests
```bash
python manage.py test
```

### Create migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Load sample data
```bash
python manage.py loaddata fixtures/
```
