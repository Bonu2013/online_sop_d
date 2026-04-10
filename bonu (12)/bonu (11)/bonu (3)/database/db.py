import asyncpg
from config import config


class Database:
    def __init__(self):
        self.pool = None

    async def connection(self):
        self.pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )
    
    async def add_user(self,telegram_id,name,surename,age,phone_number):
        query="""
        insert into users(telegram_id,name,surename,age,phone_number) values($1,$2,$3,$4,$5);
        """
        await self.pool.execute(query,telegram_id,name,surename,age,phone_number)

    
    async def is_user_exists(self, telegram_id: int) -> bool:
        query = """
        SELECT EXISTS (
        SELECT 1 FROM users WHERE telegram_id = $1
        );
        """
        return await self.pool.fetchval(query, telegram_id)
    
    async def profile(self,tg_id):
        query="""
        select name,surename,age,phone_number,role from users where telegram_id=$1;
        """
        return await self.pool.fetchrow(query,tg_id)
    
    async def get_user_role(self, telegram_id):
        query = """SELECT role FROM users WHERE telegram_id=$1"""
        return await self.pool.fetchval(query, telegram_id)
    
    async def get_user_id(self,telegram_id):
        query="""
            select id from users where telegram_id=$1;
            """
        return await self.pool.fetchval(query,telegram_id)
    
    async def get_users(self):
        query="""
        select name,surename,role,id from users order by id;
        """
        return await self.pool.fetch(query)
    
    async def get_users_telegram_id(self):
        query = "SELECT telegram_id FROM users ORDER BY id"
        return await self.pool.fetch(query)
    
    async def update_role(self,user_id,role):
        query="""
        update users set role=$1 where id=$2;
        """

        await self.pool.execute(query,role,user_id)
    
    #products
    async def get_products(self):
        query="""
        select id,name,price from products order by id;
        """
        return await self.pool.fetch(query)
    
    async def add_product(self,name,price,description):
        query="""
        insert into products(name,price,description) values($1,$2,$3);
        """

        await self.pool.execute(query,name,price,description)
    
    async def delete_product(self,product_id):
        query="""
        delete from products where id=$1;
        """
        await self.pool.execute(query,product_id)
    
    async def update_product(self,product_id,name,price,description):
        query="""
        update products set name=$1,price=$2,description=$3 where id=$4;
        """
        await self.pool.execute(query,name,price,description,product_id)
    
    #cart


    async def get_or_create_cart(self, user_id):

        order = await self.pool.fetchrow(
            """
            SELECT * FROM orders
            WHERE user_id=$1 AND order_status='cart'
            """,
            user_id
        )

        if order:
            return order["id"]

        order = await self.pool.fetchrow(
            """
            INSERT INTO orders(user_id)
            VALUES($1)
            RETURNING id
            """,
            user_id
        )

        return order["id"]
    
    async def add_product_to_cart(self, user_id, product_id):

        order_id = await self.get_or_create_cart(user_id)

        await self.pool.execute(
            """
            INSERT INTO order_items(order_id, product_id)
            VALUES($1,$2)
            """,
            order_id,
            product_id
        )
    
    async def get_cart_products(self, user_id):

        return await self.pool.fetch(
            """
            SELECT p.id, p.name, p.price
            FROM order_items oi
            JOIN orders o ON oi.order_id=o.id
            JOIN products p ON oi.product_id=p.id
            WHERE o.user_id=$1 AND o.order_status='cart'
            """,
            user_id
        )

    
    async def remove_one_product(self, user_id, product_id):

        await self.pool.execute(
            """
            DELETE FROM order_items
            WHERE id = (
                SELECT oi.id
                FROM order_items oi
                JOIN orders o ON oi.order_id=o.id
                WHERE o.user_id=$1
                AND o.order_status='cart'
                AND oi.product_id=$2
                LIMIT 1
            )
            """,
            user_id,
            product_id
        )
    
    async def get_cart_with_total(self, user_id):

        products = await self.pool.fetch(
            """
            SELECT p.id, p.name, p.price
            FROM order_items oi
            JOIN orders o ON oi.order_id=o.id
            JOIN products p ON oi.product_id=p.id
            WHERE o.user_id=$1 AND o.order_status='cart'
            """,
            user_id
        )

        total = await self.pool.fetchval(
            """
            SELECT SUM(p.price)
            FROM order_items oi
            JOIN orders o ON oi.order_id=o.id
            JOIN products p ON oi.product_id=p.id
            WHERE o.user_id=$1 AND o.order_status='cart'
            """,
            user_id
        )

        return products, total
    
    async def confirm_order(self,user_id):
        query="""
            update orders set order_status='completed' where user_id=$1;
            """
        await self.pool.execute(query,user_id)
    

    async def get_user_order_history(self, user_id):
        query = """
        SELECT 
            o.id AS order_id,
            p.name,
            p.price
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = $1 AND o.order_status = 'completed'
        ORDER BY o.id DESC
        """

        rows = await self.pool.fetch(query, user_id)

        orders = {}

        for row in rows:
            order_id = row["order_id"]

            if order_id not in orders:
                orders[order_id] = {
                    "products": [],
                    "total": 0
                }

            orders[order_id]["products"].append({
                "name": row["name"],
                "price": row["price"]
            })

            orders[order_id]["total"] += row["price"]

        return orders