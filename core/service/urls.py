from aiohttp import web

from ewt.core.views import index

urlpatterns = [
    web.get('/', handler=index.IndexView),
    web.get('/dtek/grids/v1', handler=index.IndexViewEWT),
]
