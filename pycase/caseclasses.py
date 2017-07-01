#!/usr/bin/env python
import json
import sys
from collections import OrderedDict


class CaseClassException(StandardError):
    def __init__(self, msg):
        super(CaseClassException, self).__init__(msg)


class CaseClassListType(object):
    def __init__(self, element_type):
        self.element_type = element_type


class CaseClassDictType(object):
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type


class CaseClassSelfType(object):
    def __init__(self):
        pass


class CaseClassTypeAsString(object):
    def __init__(self, real_type):
        self.real_type = real_type


class CaseClassSubTypeKey(object):
    def __init__(self, subtype_value_field_name):
        self.subtype_value_field_name = subtype_value_field_name


class CaseClassSubTypeValue(object):
    def __init__(self, subtype_key_field_name):
        self.subtype_key_field_name = subtype_key_field_name


class FrozenCaseClassMetaClass(type):
    def __new__(mcs, clsname, bases, d):
        def augmented_setattr(self, name, value):
            if not hasattr(self, name):
                raise CaseClassException("'" + name + "' not an attribute of " + clsname + " object.")
            raise CaseClassException("Caseclass is immutable - cannot update after creation. Use copy() to create a modified instance")

        def check_parameter_types(expected_types, args, kwargs):
            if expected_types is None:
                raise CaseClassException('CASE_CLASS_EXPECTED_TYPES must be defined on case class {}'.format(cls))

            merged_args_as_dict = OrderedDict(zip(expected_types.keys(), args), **kwargs)
            subtype_keys_dict = {field_name: merged_args_as_dict[field_name] for field_name, field_type in expected_types.iteritems() if isinstance(field_type, CaseClassSubTypeKey)}

            for field_name, arg in merged_args_as_dict.iteritems():
                if isinstance(arg, type(None)):
                    return
                if field_name not in expected_types:
                    raise CaseClassException('Field {} is not part of case class {}'.format(field_name, cls))
                expected_type = expected_types[field_name]
                if isinstance(expected_type, CaseClassListType):
                    expected_type = list
                if isinstance(expected_type, CaseClassDictType):
                    expected_type = dict
                if isinstance(expected_type, CaseClassSelfType):
                    expected_type = cls
                if isinstance(expected_type, CaseClassTypeAsString):
                    expected_type = expected_type.real_type
                if isinstance(expected_type, CaseClassSubTypeKey):
                    expected_type = str  # Verify that the key is a string
                if isinstance(expected_type, CaseClassSubTypeValue):
                    expected_type_name = subtype_keys_dict[expected_type.subtype_key_field_name]
                    m = sys.modules[cls.__module__]
                    try:
                        expected_type = getattr(m, expected_type_name)
                    except AttributeError:
                        raise CaseClassException(
                            'Could not find case class {} in module {} for subtype key {}. Case class subtypes must be in the same module as the supertype.'.format(expected_type_name, m,
                                                                                                                                                                    expected_type.subtype_key_field_name))
                if type(arg) != expected_type:
                    raise CaseClassException("Expected type for parameter {} is {}. Got value of type {}".format(field_name, expected_type, type(arg)))

        def check_actual_parameters(expected_types, d):
            actual_field_names = set(d.keys())
            expected_field_names = set(expected_types.keys())

            extra = actual_field_names.difference(expected_field_names)
            missing = expected_field_names.difference(actual_field_names)

            if len(extra) > 0 or len(missing):
                raise CaseClassException('Missing/Extra arguments provided for case class {}. Extra fields are {} Missing fields are {}'.format(cls, extra, missing))

        def override_setattr_after(fn):
            def _wrapper(*args, **kwargs):
                cls.__setattr__ = object.__setattr__
                check_parameter_types(cls.CASE_CLASS_EXPECTED_TYPES, args[1:], kwargs)
                try:
                    fn(*args, **kwargs)
                except TypeError:
                    raise CaseClassException('Missing data for creating case class {}'.format(cls))
                check_actual_parameters(cls.CASE_CLASS_EXPECTED_TYPES, args[0].__dict__)
                cls.__setattr__ = augmented_setattr

            return _wrapper

        cls = type.__new__(mcs, clsname, bases, d)
        cls.__init__ = override_setattr_after(cls.__init__)
        return cls

    def __init__(mcs, clsname, bases, d):
        super(FrozenCaseClassMetaClass, mcs).__init__(clsname, bases, d)


