#!/usr/bin/env python
import json
import uuid
from collections import OrderedDict
import pytest

import sys,os

# This needs to come first, before any serium imports
sys.path.insert(0, os.path.join(sys.path[0], '..'))

from serium.caseclasses import CaseClass, CaseClassDeserializationContext, create_default_env
from serium.types import cc_list, cc_dict, cc_self_type, cc_type_as_string, cc_subtype_key, cc_subtype_value
from serium.cc_exceptions import CaseClassImmutabilityException, CaseClassUnexpectedFieldException, \
    CaseClassDefinitionException, CaseClassUnexpectedFieldTypeException, CaseClassUnknownFieldException, \
    IncompatibleTypesCaseClassException, CaseClassTypeAsStringException, CaseClassCannotBeFoundException, \
    CaseClassCreationException, MissingVersionDataCaseClassException, CaseClassSubTypeCannotBeNullException


class A(CaseClass):
    CC_TYPES = OrderedDict([('a', int), ('b', int), ('c', int)])

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


# New version of class A() with a new field, and with default value. Deserialization from an old A() instance
# will succeed.
class A2(CaseClass):
    CC_TYPES = OrderedDict([('a', int), ('b', int), ('c', int), ('d', str)])

    def __init__(self, a, b, c, d='my_new_field_default_value'):
        self.a = a
        self.b = b
        self.c = c
        self.d = d


# New version of class A() with a new field, but without a default value. Deserialization from an old A() instance
# will fail (See A2 above)
class A3(CaseClass):
    CC_TYPES = OrderedDict([('a', int), ('b', int), ('c', int), ('d', str)])

    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d


class B(CaseClass):
    CC_TYPES = OrderedDict([('a', str), ('b', str)])

    def __init__(self, a, b):
        self.a = a
        self.b = b


class AllNativeTypes(CaseClass):
    CC_TYPES = OrderedDict([('b', bool), ('i', int), ('f', float), ('s', str), ('l', long)])

    def __init__(self, b, i, f, s, l):
        self.b = b
        self.i = i
        self.f = f
        self.s = s
        self.l = l


class S(CaseClass):
    CC_TYPES = OrderedDict([('myint', int), ('a_type', A), ('b_type', B)])

    def __init__(self, myint, a_type, b_type):
        self.myint = myint
        self.a_type = a_type
        self.b_type = b_type


class U(CaseClass):
    CC_TYPES = OrderedDict([('my_unicode_string', unicode)])

    def __init__(self, my_unicode_string):
        self.my_unicode_string = my_unicode_string


class CaseClassWithLists(CaseClass):
    CC_TYPES = OrderedDict([
        ('myint', int),
        ('list_of_ints', cc_list(int)),
        ('list_of_Ss', cc_list(S))
    ])

    def __init__(self, myint, list_of_ints, list_of_Ss):
        self.myint = myint
        self.list_of_ints = list_of_ints
        self.list_of_Ss = list_of_Ss


class CaseClassWithDict(CaseClass):
    CC_TYPES = OrderedDict([
        ('myint', int),
        ('mydict', cc_dict(str, B))
    ])

    def __init__(self, myint, mydict):
        self.myint = myint
        self.mydict = mydict


class CaseClassWithRecursiveReference(CaseClass):
    CC_TYPES = OrderedDict([
        ('myint', int),
        ('mystring', str),
        ('child', cc_self_type)
    ])

    def __init__(self, myint, mystring, child):
        self.myint = myint
        self.mystring = mystring
        self.child = child


class CaseClassWithRecursiveRefInList(CaseClass):
    CC_TYPES = OrderedDict([
        ('value', int),
        ('children', cc_list(cc_self_type))
    ])

    def __init__(self, value, children):
        self.value = value
        self.children = children


class CaseClassWithoutExpectedTypes(CaseClass):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class CaseClassWithUUID(CaseClass):
    CC_TYPES = OrderedDict([
        ('u', cc_type_as_string(uuid.UUID))
    ])

    def __init__(self, u):
        self.u = u


@pytest.fixture
def env(request):
    return create_default_env()


