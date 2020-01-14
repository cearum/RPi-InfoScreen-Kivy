from darksky.api import DarkSky, DarkSkyAsync
from darksky.types import languages, units, weather
from pprint import pprint

API_KEY = 'c409354b0dd0d3406e4c3252e97cb751'

# Synchronous way
darksky = DarkSky(API_KEY)

latitude = 42.3601
longitude = -71.0589
forecast = darksky.get_forecast(
    latitude, longitude,
    extend=False, # default `False`
    lang=languages.ENGLISH, # default `ENGLISH`
    units=units.AUTO, # default `auto`
    exclude=[weather.MINUTELY, weather.ALERTS], # default `[]`,
    timezone='UTC' # default None - will be set by DarkSky API automatically
)

print(forecast.currently.summary)
print(forecast.hourly.summary)
pprint(forecast.daily.data)
