from fastapi import FastAPI, HTTPException
from typing import Optional, Literal
from pydantic import BaseModel,Field
from datetime import date

app = FastAPI(version="1.0")

class CarriersSchema(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=3)
    max_weight_capacity: int = Field(gt=0)
    status: Literal[
        "ACTIVE",
        "INACTIVE",
        "SUSPENDED"
    ]

class ShipmentSchema(BaseModel):
    carrier_id: int
    order_reference: str = Field(min_length=1)
    total_weight: int = Field(gt = 0)
    dispatch_date: date
    shift: Literal[
        "MORNING",
        "AFTERNOON",
        "NIGHT"
    ]

carriers = [
{"id": 1, "code": "GHN", "name": "Giao Hang Nhanh", "max_weight_capacity": 5000, "status": "ACTIVE"},
{"id": 2, "code": "GHTK", "name": "Giao Hang Tiet Kiem", "max_weight_capacity": 3000, "status": "ACTIVE"},
{"id": 3, "code": "VTP", "name": "Viettel Post", "max_weight_capacity": 10000, "status": "SUSPENDED"}
]

shipments = [
{
"id": 1,
"carrier_id": 1,
"order_reference": "ORD-2026-001",
"total_weight": 4200,
"dispatch_date": "2026-07-01",
"shift": "MORNING"
}
]

@app.post("/carriers")
def create_carrier(carrier: CarriersSchema):
    for c in carriers:
        if c["code"] == carrier.code:
            raise HTTPException(status_code=400, detail="Carrier code already exists")
    if carriers:
        new_id = max(c["id"] for c in carriers) + 1
    else:
        new_id = 1
    
    new_carrier = {
        "id": new_id,
        "code": carrier.code,
        "name": carrier.name,
        "max_weight_capacity": carrier.max_weight_capacity,
        "status": carrier.status
    }
    carriers.append(new_carrier)
    return new_carrier

@app.get("/carriers")
def get_carrier(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    min_weight: Optional[int] = None
):
    result = carriers
    if keyword:
        result = [
            c for c in result
            if keyword.lower() in c["code"].lower()
            or keyword.lower() in c["name"].lower()
        ]
    if status:
        result = [
            c for c in result
            if c["status"] == status
        ]
    if min_weight:
        result = [
            c for c in result
            if c["max_weight_capacity"] >= min_weight
        ]
    return result

@app.get("/carriers/{carrier_id}")
def get_carrier_by_id(carrier_id: int):
    for c in carriers:
        if c["id"] == carrier_id:
            return c
    raise HTTPException(status_code=404, detail="Carrier not found")

@app.put("/carriers/{carrier_id}")
def update_carrier(carrier_id: int, carrier: CarriersSchema):
    for c in carriers:
        if c["code"] == carrier.code and c["id"] != carrier_id:
            raise HTTPException(status_code=400, detail="Carrier code already exists")
    for c in carriers:
        if c["id"] == carrier_id:
            c["code"] = carrier.code
            c["name"] = carrier.name
            c["max_weight_capacity"] = carrier.max_weight_capacity
            c["status"] = carrier.status

            return c
    raise HTTPException(status_code=404, detail="Carrier not found")

@app.delete("/carriers/{carrier_id}")
def delete_carrier(carrier_id: int):
    for c in carriers:
        if c["id"] == carrier_id:
            carriers.remove(c)
            return {"message": "Carrier deleted successfully"}

    raise HTTPException(
        status_code=404,
        detail="Carrier not found"
    )

@app.get("/shipments")
def get_shipments():
    return shipments

@app.post("/shipments")
def create_shipment(shipment: ShipmentSchema):

    carrier = None

    # 1. Kiểm tra carrier có tồn tại không
    for c in carriers:
        if c["id"] == shipment.carrier_id:
            carrier = c
            break

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found"
        )

    # 2. Carrier phải ACTIVE
    if carrier["status"] != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Carrier is not active"
        )

    # 3. Không vượt tải trọng
    if shipment.total_weight > carrier["max_weight_capacity"]:
        raise HTTPException(
            status_code=400,
            detail="Weight exceeds carrier capacity"
        )

    # 4. Không được trùng lịch
    for s in shipments:
        if (
            s["carrier_id"] == shipment.carrier_id
            and s["dispatch_date"] == str(shipment.dispatch_date)
            and s["shift"] == shipment.shift
        ):
            raise HTTPException(
                status_code=400,
                detail="Carrier already has a shipment in this shift"
            )

    # 5. Sinh id mới
    if shipments:
        new_id = max(s["id"] for s in shipments) + 1
    else:
        new_id = 1

    # 6. Tạo shipment mới
    new_shipment = {
        "id": new_id,
        "carrier_id": shipment.carrier_id,
        "order_reference": shipment.order_reference,
        "total_weight": shipment.total_weight,
        "dispatch_date": str(shipment.dispatch_date),
        "shift": shipment.shift
    }

    shipments.append(new_shipment)

    return new_shipment