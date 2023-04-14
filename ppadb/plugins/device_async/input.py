from ppadb.plugins import PluginAsync


class Source:
    KEYBOARD = 'keyboard'
    MOUSE = 'mouse'
    JOYSTICK = 'joystick'
    TOUCHNAVIGATION = 'touchnavigation'
    TOUCHPAD = 'touchpad'
    TRACKBALL = 'trackball'
    DPAD = 'dpad'
    STYLUS = 'stylus'
    GAMEPAD = 'gamepad'
    touchscreen = 'touchscreen'


class Input(PluginAsync):
    async def input_text(self, string):
        return await self.shell('input text "{}"'.format(string))

    async def input_keyevent(self, keycode, longpress=False):
        cmd = 'input keyevent {}'.format(keycode)
        if longpress:
            cmd += " --longpress"
        return await self.shell(cmd)

    async def input_tap(self, x, y):
        return await self.shell("input tap {} {}".format(x, y))

    async def input_swipe(self, start_x, start_y, end_x, end_y, duration):
        return await self.shell("input swipe {} {} {} {} {}".format(
            start_x,
            start_y,
            end_x,
            end_y,
            duration
        ))

    async def input_press(self):
        return await self.shell("input press")

    async def input_roll(self, dx, dy):
        return await self.roll("roll {} {}".format(dx, dy))
