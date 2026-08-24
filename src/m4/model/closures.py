"""Explicit v0 closure choices; none installs an empirical equation."""
from enum import Enum


class Closure(str, Enum):
    HISTORICAL_DEFAULT = "historical-default"
    FIXED_GOVERNMENT_SPENDING = "fixed-government-spending"
    USER_SPECIFIED_FISCAL_RESPONSE = "user-specified-fiscal-response"
    USER_SPECIFIED_FX = "user-specified-fx"
