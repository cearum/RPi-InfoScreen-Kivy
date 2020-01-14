from glob import glob
import os

from kivy.clock import Clock
from kivy.properties import (ObjectProperty,
                             StringProperty,
                             BoundedNumericProperty)
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition, FadeTransition
from kivy.gesture import GestureDatabase
from kivy.gesture import Gesture
from kivy.uix.floatlayout import FloatLayout

from functools import partial
from random import shuffle
from imghdr import what

from core.my_gestures import left_to_right_line_str, right_to_left_line_str
gesture_strings = {
    'left_to_right_line': left_to_right_line_str,
    'right_to_left_line': right_to_left_line_str,
}
gestures = GestureDatabase()
for name, gesture_string in gesture_strings.items():
    gesture = gestures.str_to_gesture(gesture_string)
    gesture.name = name
    gestures.add_gesture(gesture)


class BlackHole(object):
    def __init__(self, **kw):
        super(BlackHole, self).__init__()


class Photo(Screen):
    """Screen object to display a photo."""
    photo_path = StringProperty("")

    def __init__(self, **kwargs):
        super(Photo, self).__init__(**kwargs)
        self.photo_path = self.name


class PhotoLoading(Screen):
    """Holding screen to display while the screen retrieves the list of
       photos.
    """
    pass


class GestureBox(FloatLayout):

    alert_dialog = ObjectProperty()

    def __init__(self, **kwargs):
        for gesture_name in gesture_strings:
            self.register_event_type('on_{}'.format(gesture_name))
        super(GestureBox, self).__init__(**kwargs)

        self.interval = 0
        self.alert_dismissal = None

    def on_left_to_right_line(self):
        pass

    def on_right_to_left_line(self):
        pass

    def on_top_to_bottom_line(self):
        pass

    def on_bottom_to_top_line(self):
        pass

    # To recognize a gesture, you’ll need to start recording each individual event in the
    # touch_down handler, add the data points for each call to touch_move , and then do the
    # gesture calculations when all data points have been received in the touch_up handler.

    def on_touch_down(self, touch):
        # create an user defined variable and add the touch coordinates
        touch.ud['gesture_path'] = [(touch.x, touch.y)]
        super(GestureBox, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        touch.ud['gesture_path'].append((touch.x, touch.y))
        super(GestureBox, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if 'gesture_path' in touch.ud:
            # create a gesture object
            this_gesture = Gesture()
            # add the movement coordinates
            this_gesture.add_stroke(touch.ud['gesture_path'])
            # normalize so thwu will tolerate size variations

            this_gesture.normalize()
            # minscore to be attained for a match to be true
            match = gestures.find(this_gesture, minscore=0.3)
            if match:
                #print("{} happened".format(match[1].name))
                self.dispatch('on_{}'.format(match[1].name))
        super(GestureBox, self).on_touch_up(touch)


class PhotoAlbumScreen(Screen, BlackHole):
    """Base screen to run the photo album."""

    # Reference to the screen manager
    photoscreen = ObjectProperty(None)

    # Value for the screen display time
    photoduration = BoundedNumericProperty(5, min=2, max=60, errorvalue=5)

    def __init__(self, params, **kwargs):
        super(PhotoAlbumScreen, self).__init__(**kwargs)

        # Get the user's preferences
        self.folders = params["folders"]
        # self.exts = params["extensions"]
        self.photoduration = params["duration"]
        self.allow_shuffle = params.get("random", True)

        # Initialise some useful variables
        self.running = False
        self.photos = []
        self.timer = None
        self.oldPhoto = None
        self.photoindex = 0

    def on_enter(self):

        if not self.running:

            # The screen hasn't been run before so let's tell the user
            # that we need to get the photos
            self.loading = PhotoLoading(name="loading")
            self.photoscreen.add_widget(self.loading)
            self.photoscreen.current = "loading"

            # Retrieve photos
            Clock.schedule_once(self.getPhotos, 0.5)
            Clock.schedule_once(partial(self.showPhoto, 'forward'), self.photoduration)

        else:
            # We've been here before so just show the photos
            self.timer = Clock.schedule_interval(partial(self.showPhoto, 'forward'), self.photoduration)

    def on_leave(self):

        # We can stop looping over photos
        Clock.unschedule(self.timer)

    def getPhotos(self, *args):
        """Method to retrieve list of photos based on user's preferences."""

        # Get a list of extensions. Assumes all caps or all lower case.
        # exts = []
        # for ext in ([x.upper(), x.lower()] for x in self.exts):
        #     exts.extend(ext)

        # Loop over the folders
        for folder in self.folders:
            for (path, dirs, files) in os.walk(folder):
                for the_file in files:
                    path_file = os.path.join(path, the_file)

                    # uses what from IMGHDR to check for image file types
                    file_type = what(path_file)

                    # If the image type matches an image we go one further
                    if file_type is not None:

                        # We don't want Gif's though as they don't work well
                        if file_type is not 'gif':

                            self.photos.append(path_file)

        # shuffle if requested
        if self.allow_shuffle:
            shuffle(self.photos)
        else:  # Put the photos in order
            self.photos.sort()

        # We've got the photos so we can set the running flag
        self.running = True

        # and start the timer
        self.timer = Clock.schedule_interval(partial(self.showPhoto, 'forward'), self.photoduration)

        # Show the first photo
        self.showPhoto(direction="forward")

    def swipe_photo(self, direction="forward"):
        # unschedule current clock
        Clock.unschedule(self.timer)
        self.photoscreen.transition = SlideTransition()
        if direction == 'forward':
            self.photoscreen.transition.direction = 'left'
        elif direction == 'back':
            self.photoscreen.transition.direction = 'right'

        # Reschedule Clock
        self.timer = Clock.schedule_interval(partial(self.showPhoto, 'forward'), self.photoduration)

        # show the photo
        self.showPhoto(direction)

        self.photoscreen.transition = FadeTransition()

    def showPhoto(self, direction="forward", *args):
        """Method to update the currently displayed photo."""
        try:
            print(direction, args)
        except ValueError:
            print(direction)

        # Get the current photo
        if direction == "forward":
            photo = self.photos[self.photoindex]
        elif direction == "back":
            self.photoindex = (self.photoindex - 2) % len(self.photos)
            photo = self.photos[self.photoindex]

        # Create a screen object to show that photo
        scr = Photo(name=photo)

        # Add it to our screen manager and display it
        self.photoscreen.add_widget(scr)
        self.photoscreen.current = photo

        # If we've got an old photo
        if self.oldPhoto:

            # We can unload it
            self.photoscreen.remove_widget(self.oldPhoto)

        # Create reference to the new photo
        self.oldPhoto = scr

        # Increase our index for the next photo
        self.photoindex = (self.photoindex + 1) % len(self.photos)

        # If we hit the end of the photos reshuffle
        if self.photoindex == len(self.photos):
            if self.allow_shuffle:
                shuffle(self.photos)
