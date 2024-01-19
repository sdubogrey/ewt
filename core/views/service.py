from aiohttp import web

from ewt.core.utils import http


class HealthCheckView(web.View):
    async def get(self):
        response = http.response(success=True, status=http.STATUS_200_OK, message='Service is alive')
        return web.json_response(data=response, status=response.get('status'))
