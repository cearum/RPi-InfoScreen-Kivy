import os
import sys
import requests
import time
import arrow

from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView

from darksky.api import DarkSky, DarkSkyAsync
from darksky.types import languages, units, weather

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class BlackHole(object):
    def __init__(self, **kw):
        super(BlackHole, self).__init__()


class WeatherError(Screen):
    """Screen to show errors."""
    location_label = StringProperty("")

    def __init__(self, label_text, **kwargs):
        super(WeatherError, self).__init__(**kwargs)
        self.ids.error_label.text = label_text


class WeatherForecastHourly(BoxLayout):
    """Custom widget to show hourly forecast summary."""
    weather = StringProperty("")
    icon_url = StringProperty("")
    time_label = StringProperty("")
    summary = StringProperty("")

    def __init__(self, hourly_forecast_item, **kwargs):
        super(WeatherForecastHourly, self).__init__(**kwargs)
        self.buildText(hourly_forecast_item)

    def buildText(self, hourly_forecast_item):
        fc = {}
        # tm = hourly_forecast_item.time
        # fc["dy"] = "{} {}".format(str(hourly_forecast_item.time.weekday()),
        #                             str(hourly_forecast_item.time.hour))
        # fc['dy'] = arrow.get(hourly_forecast_item.time).format('ddd h A')
        self.time_label = arrow.get(hourly_forecast_item.time).format('ddd h A')
        fc["su"] = hourly_forecast_item.summary
        fc["hg"] = int(hourly_forecast_item.temperature)
        fc["po"] = int(hourly_forecast_item.precip_probability*100)
        url = "https://darksky.net/images/weather-icons/{}.png"
        self.icon_url = url.format(hourly_forecast_item.icon)
        self.weather = "[b]High: {hg}{dg}\nRain: {po}%[/b]\n".format(dg="°F", **fc)
        self.summary = "{su}".format(**fc)


class WeatherForecastDay(BoxLayout):
    """Custom widget to show daily forecast summary."""
    weather = StringProperty("")
    icon_url = StringProperty("")
    day = StringProperty("")

    def __init__(self, daily_forecast_item, **kwargs):
        super(WeatherForecastDay, self).__init__(**kwargs)
        self.buildText(daily_forecast_item)

    def buildText(self, daily_forecast_item):
        fc = {}

        fc['dy'] = arrow.get(daily_forecast_item.time).format('ddd M/D')
        fc["su"] = daily_forecast_item.summary
        fc["hg"] = int(daily_forecast_item.temperature_high)
        fc["lw"] = int(daily_forecast_item.temperature_low)
        fc["po"] = int(daily_forecast_item.precip_probability*100)
        url = "https://darksky.net/images/weather-icons/{}.png"
        self.day = "[b]{dy}[/b]\nHigh: {hg}{dg}\nLow: {lw}\nRain: {po}%".format(dg="°F", **fc)
        self.icon_url = url.format(daily_forecast_item.icon)
        self.weather = "{su}".format(dg="°F", **fc)


