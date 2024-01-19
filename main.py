from aiohttp import web

from core.service import urls


routes = web.RouteTableDef()


async def application():
    app = web.Application()
    app.add_routes(urls.urlpatterns)
    return app


if __name__ == "__main__":
    pass