#!/usr/bin/env python

from serium.caseclasses import CaseClassTypeAsString, CaseClassListType, CaseClassSelfType
from uuid import UUID
from decimal import Decimal

cc_uuid = CaseClassTypeAsString(UUID)
cc_decimal = CaseClassTypeAsString(Decimal)
cc_self_type = CaseClassSelfType()

def cc_list(t):
    return CaseClassListType(t)

def cc_dict(kt,vt):
    return CaseClassDictType(kt,vt)

