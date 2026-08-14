class SqliteAnalytics:
    """Читает аналитику из готового соединения.

    Как и SqliteStorage, соединением не владеет: его открывает и закрывает
    вызывающий код через storage.connect().
    """

    def __init__(self, connection):
        self.connection = connection

    def list_snapshots(self):

        cursor = self.connection.cursor()

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

        cursor = self.connection.cursor()

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

        cursor = self.connection.cursor()

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

    # Направление сортировки нельзя передать параметром ?, а собирать запрос
    # через f-string нельзя, поэтому держим два готовых текста запроса.
    TOP_PRICE_CHANGES_UP = """
        SELECT
            symbol,
            price,
            price_change
        FROM coin_prices
        WHERE snapshot_id = (
            SELECT MAX(id)
            FROM snapshots
        )
        ORDER BY price_change DESC
        LIMIT ?
    """

    TOP_PRICE_CHANGES_DOWN = """
        SELECT
            symbol,
            price,
            price_change
        FROM coin_prices
        WHERE snapshot_id = (
            SELECT MAX(id)
            FROM snapshots
        )
        ORDER BY price_change ASC
        LIMIT ?
    """

    def top_price_changes(self, limit=5, reverse=True):

        query = (
            self.TOP_PRICE_CHANGES_UP
            if reverse
            else self.TOP_PRICE_CHANGES_DOWN
        )

        cursor = self.connection.cursor()

        cursor.execute(query, (limit,))

        return cursor.fetchall()
