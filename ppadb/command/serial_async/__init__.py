from ppadb.command import CommandAsync


class Serial(CommandAsync):
    async def _execute_cmd(self, cmd, with_response=True):
        conn = await self.create_connection(set_transport=False)

        async with conn:
            await conn.send(cmd)
            if with_response:
                result = await conn.receive()
                return result
            else:
                await conn.check_status()

    async def forward(self, local, remote, norebind=False):
        if norebind:
            cmd = "host-serial:{serial}:forward:norebind:{local};{remote}".format(
                serial=self.serial,
                local=local,
                remote=remote)
        else:
            cmd = "host-serial:{serial}:forward:{local};{remote}".format(
                serial=self.serial,
                local=local,
                remote=remote)

        await self._execute_cmd(cmd, with_response=False)

    async def list_forward(self):
        # According to https://android.googlesource.com/platform/system/core/+/master/adb/adb_listeners.cpp#129
        # And https://android.googlesource.com/platform/system/core/+/master/adb/SERVICES.TXT#130
        # The 'list-forward' always lists all existing forward connections from the adb server
        # So we need filter these by self.
        cmd = "host-serial:{serial}:list-forward".format(serial=self.serial)
        result = await self._execute_cmd(cmd)

        forward_map = {}

        for line in result.split('\n'):
            if line:
                serial, local, remote = line.split()
                if serial == self.serial:
                    forward_map[local] = remote

        return forward_map

    async def killforward(self, local):
        cmd = "host-serial:{serial}:killforward:{local}".format(serial=self.serial, local=local)
        await self._execute_cmd(cmd, with_response=False)

    async def killforward_all(self):
        # killforward-all command ignores the <host-prefix> and remove all the forward mapping.
        # So we need to implement this function by self
        forward_map = await self.list_forward()
        for local, remote in forward_map.items():
            await self.killforward(local)

    async def get_device_path(self):
        cmd = "host-serial:{serial}:get-devpath".format(serial=self.serial)
        return await self._execute_cmd(cmd)

    async def get_serial_no(self):
        cmd = "host-serial:{serial}:get-serialno".format(serial=self.serial)
        return await self._execute_cmd(cmd)

    async def get_state(self):
        cmd = "host-serial:{serial}:get-state".format(serial=self.serial)
        return await self._execute_cmd(cmd)