class TestBasicTests:
    def test_args_creation(self):
        a = A(10, 20, 30)
        assert a.a == 10
        assert a.b == 20
        assert a.c == 30

    def test_kwargs_creation(self):
        a = A(a=10, b=20, c=30)
        assert a.a == 10
        assert a.b == 20
        assert a.c == 30

    def test_mixed_args_kwargs_creation(self):
        a = A(10, c=30, b=500)
        assert a.a == 10
        assert a.b == 500
        assert a.c == 30

    def test_values_accessible(self):
        a = A(1, 2, 3)
        assert a.a == 1
        assert a.b == 2
        assert a.c == 3

    def test_cannot_update_value(self):
        a = A(100, 200, 300)
        with pytest.raises(CaseClassImmutabilityException):
            a.a = 500

    def test_cannot_access_undefined_value(self):
        a = A(100, 200, 300)
        with pytest.raises(CaseClassUnexpectedFieldException):
            myvalue = a.unknown_field

    def test_missing_expected_types(self):
        with pytest.raises(CaseClassDefinitionException):
            a = CaseClassWithoutExpectedTypes(100, 200)

    def test_equality(self):
        a = A(1, 2, 3)
        b = A(1, 2, 3)

        assert a == b

    def test_equality_with_null(self):
        a = A(1, 2, None)
        b = A(1, 2, None)
        assert a == b

    def test_inequality(self):
        a = A(1, 2, 3)
        b = A(1, 2, 4)

        assert a != b
        assert not (a == b)

    def test_inequality_with_null(self):
        a = A(1, 2, None)
        b = A(1, 2, 5)
        assert a != b
        assert not (a == b)

    def test_hash(self):
        a = A(10, 11, 31)
        b = A(10, 11, 31)
        c = A(30, 31, 33)

        m = {a: 100, c: 300}
        m.update({b: 200})

        assert sorted(m.keys(), key=lambda v: v.a) == sorted([a, c], key=lambda v: v.a)
        assert m[a] == 200
        assert m[b] == 200
        assert m[c] == 300

    def test_hash_with_null(self):
        a = A(10, None, 31)
        b = A(10, None, 31)
        c = A(30, 31, 33)

        m = {a: 100, c: 300}
        m.update({b: 200})

        assert sorted(m.keys(), key=lambda v: v.a) == sorted([a, c], key=lambda v: v.a)
        assert m[a] == 200
        assert m[b] == 200
        assert m[c] == 300

    def test_exception_on_wrong_native_type(self):
        with pytest.raises(CaseClassUnexpectedFieldTypeException):
            s = S('a', A(1, 2, 3), B('4', '5'))

    def test_exception_on_wrong_cc_type(self):
        with pytest.raises(CaseClassUnexpectedFieldTypeException):
            s = S(42, B('4', '5'), B('4', '5'))

    def test_nested_hash_identical(self):
        s1 = S(42, A(1, 2, 3), B('4', '5'))
        s2 = S(42, A(1, 2, 3), B('4', '5'))

        m = dict({s1: 13})
        m.update({s2: 14})

        assert len(m.keys()) == 1
        assert m[s1] == 14
        assert m[s2] == 14

    def test_nested_hash_nonidentical(self):
        s1 = S(42, A(1, 2, 3), B('4', '5'))
        s2 = S(42, A(1, 2, 3), B('4', '6'))

        m = dict({s1: 13})
        m.update({s2: 14})

        assert len(m.keys()) == 2
        assert m[s1] == 13
        assert m[s2] == 14

    def test_proper_nested_expected_types(self):
        s = S(42, A(1, 2, 3), B('4', '5'))

    def test_nesting_values_accessible(self):
        s = S(42, A(1, 2, 3), B('4', '5'))

        assert s.myint == 42
        assert s.a_type == A(1, 2, 3)
        assert s.a_type.a == 1
        assert s.a_type.b == 2
        assert s.a_type.c == 3
        assert s.b_type == B('4', '5')

    def test_dict_serde(self, env):
        d = env.cc_to_dict(B('4', '5'))
        r = env.cc_from_dict(d, B)
        assert r == B('4', '5')
        assert r.a == '4'
        assert r.b == '5'

    def test_dict_serde_with_null(self, env):
        d = env.cc_to_dict(B('4', None))
        r = env.cc_from_dict(d, B)
        assert r == B('4', None)
        assert r.a == '4'
        assert r.b is None

    def test_dict_serde_all_native_types(self, env):
        d1 = env.cc_to_dict(AllNativeTypes(True, 42, -12.5, 'mystring', 12121212L))
        r1 = env.cc_from_dict(d1, AllNativeTypes)
        assert r1 == AllNativeTypes(True, 42, -12.5, 'mystring', 12121212L)
        assert r1.b == True
        assert r1.i == 42
        assert r1.f == -12.5
        assert r1.s == 'mystring'
        assert r1.l == 12121212L

    def test_dict_serde_all_native_types_as_nulls(self, env):
        d1 = env.cc_to_dict(AllNativeTypes(None, None, None, None, None))
        r1 = env.cc_from_dict(d1, AllNativeTypes)
        assert r1 == AllNativeTypes(None, None, None, None, None)
        assert r1.b is None
        assert r1.i is None
        assert r1.f is None
        assert r1.s is None
        assert r1.l is None

    def test_dict_serde_lists(self, env):

        Ss = [S(i, A(10, 20, 30), B('aa', 'bb')) for i in range(10)]
        cc = CaseClassWithLists(42, [1000, 2000, 3000], Ss)
        d = env.cc_to_dict(cc)
        r1 = env.cc_from_dict(d, CaseClassWithLists)
        assert r1 == cc
        assert r1.myint == 42
        assert type(r1.list_of_ints) == list
        assert len(r1.list_of_ints) == 3
        assert list(set([type(e) for e in r1.list_of_ints])) == [int]
        assert sum(r1.list_of_ints) == 6000
        assert type(r1.list_of_Ss) == list
        assert len(r1.list_of_Ss) == 10
        assert list(set([type(e) for e in r1.list_of_Ss])) == [S]
        for i, s in enumerate(Ss):
            deserialized_s = r1.list_of_Ss[i]
            assert deserialized_s == s
            assert deserialized_s.a_type == s.a_type
            assert deserialized_s.b_type == s.b_type

    def test_dict_with_cc_to_dict(self, env):
        m = {'key1': S(100, A(10, 20, 30), B('aa', 'bb')),
             'key2': 'some value'
             }
        d = env.dict_with_cc_to_dict(m)
        assert d == {
            'key1': {
                '_ccvt': 'S/1',
                'a_type': {
                    '_ccvt': 'A/1',
                    'a': 10, 'b': 20, 'c': 30},
                'b_type': {
                    '_ccvt': 'B/1',
                    'a': 'aa', 'b': 'bb'},
                'myint': 100
            },
            'key2': 'some value'}

    def test_nesting_dict_serde(self, env):
        s1 = S(42, A(1, 2, 3), B('4', '5'))

        d1 = env.cc_to_dict(s1)
        s2 = env.cc_from_dict(d1, S)

        assert s1 == s2
        assert s1.myint == s2.myint
        assert s1.a_type == s2.a_type
        assert s1.b_type == s2.b_type

    def test_nesting_dict_serde_with_nulls(self, env):
        s1 = S(42, A(1, 2, 3), B('4', None))

        d1 = env.cc_to_dict(s1)
        s2 = env.cc_from_dict(d1, S)

        assert s1 == s2
        assert s1.myint == s2.myint
        assert s1.a_type == s2.a_type
        assert s1.b_type == s2.b_type

        assert s2.b_type.b is None

    def test_nesting_json_serde(self, env):
        s1 = S(42, A(1, 2, 3), B('4', '5'))

        j = env.cc_to_json_str(s1)
        s2 = env.cc_from_json_str(j, S)

        assert s1 == s2
        assert s1.myint == s2.myint
        assert s1.a_type == s2.a_type
        assert s1.b_type == s2.b_type

    def test_nesting_json_serde_with_nulls(self, env):
        s1 = S(42, A(1, 2, None), B('4', None))

        j = env.cc_to_json_str(s1)
        s2 = env.cc_from_json_str(j, S)

        assert s1 == s2
        assert s1.myint == s2.myint
        assert s1.a_type == s2.a_type
        assert s1.b_type == s2.b_type

        assert s2.a_type.c is None
        assert s2.b_type.b is None

    def test_json_serde_with_dict_field(self, env):
        c = CaseClassWithDict(42, {"a": B('Z', 'X'), "b": B('Z', 'Y')})
        j = env.cc_to_json_str(c)
        deserialized = env.cc_from_json_str(j, CaseClassWithDict)
        assert deserialized == c
        assert deserialized.myint == 42
        assert sorted(deserialized.mydict.keys()) == ['a', 'b']
        assert deserialized.mydict['a'] == B('Z', 'X')
        assert deserialized.mydict['b'] == B('Z', 'Y')

    def test_json_serde_with_dict_field_containing_null_values(self, env):
        c = CaseClassWithDict(42, {"a": B('Z', 'X'), "b": None})
        j = env.cc_to_json_str(c)
        deserialized = env.cc_from_json_str(j, CaseClassWithDict)
        assert deserialized == c
        assert deserialized.myint == 42
        assert sorted(deserialized.mydict.keys()) == ['a', 'b']
        assert deserialized.mydict['a'] == B('Z', 'X')
        assert deserialized.mydict['b'] is None

    def test_json_serde_with_dict_field_with_cc(self, env):
        c = CaseClassWithDict(42, {"a": B('q', 'w'), "b": B('w', 'e')})
        j = env.cc_to_json_str(c)
        deserialized = env.cc_from_json_str(j, CaseClassWithDict)

        assert deserialized == c
        assert deserialized.myint == 42
        assert sorted(deserialized.mydict.keys()) == ['a', 'b']
        assert deserialized.mydict['a'] == B('q', 'w')
        assert deserialized.mydict['b'] == B('w', 'e')

    def test_deserialization_from_standard_json(self):
        env = create_default_env()
        env.deserialization_ctx=CaseClassDeserializationContext(fail_on_unversioned_data=False)

        json_str = """
            {
                "myint" : 100,
                "a_type": {
                    "a" : 200,
                    "b": 300,
                    "c": 400
                },
                "b_type": {
                    "a": "str1",
                    "b": "str2"
                }
            }
        """
        s = env.cc_from_json_str(json_str, S)
        assert s == S(100, A(200, 300, 400), B('str1', 'str2'))

    def test_deserialization_from_standard_json_as_unicode(self):
        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(fail_on_unversioned_data=False)

        json_str = u"""
            {
                "myint" : 100,
                "a_type": {
                    "a" : 200,
                    "b": 300,
                    "c": 400
                },
                "b_type": {
                    "a": "str1",
                    "b": "str2"
                }
            }
        """
        s = env.cc_from_json_str(json_str, S)
        assert s == S(100, A(200, 300, 400), B('str1', 'str2'))

    def test_deserialization_from_manually_deserialized_json(self):
        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(fail_on_unversioned_data=False)

        json_str = """
            {
                "myint" : 100,
                "a_type": {
                    "a" : 200,
                    "b": 300,
                    "c": 400
                },
                "b_type": {
                    "a": "str1",
                    "b": "str2"
                }
            }
        """
        d = json.loads(json_str)
        s = env.cc_from_dict(d, S)
        assert s == S(100, A(200, 300, 400), B('str1', 'str2'))

    def test_unicode_serde(self, env):
        u = U(u'ASCII\xe0\xe8\xec\xf2\xf9\xa4')

        new_u = env.cc_from_json_str(env.cc_to_json_str(u), U)

        assert new_u == u
        assert type(new_u.my_unicode_string) == unicode
        assert new_u.my_unicode_string == u'ASCII\xe0\xe8\xec\xf2\xf9\xa4'
        assert len(new_u.my_unicode_string) == len(u.my_unicode_string)
        assert len(new_u.my_unicode_string) == 11

    def test_unicode_serialization(self, env):
        u = U(u'ASCII\xe0\xe8\xec\xf2\xf9\xa4')

        d = env.cc_to_dict(u)
        assert type(d['my_unicode_string']) == unicode
        assert d['my_unicode_string'] == u'ASCII\xe0\xe8\xec\xf2\xf9\xa4'

        json_str_in_utf8 = json.dumps(d)
        j = json.loads(json_str_in_utf8, encoding='utf-8')

        assert sorted(j.keys()) == ['_ccvt', 'my_unicode_string']
        assert type(j['my_unicode_string']) == unicode
        assert len(j['my_unicode_string']) == 11

    def test_copy(self):
        a1 = A(1, 2, 3)
        a2 = a1.copy(b=4)

        assert a2 != a1
        assert not a2 == a1
        assert a2.a == 1
        assert a2.b == 4
        assert a2.c == 3

        assert id(a1) != id(a2)

    def test_copy_all_fields(self):
        a1 = A(1, 2, 3)
        a2 = a1.copy(c=300, b=200, a=100)

        assert a2 != a1
        assert not a2 == a1
        assert a2.a == 100
        assert a2.b == 200
        assert a2.c == 300

    def test_copy_set_field_to_null(self):
        a1 = A(1, 2, 3)
        a2 = a1.copy(a=None)

        assert a2 != a1
        assert not a2 == a1
        assert a2.a is None
        assert a2.b == 2
        assert a2.c == 3

    def test_copy_with_unknown_params_raises(self):
        with pytest.raises(CaseClassUnknownFieldException):
            a1 = A(1, 2, 3)
            a2 = a1.copy(d=100)

    def test_copy_replace_cc_field(self):
        s1 = S(100, A(1, 2, 3), B('a', 'b'))

        s2 = s1.copy(a_type=A(4, 5, 6))

        assert s1.myint == s2.myint
        assert s2.a_type == A(4, 5, 6)
        assert s2.b_type == B('a', 'b')

    def test_copy_replace_subfield_in_cc_field(self):
        s1 = S(100, A(1, 2, 3), B('a', 'b'))

        s2 = s1.copy(a_type=s1.a_type.copy(c=300))

        assert s1.myint == s2.myint
        assert s2.a_type == A(1, 2, 300)
        assert s2.b_type == B('a', 'b')

    def test_copy_with_serde(self, env):
        s1 = S(100, A(1, 2, 3), B('a', 'b'))

        s2 = s1.copy(a_type=s1.a_type.copy(c=300))

        new_s1 = env.cc_from_json_str(env.cc_to_json_str(s1), S)
        new_s2 = env.cc_from_json_str(env.cc_to_json_str(s2), S)

        assert new_s1.myint == new_s2.myint
        assert new_s1.a_type == A(1, 2, 3)
        assert new_s2.a_type == A(1, 2, 300)
        assert new_s1.b_type == new_s2.b_type
        assert new_s2.b_type == s2.b_type
        assert new_s2.b_type == B('a', 'b')

    def test_recursive_type(self, env):
        child = CaseClassWithRecursiveReference(20, 'child', None)
        r1 = CaseClassWithRecursiveReference(10, 'parent', child)

        new_r1 = env.cc_from_json_str(env.cc_to_json_str(r1), CaseClassWithRecursiveReference)

        assert new_r1 == r1

    def test_recursive_type_in_list(self, env):
        leaves = [CaseClassWithRecursiveRefInList(-5, None) for _ in range(3)]
        children = [CaseClassWithRecursiveRefInList(i, leaves) for i in range(10)]
        r1 = CaseClassWithRecursiveRefInList(42000, children)

        new_r1 = env.cc_from_json_str(env.cc_to_json_str(r1), CaseClassWithRecursiveRefInList)

        assert new_r1 == r1
        assert new_r1.value == 42000

        assert [child.value for child in new_r1.children] == range(10)
        assert [len(child.children) for child in new_r1.children] == [3] * 10

    def test_deserialization_into_a_different_class(self):
        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(fail_on_incompatible_types=False)

        a1 = A(10, 20, 30)

        serialized_a1 = env.cc_to_json_str(a1)

        deserialized_a1_by_a2 = env.cc_from_json_str(serialized_a1, A2)
        assert deserialized_a1_by_a2 == A2(10, 20, 30, 'my_new_field_default_value')

    def test_ignoring_extra_fields_fails_without_default_values(self, env):
        a1 = A(10, 20, 30)

        serialized_a1 = env.cc_to_json_str(a1)

        with pytest.raises(IncompatibleTypesCaseClassException):
            deserialized_a1_by_a3 = env.cc_from_json_str(serialized_a1, A3)

    def test_cc_type_as_string(self, env):
        u = CaseClassWithUUID(uuid.uuid4())

        new_u = env.cc_from_json_str(env.cc_to_json_str(u), CaseClassWithUUID)

        assert new_u == u

    def test_cc_type_as_string__type_check_fails(self):
        with pytest.raises(CaseClassUnexpectedFieldTypeException):
            u = CaseClassWithUUID('1212121')

    def test_cc_type_as_string__type_check_fails_on_deserialization(self, env):
        j = """{ "u" : 2000 , "_ccvt": "CaseClassWithUUID/1" }"""

        with pytest.raises(CaseClassTypeAsStringException):
            new_u = env.cc_from_json_str(j, CaseClassWithUUID)

    def test_cc_type_as_string__deserialization_succeeds(self):
        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(fail_on_unversioned_data=False)

        j = """{ "u" : "cedcb73b-2ca6-45e4-93e5-5c0b42dad3fd" }"""

        new_u = env.cc_from_json_str(j, CaseClassWithUUID)

        assert new_u == CaseClassWithUUID(uuid.UUID('cedcb73b-2ca6-45e4-93e5-5c0b42dad3fd'))


