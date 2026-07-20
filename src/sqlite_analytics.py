import sqlite3


class SqliteAnalytics:

    def __init__(self, db_name="crypto.db"):
        self.db_name = db_name

    def list_snapshots(self):

        with sqlite3.connect(self.db_name) as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    created_at,
                    coins_count
                FROM snapshots
                ORDER BY id
                """
            )

            return cursor.fetchall()


    def price_history(self, symbol):

        with sqlite3.connect(self.db_name) as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    snapshots.created_at,
                    coin_prices.symbol,
                    coin_prices.price
                FROM snapshots
                JOIN coin_prices
                    ON snapshots.id = coin_prices.snapshot_id
                WHERE coin_prices.symbol = ?
                ORDER BY snapshots.created_at
                """,
                (symbol,)
            )

            return cursor.fetchall()

    def compare_snapshots(self, old_id, new_id):

        with sqlite3.connect(self.db_name) as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    old.symbol,
                    old.price AS old_price,
                    new.price AS new_price,
                    new.price - old.price AS difference
                FROM coin_prices old
                JOIN coin_prices new
                    ON old.symbol = new.symbol
                WHERE old.snapshot_id = ?
                AND new.snapshot_id = ?
                ORDER BY difference DESC
                """,
                (
                    old_id,
                    new_id,
                )
            )

            return cursor.fetchall()

    def top_price_changes(self, limit=5, reverse=True):

        order = "DESC" if reverse else "ASC"

        with sqlite3.connect(self.db_name) as conn:

            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT
                    symbol,
                    price,
                    price_change
                FROM coin_prices
                WHERE snapshot_id = (
                    SELECT MAX(id)
                    FROM snapshots
                )
                ORDER BY price_change {order}
                LIMIT ?
                """,
                (limit,)
            )

            return cursor.fetchall()