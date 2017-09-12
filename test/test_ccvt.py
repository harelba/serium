#!/usr/bin/env python

from collections import OrderedDict
from unittest import TestCase

from pycase.caseclasses import CaseClass, cc_to_dict, cc_from_dict, CaseClassException, CaseClassSubTypeKey, CaseClassSubTypeValue, cc_to_json_str, cc_from_json_str, CaseClassListType, \
    CaseClassSelfType, VersionNotFoundCaseClassException, MissingVersionDataCaseClassException, IncompatibleTypesCaseClassException


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

        with self.assertRaises(MissingVersionDataCaseClassException) as cm:
            o = cc_from_dict(serialized, MyClass)
        assert str(cm.exception.ccvt) == 'MyClass/5'

    def test_deserialization_failure_of_different_class(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'AnotherClass/1'}
        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_of_unknown_class(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'UnknownClass/1'}
        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)

    def test_nested_serialization2(self):
        p = ParentClass(42, MyClass(100, 'mystr'))
        d = cc_to_dict(p)

        assert sorted(d.keys()) == ['_ccvt', 'nested', 'some_int']
        assert sorted(d['nested'].keys()) == ['_ccvt', 'x', 'y']

        assert d['some_int'] == 42

        assert d['nested']['x'] == 100
        assert d['nested']['y'] == 'mystr'

    def test_deserialization_of_different_class(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'AnotherClass/1'}

        with self.assertRaises(IncompatibleTypesCaseClassException) as cm:
            o = cc_from_dict(serialized, MyClass)
        assert str(cm.exception.ccvt) == 'AnotherClass/1'
        assert str(cm.exception.self_vt) == 'MyClass/5'

    def test_deserialization_failure_of_unknown_class_with_ignored_versioning(self):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'UnknownClass/1'}
        with self.assertRaises(CaseClassException):
            o = cc_from_dict(serialized, MyClass)


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

    def test_unversioned_data_deserialization__fails(self):
        ser_a = """{ "a": 500, "doubled": 5000 }"""

        with self.assertRaises(MissingVersionDataCaseClassException) as cm:
            a_v3 = cc_from_json_str(ser_a, A)
        print str(cm.exception.ccvt) == 'A/3'


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

    def test_top_layer_migration(self):
        c = C__v1(1000, A(500L, 30L))

        s = cc_to_json_str(c)
        print s
        deserialized_c = cc_from_json_str(s, C)
        print deserialized_c

        assert deserialized_c == C(1000, B(500, A(500L, 30L)))

    def test_two_layer_migration(self):
        c = C__v1(1000, A__v1(500, 30L))

        s = cc_to_json_str(c)
        print s
        deserialized_c = cc_from_json_str(s, C)
        print deserialized_c

        assert deserialized_c == C(1000, B(500, A(500L, 60L)))

    def test_two_layer_migration__internal_layer_only(self):
        c = C__v1(1000, A__v1(500, 30L))

        s = cc_to_json_str(c)
        print s
        deserialized_c = cc_from_json_str(s, C__v1)
        print deserialized_c

        assert deserialized_c == C__v1(1000, A(500L, 60L))


class MyCaseClassWithList(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('l', CaseClassListType(A))])
    CC_V = 1

    def __init__(self, l):
        self.l = l


class CCVTListTypeTests(TestCase):
    def test_list__no_migration(self):
        c = MyCaseClassWithList([A(100L, 200L), A(200L, 300L), A(400L, 500L)])

        d = cc_to_dict(c)
        assert set([x['_ccvt'] for x in d['l']]) == {"A/3"}

    def test_list__deserialization_without_migration(self):
        s = """
        { "l": [
            {"a": 100,"doubled": 200,"_ccvt": "A/3"},
            {"a": 200,"doubled": 300,"_ccvt": "A/3"},
            {"a": 400,"doubled": 500,"_ccvt": "A/3"}
          ],
            "_ccvt": "MyCaseClassWithList/1"
        }"""
        c = cc_from_json_str(s, MyCaseClassWithList)

        assert c == MyCaseClassWithList([A(100L, 200L), A(200L, 300L), A(400L, 500L)])

    def test_list__deserialization_with_migration(self):
        s = """
        { "l": [
            {"x": 1,"y": 10,"_ccvt": "A/2"},
            {"x": 2,"y": 20,"_ccvt": "A/2"},
            {"x": 3,"y": 30,"_ccvt": "A/2"}
          ],
            "_ccvt": "MyCaseClassWithList/1"
        }"""
        c = cc_from_json_str(s, MyCaseClassWithList)

        assert c == MyCaseClassWithList([A(1L, 20L), A(2L, 40L), A(3L, 60L)])


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

    def test_deserialization_of_unknown_subtype(self):
        d = {
            "_ccvt": "SuperType/1",
            "super_value": 1000,
            "request_type": "SubType",
            "details": {
                "x": 200, "y": 300,
                "_ccvt": "SubType/5"
            }
        }
        with self.assertRaises(VersionNotFoundCaseClassException) as cm:
            c = cc_from_dict(d, SuperType)
        assert str(cm.exception.ccvt) == 'SubType/5'

    def test_serialization_of_subtype_with_ignored_versioning(self):
        c = SuperType(1000, "SubType", SubType(200, 300))

        d = cc_to_dict(c)
        assert d['super_value'] == 1000
        assert d['request_type'] == SubType.__name__
        assert d['details']['x'] == 200
        assert d['details']['y'] == 300

    def test_serde_1_with_ignored_versioning(self):
        c1 = SuperType(1000, "SubType", SubType(200, 300))

        s = cc_to_json_str(c1)
        c2 = cc_from_json_str(s, SuperType)

        assert c1 == c2


