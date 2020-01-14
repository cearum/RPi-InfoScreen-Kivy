from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.properties import (ObjectProperty,
                             StringProperty,
                             BoundedNumericProperty)
from kivy.uix.video import Video
from kivy.graphics import Color
from kivy.clock import Clock
from kivy.graphics import Rectangle


class BlackHole(object):
    def __init__(self, **kw):
        super(BlackHole, self).__init__()


class StreamLoading(Screen):
    """
    Holding screen to display while the screen starts video.
    """
    pass


class RtspStream(Video, BlackHole):
    image_overlay_play = StringProperty('docs/image-loading.gif')
    image_loading = StringProperty('docs/image-loading.gif')

    def __init__(self, stream_uri=None, user_id=None, user_password=None, **kwargs):
        """
            Init function, calls the parent class plus images to be shown
        """
        print(kwargs)
        super(RtspStream, self).__init__(**kwargs)
        self._image = None
        self._video = None

        self.source = stream_uri
        self.volume = 0
        self.state = "play"

        # self.status_clock = Clock.schedule_interval(self.check_status, 1)
        # self.bind(eos=self.on_eos)  # position=self.on_position_change, duration=self.on_duration_change)
        self.last_position = None

    # def check_status(self, dt):
    #     print("Check Status:", self.loaded)
    #     if self.loaded:
    #         print("Check Positions (last, current):", self.last_position, self.position)
    #         if self.position == self.last_position:
    #             temp_widget = Rectangle(size=self.size, pos=self.pos, color=(0, 0, 0))
    #
    #             print("Status:", self.loaded, self.state, self.position)
    #             print("Unloading video")
    #             self.unload()
    #             print("State = stop")
    #             with self.canvas:
    #                 Color(0, 0, 0)
    #                 # Rectangle(size=self.size, pos=self.pos)
    #
    #             self.state = "stop"
    #             print("load video")
    #             self.source = "rtsp://admin:@192.168.2.103:554/h264Preview_01_sub"
    #             self.reload()
    #             print("State = play")
    #
    #             self.state = "play"
    #
    #     self.last_position = self.position
    #
    # def on_image_loading(self, instance, value):
    #     print("loading image")
    #     self.image_loading = 'docs/image-loading.gif'
    #
    # def on_source(self, instance, value):
    #     # we got a value, try to see if we have an image for it
    #     self.image_loading = 'docs/image-loading.gif'
    #
    # def on_eos(self, instance, value):
    #     print('The Video has Finished', value)
    #
    # def on_duration_change(self, instance, value):
    #     print('The duration of the video is', value)
    #
    # def on_position_change(self, instance, value):
    #     print('The position in the video is', value)


class StreamScreen(Screen, BlackHole):

    # Reference to the screen manager
    videoscreen = ObjectProperty(None)

    def __init__(self, params, **kwargs):
        super(StreamScreen, self).__init__(**kwargs)

        self.stream_uri = params["stream_uri"]
        # self.user_id = params["user_id"]
        # self.user_password = params["user_password"]
        self.rtsp_stream = RtspStream(stream_uri=self.stream_uri,
                                      # user_id=self.user_id,
                                      # user_password=self.user_password,
                                      id="video1")
        #self.add_widget(self.rtsp_stream)
        self.running = False


    def on_enter(self):
        pass

        # The screen hasn't been run before so let's tell the user
        # that we need to get the photos
        if not self.running:
            # Adding to screen manager so when I have multiple screens I can easily
            # go between the screens.
            self.loading = StreamLoading(name="loading")
            self.add_widget(self.rtsp_stream)
            self.videoscreen.add_widget(self.loading)
            self.videoscreen.current = "loading"
            self.running = True



    def on_leave(self):

        # We can pause
        pass
