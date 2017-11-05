#!/usr/bin/env python

import json
from collections import OrderedDict

import pytest

import sys,os
sys.path.insert(0, os.path.join(sys.path[0], '..'))

from serium.caseclasses import CaseClass, CaseClassException, CaseClassSubTypeKey, CaseClassSubTypeValue, CaseClassListType, \
    CaseClassSelfType, VersionNotFoundCaseClassException, MissingVersionDataCaseClassException, IncompatibleTypesCaseClassException, MigrationPathNotFoundCaseClassException, default_to_version_1_func, \
    CaseClassVersionedType, create_default_env, CaseClassSerializationContext, CaseClassDeserializationContext


@pytest.fixture
def env(request):
    return create_default_env()


class MyClass(CaseClass):
    CC_TYPES = OrderedDict([('x', int), ('y', str)])
    CC_V = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_serialization(env):
    a = MyClass(100, 'str1')
    s = env.cc_to_dict(a)
    assert s['x'] == 100
    assert s['y'] == 'str1'
    assert s['_ccvt'] == 'MyClass/5'


class ParentClass(CaseClass):
    CC_TYPES = OrderedDict([('some_int', int), ('nested', MyClass)])
    CC_V = 7

    def __init__(self, some_int, nested):
        self.some_int = some_int
        self.nested = nested


class AnotherClass(CaseClass):
    CC_TYPES = OrderedDict([('x', int)])
    CC_V = 1

    def __init__(self, x):
        self.x = x


