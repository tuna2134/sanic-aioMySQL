from sanic import Sanic
from aiomysql import create_pool

class ConnectionError(Exception):
    pass

class ExtendMySQL:
    def __init__(self, app: Sanic, *args, **kwargs):
        self.setting = (args, kwargs)
        self.app = app
        self.__pool = None
        app.register_listener(self.before_server_start, "before_server_start")
        app.register_middleware(self.on_request, "request")
        app.register_middleware(self.on_response, "response")

    @property
    def pool(self):
        if self.__pool is not None:
            return self.__pool
        else:
            raise ConnectionError("Please connect to MySQL server")

    async def before_server_start(self, app, loop):
        args, kwargs = self.setting
        kwargs["loop"] = loop
        kwargs["autocommit"] = True
        if self.app is not None:
            self.__pool = await create_pool(*args, **kwargs)
        else:
            raise ConnectionError("Already connected to MySQL server.")

    async def on_request(self, request):
        request.ctx._connection = await self.pool.acquire()
        request.ctx.cursor = await request.ctx._connection.cursor()

    async def on_response(self, request, response):
        if hasattr(request.ctx, "_connection"):
            self.pool.release(request.ctx._connection)
