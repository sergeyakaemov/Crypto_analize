import os


class CoinGecko:
    URL = "https://api.coingecko.com/api/v3/coins/markets"

    def params(self):
        return {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
        }

    def headers(self):
        return None

    def normalize(self, data):
        return [
            {
                "name": coin["name"],
                "symbol": coin["symbol"],
                "price": coin["current_price"],
                "price_change_24h": coin["price_change_percentage_24h"],
                "market_cap": coin["market_cap"],
                "total_volume": coin["total_volume"],
            }
            for coin in data
        ]




class CoinMarketCap:
    URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    def params(self):
        return {"start": 1,
                "limit": 50,
                "convert": "USD"}

    def headers(self):
        return {
            "Accept": "application/json",
            "X-CMC_PRO_API_KEY": os.getenv("COINMARKETCAP_API_KEY")
        }

    def normalize(self, data):
        return [
                {
                "name": coin["name"],
                "symbol": coin["symbol"],
                "price": coin["quote"]["USD"]["price"],
                "price_change_24h": coin["quote"]["USD"]["percent_change_24h"],
                "market_cap": coin["quote"]["USD"]["market_cap"],
                "total_volume": coin["quote"]["USD"]["volume_24h"],
            }
            for coin in data["data"]
        ]

SOURCES = {
    'coingecko': CoinGecko,
    'coinmarketcap': CoinMarketCap,
}
