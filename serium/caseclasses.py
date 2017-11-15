#!/usr/bin/env python
import itertools
import json
import sys
from collections import OrderedDict
import logging

from serium.cc_exceptions import VersionNotFoundCaseClassException, MigrationPathNotFoundCaseClassException, \
    MigrationFunctionCaseClassException, ExternalVersionProviderCaseClassException, \
    MissingVersionDataCaseClassException, IncompatibleTypesCaseClassException, CaseClassInvalidParameterException, \
    CaseClassTypeCheckException, CaseClassSubTypeException, CaseClassTypeAsStringException, \
    CaseClassCannotBeFoundException, CaseClassFieldTypeException, CaseClassUnexpectedFieldException, \
    CaseClassDefinitionException, CaseClassUnexpectedTypeException, CaseClassUnknownFieldException, \
    CaseClassInvalidVersionedTypeException, CaseClassCreationException, CaseClassFieldMismatchException, \
    CaseClassUnexpectedFieldTypeException, CaseClassImmutabilityException, CaseClassSubTypeCannotBeNullException
from serium.types import CaseClassListType, CaseClassDictType, CaseClassSelfType, CaseClassTypeAsString, \
    CaseClassSubTypeKey, CaseClassSubTypeValue

__all__ = ['CaseClass', 'cc_to_dict', 'cc_from_dict', 'cc_to_json_str', 'cc_to_json_str', 'cc_check',
           'create_default_env', 'default_to_version_1_func',
           'SeriumEnv', 'CaseClassSerializationContext', 'CaseClassDeserializationContext',
           'CaseClassJsonSerialization', 'cc_compact_json_serialization', 'cc_pretty_json_serialization']

LOG = logging.getLogger('serium')


class FrozenCaseClassMetaClass(type):
    def __new__(mcs, clsname, bases, d):
        def augmented_setattr(self, name, value):
            if '_unfrozen' in self.__dict__ and self._unfrozen:
                object.__setattr__(self, name, value)
            else:
                if not hasattr(self, name):
                    raise CaseClassImmutabilityException("'" + name + "' not an attribute of " + clsname + " object. and can't update after creation anyway")
                raise CaseClassImmutabilityException(
                    "Caseclass is immutable - cannot update after creation. Use copy() to create a modified instance {}. field name {} field value {}".format(self, name, repr(value)))

        def check_parameter_types(expected_types, args, kwargs):
            if expected_types is None:
                raise CaseClassDefinitionException('CC_TYPES must be defined on case class {}'.format(cls))

            merged_args_as_dict = OrderedDict(zip(expected_types.keys(), args), **kwargs)
            subtype_keys_dict = {field_name: merged_args_as_dict[field_name] for field_name, field_type in expected_types.iteritems() if isinstance(field_type, CaseClassSubTypeKey)}

            for field_name, arg in merged_args_as_dict.iteritems():
                if isinstance(arg, type(None)):
                    return
                if field_name not in expected_types:
                    raise CaseClassUnknownFieldException('Field {} is not part of case class {}'.format(field_name, cls))
                expected_type = expected_types[field_name]
                if isinstance(expected_type, CaseClassListType):
                    expected_type = list
                    # TODO Check element types
                if isinstance(expected_type, CaseClassDictType):
                    expected_type = dict
                    # TODO Check key/value types
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
                        raise CaseClassCannotBeFoundException(
                            'Could not find case class {} in module {} for subtype key {}. Case class subtypes must be in the same module as the supertype.'.format(expected_type_name, m,
                                                                                                                                                                    expected_type.subtype_key_field_name))
                if type(arg) != expected_type:
                    if issubclass(expected_type, CaseClass) and normalize_type_name(type(arg).__name__) == expected_type.__name__:
                        continue
                    raise CaseClassUnexpectedFieldTypeException(
                        "For caseclass {} - Expected type for parameter {} is {}. Got value of type {}. Value is {}".format(cls, field_name, expected_type, type(arg), arg))

        # check_actual_parameters is called only after __init__ is done, to prevent the need for any reflection
        def check_actual_parameters(expected_types, d):
            actual_field_names = set(d.keys())
            expected_field_names = set(expected_types.keys())

            extra = actual_field_names.difference(expected_field_names)
            missing = expected_field_names.difference(actual_field_names)

            if len(extra) > 0 or len(missing):
                raise CaseClassFieldMismatchException('Missing/Extra arguments provided for case class {}. Extra fields are {} Missing fields are {}'.format(cls, extra, missing))

        def override_setattr_after(fn):
            def _wrapper(*args, **kwargs):
                check_parameter_types(cls.CC_TYPES, args[1:], kwargs)
                # Theoretically, we would have wanted to test the actual parameters here, but this would require performing reflection stuff, and this in turn
                # would require optimizations.
                # So check_actual_parameters is called after the fn() call (which is actually the call to __init__ on the case class), and
                # tests the actual parameters. This means that the call to __init__ might fail and this is the reason for catching the exception below.
                try:
                    real_self = args[0]
                    # Set unfrozen before the call to __init__, so setattr will work
                    real_self.__dict__['_unfrozen'] = True
                    fn(*args, **kwargs)
                    # Done with initializing - Remove unfrozen. This is done on purpose so the caseclass will not contain anything except its logical fields
                    del real_self.__dict__['_unfrozen']
                except TypeError as e:
                    raise CaseClassCreationException(
                        'Missing data for creating case class {}. If this is a new version of another case class, then make sure that all new fields have defaults. {}.'.format(cls, e))
                check_actual_parameters(cls.CC_TYPES, args[0].__dict__)

            return _wrapper

        cls = type.__new__(mcs, clsname, bases, d)
        cls.__setattr__ = augmented_setattr
        cls.__init__ = override_setattr_after(cls.__init__)
        return cls

    def __init__(mcs, clsname, bases, d):
        super(FrozenCaseClassMetaClass, mcs).__init__(clsname, bases, d)


