"""Pydantic schemas for requests/responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

ListingType = Literal["buy", "rent", "commercial"]
PropertyType = Literal[
    "apartment", "independent-house", "villa", "builder-floor",
    "studio", "pg-hostel", "office", "shop", "warehouse", "plot",
]
Furnishing = Literal["furnished", "semi-furnished", "unfurnished"]
PropertyStatus = Literal["pending", "active", "rejected", "sold", "rented"]


# ---------- Auth ----------
class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    phone: Optional[str] = Field(default=None, max_length=20)
    about: Optional[str] = Field(default=None, max_length=500)


# ---------- Properties ----------
class PropertyBase(BaseModel):
    title: str = Field(min_length=5, max_length=140)
    description: str = Field(default="", max_length=4000)
    listing_type: ListingType
    property_type: PropertyType
    price: float = Field(gt=0)
    area_sqft: float = Field(gt=0, le=200_000)
    bedrooms: int = Field(default=0, ge=0, le=20)
    bathrooms: int = Field(default=0, ge=0, le=20)
    balconies: int = Field(default=0, ge=0, le=20)
    floor: Optional[str] = Field(default=None, max_length=40)
    total_floors: Optional[int] = Field(default=None, ge=0, le=200)
    furnishing: Furnishing = "unfurnished"
    facing: Optional[str] = Field(default=None, max_length=30)
    age_years: Optional[int] = Field(default=None, ge=0, le=120)
    city: str = Field(min_length=2, max_length=60)
    locality: str = Field(min_length=1, max_length=80)
    address: str = Field(default="", max_length=300)
    pincode: Optional[str] = Field(default=None, max_length=10)
    amenities: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    contact_name: Optional[str] = Field(default=None, max_length=80)
    contact_phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("amenities", "images")
    @classmethod
    def _cap_list(cls, v: list[str]) -> list[str]:
        return [str(x)[:500] for x in v][:15]

    @field_validator("title", "city", "locality")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=140)
    description: Optional[str] = Field(default=None, max_length=4000)
    listing_type: Optional[ListingType] = None
    property_type: Optional[PropertyType] = None
    price: Optional[float] = Field(default=None, gt=0)
    area_sqft: Optional[float] = Field(default=None, gt=0, le=200_000)
    bedrooms: Optional[int] = Field(default=None, ge=0, le=20)
    bathrooms: Optional[int] = Field(default=None, ge=0, le=20)
    balconies: Optional[int] = Field(default=None, ge=0, le=20)
    floor: Optional[str] = None
    total_floors: Optional[int] = Field(default=None, ge=0, le=200)
    furnishing: Optional[Furnishing] = None
    facing: Optional[str] = None
    age_years: Optional[int] = Field(default=None, ge=0, le=120)
    city: Optional[str] = Field(default=None, min_length=2, max_length=60)
    locality: Optional[str] = Field(default=None, min_length=1, max_length=80)
    address: Optional[str] = Field(default=None, max_length=300)
    pincode: Optional[str] = None
    amenities: Optional[list[str]] = None
    images: Optional[list[str]] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class StatusUpdate(BaseModel):
    status: PropertyStatus
    featured: Optional[bool] = None


# ---------- Enquiries ----------
class EnquiryCreate(BaseModel):
    property_id: str
    message: str = Field(min_length=5, max_length=1000)
    phone: Optional[str] = Field(default=None, max_length=20)


class EnquiryReply(BaseModel):
    reply: str = Field(min_length=2, max_length=1000)


# ---------- ML / AI Valuation ----------
class PredictRequest(BaseModel):
    city: str = Field(default="Chennai", min_length=2, max_length=100)
    locality: Optional[str] = Field(default="", max_length=100)
    property_type: Optional[str] = Field(default="apartment", max_length=50)
    area: int = Field(gt=0, le=200_000)
    bedrooms: int = Field(ge=1, le=20)
    bathrooms: int = Field(ge=1, le=20)
    stories: int = Field(ge=1, le=10)
    parking: int = Field(ge=0, le=10)
    mainroad: bool = True
    guestroom: bool = False
    basement: bool = False
    hotwaterheating: bool = False
    airconditioning: bool = False
    prefarea: bool = False
    furnishingstatus: Literal["furnished", "semi-furnished", "unfurnished"] = "semi-furnished"

    @field_validator("city", "locality")
    @classmethod
    def _strip_strings(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class ApiResponse(BaseModel):
    ok: bool = True
    message: str = ""
    data: Optional[Any] = None
    created_at: Optional[datetime] = None