class MyTreeNode__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('value', int),
        ('children', CaseClassListType(CaseClassSelfType()))
    ])
    CC_V = 1

    def __init__(self, value, children):
        self.value = value
        self.children = children


class MyTreeNode(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('value', int),
        ('name', str),
        ('children', CaseClassListType(CaseClassSelfType()))
    ])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: MyTreeNode(old.value, 'noname', old.children)
    }

    def __init__(self, value, name, children):
        self.value = value
        self.name = name
        self.children = children


class CCVTSelfTypeTests(TestCase):
    def test_self_type_serde__without_migration(self):
        children = [MyTreeNode(2, 'name2', []), MyTreeNode(3, 'name3', [MyTreeNode(4, 'name4', [])])]
        t1 = MyTreeNode(1, 'name1', children)

        s = cc_to_json_str(t1)
        print s
        t2 = cc_from_json_str(s, MyTreeNode)

        assert t1 == t2

    def test_self_type_serde__with_migration(self):
        s = """
            {"_ccvt":"MyTreeNode/1","value":1,
            "children":[
                {"_ccvt":"MyTreeNode/1","value":2,"children":[]},
                    {"_ccvt":"MyTreeNode/1","value":3,
                        "children":[{"_ccvt":"MyTreeNode/1","value":4,"children":[]}]}]}
        """
        t2 = cc_from_json_str(s, MyTreeNode)

        children = [MyTreeNode(2, 'noname', []), MyTreeNode(3, 'noname', [MyTreeNode(4, 'noname', [])])]
        t1 = MyTreeNode(1, 'noname', children)
        assert t1 == t2

    def test_self_type_serde__with_mixed_migration_and_no_migration(self):
        s = """
            {"_ccvt":"MyTreeNode/2","value":1,"name":"name1",
            "children":[
                {"_ccvt":"MyTreeNode/1","value":2,"children":[]},
                {"_ccvt":"MyTreeNode/2","value":3,"name":"name3","children":[]}
            ]
            }
        """
        t2 = cc_from_json_str(s, MyTreeNode)

        assert t2 == MyTreeNode(1, 'name1', [MyTreeNode(2, 'noname', []), MyTreeNode(3, 'name3', [])])

    def test_self_data_contains_future_version__fails(self):
        s = """
            {"_ccvt":"MyTreeNode/1","value":1,
            "children":[
                   {"_ccvt":"MyTreeNode/2","value":3,"name":"name3","children":[]}
                ]
            }
        """
        with self.assertRaises(VersionNotFoundCaseClassException):
            t2 = cc_from_json_str(s, MyTreeNode)


class TwoWayMigrationData__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('x1', int), ('x2', int)])
    CC_V = 1
    CC_MIGRATIONS = {
        2: lambda new: TwoWayMigrationData__v1(new.y1, new.y2)
    }

    def __init__(self, x1, x2):
        self.x1 = x1
        self.x2 = x2


class TwoWayMigrationData(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([('y1', int), ('y2', int), ('s', int)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: TwoWayMigrationData(old.x1, old.x2, old.x1 + old.x2)
    }

    def __init__(self, y1, y2, s):
        self.y1 = y1
        self.y2 = y2
        self.s = s


class TwoWayMigrationTests(TestCase):
    def test_two_way_migration_forward(self):
        c1 = TwoWayMigrationData__v1(100, 200)
        s = cc_to_json_str(c1)

        c2 = cc_from_json_str(s, TwoWayMigrationData)

        assert c2 == TwoWayMigrationData(100, 200, 300)

    def test_two_way_migration_backward(self):
        c1 = TwoWayMigrationData(100, 200, 300)
        s = cc_to_json_str(c1)

        c2 = cc_from_json_str(s, TwoWayMigrationData__v1)

        assert c2 == TwoWayMigrationData__v1(100, 200)


class WithDict__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('val', int),
        ('d', dict)
    ])
    CC_V = 1

    def __init__(self, val, d):
        self.val = val
        self.d = d


class WithDict(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('val', int),
        ('d', dict),
        ('x', int)
    ])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: WithDict(old.val, old.d, old.d['x'])
    }

    def __init__(self, val, d, x):
        self.val = val
        self.d = d
        self.x = x


class MigrationOfCaseClassWithDict(TestCase):
    def test_serde_of_caseclass_with_dict(self):
        c1 = WithDict__v1(100, {"x": 100, "y": 200})
        s = cc_to_json_str(c1)

        c2 = cc_from_json_str(s, WithDict)

        assert c2.val == c1.val
        assert c2.x == c1.d['x']
        assert c2.d == c1.d
