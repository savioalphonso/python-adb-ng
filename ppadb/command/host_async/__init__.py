from ppadb.device_async import DeviceAsync


class HostAsync:
    CONNECT_RESULT_PATTERN = "(connected to|already connected)"

    OFFLINE = "offline"
    DEVICE = "device"
    BOOTLOADER = "bootloader"

    async def _execute_cmd(self, cmd):
        async with await self.create_connection() as conn:
            await conn.send(cmd)
            return await conn.receive()

    async def devices(self):
        cmd = "host:devices"
        result = await self._execute_cmd(cmd)

        devices = []

        for line in result.split('\n'):
            if not line:
                break

            devices.append(DeviceAsync(self, line.split()[0]))

        return devices
    
    async def features(self):
        cmd = "host:features"
        result = await self._execute_cmd(cmd)
        features = result.split(",")
        return features

    async def version(self):
        async with await self.create_connection() as conn:
            await conn.send("host:version")
            version = await conn.receive()
            return int(version, 16)

    async def kill(self):
        """
            Ask the ADB server to quit immediately. This is used when the
            ADB client detects that an obsolete server is running after an
            upgrade.
        """
        async with await self.create_connection() as conn:
            await conn.send("host:kill")

        return True

    async def killforward_all(self):
        cmd = "host:killforward-all"
        await self._execute_cmd(cmd, with_response=False)

    async def list_forward(self):
        cmd = "host:list-forward"
        result = await self._execute_cmd(cmd)

        device_forward_map = {}
        for line in result.split('\n'):
            if line:
                serial, local, remote = line.split()
                if serial not in device_forward_map:
                    device_forward_map[serial] = {}

                device_forward_map[serial][local] = remote

        return device_forward_map

    async def remote_connect(self, host, port):
        cmd = "host:connect:%s:%d" % (host, port)
        result = await self._execute_cmd(cmd)

        return "connected" in result

    async def remote_disconnect(self, host=None, port=None):
        cmd = "host:disconnect:"
        if host:
            cmd = "host:disconnect:{}".format(host)
            if port:
                cmd = "{}:{}".format(cmd, port)

        return await self._execute_cmd(cmd)