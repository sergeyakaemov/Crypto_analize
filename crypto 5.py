import requests
import time
import datetime
import json
from datetime import datetime
from rich.console import Console
from rich.diagnose import report

console = Console(markup=True)
from rich.table import Table

# Декоратор retry
def retry(max_attempts=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    print(f"Ошибка. Попытка {attempt + 1}/{max_attempts}")
                    time.sleep(delay)
            raise Exception("Не удаётся подключиться к удалённому серверу.")
        return wrapper
    return decorator


# Запрос данных по API
@retry(max_attempts=3, delay=2)
def get_data():
    with console.status("Получение данных", spinner="aesthetic"):
        page = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1")
        data = page.json()
        return data

data = get_data()


# Ищем Изменения цены за 24 часа
def price_change_24h(data):
    clean_data = []
    for coin in data:
        if coin ["price_change_percentage_24h"] is not None:
            clean_data.append(coin)
    return clean_data

# ТОП лидеров роста (Вычисление)
def top_price_up_TOP_3(clean_data):
    top_price_up = sorted(clean_data, key=lambda k: k["price_change_percentage_24h"], reverse=True)
    return top_price_up[:3]

# ТОП лидеров падения (Вычисление)
def top_price_down_TOP_3(clean_data):
    top_price_down = sorted(clean_data, key=lambda k: k["price_change_percentage_24h"], reverse=False)
    return top_price_down[:3]


# Лидер по объёму торгов (Вычисление)
def top_total_volume(clean_data):
    return max(clean_data, key=lambda coin: coin["total_volume"])


# Суммарная капитализация 50 монет (Вычисление)
def total_market_cap(clean_data):
    total = sum(coin['market_cap'] for coin in clean_data) # Для отчета
    return total


# Вывод в таблицу
table = Table(title="[bold]Крипто мониторинг рынка[/bold]")
table.add_column("[bold]ТОП лидеров роста.[/bold]", no_wrap=True)
table.add_column("[bold]ТОП лидеров падения.[/bold]", no_wrap=True)
table.add_column("[bold]Лидер по объёму торгов.[/bold]", no_wrap=True)
table.add_column("[bold]Суммарная капитализация 50 монет.[/bold]", no_wrap=True)

clean_data = price_change_24h(data)
top_up = top_price_up_TOP_3(clean_data)
top_down = top_price_down_TOP_3(clean_data)
volume = top_total_volume(clean_data)
market_cap = total_market_cap(clean_data)

table.add_row("[green]" + "\n".join(f"{c['name']} {c['price_change_percentage_24h']}%" for c in top_up) + "[/green]",
              "[red]" + "\n".join(f"{c['name']} {c['price_change_percentage_24h']}%" for c in top_down) + "[/red]",
              "[yellow]" + f"{volume['name']} ${volume['total_volume']}" + "[/yellow]",
              "[blue]" + str(market_cap) + "[/blue]")

console.print(table)

# Преобразование данных в словари для отчета
top_gainers = []
for coin in top_up:
    top_gainers.append({
        "name": coin["name"],
        "symbol": coin["symbol"],
        "change_24h": coin["price_change_percentage_24h"]
    })

top_losers = []
for coin in top_down:
    top_losers.append({
        "name": coin["name"],
        "symbol": coin["symbol"],
        "change_24h": coin["price_change_percentage_24h"]
    })

highest_volume = {
    "name": volume["name"],
    "symbol": volume["symbol"],
    "volume_usd": volume["total_volume"]
}

crypto_report = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "total_coins_analyzed": len(clean_data),
          "total_market_cap_usd": market_cap,
          "top_gainers": top_gainers,
          "top_losers": top_losers,
          "highest_volume": highest_volume}

with open("crypto_report.json", "w", encoding="utf-8") as file:
    json.dump(crypto_report, file, indent=4, ensure_ascii=False)
