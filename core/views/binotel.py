from typing import Optional

from pydantic import BaseModel


class BinotelEpmloyees(BaseModel):
    class BinotelEndpointDataEpmloyees(BaseModel):
        class BinotelStatusEpmloyees(BaseModel):
            status: Optional[str] = None
        id: Optional[str] = ""
        department: Optional[str] = ""
        status: Optional[BinotelStatusEpmloyees] = None
    employeeID: Optional[str] = ""
    email: Optional[str] = ""
    name: Optional[str] = ""
    department: Optional[str] = ""
    presenceState: Optional[str] = ""
    endpointData: BinotelEndpointDataEpmloyees
    mobileNumber: Optional[str] = ""


class BinotelHistoryCall(BaseModel):
    class BinotelEndpointDataEpmloyees(BaseModel):
        name: Optional[str] = ""
        email: Optional[str] = ""
    companyID: Optional[str] = ""
    disposition: Optional[str] = ""
    waitsec:  Optional[str] = ""
    billsec: Optional[str] = ""
    employeeData: BinotelEndpointDataEpmloyees


class BinotelCallOnline(BaseModel):
    class BinotelEndpointDataEpmloyees(BaseModel):
        name: Optional[str] = ""
        email: Optional[str] = ""
    companyID: Optional[str] = ""
    startTime: Optional[int] = 0
    employeeData: BinotelEndpointDataEpmloyees
