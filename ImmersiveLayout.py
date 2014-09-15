'''
ImmersiveLayout
===============

ImmersiveLayout is a Container widget that allows you to mimic Android's full-screen (A.K.A immersive) mode.
It contain's two widgets: the main panel and the dock. Upon activating immersive mode, either by calling
:meth: ImmersiveLayout.enter_immersive_mode() or by setting the immersed property to True, the dock will animate out
of view and be hidden. The main panel will simultaneously animate to take up the space previously occupied by the dock.

.. note:: You must first add the main panel widget, then the dock widget.

'''


from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.stencilview import StencilView
Builder.load_string("""
# <Label>:
#     canvas.after:
#         Color:
#             rgba: 1, 1, 1, 1
#         Line:
#             rectangle: [self.x, self.y, self.width, self.height]


<ImmersiveLayout>
    _main_panel: _main_panel
    _dock: _dock
    orientation: 'vertical'
    _max_dock_size: root.max_dock_size * self.height

    BoxLayout:
        id: _main_panel
        x: root.x
        y: root.y + root._max_dock_size * root._anim_progress
        width: root.width
        height: root.height - root._max_dock_size * root._anim_progress
        #top: root.top - root._max_dock_size * root._anim_progress


    BoxLayout:
        id: _dock
        x: root.x
        y: root.y - root._max_dock_size * (1 - root._anim_progress)
        height: root._max_dock_size
        width: root.width
        opacity: root._anim_progress if root.fade else 1

""")


