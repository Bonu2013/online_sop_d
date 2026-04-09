import os
import asyncpg
import logging

# Loglarni ko'rish uchun sozlama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def connection(self):
        """Baza bilan ulanishni o'rnatish"""
        dsn = os.getenv("DATABASE_URL")
        
        if dsn:
            # Railway uchun postgres:// -> postgresql:// o'zgarishi
            if dsn.startswith("postgres://"):
                dsn = dsn.replace("postgres://", "postgresql://", 1)
            
            try:
                # SSL ulanish cloud bazalar uchun juda muhim
                self.pool = await asyncpg.create_pool(
                    dsn=dsn,
                    ssl="require", # Railway va tashqi ulanishlar uchun shart
                    min_size=1,
                    max_size=10
                )
                logger.info("Railway bazasiga muvaffaqiyatli ulanish o'rnatildi.")
            except Exception as e:
                logger.error(f"Railway ulanishida xatolik: {e}")
        else:
            logger.warning("DATABASE_URL topilmadi! Localhostga ulanish boshlanmoqda.")
            try:
                from config import config
                self.pool = await asyncpg.create_pool(
                    host=config.DB_HOST,
                    port=config.DB_PORT,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    database=config.DB_NAME,
                )
                logger.info("Localhost bazasiga ulanish o'rnatildi.")
            except Exception as e:
                logger.error(f"Localhost ulanishida xatolik: {e}")

    # --- FOYDALANUVCHI METODLARI ---

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

    async def update_role(self, user_id, role):
        query = "UPDATE users SET role = $1 WHERE id = $2;"
        await self.pool.execute(query, role, user_id)

    # --- MAHSULOT METODLARI ---

    async def get_products(self):
        query = "SELECT id, name, price, description FROM products ORDER BY id;"
        return await self.pool.fetch(query)

    async def add_product(self, name, price, description):
        query = "INSERT INTO products(name, price, description) VALUES($1, $2, $3);"
        await self.pool.execute(query, name, price, description)

    async def delete_product(self, product_id):
        query = "DELETE FROM products WHERE id = $1;"
        await self.pool.execute(query, product_id)

    # --- SAVATCHA (CART) VA BUYURTMA ---

    async def get_or_create_cart(self, user_id):
        """Foydalanuvchi uchun ochiq savat topish yoki yaratish"""
        order = await self.pool.fetchrow(
            "SELECT id FROM orders WHERE user_id = $1 AND order_status = 'cart';",
            user_id
        )
        if order:
            return order["id"]

        return await self.pool.fetchval(
            "INSERT INTO orders(user_id, order_status) VALUES($1, 'cart') RETURNING id;",
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
        """Savatchadan bitta mahsulotni o'chirish"""
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
        """Savatchani 'completed' holatiga o'tkazish (buyurtma berish)"""
        query = "UPDATE orders SET order_status = 'completed' WHERE user_id = $1 AND order_status = 'cart';"
        await self.pool.execute(query, user_id)

    async def get_user_order_history(self, user_id):
        """Sotib olingan barcha mahsulotlar tarixi"""
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