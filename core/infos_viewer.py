# -*- coding: utf-8 -*-
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty
from kivy.core.window import Window

# from frame_config import FrameConfiguration
from math import ceil
import time
import os
import pyowm
import platform




class WeatherViewer(RelativeLayout):
    """
        This class handles the weather information that is
        shown to the user
    """
    weather_text = StringProperty()

    def __init__(self, **kwargs):
        super(WeatherViewer, self).__init__(**kwargs)
        self.increment = 0
        # Allow the Viewer tobe on the from when touched
        self.country = "United States"
        self.city = "Wixom"
        self.set_temp_unit("F")

        # Set the icon size to a percentage of the windows
        self.icon_size = [size_val*100/100 for size_val in Window.size]
        self.api_key = "f754e8ecce23aeece77af6240d610c90"
        self.owm = pyowm.OWM(self.api_key)
        self.city_weather = self.owm.weather_at_place(self.city + ',' + self.country)
        self.update_weather(-1)
        self.refresh_rate = 300  # Seconds
        self.clk = Clock.schedule_interval(self.update_weather, self.refresh_rate)


    def on_touch_up(self, touch):
        pass
        
    def set_temp_unit(self, unit_string):
        if unit_string == 'F' or 'f' or 'fahrenheit' or 'Fahrenheit':
            self.temp_unit = 'fahrenheit'
        else:
            self.temp_unit = 'celsius'

    def _get_current_weather(self):
        """
            Get the current weather with the proper formatting
        """
        try:
            self.city_weather = self.owm.weather_at_place(self.city + ',' + self.country)
        except:
            pass
        weather = self.city_weather.get_weather()
        if self.temp_unit == 'fahrenheit':
            temp_abbrev = 'F'
        else:
            temp_abbrev = 'C'
        #color=148F77
        weather_str = '    [color=FFFFFF][b][size={}]{} : {}°{} [/size][/b][/color]'.format(
            int(self.icon_size[0]),
            self.city,
            int(ceil(weather.get_temperature(unit=self.temp_unit).get('temp'))),
            temp_abbrev,
        )
        print("Current Weather String:", weather_str)
        self.increment += 1
        return weather_str

    def _get_icon_path(self, icon_id):
        """
            Get the path to the icon weather
            :param the icon_id
            return the path to Image
        """
        #TODO: This has to be tested to always find the incons and be coonfigurable
        if platform.system() == "Windows":
            path = os.path.join('..\images\weather_icons', '{}.png'.format(icon_id))
        else:
           
            print("current_directory:", os.path.dirname(os.path.abspath(__file__)))
            path1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../images/weather_icons')
            print("path1:", path1)
            path = os.path.join(path1, '{}.png'.format(icon_id))
            print("Path:", path)
        print("Icon Path:", path)
        return path

    def _get_current_weather_image(self):
        weather = self.city_weather.get_weather()
        icon = weather.get_weather_icon_name()
        returnPath = self._get_icon_path(icon)
        
        if os.path.exists(returnPath):
            return returnPath
        else:
            return None

    def update_weather(self, dt):
        self.weather_icon = self._get_current_weather_image()
        print("Update Weather Icon:", self.weather_icon)
        self.weather_text = self._get_current_weather()