class ImmersiveLayout(StencilView):
    immersed = BooleanProperty(None)
    '''State of the layout. If True, the dock is hidden. '''
    auto_show = BooleanProperty(True)
    '''Boolean specifying whether input events trigger the ImmersiveLayout to exit immersive mode.'''
    auto_hide = BooleanProperty(True)
    '''Boolean specifying whether the dock will hide after **timeout** seconds.'''
    timeout = NumericProperty(5)
    '''Time after the last input event (keyboard, touch, mouse) after which the dock is hidden. If set to 0, the layout
    will stay opened until manually closed.'''
    animation_duration = NumericProperty(0.75)
    '''Speed at which the dock opens, in seconds. '''
    max_dock_size = NumericProperty(0.2)
    '''Maximum dock size as a fraction of the ImmersiveLayout's size. '''
    fade = BooleanProperty(True)
    '''Boolean specifying whether the dock fades into view when opening. '''
    transition = StringProperty('in_out_sine')
    '''The name of the animation transition type to use when animating. Defaults to 'out_cubic'.'''
    _anim_progress = NumericProperty(1 * (not immersed))
    ''' Internal parameter monitoring the progress of the dock's opening animation. 1 is opened, 0 is closed.'''
    _anim = ObjectProperty(None)
    '''Animation. '''
    _scheduled_close = ObjectProperty(None, allownone=True)
    '''Scheduled close event. '''
    main_panel = ObjectProperty(None, allownone=True)
    '''Automatically bound to whatever widget is added as the main panel.'''
    dock = ObjectProperty(None, allownone=True)
    '''Automatically bound to whatever widget is added as the dock.'''


    def __init__(self, **kwargs):
        super(ImmersiveLayout, self).__init__(**kwargs)
        self._anim = Animation(_anim_progress=1 * (not self.immersed),
                              duration=self.animation_duration,
                              t=self.transition)
        Window.bind(on_keyboard=self._keyboard_handler)
        self.register_event_type('on_enter_immersive')
        self.register_event_type('on_exit_immersive')
        self.register_event_type('on_finished_entering')
        self.register_event_type('on_finished_exiting')

    def _keyboard_handler(self, window, key, *args):
        """
        If auto_show is True. The first keyboard event will open the dock and block. If the dock is opened, then the
        key events will be passed
        """
        if self.auto_show:
            immersed = self.immersed
            #self.immersed = False
            self.exit_immersive_mode()
            self._schedule_close()
            # If the dock was opened, pass on the event, otherwise block it from the system
            return immersed

    def add_widget(self, widget, index=0):
        """
        The first two widget we add are the containers for the main panel and dock, _main_panel and _dock, this is done
        automatically by instantiating the class. After, when the user adds widgets to the ImmersiveLayout, we add the
        first widget supplied to the the _main_panel and the second widget to the _dock.
        """
        if len(self.children) == 0:
            super(ImmersiveLayout, self).add_widget(widget)
            self._main_panel = widget
        elif len(self.children) == 1:
            super(ImmersiveLayout, self).add_widget(widget)
            self._dock = widget
        elif self.main_panel is None:
            self._main_panel.add_widget(widget)
            self.main_panel = widget
        elif self.dock is None:
            self._dock.add_widget(widget)
            self.dock = widget

    def cancel_scheduled_close(self):
        """
        Cancel a scheduled close and schedule a new one.
        """
        if self._scheduled_close:
            self._scheduled_close.cancel()

    def _schedule_close(self, *args):
        """
        Schedules a close event for the dock.
        """
        if self.timeout > 0:
            self.cancel_scheduled_close()
            self._scheduled_close = Clock.schedule_once(self.enter_immersive_mode, self.timeout)

    def toggle_state(self, *args):
        """
        Toggle the state of immersion
        """
        if self.immersed:
            self.exit_immersive_mode()
        else:
            self.enter_immersive_mode()

    def enter_immersive_mode(self, *args):
        """
        Enter immersive mode.
        """
        self._anim.cancel(self)
        self._anim = Animation(_anim_progress=0, duration=self.animation_duration, t=self.transition)
        self._anim.start(self)
        self._anim.bind(on_complete=lambda *x: self.dispatch('on_finished_entering'))
        self.immersed = True
        self.dispatch('on_enter_immersive')

    def exit_immersive_mode(self, *args):
        """
        Exit immersive mode.
        """
        self._anim.cancel(self)
        self._anim = Animation(_anim_progress=1, duration=self.animation_duration, t=self.transition)
        self._anim.start(self)
        self.immersed = False
        self._anim.bind(on_complete=lambda *x: self.dispatch('on_finished_exiting'))
        self.dispatch('on_exit_immersive')
        # Schedule a close event if auto_hide is enabled.
        if self.auto_hide:
            self._schedule_close()


    def on_enter_immersive(self, *args):
        """
        Signals the beginning of the event to enter immersive mode.
        """
        pass

    def on_finished_entering(self, *args):
        """
        Signals the end of the event to enter immersive mode.
        """
        pass

    def on_exit_immersive(self, *args):
        """
        Signals the beginning of the event to leave immersive mode.
        """
        pass

    def on_finished_exiting(self, *args):
        """
        Signals the end of the event to exit immersive mode.
        """
        pass

    def on_auto_hide(self, *args):
        if self.timeout > 0:
            # Store the value of the timeout in case we turn on auto_hide again.
            self._timeout = self.timeout
        if self._scheduled_close:
            self._scheduled_close.cancel()
        self.timeout = self._timeout * self.auto_hide
        if self.auto_hide:
            self._schedule_close()


    def on_touch_down(self, touch):
        if self.auto_show:
            immersed = self.immersed
            if not self.immersed:
                self.cancel_scheduled_close()
            self.exit_immersive_mode()
            # While the dock is hidden, do not pass the touch event through.
            if immersed:
                return
            else:
                super(ImmersiveLayout, self).on_touch_down(touch)
        else:
            super(ImmersiveLayout, self).on_touch_down(touch)



if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.clock import Clock
    import time


    def _timer(*args):
        if main_panel._start_time:
            main_panel.text = 'MAIN PANEL' \
                              '\nTimeout = 5 Seconds' \
                              '\nClick anywhere on the screen.' \
                              '\nEntering immersive mode in {:.2f} seconds'\
                .format(time.time() - main_panel._start_time)
        else:
            main_panel.text = 'MAIN PANEL' \
                              '\nTimeout = 5 Seconds' \
                              '\n Click anywhere on the screen.'

    def start_timer(*args):
        main_panel._start_time = time.time()

    def end_timer(*args):
        main_panel._start_time = None

    il=ImmersiveLayout()
    il.bind(on_exit_immersive=start_timer)
    il.bind(on_enter_immersive=end_timer)

    b=BoxLayout()
    b.add_widget(Button(text='1'))
    b.add_widget(Button(text='2'))
    hide_btn =Button(text='Hide Dock')
    hide_btn.bind(on_press=il.enter_immersive_mode)
    b.add_widget(hide_btn)

    main_panel = Label(halign='center')
    main_panel._start_time = None
    Clock.schedule_interval(_timer, 0.1)
    il.add_widget(main_panel)
    il.add_widget(b)

    box = BoxLayout(orientation='vertical')
    box.add_widget(il)
    runTouchApp(box)