class WeatherSummary(Screen):
    """Screen to show weather summary for a selected location."""
    location_label = StringProperty("")

    def __init__(self, api_key, location, **kwargs):
        super(WeatherSummary, self).__init__(**kwargs)
        self._location = location
        # self._key = api_key
        self.location_label = self.name
        self._darksky = DarkSky(api_key)
        self._forecast = None
        self._hourly = None
        self.bx_forecast = self.ids.bx_forecast
        self.bx_hourly = self.ids.bx_hourly
        self.nextupdate = 0
        self.timer = None

    def on_enter(self):
        # Check if the next update is due
        if (time.time() > self.nextupdate):
            dt = 0.5
        else:
            dt = self.nextupdate - time.time()

        self.timer = Clock.schedule_once(self.getData, dt)

    def on_leave(self):
        Clock.unschedule(self.timer)

    def getData(self, *args):
        # Get the forecast
        self._forecast = self._darksky.get_forecast(
            float(self._location[0]), float(self._location[1]),
            extend=False,  # default `False`
            lang=languages.ENGLISH,  # default `ENGLISH`
            units=units.AUTO,  # default `auto`
            exclude=[weather.MINUTELY, weather.ALERTS],  # default `[]`,
            # timezone='UTC'  # default None - will be set by DarkSky API automatically
        )

        # Clear the screen of existing overlays
        self.bx_forecast.clear_widgets()
        self.bx_hourly.clear_widgets()

        # If we've got daily info then we can display it.
        if self._forecast.daily:
            for day in self._forecast.daily.data[:4]:
                frc = WeatherForecastDay(daily_forecast_item=day)
                self.bx_forecast.add_widget(frc)

        # If not, let the user know.
        else:
            error_label = Label(text="Error getting weather data.")
            self.bx_forecast.add_widget(error_label)

        # If we've got hourly weather data then show it
        if self._forecast.hourly:

            # We need a scroll view as there's a lot of data...
            w = len(self._forecast.hourly.data) * 130
            bx = BoxLayout(orientation="horizontal", size=(w, 180),
                           size_hint=(None, None), spacing=5)
            sv = ScrollView(size_hint=(1, 1))
            sv.add_widget(bx)

            for hour in self._forecast.hourly.data:
                frc = WeatherForecastHourly(hourly_forecast_item=hour)
                bx.add_widget(frc)
            self.bx_hourly.add_widget(sv)

        # If there's no data, let the user know
        else:
            error_label = Label(text="Error getting weather data.")
            self.bx_forecast.add_widget(error_label)

        # We're done, so schedule the next update
        if self._forecast.hourly and self._forecast.daily:
            dt = 60 * 60
        else:
            dt = 5 * 60

        self.nextupdate = time.time() + dt
        self.timer = Clock.schedule_once(self.getData, dt)


class DarkSkyWeatherScreen(Screen, BlackHole):
    forecast = "http://api.wunderground.com/api/{key}/forecast/q/{location}"
    hourly = "http://api.wunderground.com/api/{key}/hourly/q/{location}"

    def __init__(self, params, **kwargs):
        self._key = params["key"]
        self.locations = params["locations"]
        super(DarkSkyWeatherScreen, self).__init__(**kwargs)
        self.flt = self.ids.weather_float
        self.flt.remove_widget(self.ids.weather_base_box)
        self.screen_manager = self.ids.weather_screen_manager
        self.running = False
        # self.darksky = DarkSky(key)
        self.screen_id = 0
        self.my_screens = [x["name"] for x in self.locations]

        self.default_api_key_text = "<api-key-goes-here>"

    def on_enter(self):
        # If the screen hasn't been displayed before then let's load up
        # the locations
        if not self.running:
            if self._key == "<api-key-goes-here>":
                es = WeatherError(label_text="DarkSky Weather: Please Update API Key")
                self.screen_manager.add_widget(es)
            else:
                for location in self.locations:

                    # Create a weather summary screen
                    ws = WeatherSummary(api_key=self._key,
                                        location=(location["latitude"], location["longitude"]),
                                        name=location['name']  # Kivy Widget Name
                                        )

                    # and add to our screen manager.
                    self.screen_manager.add_widget(ws)

                # set the flag so we don't do this again.
                self.running = True

        else:
            # Fixes bug where nested screens don't have "on_enter" or
            # "on_leave" methods called.
            for c in self.screen_manager.children:
                if c.name == self.screen_manager.current:
                    c.on_enter()

    def on_leave(self):
        # Fixes bug where nested screens don't have "on_enter" or
        # "on_leave" methods called.
        for c in self.screen_manager.children:
            if c.name == self.screen_manager.current:
                c.on_leave()

    def next_screen(self, rev=True):
        a = self.my_screens
        n = -1 if rev else 1
        self.screen_id = (self.screen_id + n) % len(a)
        self.screen_manager.transition.direction = "up" if rev else "down"
        self.screen_manager.current = a[self.screen_id]
