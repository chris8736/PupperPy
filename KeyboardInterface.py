from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow
from pynput import keyboard
import numpy as np
import sys
import os
import configparser
import tkinter as tk
from tkinter import ttk
from pupperpy.Controller.Controller_QT import Ui_MainWindow
import time
from pupperpy.BluetoothInterface import BluetoothInterface


__location__ = os.path.dirname(__file__)
KEY_CONFIG = os.path.join(__location__, 'pupperpy', 'keyboard_mapping.conf')
MESSAGE_RATE = 20
PUPPER_COLOR = {"red":0, "blue":0, "green":255}
RESET_KEY = Qt.Key_Space
EXIT_KEY = Qt.Key_Escape

# So on mac at least, holding down a key counts as repeated presses with no release, except shift and capslock those are only single
class Test(object):
        def __init__(self):
            self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release, supress=True)
            self.last_key = None
            self.active = False
            self.n = 0

        def on_release(self, key):
            if key == keyboard.Key.esc:
                print(key.name)
                self.active = False
                return False  # stop listener
            else:
                try:
                    k = key.char
                    print('char: ' + k)
                except:
                    print('name: ' + key.name)

            self.n = 0

        def on_press(self, key):
            if key == self.last_key:
                self.n += 1
            else:
                self.n = 0

            self.last_key = key
            print(self.n)

        def run(self):
            self.listener.start()

        def join(self):
            self.listener.join()

        def __enter__(self):
            self.run()
            self.active = True
            return self

        def __exit__(self, type, value, tb):
            self.active = False
            self.listener.stop()


class ControllerState(object):
    LEFT_ANALOG_X_STEP = 0.05
    LEFT_ANALOG_Y_STEP = 0.05
    RIGHT_ANALOG_X_STEP = 0.05
    RIGHT_ANALOG_Y_STEP = 0.05
    DPAD_X_STEP = 1
    DPAD_Y_STEP = 1

    LEFT_ANALOG_X_MAX = 0.20
    LEFT_ANALOG_Y_MAX = 0.6
    RIGHT_ANALOG_X_MAX = 0.5
    RIGHT_ANALOG_Y_MAX = 0.6
    DPAD_X_MAX = 1
    DPAD_Y_MAX = 1

    def __init__(self, keymap=KEY_CONFIG):
        self.left_analog_x = 0
        self.left_analog_y = 0
        self.right_analog_x = 0
        self.right_analog_y = 0
        self.dpad_x = 0
        self.dpad_y = 0
        self.l1 = False
        self.l2 = False
        self.r1 = False
        self.r2 = False
        self.square = False
        self.circle = False
        self.cross = False
        self.triangle = False

    @property
    def left_analog_x(self):
        return self._left_analog_x

    @left_analog_x.setter
    def left_analog_x(self, value):
        if np.abs(value) > self.LEFT_ANALOG_X_MAX:
            self._left_analog_x = np.sign(value)*self.LEFT_ANALOG_X_MAX
        else:
            self._left_analog_x = value

    @property
    def left_analog_y(self):
        return self._left_analog_y

    @left_analog_y.setter
    def left_analog_y(self, value):
        if np.abs(value) > self.LEFT_ANALOG_Y_MAX:
            self._left_analog_y = np.sign(value)*self.LEFT_ANALOG_Y_MAX
        else:
            self._left_analog_y = value

    @property
    def right_analog_x(self):
        return self._right_analog_x

    @right_analog_x.setter
    def right_analog_x(self, value):
        if np.abs(value) > self.RIGHT_ANALOG_X_MAX:
            self._right_analog_x = np.sign(value)*self.RIGHT_ANALOG_X_MAX
        else:
            self._right_analog_x = value

    @property
    def right_analog_y(self):
        return self._right_analog_y

    @right_analog_y.setter
    def right_analog_y(self, value):
        if np.abs(value) > self.RIGHT_ANALOG_Y_MAX:
            self._right_analog_y = np.sign(value)*self.RIGHT_ANALOG_Y_MAX
        else:
            self._right_analog_y = value

    @property
    def dpad_x(self):
        return self._dpad_x

    @dpad_x.setter
    def dpad_x(self, value):
        if np.abs(value) > self.DPAD_X_MAX:
            self._dpad_x = np.sign(value)*self.DPAD_X_MAX
        else:
            self._dpad_x = value

    @property
    def dpad_y(self):
        return self._dpad_y

    @dpad_y.setter
    def dpad_y(self, value):
        if np.abs(value) > self.DPAD_Y_MAX:
            self._dpad_y = np.sign(value)*self.DPAD_Y_MAX
        else:
            self._dpad_y = value

    def increment(self, attr):
        try:
            x = getattr(self, attr)
            step = getattr(self, (attr + '_step').upper())
            x += step
            setattr(self, attr, x)
        except:
            print('Attribute %s not found.' % attr)

    def decrement(self, attr):
        try:
            x = getattr(self, attr)
            step = getattr(self, (attr + '_step').upper())
            x -= step
            setattr(self, attr, x)
        except:
            print('Attribute %s not found.' % attr)

    def get_state(self):
        out = {}
        out['left_analog_x'] = self.left_analog_x
        out['left_analog_y'] = self.left_analog_y
        out['right_analog_x'] = self.right_analog_x
        out['right_analog_y'] = self.right_analog_y
        out['dpad_x'] = self.dpad_x
        out['dpad_y'] = self.dpad_y
        out['l1'] = self.l1
        out['l2'] = self.l2
        out['r1'] = self.r1
        out['r2'] = self.r2
        out['button_square'] = self.square
        out['button_circle'] = self.circle
        out['button_triangle'] = self.triangle
        out['button_cross'] = self.cross
        return out

    def __str__(self):
        return repr(self.get_state())


