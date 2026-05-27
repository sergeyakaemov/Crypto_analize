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

API_URL = "https://api.coingecko.com/api/v3/coins/markets"

# Запрос данных по API
@retry(max_attempts=3, delay=2)
def get_data(vs_currency="usd", order="market_cap_desc", per_page=50, page_number=1):
    params = {
        "vs_currency": vs_currency,
        "order": order,
        "per_page": per_page,
        "page": page_number
    }
    with console.status("Получение данных", spinner="aesthetic"):
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data


# Ищем Изменения цены за 24 часа
def filter_coins_with_price_change(data):
    clean_data = []
    for coin in data:
        if coin ["price_change_percentage_24h"] is not None:
            clean_data.append(coin)
    return clean_data


# Сортировка по убыванию/возрастанию
def get_top_price_changes(clean_data, limit=3, reverse=True):
    sorted_data = sorted(
        clean_data,
        key=lambda coin: coin["price_change_percentage_24h"],
        reverse=reverse
    )

    return sorted_data[:limit]


# Лидер по объёму торгов (Вычисление)
def top_total_volume(clean_data):
    return max(clean_data, key=lambda coin: coin["total_volume"])


# Суммарная капитализация 50 монет (Вычисление)
def total_market_cap(clean_data):
    total = sum(coin['market_cap'] for coin in clean_data) # Для отчета
    return total


# Вывод в таблицу
def build_report_table(top_up, top_down, volume, market_cap):
    table = Table(title="[bold]Крипто мониторинг рынка[/bold]")
    table.add_column("[bold]ТОП лидеров роста.[/bold]", no_wrap=True)
    table.add_column("[bold]ТОП лидеров падения.[/bold]", no_wrap=True)
    table.add_column("[bold]Лидер по объёму торгов.[/bold]", no_wrap=True)
    table.add_column("[bold]Суммарная капитализация 50 монет.[/bold]", no_wrap=True)

    table.add_row("[green]" + "\n".join(f"{c['name']} {c['price_change_percentage_24h']} %" for c in top_up) + "[/green]",
                    "[red]" + "\n".join(f"{c['name']} {c['price_change_percentage_24h']} %" for c in top_down) + "[/red]",
                    "[yellow]" + f"{volume['name']} ${volume['total_volume']}" + "[/yellow]",
                    "[blue]" + f"${str(market_cap)}" + "[/blue]")
    return table



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
    clean_data = filter_coins_with_price_change(data)
    top_up = get_top_price_changes(clean_data, limit=3, reverse=True)
    top_down = get_top_price_changes(clean_data, limit=3, reverse=False)
    volume = top_total_volume(clean_data)
    market_cap = total_market_cap(clean_data)
    table = build_report_table(top_up, top_down, volume, market_cap)
    console.print(table)
    top_gainers = build_top_list(top_up)
    top_losers = build_top_list(top_down)
    highest_volume = build_highest_volume(volume)
    report_data = build_report(clean_data, top_gainers, top_losers, highest_volume, market_cap)
    save_report(report_data)

if __name__ == "__main__":
    main()