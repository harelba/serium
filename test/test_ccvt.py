#!/usr/bin/env python

from collections import OrderedDict
from unittest import TestCase

from pycase.caseclasses import CaseClass, cc_to_dict, cc_from_dict, CaseClassException, CaseClassSubTypeKey, CaseClassSubTypeValue, cc_to_json_str, cc_from_json_str


class MyClass(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('x', int), ('y', str)])
    CC_V = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_serialization():
    a = MyClass(100, 'str1')
    s = cc_to_dict(a)
    print s
    assert s['x'] == 100
    assert s['y'] == 'str1'
    assert s['_ccvt'] == 'MyClass/5'


class ParentClass(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('some_int', int), ('nested', MyClass)])
    CC_V = 7

    def __init__(self, some_int, nested):
        self.some_int = some_int
        self.nested = nested


class AnotherClass(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('x', int)])
    CC_V = 1

    def __init__(self, x):
        self.x = x


class CCVTTests(TestCase):
    def test_nested_serialization(self):
        p = ParentClass(42, MyClass(100, 'mystr'))
        d = cc_to_dict(p)
        print d
        assert d['some_int'] == 42
        assert d['_ccvt'] == 'ParentClass/7'
        assert d['nested']['x'] == 100
        assert d['nested']['y'] == 'mystr'
        assert d['nested']['_ccvt'] == 'MyClass/5'

    def test_deserialization_of_same_version(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/5'}
        o = cc_from_dict(serialized, MyClass)

        assert o == MyClass(100, 'str1')

    def test_deserialization_failure_when_invalid_ccvt(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass'}

        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_when_invalid_version_in_ccvt(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/-3'}

        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_when_invalid_version_in_ccvt2(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/aaa'}

        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_when_ccvt_missing(self):
        serialized = {'y': 'str1', 'x': 100}

        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_deserialization_ok_when_ccvt_missing_and_ignored_versioning(self):
        serialized = {'y': 'str1', 'x': 100}

        o = cc_from_dict(serialized, MyClass, ignore_versioning=True)

        assert o == MyClass(100, 'str1')

    def test_deserialization_failure_of_different_class(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'AnotherClass/1'}
        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_of_unknown_class(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'UnknownClass/1'}
        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_nested_serialization_with_ignored_versioning(self):
        p = ParentClass(42, MyClass(100, 'mystr'))
        d = cc_to_dict(p, ignore_versioning=True)

        assert sorted(d.keys()) == ['nested', 'some_int']
        assert sorted(d['nested'].keys()) == ['x', 'y']

        assert d['some_int'] == 42

        assert d['nested']['x'] == 100
        assert d['nested']['y'] == 'mystr'

    def test_deserialization_of_same_version_with_ignored_versioning(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/5'}
        o = cc_from_dict(serialized, MyClass, ignore_versioning=True)

        assert o == MyClass(100, 'str1')

    def test_deserialization_of_different_class_with_ignored_versioning(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'AnotherClass/1'}
        o = cc_from_dict(serialized, MyClass, ignore_versioning=True)

        assert o == MyClass(100, 'str1')

    def test_deserialization_failure_of_unknown_class_with_ignored_versioning(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'UnknownClass/1'}
        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass, ignore_versioning=True)


class SuperType(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('super_value', int),
        ('request_type', CaseClassSubTypeKey("details")),
        ('details', CaseClassSubTypeValue('request_type'))
    ])
    CC_V = 1

    def __init__(self, super_value, request_type, details):
        self.super_value = super_value
        self.request_type = request_type
        self.details = details


class SubType(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('x', int),
        ('y', int)
    ])
    CC_V = 2

    def __init__(self, x, y):
        self.x = x
        self.y = y


class A__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('x', int), ('y', long)])
    CC_V = 1

    def __init__(self, x, y):
        self.x = x
        self.y = y


class A__v2(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('x', long), ('y', long)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: A__v2(x=long(old.x), y=old.y)
    }

    def __init__(self, x, y):
        self.x = x
        self.y = y


class A(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('a', long), ('doubled', long)])
    CC_V = 3
    CC_MIGRATIONS = {
        2: lambda old: A(a=old.x, doubled=old.y * 2)
    }

    def __init__(self, a, doubled):
        self.a = a
        self.doubled = doubled


