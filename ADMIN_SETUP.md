# Admin Dashboard Setup

The Django admin panel is fully configured with all models for managing the system.

## Access Admin Dashboard

**URL:** `https://preciousback.onrender.com/admin/`

## Create Superuser

To create a superuser account for admin access:

### Option 1: Using Render Shell

1. Go to Render Dashboard
2. Select the `plasticprecious-api` service
3. Click "Shell" tab
4. Run:
```bash
python manage.py createsuperuser
```
5. Follow the prompts:
   - Email: your@email.com
   - First name: (optional)
   - Last name: (optional)
   - Password: (choose a strong password)
   - Confirm password

### Option 2: Using Local Machine

1. In your local development environment:
```bash
cd preciousback
python manage.py createsuperuser
```
2. Then push the changes to trigger a redeploy

## Admin Features

The admin panel includes:

### 📦 Products Management
- Add, edit, delete products
- Manage categories
- View product reviews
- Track ratings and reviews count

### 👥 Users & Accounts
- Manage user accounts
- View user orders and cart
- Manage addresses
- Control user permissions

### 🛒 Orders & Cart
- View all orders
- Update order status (Pending → Processing → Shipped → Delivered)
- View order items and total price
- Manage shopping carts

### 💳 Payments
- Track payment transactions
- View payment status and method
- Update payment records

### 📝 CMS Content
- Create and manage pages
- Add testimonials
- Manage banners and promotions
- Create blog posts
- Manage FAQ
- Add services and features
- Contact information
- Newsletter subscriptions
- Contact messages

## Default Admin Features

- Search functionality on all models
- Filtering by status, date, category, etc.
- Bulk actions
- Customized list displays
- Read-only fields for timestamps
- Organized fieldsets for better UX

## Quick Actions

After login, you can:

1. **Add Products:**
   - Navigate to Products → Products
   - Click "Add Product"
   - Fill in name, description, price, stock, category
   - Upload image
   - Save

2. **Configure Site Settings:**
   - Navigate to CMS → Site Settings
   - Set site name, logo, favicon
   - Enable/disable maintenance mode
   - Configure analytics

3. **Manage Orders:**
   - Navigate to Orders → Orders
   - View all customer orders
   - Update status
   - View order items and total

4. **Contact Management:**
   - View and respond to contact messages
   - Manage newsletter subscribers
   - View contact information

## Superuser Credentials

Once created, use these credentials to login:
- URL: `/admin/`
- Email: [your superuser email]
- Password: [your chosen password]
