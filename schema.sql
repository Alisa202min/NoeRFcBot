-- Product Categories (4-level hierarchy)
CREATE TABLE IF NOT EXISTS product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    level INTEGER NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES product_categories (id) ON DELETE CASCADE
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price TEXT,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES product_categories (id) ON DELETE CASCADE
);

-- Service Categories (3-level hierarchy)
CREATE TABLE IF NOT EXISTS service_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    level INTEGER NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES service_categories (id) ON DELETE CASCADE
);

-- Services
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES service_categories (id) ON DELETE CASCADE
);

-- Price Inquiries
CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    description TEXT,
    item_type TEXT NOT NULL, -- 'product' or 'service'
    item_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new' -- 'new', 'processing', 'completed', 'canceled'
);

-- Educational Content Categories
CREATE TABLE IF NOT EXISTS edu_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES edu_categories (id) ON DELETE CASCADE
);

-- Educational Content
CREATE TABLE IF NOT EXISTS edu_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,
    media_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES edu_categories (id) ON DELETE CASCADE
);

-- Static Content
CREATE TABLE IF NOT EXISTS static_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL, -- 'contact', 'about', etc.
    content TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default static content
INSERT OR IGNORE INTO static_content (id, type, content) VALUES 
    (1, 'contact', 'با ما از طریق شماره 1234567890+ یا ایمیل info@example.com در تماس باشید.'),
    (2, 'about', 'ما یک شرکت فعال در زمینه تجهیزات الکترونیکی هستیم.');
