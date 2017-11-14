#!/usr/bin/env python

from uuid import UUID
from decimal import Decimal

__all__ = ['cc_uuid', 'cc_decimal', 'cc_self_type', 'cc_list', 'cc_dict', 'cc_subtype_key', 'cc_subtype_value', 'cc_type_as_string']


class CaseClassListType(object):
    def __init__(self, element_type):
        self.element_type = element_type

    def __str__(self):
        return "CaseClassListType(element_type={}".format(repr(self.element_type))

    def __repr__(self):
        return self.__str__()


class CaseClassDictType(object):
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type

    def __str__(self):
        return "CaseClassDictType(key_type={},value_type={})".format(repr(self.key_type), repr(self.value_type))

    def __repr__(self):
        return self.__str__()


class CaseClassSelfType(object):
    def __init__(self):
        pass

    def __str__(self):
        return "CaseClassSelfType()"

    def __repr__(self):
        return self.__str__()


class CaseClassTypeAsString(object):
    def __init__(self, real_type):
        self.real_type = real_type

    def __str__(self):
        return "CaseClassTypeAsString(real_type={})".format(repr(self.real_type))

    def __repr__(self):
        return self.__str__()


class CaseClassSubTypeKey(object):
    def __init__(self, subtype_value_field_name):
        self.subtype_value_field_name = subtype_value_field_name

    def __str__(self):
        return "CaseClassSubTypeKey(subtype_value_field_name={})".format(repr(self.subtype_value_field_name))

    def __repr__(self):
        return self.__str__()


class CaseClassSubTypeValue(object):
    def __init__(self, subtype_key_field_name):
        self.subtype_key_field_name = subtype_key_field_name

    def __str__(self):
        return "CaseClassSubTypeValue(subtype_key_field_name={})".format(repr(self.subtype_key_field_name))

    def __repr__(self):
        return self.__str__()


cc_uuid = CaseClassTypeAsString(UUID)
cc_decimal = CaseClassTypeAsString(Decimal)
cc_self_type = CaseClassSelfType()


def cc_list(t):
    return CaseClassListType(t)


def cc_dict(kt, vt):
    return CaseClassDictType(kt, vt)


def cc_subtype_key(value_field_name):
    return CaseClassSubTypeKey(value_field_name)


def cc_subtype_value(key_field_name):
    return CaseClassSubTypeValue(key_field_name)


def cc_type_as_string(t):
    return CaseClassTypeAsString(t)
