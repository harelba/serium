#!/usr/bin/env python

from serium.caseclasses import CaseClassTypeAsString, CaseClassListType
from uuid import UUID
from decimal import Decimal

cc_uuid = CaseClassTypeAsString(UUID)
cc_decimal = CaseClassTypeAsString(Decimal)

def cc_list(t):
    return CaseClassListType(t)
