"""Bank Holidays."""

from datetime import date

from requests import codes, get


def bank_holidays(year: int) -> dict[str, date]:
    """List bank holidays.

    Args:
        year (int): year to lookup for bank holidays

    Returns:
        dict[str, date]: dict of bank holidays, by name and date
    """
    # get list of UK bank holidays
    response = get("https://www.gov.uk/bank-holidays.json", timeout=5)
    if response.status_code != codes.ok:
        return {}
    data = response.json()

    # extract for the current year
    results = {}
    for event in data["england-and-wales"]["events"]:
        timestamp = date.fromisoformat(event["date"])
        if timestamp.year == year:
            results[event["title"]] = timestamp

    return results
