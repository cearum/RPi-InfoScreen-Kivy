import time

from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.clock import Clock


class BlackHole(object):
    def __init__(self, **kw):
        super(BlackHole, self).__init__()


class ClockOverlay(RelativeLayout, BlackHole):
    """
        This class handles the time information that is shown
        to the user for the Clock Overlay

    """
    clock_overlay_text = StringProperty()

    def __init__(self, params, **kwargs):
        super(ClockOverlay, self).__init__(**kwargs)

        self.clock_format = params['clock_format']
        self.icon_size_percent = params['icon_size_percent']

        #(root.width - self.width - 10, ctimer_label.height/2)
        # print("Window, self", Window.width, self.width)
        # self.x_pos = Window.width - self.width - 10
        # print("x_pos", self.x_pos)
        # self.pos = (self.x_pos, 20)

        self.icon_size = [size_val * self.icon_size_percent / 100 for size_val in Window.size]
        self.clock_overlay_text = self._get_current_date()

        self.clock_refresh_rate = 1  # seconds
        self.clk = Clock.schedule_interval(self.update_time, int(self.clock_refresh_rate))

    def _get_current_date(self):
        """
            Return the current data with the desired configuration
        """
        if '24h' in self.clock_format:
            date_str = '[color=FFFFFF][b][size={}]%H:%M[/size]\n[size={}]%a, %d %B[/size][/color][/b]'.format(
                int(self.icon_size[0]), int(self.icon_size[1]))
        else:
            date_str = '[color=FFFFFF][b][size={}]%I:%M[/size][size={}] %p[/size]\n[size=25]%a, %d %B[/size][/b][/color]'.format(
                int(self.icon_size[0]), int(self.icon_size[1]))
        return time.strftime(date_str)

    def update_time(self, dt):
        """
            This function does the update of the time on screen
        """
        self.clock_overlay_text = self._get_current_date()
