import os
import asyncpg

class Database:
    def __init__(self):
        self.pool = None

    async def connection(self):
        dsn = os.getenv("DATABASE_URL")
        print(f"DEBUG: DATABASE_URL qiymati: {dsn}") # Buni logda ko'rasiz

        if dsn:
            if dsn.startswith("postgres://"):
                dsn = dsn.replace("postgres://", "postgresql://", 1)
            self.pool = await asyncpg.create_pool(dsn=dsn)
            print("Railway bazasiga ulanishga harakat qilindi.")
        else:
            print("DATABASE_URL topilmadi! Localhostga ulanishga majburmiz.")
            from config import config
            self.pool = await asyncpg.create_pool(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
        )

    async def add_user(self, telegram_id, name, surname, age, phone_number):
        query = """
        INSERT INTO users(telegram_id, name, surname, age, phone_number) 
        VALUES($1, $2, $3, $4, $5)
        ON CONFLICT (telegram_id) DO NOTHING;
        """
        await self.pool.execute(query, telegram_id, name, surname, age, phone_number)

    async def is_user_exists(self, telegram_id: int) -> bool:
        query = "SELECT EXISTS (SELECT 1 FROM users WHERE telegram_id = $1);"
        return await self.pool.fetchval(query, telegram_id)

    async def profile(self, tg_id):
        query = "SELECT name, surname, age, phone_number, role FROM users WHERE telegram_id = $1;"
        return await self.pool.fetchrow(query, tg_id)

    async def get_user_role(self, telegram_id):
        query = "SELECT role FROM users WHERE telegram_id = $1;"
        return await self.pool.fetchval(query, telegram_id)

    async def get_user_id(self, telegram_id):
        query = "SELECT id FROM users WHERE telegram_id = $1;"
        return await self.pool.fetchval(query, telegram_id)

    async def get_users(self):
        query = "SELECT name, surname, role, id FROM users ORDER BY id;"
        return await self.pool.fetch(query)

    async def get_users_telegram_id(self):
        query = "SELECT telegram_id FROM users ORDER BY id;"
        return await self.pool.fetch(query)

    async def update_role(self, user_id, role):
        query = "UPDATE users SET role = $1 WHERE id = $2;"
        await self.pool.execute(query, role, user_id)

    # --- PRODUCT METODLARI ---

    async def get_products(self):
        query = "SELECT id, name, price FROM products ORDER BY id;"
        return await self.pool.fetch(query)

    async def add_product(self, name, price, description):
        query = "INSERT INTO products(name, price, description) VALUES($1, $2, $3);"
        await self.pool.execute(query, name, price, description)

    async def delete_product(self, product_id):
        query = "DELETE FROM products WHERE id = $1;"
        await self.pool.execute(query, product_id)

    async def update_product(self, product_id, name, price, description):
        query = "UPDATE products SET name = $1, price = $2, description = $3 WHERE id = $4;"
        await self.pool.execute(query, name, price, description, product_id)

    # --- CART (SAVATCHA) METODLARI ---

    async def get_or_create_cart(self, user_id):
        # Mavjud savatchani tekshirish
        order = await self.pool.fetchrow(
            "SELECT id FROM orders WHERE user_id = $1 AND order_status = 'cart';",
            user_id
        )
        if order:
            return order["id"]

        # Yangi savatcha yaratish
        return await self.pool.fetchval(
            "INSERT INTO orders(user_id) VALUES($1) RETURNING id;",
            user_id
        )

    async def add_product_to_cart(self, user_id, product_id):
        order_id = await self.get_or_create_cart(user_id)
        await self.pool.execute(
            "INSERT INTO order_items(order_id, product_id) VALUES($1, $2);",
            order_id, product_id
        )

    async def get_cart_products(self, user_id):
        query = """
        SELECT p.id, p.name, p.price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = $1 AND o.order_status = 'cart';
        """
        return await self.pool.fetch(query, user_id)

    async def remove_one_product(self, user_id, product_id):
        query = """
        DELETE FROM order_items
        WHERE id = (
            SELECT oi.id FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.user_id = $1 AND o.order_status = 'cart' AND oi.product_id = $2
            LIMIT 1
        );
        """
        await self.pool.execute(query, user_id, product_id)

    async def get_cart_with_total(self, user_id):
        products = await self.get_cart_products(user_id)
        query = """
        SELECT SUM(p.price)
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = $1 AND o.order_status = 'cart';
        """
        total = await self.pool.fetchval(query, user_id)
        return products, total or 0

    async def confirm_order(self, user_id):
        query = "UPDATE orders SET order_status = 'completed' WHERE user_id = $1 AND order_status = 'cart';"
        await self.pool.execute(query, user_id)

    async def get_user_order_history(self, user_id):
        query = """
        SELECT o.id AS order_id, p.name, p.price
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = $1 AND o.order_status = 'completed'
        ORDER BY o.id DESC;
        """
        rows = await self.pool.fetch(query, user_id)
        
        orders = {}
        for row in rows:
            oid = row["order_id"]
            if oid not in orders:
                orders[oid] = {"products": [], "total": 0}
            
            orders[oid]["products"].append({"name": row["name"], "price": row["price"]})
            orders[oid]["total"] += row["price"]
        
        return orders