class StateManager(object):
    def __init__(self, keymap=KEY_CONFIG):
        self.config = configparser.ConfigParser()
        self.config.read(keymap)
        self.state = ControllerState()
        self.listener = keyboard.Listener(on_press=self.on_press,
                                          on_release=self.on_release)
        self.active = False

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self.state = ControllerState() # set state to default
            self.active = False
            return False  # stop Listener

        try:
            k = key.char
        except:
            k = key.name

        # if statements to match to keyboard_mapping and set correct variables
        group, key_val = None, None
        for k1, v1 in self.config.items():
            for k2, v2 in v1.items():
                if k == v2:
                    group = k1
                    key_val = k2
                    break

        if group is None or key_val is None:
            return

        if k == RESET_KEY or key_val == 'reset':
            # reset key sends resets controller state to default
            self.state = ControllerState()
        elif group != 'toggle':
            if key_val == 'increment':
                self.state.increment(group)
            elif key_val == 'decrement':
                self.state.decrement(group)
            else:
                raise ValueError('Unknown keyword %s' % key_val)

        elif group == 'toggle':
            setattr(self.state, key_val, True)

    def on_release(self, key):
        # toggles get set to True while pressed and False when released
        # if one is turned on, turn off all others
        if key == keyboard.Key.esc:
            self.state = ControllerState() # set state to default
            self.active = False
            return False # stop listener

        try:
            k = key.char
        except:
            k = key.name

        group, key_val = None, None
        for k1, v1 in self.config.items():
            for k2, v2 in v1.items():
                if k == v2:
                    group = k1
                    key_val = k2
                    break

        if (group is None or key_val is None or
            k == RESET_KEY or key_val == 'reset'):
            return

        if group is not None and group == 'toggle':
            setattr(self.state, key_val, False)
        elif k == RESET_KEY:
            # reset key sends resets controller state to default
            self.state = ControllerState()
        elif group is not None and 'dpad' in group:
            # reset dpad values when reset, dpad must be 1 or -1 while pressed
            # and 0 otherwise
            if key_val == 'increment':
                self.state.decrement(group)
            elif key_val == 'decrement':
                self.state.increment(group)

    def get_state(self):
        '''returns dict with controller state information, ready to be passed
        to PupperBLE via bluetooth
        '''
        return self.state.get_state()

    def start(self):
        self.listener.start()
        self.active = True

    def stop(self):
        self.state = ControllerState()
        self.listener.stop()
        self.active = False

    def join(self):
        self.listener.join()

    def __enter__(self):
        self.listener.start()
        self.active = True
        return self

    def __exit__(self, type, value, tb):
        self.state = ControllerState()
        self.listener.stop()
        self.active = False


def launch_pupper_controller():
    app = QApplication(sys.argv)
    cgi = ControlGUI()
    sys.exit(app.exec_())