def normalize_type_name(type_name):
    if '__v' in type_name:
        return type_name[:type_name.find('__v')]
    else:
        return type_name


class CaseClassVersionedType(object):
    def __init__(self, cc_type, version):
        self.cc_type = cc_type
        self.cc_type_name = normalize_type_name(cc_type.__name__)
        self.version = version

    def __str__(self):
        return "{}/{}".format(self.cc_type_name, self.version)

    def __repr__(self):
        return "CaseClassVersionedType(cc_type={},version={})".format(repr(self.cc_type), repr(self.version))


def str_to_versioned_type(cls, s):
    try:
        t_name, v_name = s.split("/", 1)
        v = int(v_name)
        assert v > 0
    except Exception, e:
        raise CaseClassInvalidVersionedTypeException("Invalid versioned type: '{}'".format(s))

    target_module = sys.modules[cls.__module__]
    try:
        t = getattr(target_module, t_name)
        return CaseClassVersionedType(t, v)
    except AttributeError:
        raise CaseClassCannotBeFoundException('Could not find case class definition for type {} in module {}'.format(s, target_module))


def find_versioned_cc(cls, ccvt):
    if cls.CC_V == ccvt.version:
        return cls

    vt_class_name = '{}__v{}'.format(cls.get_versioned_type().cc_type_name, ccvt.version)
    target_module = sys.modules[cls.__module__]
    try:
        t = getattr(target_module, vt_class_name)
        return t
    except AttributeError:
        try:
            t = getattr(target_module, cls.get_versioned_type().cc_type_name)
            if t.CC_V == ccvt.version:
                return t
            else:
                raise AttributeError('')
        except AttributeError:
            raise VersionNotFoundCaseClassException(ccvt, target_module)


def versioned_type_to_str(vt):
    return vt.__str__()