class CaseClassSubType1(CaseClass):
    CC_TYPES = OrderedDict([
        ('subtype1_field1', int),
        ('subtype1_field2', int)
    ])

    def __init__(self, subtype1_field1, subtype1_field2):
        self.subtype1_field1 = subtype1_field1
        self.subtype1_field2 = subtype1_field2


class CaseClassSubType2(CaseClass):
    CC_TYPES = OrderedDict([
        ('subtype2_field1', int),
        ('subtype2_field2', int)
    ])

    def __init__(self, subtype2_field1, subtype2_field2):
        self.subtype2_field1 = subtype2_field1
        self.subtype2_field2 = subtype2_field2


class CaseClassSuperType(CaseClass):
    CC_TYPES = OrderedDict([
        ('submessage_type', cc_subtype_key('details')),
        ('details', cc_subtype_value('submessage_type'))
    ])

    def __init__(self, submessage_type, details):
        self.submessage_type = submessage_type
        self.details = details


class TestSubTypingTests:
    def test_creation_with_subtype(self, env):
        supertype = CaseClassSuperType('CaseClassSubType1', CaseClassSubType1(100, 200))

        new_supertype = env.cc_from_json_str(env.cc_to_json_str(supertype), CaseClassSuperType)
        assert new_supertype == supertype

    def test_creation_of_wrong_subtype(self):
        with pytest.raises(CaseClassUnexpectedFieldTypeException):
            supertype = CaseClassSuperType('CaseClassSubType1', CaseClassSubType2(1000, 2000))

    def test_creation_of_unknown_subtype(self):
        with pytest.raises(CaseClassCannotBeFoundException):
            supertype = CaseClassSuperType('UnknownSubType', CaseClassSubType1(1000, 2000))

    def test_deserialization_of_known_subtype(self, env):
        env = create_default_env()
        env.deserialization_ctx = CaseClassDeserializationContext(fail_on_unversioned_data=False)

        j = {
            "submessage_type": "CaseClassSubType2",
            "details": {
                "subtype2_field1": 100,
                "subtype2_field2": 200
            }
        }

        st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)
        assert st == CaseClassSuperType("CaseClassSubType2", CaseClassSubType2(100, 200))

    def test_deserialization_of_known_but_wrong_subtype(self, env):
        j = {
            "submessage_type": "CaseClassSubType1",
            "details": {
                "subtype2_field1": 100,
                "subtype2_field2": 200,
                "_ccvt": "CaseClassSubType2/1"
            },
            "_ccvt": "CaseClassSuperType/1"
        }

        with pytest.raises(IncompatibleTypesCaseClassException):
            st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)

    def test_deserialization_of_unknown_subtype(self, env):
        j = {
            "submessage_type": "UnknownSubType",
            "details": {
                "subtype2_field1": 100,
                "subtype2_field2": 200,
                "_ccvt": "CaseClassSubType2/1"
            },
            "_ccvt": "CaseClassSuperType/1"
        }
        with pytest.raises(CaseClassCannotBeFoundException):
            st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)

    def test_deserialization_with_missing_subtype_field(self, env):
        j = {
            "submessage_type": "CaseClassSubType1",
            "_ccvt": "CaseClassSuperType/1"
        }
        with pytest.raises(CaseClassCreationException):
            st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)

    def test_deserialization_with_empty_subtype_field(self, env):
        j = {
            "submessage_type": "CaseClassSubType1",
            "details": {},
            "_ccvt": "CaseClassSuperType/1"
        }
        with pytest.raises(MissingVersionDataCaseClassException):
            st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)

    def test_deserialization_with_null_subtype_field__with_failure_disabled(self):
        env = create_default_env()
        env.deserialization_ctx=CaseClassDeserializationContext(fail_on_null_subtypes=False)

        j = {
            "submessage_type": "CaseClassSubType1",
            "details": None,
            "_ccvt": "CaseClassSuperType/1"
        }
        st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)

    def test_deserialization_with_null_subtype_field__with_failure_enabled(self):
        env = create_default_env()
        env.deserialization_ctx=CaseClassDeserializationContext(fail_on_null_subtypes=True)

        j = {
            "submessage_type": "CaseClassSubType1",
            "details": None,
            "_ccvt": "CaseClassSuperType/1"
        }
        with pytest.raises(CaseClassSubTypeCannotBeNullException):
            st = env.cc_from_json_str(json.dumps(j), CaseClassSuperType)