def window_center(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

def load_keymap(keymap=KEY_CONFIG):
    config = configparser.ConfigParser()
    config.read(keymap)
    out_map = {}
    for k1, v1 in config.items():
        for k2, v2 in v1.items():
            if v2 == '':
                continue

            key = QKeySequence(v2)[0]
            out_map[key] = (k1, k2)

    return out_map

class DummyBLE(object):
    def __init__(self):
        pass
    def send(self, msg):
        pass
    def recv(self):
        return None

class ControlGUI(QMainWindow):
    '''This will start a keyboard listener and display the controller state. It
    will loop and poll the listener for controller state, then send the state
    on to the raspberry pi via Bluetooth, will also check for a response from
    the pi
    '''
    def __init__(self, *args, **kwargs):
        if 'keymap' in kwargs:
            keymap = kwargs.pop('keymap')
        else:
            keymap = KEY_CONFIG

        super(ControlGUI, self).__init__(*args, **kwargs)
        #window_center(self.root)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.state = ControllerState()
        self.pupper_color = PUPPER_COLOR
        self.active = True

        self.config = load_keymap(keymap)
        self.updateUI()

        #self.ble_interface = BluetoothInterface()
        self.ble_interface = DummyBLE()
        self.timer = QTimer()
        self.timer.setInterval(1000 / MESSAGE_RATE)
        self.timer.timeout.connect(self.send_signal)
        self.timer.start()

        self.show()

    def keyPressEvent(self, event):
        key = event.key()
        mapped = self.config.get(key)
        if key == EXIT_KEY:
            self.active = False
            self.timer.stop()
            self.close()

        if key == RESET_KEY:
            self.state = ControllerState()
        elif mapped is None:
            return
        else:
            group, key_val = mapped
            if key_val == 'reset':
                self.state = ControllerState()
            elif key_val == 'quit':
                self.active = False
                self.close()
            elif group == 'toggle':
                setattr(self.state, key_val, True)
            else:
                if key_val == 'increment':
                    self.state.increment(group)
                elif key_val == 'decrement':
                    self.state.decrement(group)
                else:
                    raise ValueError('Unknown keyword %s' % key_val)

        self.updateUI()

    def keyReleaseEvent(self, event):
        key = event.key()
        mapped = self.config.get(key)
        if mapped is None:
            return

        group, key_val = mapped
        if group is None or key_val is None:
            return

        if group == 'toggle':
            setattr(self.state, key_val, False)
        elif 'dpad' in group:
            # reset dpad values when reset, dpad must be 1 or -1 while pressed
            # and 0 otherwise
            if key_val == 'increment':
                self.state.decrement(group)
            elif key_val == 'decrement':
                self.state.increment(group)

        self.updateUI()
        print(self.state)

    @property
    def pupper_color(self):
        return self._pupper_color

    @pupper_color.setter
    def pupper_color(self, value):
        if value is None:
            return

        if not all([x in value.keys() for x in ['red', 'blue', 'green']]):
            raise ValueError('Invalid Color Message')

        self._pupper_color = value


    def updateUI(self, state=None, pupper_msg=None):
        if state is not None:
            self.state = state
        else:
            state = self.state

        if pupper_msg is not None:
            self.pupper_color = pupper_msg['ps4_color']

        state_dict = state.get_state()

        lx = state.left_analog_x
        ly = state.left_analog_y
        rx = state.right_analog_x
        ry = state.right_analog_y
        dx = state.dpad_x
        dy = state.dpad_y
        l1 = state.l1
        r1 = state.r1
        hop = state.cross

        if l1 and not self.active:
            self.active = True
            self.ui.active_label.setText('Active')

        r,g,b = (self._pupper_color[x] for x in ['red', 'green', 'blue'])
        self.ui.active_label.setStyleSheet("background-color: rgb(%i, %i, %i)"
                                           % (r,g,b))

        set_toggle(self.ui.gait_button, r1)
        set_toggle(self.ui.hop_button, hop)

        if dx > 0:
            set_toggle(self.ui.dpad_right, True)
            set_toggle(self.ui.dpad_left, False)
        elif dx < 0:
            set_toggle(self.ui.dpad_right, False)
            set_toggle(self.ui.dpad_left, True)
        else:
            set_toggle(self.ui.dpad_right, False)
            set_toggle(self.ui.dpad_left, False)

        if dy > 0:
            set_toggle(self.ui.dpad_up, True)
            set_toggle(self.ui.dpad_down, False)
        elif dy < 0:
            set_toggle(self.ui.dpad_up, False)
            set_toggle(self.ui.dpad_down, True)
        else:
            set_toggle(self.ui.dpad_up, False)
            set_toggle(self.ui.dpad_down, False)

        self.ui.left_x_slider = int(100 * lx / state.LEFT_ANALOG_X_MAX)
        self.ui.left_y_slider = int(100 * ly / state.LEFT_ANALOG_Y_MAX)

        self.ui.right_x_slider = int(100 * lx / state.RIGHT_ANALOG_X_MAX)
        self.ui.right_y_slider = int(100 * ly / state.RIGHT_ANALOG_Y_MAX)

    def send_signal(self):
        self.ble_interface.send(self.state.get_state())
        msg = self.ble_interface.recv()
        if msg is not None:
            self.pupper_color = msg['ps4_color']



def set_toggle(obj, val):
    if obj.isChecked() != val:
        obj.toggle()


if __name__ == '__main__':
    #app = QApplication(sys.argv)
    #cgi = ControllerViewer(ControllerState())
    #sys.exit(app.exec_())
    #listener = keyboard.Listener(on_press=on_press)
    #listener.start()
    # test = Test()
    #with Test() as listener:
    #    while listener.active:
    #        print('trees')
    #        time.sleep(5)

        #listener.join()
    # print('cats')
    launch_pupper_controller()
