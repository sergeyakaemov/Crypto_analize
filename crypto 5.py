import requests
import time
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table


console = Console(markup=True)


# Декоратор retry
def retry(max_attempts=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as error:
                    print(f"Ошибка: {error}."
                          f"Попытка {attempt + 1}/{max_attempts}")
                    time.sleep(delay)
            raise Exception("Не удаётся подключиться к удалённому серверу.")
        return wrapper
    return decorator


# Запрос данных по API
@retry(max_attempts=3, delay=2)
def get_data():
    with console.status("Получение данных", spinner="aesthetic"):
        page = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1")
        page.raise_for_status()
        data = page.json()
        return data


# Ищем Изменения цены за 24 часа
def price_change_24h(data):
    clean_data = []
    for coin in data:
        if coin ["price_change_percentage_24h"] is not None:
            clean_data.append(coin)
    return clean_data


# ТОП лидеров роста (Вычисление)
def top_price_up_top(clean_data):
    top_price_up = sorted(clean_data, key=lambda k: k["price_change_percentage_24h"], reverse=True)
    return top_price_up[:3]


# ТОП лидеров падения (Вычисление)
def top_price_down_top(clean_data):
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
def render_report(top_up, top_down, volume, market_cap):
    table = Table(title="[bold]Крипто мониторинг рынка[/bold]")
    table.add_column("[bold]ТОП лидеров роста.[/bold]", no_wrap=True)
    table.add_column("[bold]ТОП лидеров падения.[/bold]", no_wrap=True)
    table.add_column("[bold]Лидер по объёму торгов.[/bold]", no_wrap=True)
    table.add_column("[bold]Суммарная капитализация 50 монет.[/bold]", no_wrap=True)

    table.add_row("[green]" + "\n".join(f"{c['name']} {c['price_change_percentage_24h']} %" for c in top_up) + "[/green]",
                    "[red]" + "\n".join(f"{c['name']} {c['price_change_percentage_24h']} %" for c in top_down) + "[/red]",
                    "[yellow]" + f"{volume['name']} ${volume['total_volume']}" + "[/yellow]",
                    "[blue]" + f"${str(market_cap)}" + "[/blue]")
    console.print(table)



def build_top_list(data):
    # Преобразование данных в словари для отчета
    result = []
    for coin in data:
        result.append({
            "name": coin["name"],
            "symbol": coin["symbol"],
            "change_24h": coin["price_change_percentage_24h"]
        })
    return result


def build_highest_volume(volume):
    return {
        "name": volume["name"],
        "symbol": volume["symbol"],
        "volume_usd": volume["total_volume"]
    }


def build_report(clean_data, top_gainers, top_losers, highest_volume, market_cap):
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_coins_analyzed": len(clean_data),
        "total_market_cap_usd": market_cap,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "highest_volume": highest_volume
    }


def save_report(report, filename="crypto_report.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)



# Точка входа в программу
def main():
    data = get_data()
    clean_data = price_change_24h(data)
    top_up = top_price_up_top(clean_data)
    top_down = top_price_down_top(clean_data)
    volume = top_total_volume(clean_data)
    market_cap = total_market_cap(clean_data)
    render_report(top_up, top_down, volume, market_cap)
    top_gainers = build_top_list(top_up)
    top_losers = build_top_list(top_down)
    highest_volume = build_highest_volume(volume)
    report_data = build_report(clean_data, top_gainers, top_losers, highest_volume, market_cap)
    save_report(report_data)

if __name__ == "__main__":
    main()