import logging
import re
import time
from ppadb import ClearError

from ppadb.utils import logger


class TransportAsync:
    async def transport(self, connection):
        cmd = "host:transport:{}".format(self.serial)
        await connection.send(cmd)

        return connection

    async def shell(self, cmd, timeout=None):
        conn = await self.create_connection(timeout=timeout)

        cmd = "shell:{}".format(cmd)
        await conn.send(cmd)

        result = await conn.read_all()
        await conn.close()
        return result.decode('utf-8')

    async def sync(self):
        conn = await self.create_connection()

        cmd = "sync:"
        await conn.send(cmd)

        return conn

    async def screencap(self):
        async with await self.create_connection() as conn:
            cmd = "shell:/system/bin/screencap -p"
            await conn.send(cmd)
            result = await conn.read_all()

        if result and len(result) > 5 and result[5] == 0x0d:
            return result.replace(b'\r\n', b'\n')
        else:
            return result

    async def clear(self, package):
        clear_result_pattern = "(Success|Failed)"

        result = await self.shell("pm clear {}".format(package))
        m = re.search(clear_result_pattern, result)

        if m is not None and m.group(1) == "Success":
            return True
        else:
            logger.error(result)
            raise ClearError(package, result.strip())
        
    
    async def framebuffer(self):
        raise NotImplemented()

    async def list_features(self):
        result = await self.shell("pm list features 2>/dev/null")

        result_pattern = "^feature:(.*?)(?:=(.*?))?\r?$"
        features = {}
        for line in result.split('\n'):
            m = re.match(result_pattern, line)
            if m:
                value = True if m.group(2) is None else m.group(2)
                features[m.group(1)] = value

        return features

    async def list_packages(self):
        result = await self.shell("pm list packages 2>/dev/null")
        result_pattern = "^package:(.*?)\r?$"

        packages = []
        for line in result.split('\n'):
            m = re.match(result_pattern, line)
            if m:
                packages.append(m.group(1))

        return packages

    async def get_properties(self):
        result = await self.shell("getprop")
        result_pattern = "^\[([\s\S]*?)\]: \[([\s\S]*?)\]\r?$"

        properties = {}
        for line in result.split('\n'):
            m = re.match(result_pattern, line)
            if m:
                properties[m.group(1)] = m.group(2)

        return properties

    async def list_reverses(self):
        conn = await self.create_connection()
        with conn:
            cmd = "reverse:list-forward"
            await conn.send(cmd)
            result = await conn.receive()

        reverses = []
        for line in result.split('\n'):
            if not line:
                continue

            _, remote, local = line.split()
            reverses.append(
                {
                    'remote': remote,
                    'local': local
                }
            )

        return reverses

    async def local(self, path):
        if ":" not in path:
            path = "localfilesystem:{}".format(path)

        conn = await self.create_connection()
        conn.send(path)

        return conn

    async def log(self, name):
        conn = await self.create_connection()
        cmd = "log:{}".format(name)

        await conn.send(cmd)

        return conn

    def logcat(self, clear=False):
        raise NotImplemented()

    async def reboot(self):
        conn = await self.create_connection()

        async with conn:
            await conn.send("reboot:")
            await conn.read_all()

        return True

    async def remount(self):
        conn = await self.create_connection()

        async with conn:
            await conn.send("remount:")

        return True

    async def reverse(self, remote, local):
        cmd = "reverse:forward:{remote}:{local}".format(
            remote=remote,
            local=local
        )

        conn = await self.create_connection()
        async with conn:
            await conn.send(cmd)

            # Check status again, the first check is send cmd status, the second time is check the forward status.
            await conn.check_status()

        return True

    async def root(self):
        # Restarting adbd as root
        conn = await self.create_connection()
        async with conn:
            await conn.send("root:")
            result = await conn.read_all()
            result = result.decode('utf-8')

            if "restarting adbd as root" in result:
                return True
            else:
                raise RuntimeError(result.strip())

    async def wait_boot_complete(self, timeout=60, timedelta=1):
        """
        :param timeout: second
        :param timedelta: second
        """
        cmd = 'getprop sys.boot_completed'

        end_time = time.time() + timeout

        while True:
            try:
                result = await self.shell(cmd)
            except RuntimeError as e:
                logger.warning(e)
                continue

            if result.strip() == "1":
                return True

            if time.time() > end_time:
                raise TimeoutError()
            elif timedelta > 0:
                time.sleep(timedelta)