class TestCCVTTests:
    def test_nested_serialization(self, env):
        p = ParentClass(42, MyClass(100, 'mystr'))
        d = env.cc_to_dict(p)
        assert d['some_int'] == 42
        assert d['_ccvt'] == 'ParentClass/7'
        assert d['nested']['x'] == 100
        assert d['nested']['y'] == 'mystr'
        assert d['nested']['_ccvt'] == 'MyClass/5'

    def test_deserialization_of_same_version(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/5'}
        o = env.cc_from_dict(serialized, MyClass)

        assert o == MyClass(100, 'str1')

    def test_deserialization_failure_when_invalid_ccvt(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass'}

        with pytest.raises(CaseClassException):
            o = env.cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_when_invalid_version_in_ccvt(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/-3'}

        with pytest.raises(CaseClassException):
            o = env.cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_when_invalid_version_in_ccvt2(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'MyClass/aaa'}

        with pytest.raises(CaseClassException):
            o = env.cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_when_ccvt_missing(self, env):
        serialized = {'y': 'str1', 'x': 100}

        with pytest.raises(MissingVersionDataCaseClassException) as cm:
            o = env.cc_from_dict(serialized, MyClass)
        assert str(cm.value.ccvt) == 'MyClass/5'

    def test_deserialization_failure_of_different_class(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'AnotherClass/1'}
        with pytest.raises(CaseClassException):
            o = env.cc_from_dict(serialized, MyClass)

    def test_deserialization_failure_of_unknown_class(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'UnknownClass/1'}
        with pytest.raises(CaseClassException):
            o = env.cc_from_dict(serialized, MyClass)

    def test_nested_serialization2(self, env):
        p = ParentClass(42, MyClass(100, 'mystr'))
        d = env.cc_to_dict(p)

        assert sorted(d.keys()) == ['_ccvt', 'nested', 'some_int']
        assert sorted(d['nested'].keys()) == ['_ccvt', 'x', 'y']

        assert d['some_int'] == 42

        assert d['nested']['x'] == 100
        assert d['nested']['y'] == 'mystr'

    def test_deserialization_of_different_class(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'AnotherClass/1'}

        with pytest.raises(IncompatibleTypesCaseClassException) as cm:
            o = env.cc_from_dict(serialized, MyClass)
        assert str(cm.value.ccvt) == 'AnotherClass/1'
        assert str(cm.value.self_vt) == 'MyClass/5'

    def test_deserialization_failure_of_unknown_class_with_ignored_versioning(self, env):
        serialized = {'y': 'str1', 'x': 100, '_ccvt': 'UnknownClass/1'}
        with pytest.raises(CaseClassException):
            o = env.cc_from_dict(serialized, MyClass)


class SuperType(CaseClass):
    CC_TYPES = OrderedDict([
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
    CC_TYPES = OrderedDict([
        ('x', int),
        ('y', int)
    ])
    CC_V = 2

    def __init__(self, x, y):
        self.x = x
        self.y = y


class A__v1(CaseClass):
    CC_TYPES = OrderedDict([('x', int), ('y', long)])
    CC_V = 1

    def __init__(self, x, y):
        self.x = x
        self.y = y


class A__v2(CaseClass):
    CC_TYPES = OrderedDict([('x', long), ('y', long)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: A__v2(x=long(old.x), y=old.y)
    }

    def __init__(self, x, y):
        self.x = x
        self.y = y


class A(CaseClass):
    CC_TYPES = OrderedDict([('a', long), ('doubled', long)])
    CC_V = 3
    CC_MIGRATIONS = {
        2: lambda old: A(a=old.x, doubled=old.y * 2)
    }

    def __init__(self, a, doubled):
        self.a = a
        self.doubled = doubled


class TestCCVTMigrationOnRead:
    def test_migration_on_read(self, env):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/1" }"""

        a_v3 = env.cc_from_json_str(ser_a, A)

        assert a_v3 == A(a=100L, doubled=4002L)

    def test_migration_on_read_2(self, env):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/1" }"""

        a_v2 = env.cc_from_json_str(ser_a, A__v2)
        assert a_v2 == A__v2(100L, 2001L)

    def test_migration_on_read_3(self, env):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/2" }"""

        a_v3 = env.cc_from_json_str(ser_a, A)

        assert a_v3 == A(100L, 4002L)

    def test_failure_to_migrate_on_nonexisting_version(self, env):
        ser_a = """{ "x": 100, "y": 2001 , "_ccvt": "A/4" }"""

        with pytest.raises(CaseClassException):
            a_v4 = env.cc_from_json_str(ser_a, A)

    def test_non_migration(self, env):
        ser_a = """{ "a": 500, "doubled": 5000 , "_ccvt": "A/3" }"""

        a_v3 = env.cc_from_json_str(ser_a, A)

        assert a_v3 == A(500L, 5000L)

    def test_full_serde_with_migration(self, env):
        a_v1 = A__v1(1, 2L)
        s = env.cc_to_json_str(a_v1)

        a = env.cc_from_json_str(s, A)

        assert a == A(a=1L, doubled=4L)

    def test_serde_to_specific_version(self, env):
        a_v1 = A__v1(1, 2L)
        s = env.cc_to_json_str(a_v1)

        a_v2 = env.cc_from_json_str(s, A__v2)

        assert a_v2 == A__v2(1L, 2L)

    def test_unversioned_data_deserialization__fails(self, env):
        ser_a = """{ "a": 500, "doubled": 5000 }"""

        with pytest.raises(MissingVersionDataCaseClassException) as cm:
            a_v3 = env.cc_from_json_str(ser_a, A)
        assert str(cm.value.ccvt) == 'A/3'


class B(CaseClass):
    CC_TYPES = OrderedDict([('my_value', int), ('my_a', A)])
    CC_V = 1
    CC_MIGRATIONS = {}

    def __init__(self, my_value, my_a):
        self.my_value = my_value
        self.my_a = my_a


class C__v1(CaseClass):
    CC_TYPES = OrderedDict([('val1', int), ('my_a', A)])
    CC_V = 1
    CC_MIGRATIONS = {}

    def __init__(self, val1, my_a):
        self.val1 = val1
        self.my_a = my_a


class C(CaseClass):
    CC_TYPES = OrderedDict([('val1', int), ('my_b', B)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: C(old.val1, B(500, old.my_a))
    }

    def __init__(self, val1, my_b):
        self.val1 = val1
        self.my_b = my_b


class T__v1(CaseClass):
    CC_TYPES = OrderedDict([('a', int), ('b', int)])
    CC_V = 1

    def __init__(self, a, b):
        self.a = a
        self.b = b


class T(CaseClass):
    CC_TYPES = OrderedDict([('s1', str), ('s2', str)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: T('a was %d' % old.a, 'b was %d' % old.b)
    }

    def __init__(self, s1, s2):
        self.s1 = s1
        self.s2 = s2


class TTag(CaseClass):
    CC_TYPES = OrderedDict([('a', int), ('b', int)])
    CC_V = 1

    def __init__(self, a, b):
        self.a = a
        self.b = b


class TestCCVTNestedMigrationOnReadTests:
    def test_serde(self, env):
        b = B(300, A(12L, 500L))
        s = env.cc_to_json_str(b)

        deserialized_b = env.cc_from_json_str(s, B)

        assert deserialized_b == b

    def test_serde_with_specific_version(self, env):
        b = B(300, A__v2(5L, 6L))
        s = env.cc_to_json_str(b)
        deserialized_b = env.cc_from_json_str(s, B)

        assert deserialized_b == B(300, A(5L, 12L))

    def test_full_serde_2(self, env):
        c = C(1000, B(230, A(500L, 30L)))

        s = env.cc_to_json_str(c)

        deserialized_c = env.cc_from_json_str(s, C)

        assert deserialized_c == C(1000, B(230, A(500L, 30L)))

    def test_top_layer_migration(self, env):
        c = C__v1(1000, A(500L, 30L))

        s = env.cc_to_json_str(c)
        deserialized_c = env.cc_from_json_str(s, C)

        assert deserialized_c == C(1000, B(500, A(500L, 30L)))

    def test_two_layer_migration(self, env):
        c = C__v1(1000, A__v1(500, 30L))

        s = env.cc_to_json_str(c)
        deserialized_c = env.cc_from_json_str(s, C)

        assert deserialized_c == C(1000, B(500, A(500L, 60L)))

    def test_two_layer_migration__internal_layer_only(self, env):
        c = C__v1(1000, A__v1(500, 30L))

        s = env.cc_to_json_str(c)
        deserialized_c = env.cc_from_json_str(s, C__v1)

        assert deserialized_c == C__v1(1000, A(500L, 60L))

    def test_force_unversioned_serialization(self):
        env = create_default_env()
        env.serialization_ctx = CaseClassSerializationContext(force_unversioned_serialization=True)

        c = C__v1(1000, A__v1(500, 30L))
        d = env.cc_to_dict(c)

        assert sorted(d.keys()) == ['my_a', 'val1']
        assert d['val1'] == 1000
        assert sorted(d['my_a'].keys()) == ['x', 'y']
        assert d['my_a']['x'] == 500
        assert d['my_a']['y'] == 30L

    def test_initial_versioning_logic(self):
        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(fail_on_unversioned_data=False, external_version_provider_func=default_to_version_1_func)
        s = """
        {
          "val1": 98,
          "my_a": {
            "y": 30,
            "x": 80
          }
        }"""

        c = env.cc_from_json_str(s, C)

        assert c == C(val1=98, my_b=B(500, A(80L, 30 * 2L)))

        s2 = env.cc_to_json_str(c)
        d2 = json.loads(s2)

        assert sorted(d2.keys()) == ['_ccvt', 'my_b', 'val1']
        assert d2['_ccvt'] == 'C/2'
        assert d2['my_b']['_ccvt'] == 'B/1'
        assert d2['my_b']['my_a']['_ccvt'] == 'A/3'

    def test_externally_provided_non_existent_version(self):
        def force_version_100(cc_type, d):
            return 100

        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(external_version_provider_func=force_version_100)

        s1 = """{ "a" : 111, "b": 222 }"""

        with pytest.raises(VersionNotFoundCaseClassException) as e1:
            t1 = env.cc_from_json_str(s1, T__v1)
        assert str(e1.value.ccvt) == 'T/100'

    def test_externally_provided_version__with_static_version_class(self):
        def force_version_1(cc_type, d):
            return 1

        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(external_version_provider_func=force_version_1)

        s1 = """{ "a" : 111, "b": 222 }"""

        t1 = env.cc_from_json_str(s1, T__v1)
        assert t1 == T__v1(111, 222)

    def test_externally_provided_ccvt__with_static_version_class(self):
        def force_version_1(cc_type, d):
            return CaseClassVersionedType(cc_type, 1)

        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(external_version_provider_func=force_version_1)

        s1 = """{ "a" : 111, "b": 222 }"""

        t1 = env.cc_from_json_str(s1, T__v1)
        assert t1 == T__v1(111, 222)

    def test_externally_provided_version__with_static_version_class_that_is_the_current_one(self):
        def force_version_2(cc_type, d):
            return 2

        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(external_version_provider_func=force_version_2)

        s1 = """{ "s1" : "blah 1", "s2": "blah 2" }"""

        t1 = env.cc_from_json_str(s1, T)
        assert t1 == T("blah 1", "blah 2")

    def test_externally_provided_version__with_auto_migration(self):
        def force_version_1(cc_type, d):
            return 1

        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(external_version_provider_func=force_version_1)

        s1 = """{ "a" : 111, "b": 222 }"""

        t1 = env.cc_from_json_str(s1, T)
        assert t1 == T('a was 111', 'b was 222')

    def test_externally_provided_version__that_returned_different_class(self, env):
        def force_ttag(cc_type, d):
            return CaseClassVersionedType(TTag, 5)

        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(external_version_provider_func=force_ttag)

        s1 = """{ "a" : 111, "b": 222 }"""

        with pytest.raises(IncompatibleTypesCaseClassException) as e:
            t1 = env.cc_from_json_str(s1, T__v1)
        assert str(e.value.ccvt) == 'TTag/5'
        assert str(e.value.self_vt) == 'T/1'


class MyCaseClassWithList(CaseClass):
    CC_TYPES = OrderedDict([('l', CaseClassListType(A))])
    CC_V = 1

    def __init__(self, l):
        self.l = l


class TestCCVTListTypeTests:
    def test_list__no_migration(self, env):
        c = MyCaseClassWithList([A(100L, 200L), A(200L, 300L), A(400L, 500L)])

        d = env.cc_to_dict(c)
        assert set([x['_ccvt'] for x in d['l']]) == {"A/3"}

    def test_list__deserialization_without_migration(self, env):
        s = """
        { "l": [
            {"a": 100,"doubled": 200,"_ccvt": "A/3"},
            {"a": 200,"doubled": 300,"_ccvt": "A/3"},
            {"a": 400,"doubled": 500,"_ccvt": "A/3"}
          ],
            "_ccvt": "MyCaseClassWithList/1"
        }"""
        c = env.cc_from_json_str(s, MyCaseClassWithList)

        assert c == MyCaseClassWithList([A(100L, 200L), A(200L, 300L), A(400L, 500L)])

    def test_list__deserialization_with_migration(self, env):
        s = """
        { "l": [
            {"x": 1,"y": 10,"_ccvt": "A/2"},
            {"x": 2,"y": 20,"_ccvt": "A/2"},
            {"x": 3,"y": 30,"_ccvt": "A/2"}
          ],
            "_ccvt": "MyCaseClassWithList/1"
        }"""
        c = env.cc_from_json_str(s, MyCaseClassWithList)

        assert c == MyCaseClassWithList([A(1L, 20L), A(2L, 40L), A(3L, 60L)])


class TestCCVTSubTypeTests:
    def test_deserialization_of_subtype(self, env):
        d = {
            "_ccvt": "SuperType/1",
            "super_value": 1000,
            "request_type": "SubType",
            "details": {
                "x": 200, "y": 300,
                "_ccvt": "SubType/2"
            }
        }
        c = env.cc_from_dict(d, SuperType)

        assert c == SuperType(1000, "SubType", SubType(200, 300))

    def test_serialization_of_subtype(self, env):
        c = SuperType(1000, "SubType", SubType(200, 300))

        d = env.cc_to_dict(c)
        assert d['_ccvt'] == 'SuperType/1'
        assert d['super_value'] == 1000
        assert d['request_type'] == SubType.__name__
        assert d['details']['x'] == 200
        assert d['details']['y'] == 300
        assert d['details']['_ccvt'] == 'SubType/2'

    def test_serde_1(self, env):
        c1 = SuperType(1000, "SubType", SubType(200, 300))

        s = env.cc_to_json_str(c1)
        c2 = env.cc_from_json_str(s, SuperType)

        assert c1 == c2

    def test_deserialization_of_unknown_subtype(self, env):
        d = {
            "_ccvt": "SuperType/1",
            "super_value": 1000,
            "request_type": "SubType",
            "details": {
                "x": 200, "y": 300,
                "_ccvt": "SubType/5"
            }
        }
        with pytest.raises(VersionNotFoundCaseClassException) as exception:
            c = env.cc_from_dict(d, SuperType)
        assert str(exception.value.ccvt) == 'SubType/5'

    def test_serialization_of_subtype_with_ignored_versioning(self, env):
        c = SuperType(1000, "SubType", SubType(200, 300))

        d = env.cc_to_dict(c)
        assert d['super_value'] == 1000
        assert d['request_type'] == SubType.__name__
        assert d['details']['x'] == 200
        assert d['details']['y'] == 300

    def test_serde_1_with_ignored_versioning(self, env):
        c1 = SuperType(1000, "SubType", SubType(200, 300))

        s = env.cc_to_json_str(c1)
        c2 = env.cc_from_json_str(s, SuperType)

        assert c1 == c2


class MyTreeNode__v1(CaseClass):
    CC_TYPES = OrderedDict([
        ('value', int),
        ('children', CaseClassListType(CaseClassSelfType()))
    ])
    CC_V = 1

    def __init__(self, value, children):
        self.value = value
        self.children = children


class MyTreeNode(CaseClass):
    CC_TYPES = OrderedDict([
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


class TestCCVTSelfTypeTests:
    def test_self_type_serde__without_migration(self, env):
        children = [MyTreeNode(2, 'name2', []), MyTreeNode(3, 'name3', [MyTreeNode(4, 'name4', [])])]
        t1 = MyTreeNode(1, 'name1', children)

        s = env.cc_to_json_str(t1)
        t2 = env.cc_from_json_str(s, MyTreeNode)

        assert t1 == t2

    def test_self_type_serde__with_migration(self, env):
        s = """
            {"_ccvt":"MyTreeNode/1","value":1,
            "children":[
                {"_ccvt":"MyTreeNode/1","value":2,"children":[]},
                    {"_ccvt":"MyTreeNode/1","value":3,
                        "children":[{"_ccvt":"MyTreeNode/1","value":4,"children":[]}]}]}
        """
        t2 = env.cc_from_json_str(s, MyTreeNode)

        children = [MyTreeNode(2, 'noname', []), MyTreeNode(3, 'noname', [MyTreeNode(4, 'noname', [])])]
        t1 = MyTreeNode(1, 'noname', children)
        assert t1 == t2

    def test_self_type_serde__with_mixed_migration_and_no_migration(self, env):
        s = """
            {"_ccvt":"MyTreeNode/2","value":1,"name":"name1",
            "children":[
                {"_ccvt":"MyTreeNode/1","value":2,"children":[]},
                {"_ccvt":"MyTreeNode/2","value":3,"name":"name3","children":[]}
            ]
            }
        """
        t2 = env.cc_from_json_str(s, MyTreeNode)

        assert t2 == MyTreeNode(1, 'name1', [MyTreeNode(2, 'noname', []), MyTreeNode(3, 'name3', [])])

    def test_self_data_contains_future_version__fails(self, env):
        s = """
            {"_ccvt":"MyTreeNode/1","value":1,
            "children":[
                   {"_ccvt":"MyTreeNode/2","value":3,"name":"name3","children":[]}
                ]
            }
        """
        with pytest.raises(MigrationPathNotFoundCaseClassException):
            t2 = env.cc_from_json_str(s, MyTreeNode)


class TwoWayMigrationData__v1(CaseClass):
    CC_TYPES = OrderedDict([('x1', int), ('x2', int)])
    CC_V = 1
    CC_MIGRATIONS = {
        2: lambda new: TwoWayMigrationData__v1(new.y1, new.y2)
    }

    def __init__(self, x1, x2):
        self.x1 = x1
        self.x2 = x2


class TwoWayMigrationData(CaseClass):
    CC_TYPES = OrderedDict([('y1', int), ('y2', int), ('s', int)])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: TwoWayMigrationData(old.x1, old.x2, old.x1 + old.x2)
    }

    def __init__(self, y1, y2, s):
        self.y1 = y1
        self.y2 = y2
        self.s = s


class TestTwoWayMigrationTests:
    def test_two_way_migration_forward(self, env):
        c1 = TwoWayMigrationData__v1(100, 200)
        s = env.cc_to_json_str(c1)

        c2 = env.cc_from_json_str(s, TwoWayMigrationData)

        assert c2 == TwoWayMigrationData(100, 200, 300)

    def test_two_way_migration_backward(self, env):
        c1 = TwoWayMigrationData(100, 200, 300)
        s = env.cc_to_json_str(c1)

        c2 = env.cc_from_json_str(s, TwoWayMigrationData__v1)

        assert c2 == TwoWayMigrationData__v1(100, 200)


class WithDict__v1(CaseClass):
    CC_TYPES = OrderedDict([
        ('val', int),
        ('d', dict)
    ])
    CC_V = 1

    def __init__(self, val, d):
        self.val = val
        self.d = d


class WithDict(CaseClass):
    CC_TYPES = OrderedDict([
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


class TestMigrationOfCaseClassWithDict:
    def test_serde_of_caseclass_with_dict(self, env):
        c1 = WithDict__v1(100, {"x": 100, "y": 200})
        s = env.cc_to_json_str(c1)

        c2 = env.cc_from_json_str(s, WithDict)

        assert c2.val == c1.val
        assert c2.x == c1.d['x']
        assert c2.d == c1.d