class CaseClass(object):
    __metaclass__ = FrozenCaseClassMetaClass
    # Needs to be an OrderedDict. Could be replaced with type hinting at some point
    CC_TYPES = None
    # TODO Should backward compatibility be done here or in the code itself
    CC_V = 1
    CC_MIGRATIONS = {}

    def __str__(self):
        params_str = ",".join(["{}={}".format(field_name, repr(self.__dict__[field_name])) for field_name, desc in self.__class__.CC_TYPES.iteritems()])
        return "{}({})".format(self._type_name(), params_str)

    def __repr__(self):
        return self.__str__()

    def _type_name(self):
        return self.__class__.__name__

    def copy(self, **kwargs):
        for k in kwargs:
            if k not in self.__class__.CC_TYPES.keys():
                raise CaseClassUnknownFieldException("Field {} doesn't exist in the case class {}".format(k, self.__class__))
        d = dict(self.__dict__, **kwargs)
        try:
            return self.__class__(**d)
        except TypeError, e:
            raise CaseClassUnknownFieldException("field which doesn't exist in the original class passed to copy() - {}".format(e))

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

    def _to_dict(self, serialization_ctx):
        subtype_keys_dict = {field_name: self.__dict__[field_name] for field_name, field_type in self.__class__.CC_TYPES.iteritems()
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
                    raise CaseClassCannotBeFoundException(
                        'Could not find case class {} in module {} for subtype key {}. Case class subtypes must be in the same module as the supertype.'.format(subtype_class_name, m,
                                                                                                                                                                expected_type.subtype_key_field_name))
            elif issubclass(expected_type, CaseClass):
                if isinstance(v, CaseClass):
                    return v._to_dict(serialization_ctx)
                else:
                    raise CaseClassUnexpectedTypeException("Expected CaseClass of type {} and got instead value of type {}. Value is {}".format(expected_type, type(v), v))
            else:
                if isinstance(v, expected_type):
                    return v
                else:
                    return expected_type(v)

        resulting_dict = {field_name: cc_value(field_value, self.__class__.CC_TYPES[field_name])  # pylint: disable=unsubscriptable-object
                          for field_name, field_value in self.__dict__.iteritems()}

        if not serialization_ctx.force_unversioned_serialization:
            ccvt = self.__class__.get_versioned_type()
            resulting_dict['_ccvt'] = versioned_type_to_str(ccvt)
        return resulting_dict

    @classmethod
    def get_ccv(cls):
        return cls.CC_V

    @classmethod
    def get_versioned_type(cls):
        ccv = cls.get_ccv()
        return CaseClassVersionedType(cls, ccv)

    def __getattr__(self, item):
        if item not in self.__class__.CC_TYPES.keys():
            raise CaseClassUnexpectedFieldException("Field {} not part of case class".format(item))

    @classmethod
    def check_expected_types_metadata(cls):
        if cls.CC_TYPES is None:
            raise CaseClassDefinitionException('Must provide a dict of field names to types at the class level using a CC_TYPES class field')
        expected_types = cls.CC_TYPES
        if not isinstance(expected_types, OrderedDict):
            raise CaseClassDefinitionException('CC_TYPES must be an OrderedDict of field names to types')
            # TODO Check keys are strings and values are types

    @classmethod
    def check_data(cls, d):
        for k in d.keys():
            if k not in cls.CC_TYPES.keys():
                raise CaseClassUnexpectedFieldException("Data contains an unexpected field {}, which does not belong to case class {}".format(k, cls))

    @classmethod
    def find_migration_path(cls, to_version, from_version):
        if to_version == from_version:
            return [to_version]
        else:
            cc_of_to_version = find_versioned_cc(cls, CaseClassVersionedType(cls, to_version))
            possible_migrations = cc_of_to_version.CC_MIGRATIONS.keys()
            for possible_version in possible_migrations:
                mp = cls.find_migration_path(possible_version, from_version)
                if mp is not None:
                    return mp + [to_version]
            return None

    @classmethod
    def migrate(cls, old_instance, ccvt):
        old_version = ccvt.version
        new_version = cls.CC_V
        LOG.debug("Gonna migrate instance {} from version {} to version {}".format(old_instance, old_version, new_version))
        mp = cls.find_migration_path(new_version, old_version)
        if mp is None:
            raise MigrationPathNotFoundCaseClassException(ccvt, cls.get_versioned_type())

        intermediate_instance = old_instance
        for from_version, to_version in itertools.izip(mp, mp[1:]):
            LOG.debug("-- Migrating instance of type {} from version {} to version {}".format(cls.__name__, from_version, to_version))
            vcc = find_versioned_cc(cls, CaseClassVersionedType(cls, to_version)).CC_MIGRATIONS
            migration_func = vcc[from_version]
            try:
                intermediate_instance = migration_func(intermediate_instance)
            except Exception, e:
                raise MigrationFunctionCaseClassException(intermediate_instance, from_version, to_version, e)

        LOG.debug("Migrated instance {} from version {} to version {} - End result is {}".format(old_instance, old_version, new_version, intermediate_instance))
        return intermediate_instance

    @classmethod
    def _get_version_from_external_provider(cls, d, external_version_provider_func):
        if external_version_provider_func is None:
            return None

        try:
            result = external_version_provider_func(cls, d)
        except Exception, e:
            import traceback
            print traceback.format_exc()
            msg = "Exception while calling external version provider function for case class {} dict {}".format(cls, d)
            LOG.exception(msg)
            raise ExternalVersionProviderCaseClassException(msg)

        if result is not None:
            if isinstance(result, int):
                ccvt = CaseClassVersionedType(cls, result)
            elif isinstance(result, CaseClassVersionedType):
                ccvt = result
            else:
                raise ExternalVersionProviderCaseClassException("Result from external version provider must either be a version number or a CaseClassVersionedType instance")
            LOG.debug("External version provider returned version {} for case class {}".format(ccvt, cls))
        else:
            ccvt = None

        return ccvt

    @classmethod
    def deversionize_dict(cls, d, deserialization_ctx, cc_from_dict_func, cc_to_dict_func):
        if not '_ccvt' in d:
            LOG.debug("Cannot find ccvt in data for case class {}".format(cls))
            ccvt = cls._get_version_from_external_provider(d, deserialization_ctx.external_version_provider_func)
            LOG.debug("External version provider returned {} for case class {}".format(ccvt, cls))

            if ccvt is None:
                if deserialization_ctx.fail_on_unversioned_data:
                    raise MissingVersionDataCaseClassException(cls.get_versioned_type())
                else:
                    ccvt = cls.get_versioned_type()
                    LOG.debug('Data does not contain version info. Assuming current version {}. Use fail_on_unversioned_data=True to generate failure in such cases'.format(ccvt))
            else:
                LOG.debug("ccvt for case class {} has been set be external provider to {}".format(cls, ccvt))
        else:
            ccvt = str_to_versioned_type(cls, d['_ccvt'])
            del d['_ccvt']

        self_vt = cls.get_versioned_type()
        if ccvt.cc_type_name != self_vt.cc_type_name:
            if deserialization_ctx.fail_on_incompatible_types:
                raise IncompatibleTypesCaseClassException(ccvt, self_vt)
            else:
                LOG.debug('Incompatible types {} and {}, but fail_on_incompatible_types=False, so continuing anyway'.format(ccvt, self_vt))
                return d
        else:
            LOG.debug('Types {} and {} are compatible'.format(ccvt, self_vt))
            if ccvt.version != cls.get_ccv():
                LOG.debug("version {} vs {} - Gonna do a migration".format(ccvt.version, cls.get_ccv()))
                old_version_cc = find_versioned_cc(cls, ccvt)
                LOG.debug("old version cc {}".format(old_version_cc))

                d['_ccvt'] = versioned_type_to_str(ccvt)
                old_version_instance = cc_from_dict_func(d, old_version_cc)

                LOG.debug("old version instance {}".format(old_version_instance))
                new_version_instance = cls.migrate(old_version_instance, ccvt)
                # Hack - Reconvert the new instance to a dict, and delete the top-level version info (we already know that we have the right version, we just migrated to it)
                new_d = cc_to_dict_func(new_version_instance)
                del new_d['_ccvt']

                return new_d
            else:
                LOG.debug("Instance of class {} - No need for migration".format(ccvt))
                return d

    @classmethod
    def _from_dict(cls, d, deserialization_ctx, cc_from_dict_func, cc_to_dict_func):
        subtype_keys_dict = {field_name: d[field_name] for field_name, field_type in cls.CC_TYPES.iteritems()
                             if isinstance(field_type, CaseClassSubTypeKey)}

        def value_with_cc_support(v, expected_type):
            if v is None:
                if deserialization_ctx.fail_on_null_subtypes:
                    if type(expected_type) is CaseClassSubTypeValue:
                        raise CaseClassSubTypeCannotBeNullException('Subtype value cannot be null')
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
                if isinstance(v, expected_type.real_type):
                    return value_with_cc_support(v, expected_type.real_type)
                else:
                    try:
                        real_v = expected_type.real_type(v)
                    except Exception as ee:
                        raise CaseClassTypeAsStringException('Could not convert the value {} to the expected type {}. Low-level error:{}'.format(v, expected_type, str(ee)))
                    return value_with_cc_support(real_v, expected_type.real_type)
            if type(expected_type) is CaseClassSubTypeKey:
                return value_with_cc_support(v, str)
            if type(expected_type) is CaseClassSubTypeValue:
                subtype_key = subtype_keys_dict[expected_type.subtype_key_field_name]
                target_module = sys.modules[cls.__module__]
                try:
                    expected_subtype = getattr(target_module, subtype_key)
                    if v is None:
                        raise CaseClassSubTypeException('Value of expected type {} cannot be null'.format(expected_subtype))
                    return value_with_cc_support(v, expected_subtype)
                except AttributeError:
                    raise CaseClassCannotBeFoundException('Could not find case class definition for subtype {} in module {}'.format(subtype_key, target_module))
            if issubclass(expected_type, CaseClass):
                return expected_type._from_dict(v, deserialization_ctx, cc_from_dict_func, cc_to_dict_func)
            else:
                if isinstance(v, expected_type):
                    return v
                else:
                    try:
                        return expected_type(v)
                    except Exception as ee:
                        raise CaseClassFieldTypeException('Value is of type {} while expected type is {}. Original Error: {}. Actual Value: {}'.format(type(v), expected_type, str(ee), v))

        cls.check_expected_types_metadata()

        deversionied_d = cls.deversionize_dict(d, deserialization_ctx, cc_from_dict_func, cc_to_dict_func)
        cls.check_data(deversionied_d)
        kwargs = {field_name: value_with_cc_support(deversionied_d[field_name], cls.CC_TYPES[field_name])  # pylint: disable=unsubscriptable-object
                  for field_name, field_type in deversionied_d.iteritems()}
        return cls(**kwargs)


def default_to_version_1_func(cc_type, d):
    return 1


class CaseClassJsonSerialization(object):
    def __init__(self, encoding='utf-8', **json_kwargs):
        self.encoding = encoding
        self.json_kwargs = json_kwargs

    def serialize(self, d, **kwargs):
        if len(kwargs) > 0:
            effective_kwargs = dict(self.json_kwargs, **kwargs)
        else:
            effective_kwargs = self.json_kwargs
        return json.dumps(d, **effective_kwargs)

    def deserialize(self, s):
        return json.loads(s, encoding=self.encoding)


cc_compact_json_serialization = CaseClassJsonSerialization(indent=None, separators=(',', ':'), sort_keys=False)
cc_standard_json_serialization = CaseClassJsonSerialization(indent=None, separators=(',', ': '), sort_keys=False)
cc_pretty_json_serialization = CaseClassJsonSerialization(indent=2, separators=(',', ': '), sort_keys=True)


class CaseClassSerializationContext(object):
    def __init__(self, force_unversioned_serialization=False):
        self.force_unversioned_serialization = force_unversioned_serialization


class CaseClassDeserializationContext(object):
    def __init__(self, fail_on_unversioned_data=True, fail_on_incompatible_types=True, external_version_provider_func=None, fail_on_null_subtypes=False):
        self.fail_on_unversioned_data = fail_on_unversioned_data
        self.fail_on_incompatible_types = fail_on_incompatible_types
        self.external_version_provider_func = external_version_provider_func
        self.fail_on_null_subtypes = fail_on_null_subtypes


class SeriumEnv(object):
    def __init__(self, serialization_ctx, deserialization_ctx, serialization):
        self.serialization_ctx = serialization_ctx
        self.deserialization_ctx = deserialization_ctx
        self.serialization = serialization

    def cc_to_dict(self, cc):
        if isinstance(cc, list):
            return [self.cc_to_dict(e) for e in cc]
        if not isinstance(cc, CaseClass):
            raise CaseClassInvalidParameterException('Must provide a case class ({})'.format(cc))
        return cc._to_dict(self.serialization_ctx)

    # Experimental - One way conversion only
    def dict_with_cc_to_dict(self, d):
        if isinstance(d, dict):
            def to_value(v):
                if isinstance(v, CaseClass):
                    return self.cc_to_dict(v)
                else:
                    return v

            return {k: to_value(v) for k, v in d.iteritems()}
        else:
            raise CaseClassInvalidParameterException('Must provide a dict to dict_with_cc_to_dict')

    def cc_to_json_str(self, cc, **kwargs):
        d = self.cc_to_dict(cc)
        return self.serialization.serialize(d, **kwargs)

    def cc_from_json_str(self, s, cc_type):
        if isinstance(cc_type, CaseClass):
            raise CaseClassInvalidParameterException('Must provide a case class type (actual type is {})'.format(type(cc_type)))
        d = self.serialization.deserialize(s)
        return self.cc_from_dict(d, cc_type)

    def cc_from_dict(self, d, cc_type, raise_on_empty=True):
        if d is None:
            if raise_on_empty:
                raise CaseClassInvalidParameterException('Could not create case class {} - Empty input'.format(cc_type))
            else:
                return None
        if not isinstance(d, dict):
            raise CaseClassInvalidParameterException('Must provide a dict to convert to a case class. Provided object of type {}. value {}'.format(type(d), d))
        return cc_type._from_dict(d, self.deserialization_ctx, self.cc_from_dict, self.cc_to_dict)

    def cc_check(self, o, cc_type):
        if not isinstance(o, cc_type):
            raise CaseClassTypeCheckException('Object is not of type {}. Object: {}'.format(cc_type, repr(o)))


def create_default_env():
    return SeriumEnv(CaseClassSerializationContext(), CaseClassDeserializationContext(), cc_standard_json_serialization)


default_env = create_default_env()


def cc_to_dict(cc):
    return default_env.cc_to_dict(cc)


def dict_with_cc_to_dict(d):
    return default_env.dict_with_cc_to_dict(d)


def cc_to_json_str(cc, **kwargs):
    return default_env.cc_to_json_str(cc, **kwargs)


def cc_from_json_str(s, cc_type):
    return default_env.cc_from_json_str(s, cc_type)


def cc_from_dict(d, cc_type, raise_on_empty=True):
    return default_env.cc_from_dict(d, cc_type, raise_on_empty)


def cc_check(o, cc_type):
    return default_env.cc_check(o, cc_type)
