import iso3166

def getRegion(country: str, number: int, classification: str):
    country_numeric = str(country).zfill(3)
    country_code = iso3166.countries_by_numeric[country_numeric].alpha2
    region_number = 'xxx' if number is None else str(number).zfill(3)
    return f'{country_code}_{classification}{region_number}'
