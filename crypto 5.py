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
def retry():
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(3):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    print("URL недоступен.")
                    time.sleep(2)
            raise Exception("Не удаётся подключиться к удалённому серверу.")
        return wrapper
    return decorator


# Запрос данных по API
@retry()
def get_data():
    with console.status("Получение данных", spinner="aesthetic"):
        page = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1")
        data = page.json()
        return data

data = get_data()


# Ищем Изменения цены за 24 часа
clean_data = []
for coin in get_data():
    if coin ["price_change_percentage_24h"] is not None:
        clean_data.append(coin)

# ТОП лидеров роста (Вычисление)
top_price_up = sorted(clean_data, key=lambda k: k["price_change_percentage_24h"], reverse=True)
top_price_up_TOP_3_full = top_price_up[:3]
top_price_up_TOP_3_final = []
for coin in top_price_up_TOP_3_full:
    top_price_up_TOP_3_final.append(f"{coin['name']} {coin['price_change_percentage_24h']}%")

# ТОП лидеров падения (Вычисление)
top_price_down = sorted(clean_data, key=lambda k: k["price_change_percentage_24h"], reverse=False)
top_price_down_TOP_3_full = top_price_down[:3]
top_price_down_TOP_3_final = []
for coin in top_price_down_TOP_3_full:
    top_price_down_TOP_3_final.append(f"{coin['name']} {coin['price_change_percentage_24h']}%")


# Лидер по объёму торгов (Вычисление)
top_total_volume = max(clean_data, key=lambda coin: coin["total_volume"]) # монета с максимальным объёмом торгов
top_total_volume_final = f"{top_total_volume['name']} ${top_total_volume['total_volume']}"


# Суммарная капитализация 50 монет (Вычисление)
total_market_cap = f"${str(sum(coin["market_cap"] for coin in clean_data))}"
total_market_cap_final = sum(coin["market_cap"] for coin in clean_data) # Для отчета


# Вывод в таблицу
table = Table(title="[bold]Крипто мониторинг рынка[/bold]")
table.add_column("[bold]ТОП лидеров роста.[/bold]", no_wrap=True)
table.add_column("[bold]ТОП лидеров падения.[/bold]", no_wrap=True)
table.add_column("[bold]Лидер по объёму торгов.[/bold]", no_wrap=True)
table.add_column("[bold]Суммарная капитализация 50 монет.[/bold]", no_wrap=True)

table.add_row("[green]" + "\n".join(top_price_up_TOP_3_final) + "[/green]",
              "[red]" + "\n".join(top_price_down_TOP_3_final) + "[/red]",
              "[yellow]" + top_total_volume_final + "[/yellow]",
              "[blue]" + total_market_cap + "[/blue]")

console.print(table)

# Преобразование данных в словари для отчета
top_gainers = []
for coin in top_price_up_TOP_3_full:
    top_gainers.append({
        "name": coin["name"],
        "symbol": coin["symbol"],
        "change_24h": coin["price_change_percentage_24h"]
    })

top_losers = []
for coin in top_price_down_TOP_3_full:
    top_losers.append({
        "name": coin["name"],
        "symbol": coin["symbol"],
        "change_24h": coin["price_change_percentage_24h"]
    })

highest_volume = {
    "name": top_total_volume["name"],
    "symbol": top_total_volume["symbol"],
    "volume_usd": top_total_volume["total_volume"]
}

crypto_report = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "total_coins_analyzed": len(clean_data),
          "total_market_cap_usd": total_market_cap,
          "top_gainers": top_gainers,
          "top_losers": top_losers,
          "highest_volume": highest_volume}

crypto_report = json.dumps(crypto_report, indent=4, ensure_ascii=False)
with open("crypto_report.json", "w", encoding="utf-8") as file:
    json.dump(crypto_report, file, indent=4, ensure_ascii=False)
