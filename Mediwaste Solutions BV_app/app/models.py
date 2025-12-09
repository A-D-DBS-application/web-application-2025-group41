import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import quoted_name # <-- belangrijk
from sqlalchemy import Computed #nodig voor total cost hmw barrels
from . import db

class User(db.Model):
    __tablename__ = quoted_name("USER", True)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_user = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    company_number = Column(Integer, nullable=False)
    password = Column(String, nullable=False)
    name_organization = Column(String, nullable=False)
    position = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    confirm = Column(String)

    requests = relationship("Request", back_populates="user")


class Request(db.Model):
    __tablename__ = quoted_name("REQUEST", True)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(quoted_name("USER", True) + ".id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="requests")
    waste_profile = relationship("WasteProfile", uselist=False, back_populates="request")
    machine_size_calc = relationship("MachineSizeCalc1", uselist=False, back_populates="request")
    payback_period_calc = relationship("PaybackPeriodCalc2", uselist=False, back_populates="request")


class WasteProfile(db.Model):
    __tablename__ = quoted_name("WASTE_PROFILE", True)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey(quoted_name("REQUEST", True) + ".id"), nullable=False)

    cost_collection_processing = Column(Numeric)
    hmw_total_weight = Column(Numeric)

    wiva_types = Column(Integer, nullable=True)

    number_of_barrels_1 = Column(Integer)
    number_of_barrels_2 = Column(Integer)
    number_of_barrels_3 = Column(Integer)
    number_of_barrels_4 = Column(Integer)

    volume_barrels_1 = Column(Integer)
    volume_barrels_2 = Column(Integer)
    volume_barrels_3 = Column(Integer)
    volume_barrels_4 = Column(Integer)

    cost_hmw_barrels_1 = Column(Numeric)
    cost_hmw_barrels_2 = Column(Numeric)
    cost_hmw_barrels_3 = Column(Numeric)
    cost_hmw_barrels_4 = Column(Numeric)



    total_cost_hmw_barrels = Column( Numeric, Computed("NULL"), nullable=True)
    steam_generator_needed = Column(Boolean)

    request = relationship("Request", back_populates="waste_profile")


class MachineSpecs(db.Model):
    __tablename__ = quoted_name("MACHINE_SPECS", True)

    id = Column(Integer, primary_key=True)
    size_code = Column(Text)
    capacity = Column(Integer)
    selling_price = Column(Numeric)
    electricity_consumption = Column(Numeric)
    water_consumption = Column(Numeric)


class MachineSizeCalc1(db.Model):
    __tablename__ = quoted_name("MACHINE_SIZE_CALC1", True)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey(quoted_name("REQUEST", True) + ".id"), nullable=False)
    recommended_machine_id = Column(Integer) # <- aangepast naar de naam in de database

    request = relationship("Request", back_populates="machine_size_calc")

    machine = relationship(
        "MachineSpecs",
        primaryjoin="foreign(MachineSizeCalc1.recommended_machine_id) == remote(MachineSpecs.id)",
        uselist=False,
        viewonly=True
    )


class PaybackPeriodCalc2(db.Model):
    __tablename__ = quoted_name("PAYBACK_PERIOD_CALC2", True)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey(quoted_name("REQUEST", True) + ".id"), nullable=False)
    payback_months = Column(Numeric)

    request = relationship("Request", back_populates="payback_period_calc")