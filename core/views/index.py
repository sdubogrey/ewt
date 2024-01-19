import json
import sqlite3

import requests
from aiohttp_basicauth import BasicAuthMiddleware
from pydantic import BaseModel

from random import randint

from ewt.core.service import settings

from ewt.core.views.binotel import BinotelEpmloyees, BinotelHistoryCall, BinotelCallOnline

from datetime import datetime, timedelta
import time

import logging

from aiohttp import web

logger = logging.getLogger('gunicorn.access')


class CustomBasicAuth(BasicAuthMiddleware):
    token = None
    
    async def check_credentials(self, username, password, request):
        # print(username)
        # print(password)
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        res = cur.execute(f"SELECT password, token FROM users_auth where username='{username.lower()}'")
        auth_user = res.fetchone()
        
        if auth_user is None:
            return False
        else:
            self.token = auth_user[1]
            return password == auth_user[0]


auth = CustomBasicAuth()


@auth.required
class IndexView(web.View):
    async def get(self):
        # print(auth.token)
        
        data = {
            'token': auth.token
        }
        
        return web.json_response(data)


class EpmloyeersOnline(BaseModel):
    @classmethod
    def from_binotel(cls, empl: BinotelEpmloyees):
        online_empl = 0
        offline_empl = 0
        all_empl = 0
        email_dtek = ''
        
        if empl.department.lower().find('дтек') != -1:
            all_empl += 1
            email_dtek = empl.email
            
            if empl.endpointData.status.status == 'online' and empl.presenceState == 'active':
                online_empl += 1
                # email_dtek = empl.email
                # print(empl.email)
            
            if empl.endpointData.status.status == 'offline':
                offline_empl += 1
        
        return cls(
            count_online=online_empl,
            count_offline=offline_empl,
            count_all=all_empl,
            email=email_dtek
        )
    
    count_online: int
    count_offline: int
    count_all: int
    email: str


class HistoryCall(BaseModel):
    @classmethod
    def from_binotel(cls, hist: BinotelHistoryCall):
        if hist.disposition == "ANSWER":
            return cls(
                wait=hist.waitsec,
                bill=hist.billsec,
                email=hist.employeeData.email
            )
        else:
            return cls(
                wait=-1,
                bill=-1,
                email=''
            )
    
    wait: int
    bill: int
    email: str


class CallOnline(BaseModel):
    @classmethod
    def from_binotel(cls, call: BinotelCallOnline):
        return cls(
            time=int(time.time()) - call.startTime if call.startTime else 0,
            email=call.employeeData.email
        )
    
    time: int
    email: str