class CCVTMigrationOnRead(TestCase):
    def test_migration_on_read(self):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/1" }"""

        a_v3 = cc_from_json_str(ser_a, A)

        assert a_v3 == A(a=100L, doubled=4002L)

    def test_migration_on_read_2(self):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/1" }"""

        a_v2 = cc_from_json_str(ser_a, A__v2)
        assert a_v2 == A__v2(100L, 2001L)

    def test_migration_on_read_3(self):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/2" }"""

        a_v3 = cc_from_json_str(ser_a, A)

        assert a_v3 == A(100L, 4002L)

    def test_failure_to_migrate_on_nonexisting_version(self):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/4" }"""

        with self.assertRaises(CaseClassException):
            a_v4 = cc_from_json_str(ser_a, A)

    def test_non_migration(self):
        ser_a = """{ "a": 500, "doubled": 5000 , "_ccvt": "A/3" }"""

        a_v3 = cc_from_json_str(ser_a, A)

        assert a_v3 == A(500L, 5000L)

    def test_full_serde_with_migration(self):
        a_v1 = A__v1(1, 2L)
        s = cc_to_json_str(a_v1)

        a = cc_from_json_str(s, A)

        assert a == A(a=1L, doubled=4L)

    def test_serde_to_specific_version(self):
        a_v1 = A__v1(1, 2L)
        s = cc_to_json_str(a_v1)

        a_v2 = cc_from_json_str(s, A__v2)

        assert a_v2 == A__v2(1L, 2L)

    def test_unversioned_data_deserialization(self):
        ser_a = """{ "a": 500, "doubled": 5000 }"""

        a_v3 = cc_from_json_str(ser_a, A, ignore_versioning=True)

        assert a_v3 == A(500L, 5000L)


class B(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('my_value', int), ('my_a', A)])
    CC_V = 1
    CC_MIGRATIONS = {}

    def __init__(self, my_value, my_a):
        self.my_value = my_value
        self.my_a = my_a


class C__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('val1', int), ('my_a', A)])
    CC_V = 1
    CC_MIGRATIONS = {}

    def __init__(self, val1, my_a):
        self.val1 = val1
        self.my_a = my_a


class C(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('val1', int), ('my_b', B)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: C(old.val1, B(500, old.my_a))
    }

    def __init__(self, val1, my_b):
        self.val1 = val1
        self.my_b = my_b


class CCVTNestedMigrationOnReadTests(TestCase):
    def test_serde(self):
        b = B(300, A(12L, 500L))
        s = cc_to_json_str(b)

        deserialized_b = cc_from_json_str(s, B)

        assert deserialized_b == b

    def test_serde_with_specific_version(self):
        b = B(300, A__v2(5L, 6L))
        s = cc_to_json_str(b)
        deserialized_b = cc_from_json_str(s, B)

        assert deserialized_b == B(300, A(5L, 12L))

    def test_full_serde_2(self):
        c = C(1000, B(230, A(500L, 30L)))

        s = cc_to_json_str(c)

        deserialized_c = cc_from_json_str(s, C)

        assert deserialized_c == C(1000, B(230, A(500L, 30L)))

    def test_two_layer_migration(self):
        c = C__v1(1000, A(500L, 30L))

        s = cc_to_json_str(c)
        print s
        deserialized_c = cc_from_json_str(s, C)
        print deserialized_c

        assert deserialized_c == C(1000, B(500, A(500L, 30L)))

class CCVTSubTypeTests(TestCase):
    def test_deserialization_of_subtype(self):
        d = {
            "_ccvt": "SuperType/1",
            "super_value": 1000,
            "request_type": "SubType",
            "details": {
                "x": 200, "y": 300,
                "_ccvt": "SubType/2"
            }
        }
        c = cc_from_dict(d, SuperType)

        assert c == SuperType(1000, "SubType", SubType(200, 300))

    def test_serialization_of_subtype(self):
        c = SuperType(1000, "SubType", SubType(200, 300))

        d = cc_to_dict(c)
        print d
        assert d['_ccvt'] == 'SuperType/1'
        assert d['super_value'] == 1000
        assert d['request_type'] == SubType.__name__
        assert d['details']['x'] == 200
        assert d['details']['y'] == 300
        assert d['details']['_ccvt'] == 'SubType/2'

    def test_serde_1(self):
        c1 = SuperType(1000, "SubType", SubType(200, 300))

        s = cc_to_json_str(c1)
        c2 = cc_from_json_str(s, SuperType)

        assert c1 == c2

    def test_deserialization_of_subtype_with_ignored_versioning(self):
        d = {
            "_ccvt": "SuperType/1",
            "super_value": 1000,
            "request_type": "SubType",
            "details": {
                "x": 200, "y": 300,
                "_ccvt": "SubType/5"
            }
        }
        c = cc_from_dict(d, SuperType, ignore_versioning=True)

        assert c == SuperType(1000, "SubType", SubType(200, 300))

    def test_serialization_of_subtype_with_ignored_versioning(self):
        c = SuperType(1000, "SubType", SubType(200, 300))

        d = cc_to_dict(c, ignore_versioning=True)
        assert d['super_value'] == 1000
        assert d['request_type'] == SubType.__name__
        assert d['details']['x'] == 200
        assert d['details']['y'] == 300

    def test_serde_1_with_ignored_versioning(self):
        c1 = SuperType(1000, "SubType", SubType(200, 300))

        s = cc_to_json_str(c1, ignore_versioning=True)
        c2 = cc_from_json_str(s, SuperType, ignore_versioning=True)

        assert c1 == c2