class CaseClass(object):
    __metaclass__ = FrozenCaseClassMetaClass
    # Needs to be an OrderedDict. Could be replaced with type hinting at some point
    CASE_CLASS_EXPECTED_TYPES = None

    def __str__(self):
        params_str = ",".join(["{}={}".format(field_name, repr(self.__dict__[field_name])) for field_name, desc in self.__class__.CASE_CLASS_EXPECTED_TYPES.iteritems()])
        return "{}({})".format(self._type_name(), params_str)

    def __repr__(self):
        return self.__str__()

    def _type_name(self):
        return self.__class__.__name__

    def copy(self, **kwargs):
        for k in kwargs:
            if k not in self.__class__.CASE_CLASS_EXPECTED_TYPES.keys():
                raise CaseClassException("Field {} doesn't exist in the case class {}".format(k, self.__class__))
        d = dict(self.__dict__, **kwargs)
        try:
            return self.__class__(**d)
        except TypeError, e:
            raise CaseClassException("field which doesn't exist in the original class passed to copy() - {}".format(e))

    def __eq__(self, other):
        if other is None:
            return False
        if type(self) is not type(other):
            return False
        for k, v in self.__dict__.iteritems():
            other_v = getattr(other, k)
            if other_v != v:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        to_hash = [[hash(k), hash(self.__dict__[k])] for k in sorted(self.__dict__.keys())]
        return reduce(lambda x, y: x ^ y, [hash(self.__class__)] + [i for j in to_hash for i in j])

    # Missing some stuff for completeness, but not urgent

    def _to_dict(self):
        subtype_keys_dict = {field_name: self.__dict__[field_name] for field_name, field_type in self.__class__.CASE_CLASS_EXPECTED_TYPES.iteritems()
                             if isinstance(field_type, CaseClassSubTypeKey)}

        def cc_value(v, expected_type):
            if v is None:
                return None
            if type(expected_type) is CaseClassListType:
                element_type = expected_type.element_type
                return [cc_value(e, element_type) for e in v]
            if type(expected_type) is CaseClassDictType:
                key_type = expected_type.key_type
                value_type = expected_type.value_type
                return {cc_value(k, key_type): cc_value(v, value_type) for k, v in v.iteritems()}
            if type(expected_type) is CaseClassSelfType:
                return cc_value(v, self.__class__)  # TODO probably wrong
            if type(expected_type) is CaseClassTypeAsString:
                return cc_value(str(v), str)
            if type(expected_type) is CaseClassSubTypeKey:
                return cc_value(v, str)
            if type(expected_type) is CaseClassSubTypeValue:
                subtype_class_name = subtype_keys_dict[expected_type.subtype_key_field_name]

                m = sys.modules[self.__module__]
                try:
                    subtype_class = getattr(m, subtype_class_name)
                    return cc_value(v, subtype_class)
                except AttributeError:
                    raise CaseClassException(
                        'Could not find case class {} in module {} for subtype key {}. Case class subtypes must be in the same module as the supertype.'.format(subtype_class_name, m,
                                                                                                                                                                expected_type.subtype_key_field_name))
            elif issubclass(expected_type, CaseClass):
                if isinstance(v, CaseClass):
                    return v._to_dict()
                else:
                    raise CaseClassException("Expected CaseClass of type {} and got instead value of type {}. Value is {}".format(expected_type, type(v), v))
            else:
                if isinstance(v, expected_type):
                    return v
                else:
                    return expected_type(v)

        return {field_name: cc_value(field_value, self.__class__.CASE_CLASS_EXPECTED_TYPES[field_name])  # pylint: disable=unsubscriptable-object
                for field_name, field_value in self.__dict__.iteritems()}

    def __getattr__(self, item):
        if item not in self.__class__.CASE_CLASS_EXPECTED_TYPES.keys():
            raise CaseClassException("Field {} not part of case class".format(item))

    @classmethod
    def check_expected_types_metadata(cls):
        if cls.CASE_CLASS_EXPECTED_TYPES is None:
            raise CaseClassException('Must provide a dict of field names to types at the class level using a CASE_CLASS_EXPECTED_TYPES class field')
        expected_types = cls.CASE_CLASS_EXPECTED_TYPES
        if not isinstance(expected_types, OrderedDict):
            raise CaseClassException('CASE_CLASS_EXPECTED_TYPES must be an OrderedDict of field names to types')
            # TODO Check keys are strings and values are types

    @classmethod
    def check_data(cls, d):
        for k in d.keys():
            if k not in cls.CASE_CLASS_EXPECTED_TYPES.keys():
                raise CaseClassException("Data contains an unexpected field {}, which does not belong to case class {}".format(k, cls))

    @classmethod
    def _from_dict(cls, d):
        subtype_keys_dict = {field_name: d[field_name] for field_name, field_type in cls.CASE_CLASS_EXPECTED_TYPES.iteritems()
                             if isinstance(field_type, CaseClassSubTypeKey)}

        def value_with_cc_support(v, expected_type):
            if v is None:
                if type(expected_type) is CaseClassSubTypeValue:
                    raise CaseClassException('Subtype value cannot be null')
                return None
            if type(expected_type) is CaseClassListType:
                element_type = expected_type.element_type
                return [value_with_cc_support(e, element_type) for e in v]
            if type(expected_type) is CaseClassDictType:
                key_type = expected_type.key_type
                value_type = expected_type.value_type
                return {value_with_cc_support(k, key_type): value_with_cc_support(v, value_type) for k, v in v.iteritems()}
            if type(expected_type) is CaseClassSelfType:
                return value_with_cc_support(v, cls)
            if type(expected_type) is CaseClassTypeAsString:
                return value_with_cc_support(expected_type.real_type(v), expected_type.real_type)
            if type(expected_type) is CaseClassSubTypeKey:
                return value_with_cc_support(v, str)
            if type(expected_type) is CaseClassSubTypeValue:
                subtype_key = subtype_keys_dict[expected_type.subtype_key_field_name]
                target_module = sys.modules[cls.__module__]
                try:
                    expected_subtype = getattr(target_module, subtype_key)
                    if v is None:
                        raise CaseClassException('Value of expected type {} cannot be null'.format(expected_subtype))
                    return value_with_cc_support(v, expected_subtype)
                except AttributeError:
                    raise CaseClassException('Could not find case class definition for subtype {} in module {}'.format(subtype_key, target_module))
            if issubclass(expected_type, CaseClass):
                return expected_type._from_dict(v)
            else:
                if isinstance(v, expected_type):
                    return v
                else:
                    return expected_type(v)

        cls.check_expected_types_metadata()
        cls.check_data(d)
        kwargs = {field_name: value_with_cc_support(d[field_name], cls.CASE_CLASS_EXPECTED_TYPES[field_name])  # pylint: disable=unsubscriptable-object
                  for field_name, field_type in d.iteritems()}
        # kwargs = {field_name: value_with_cc_support(d[field_name], field_type) for field_name, field_type in cls.CASE_CLASS_EXPECTED_TYPES.iteritems()}
        return cls(**kwargs)


def cc_to_dict(cc):
    if not isinstance(cc, CaseClass):
        raise CaseClassException('Must provide a case class ({})'.format(cc))
    return cc._to_dict()


def cc_to_json_str(cc, **kwargs):
    def serialize_cc_if_needed(v):
        if isinstance(v, CaseClass):
            return cc_to_dict(v)
        else:
            return v

    return json.dumps(cc_to_dict(cc), default=serialize_cc_if_needed, indent=2, **kwargs)


def cc_from_json_str(s, cc_type):
    if isinstance(cc_type, CaseClass):
        raise CaseClassException('Must provide a case class type (actual type is {})'.format(type(cc_type)))
    return cc_from_dict(json.loads(s), cc_type)


def cc_from_dict(d, cc_type):
    return cc_type._from_dict(d)


def cc_check(o, cc_type):
    return isinstance(o, cc_type)