@auth.required
class IndexViewEWT(web.View):
    async def save_last_ewt(self, ewt: int):
        file1 = open("ewt.txt", "w")
        file1.write(str(ewt))
        file1.close()
    
    async def get_last_ewt(self):
        file1 = open("ewt.txt", "r+")
        ewt_f = file1.read()
        file1.close()
        delta = randint(0, 9)
        ewt = float(ewt_f) + delta if ewt_f != '' else 87
        
        data = {
            'result': 'ok',
            'message': 'estimated wait time',
            'ewt': ewt
        }
        
        return data
    
    async def get_emloyees_from_binotel(self):
        body_request = {
            "key": settings.BINOTEL_KEY,
            "secret": settings.BINOTEL_SECRET
        }
        
        print(body_request)
        
        binotel_response = requests.post(f'{settings.BINOTEL_URL}/settings/list-of-employees.json',
                                         json=body_request)
        
        data_binotel = json.loads(binotel_response.content)
        if data_binotel.get("status") != 'success':
            return None
        
        employees_list = data_binotel.get("listOfEmployees")
        
        online = 0
        offline = 0
        all_empl = 0
        emails = []
        
        # print(employees_list)
        
        for employee_object in employees_list:
            employee_parce_data = employees_list.get(employee_object)
            employee_data = BinotelEpmloyees.parse_obj(employee_parce_data)
            
            # print(employee_data)
            
            data = EpmloyeersOnline.from_binotel(employee_data)
            
            online += data.count_online
            offline += data.count_offline
            all_empl += data.count_all
            
            if data.email != '':
                emails.append(data.email)
        
        return {
            'online': online,
            'offline': offline,
            'all_empl': all_empl,
            'emails': emails
        }
    
    async def get_history_from_binotel(self, emails):
        now = datetime.now();
        hour_ago = now - timedelta(hours=1)
        now_timestamp = int(time.time())
        hour_ago_timestamp = int(datetime.timestamp(hour_ago))
        
        body_request = {
            "key": settings.BINOTEL_KEY,
            "secret": settings.BINOTEL_SECRET,
            "startTime": hour_ago_timestamp,
            "stopTime": now_timestamp
        }
        
        print(body_request)
        
        binotel_response = requests.post(f'{settings.BINOTEL_URL}/stats/list-of-calls-for-period.json',
                                         json=body_request)
        
        data_binotel = json.loads(binotel_response.content)
        if data_binotel.get("status") != 'success':
            return None
        
        calls_list = data_binotel.get("callDetails")
        
        wait_arr = []
        bill_arr = []
        for history_object in calls_list:
            history_parce_data = calls_list.get(history_object)
            history_data = BinotelHistoryCall.parse_obj(history_parce_data)
            data = HistoryCall.from_binotel(history_data)
            # if data.email in emails and (data.wait > 0 and data.bill > 0):
            
            print(emails)
            
            if data.email in emails and data.bill > 0:
                wait_arr.append(data.wait)
                bill_arr.append(data.bill)
        
        return {"wait_arr": wait_arr, "bill_arr": bill_arr}
    
    async def get_online_call_from_binotel(self, emails):
        body_request = {
            "key": settings.BINOTEL_KEY,
            "secret": settings.BINOTEL_SECRET
        }
        
        binotel_response = requests.post(f'{settings.BINOTEL_URL}/stats/online-calls.json',
                                         json=body_request)
        
        data_binotel = json.loads(binotel_response.content)
        if data_binotel.get("status") != 'success':
            return None
        
        calls_list = data_binotel.get("callDetails")
        
        print(emails)
        
        time_in_call = []
        for call_object in calls_list:
            call_parce_data = calls_list.get(call_object)
            call_data = BinotelCallOnline.parse_obj(call_parce_data)
            data = CallOnline.from_binotel(call_data)
            if data.email in emails:
                time_in_call.append(data.time)
        
        return time_in_call
    
    async def get(self):
        # branch = self.request.query.get('branch')
        # queue = self.request.query.get('queue')
        
        # if (branch is None or queue is None):
        #     data = {
        #         'result': 400,
        #         'message': 'branch/queue is required',
        #         'ewt': 99999
        #     }
        #     return web.json_response(data)
        employees = await self.get_emloyees_from_binotel()
        print(employees)
        
        if employees is None:
            data = {
                'result': 'error',
                'message': 'no agents',
                'ewt': 99999,
                'calc_param': {
                    'free': None
                }
            }
            return web.json_response(data)
        #    return web.json_response(await self.get_last_ewt())
        
        
        
        if employees.get('all_empl') == employees.get('offline'):
            data = {
                'result': 'error',
                'message': 'no agents',
                'ewt': 99999,
                'calc_param': {
                    'free': None
                }
            }
            return web.json_response(data)
        
        elif employees.get('online') != 0:
            await self.save_last_ewt(10)
            data = {
                'result': 'ok',
                'message': 'estimated wait time',
                'ewt': 7,
                'calc_param': {
                    'free': employees.get('online')
                }
            }
            return web.json_response(data)
        
        emails = employees.get('emails')
        
        # last calls at hour ago
        history_data = await self.get_history_from_binotel(emails)
        if history_data is None:
            data = {
                'result': 'error',
                'message': 'no agents',
                'ewt': 99999,
                'calc_param': {
                    'free': None
                }
            }
            return web.json_response(data)
            #return web.json_response(await self.get_last_ewt())
            max_value_call_history = 0
        
        # wait_arr = history_data.get("wait_arr")
        bill_arr = history_data.get("bill_arr")
        
        max_value_call_history = 0 if len(bill_arr) == 0 else max(bill_arr)
        # min_value_bill = 0 if len(bill_arr) == 0 else max(bill_arr)
        avg_value_bill_history = 0 if len(bill_arr) == 0 else int(sum(bill_arr) / len(bill_arr))
        
        # max_value_wait = 0 if len(wait_arr) == 0 else max(wait_arr)
        # min_value_wait = 0 if len(wait_arr) == 0 else max(wait_arr)
        # avg_value_wait = 0 if len(wait_arr) == 0 else sum(wait_arr) / len(wait_arr)
        
        # calls online
        call_online = await self.get_online_call_from_binotel(emails)
        if call_online is None:
            data = {
                'result': 'error',
                'message': 'no agents',
                'ewt': 99999,
                'calc_param': {
                    'free': None
                }
            }
            return web.json_response(data)
            max_value_call_online = 0
            # return web.json_response(await self.get_last_ewt())
        
        max_value_call_online = 0 if len(call_online) == 0 else max(call_online)
        
        max_value_call = max(max_value_call_online, max_value_call_history)
        
        # min_value_call = 0 if len(call_online) == 0 else min(call_online)
        #avg_value_call = 0 if len(call_online) == 0 else sum(call_online) / len(call_online)
        
        # ewt = avg_value_bill - (avg_value_call + avg_value_wait)
        # if ewt < 0:
        #      ewt = (max_value_call + 60) - (max_value_call + avg_value_wait)
        ewt = (max_value_call + 180) - (avg_value_bill_history + 10)
        
        data = {
            'result': 'ok',
            'message': 'estimated wait time',
            'ewt': int(ewt),
            'calc_param': {
                'max_value_call': max_value_call,
                'max_value_call_online': max_value_call_online,
                'max_value_call_history': max_value_call_history,
                "avg_value_bill_history": avg_value_bill_history
            }
        }
        await self.save_last_ewt(ewt)
        return web.json_response(data)

