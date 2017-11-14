#!/usr/bin/env python


class CaseClassException(StandardError):
    def __init__(self, msg):
        super(CaseClassException, self).__init__(msg)


class VersionNotFoundCaseClassException(CaseClassException):
    def __init__(self, ccvt, module):
        self.ccvt = ccvt
        self.module = module
        super(VersionNotFoundCaseClassException, self).__init__(
            'Could not find case class definition for type {} in module {}'.format(ccvt, module))


class MissingVersionDataCaseClassException(CaseClassException):
    def __init__(self, ccvt):
        self.ccvt = ccvt
        super(MissingVersionDataCaseClassException, self).__init__(
            'Could not find version info in data when deserialization type {} '.format(ccvt))


class IncompatibleTypesCaseClassException(CaseClassException):
    def __init__(self, ccvt, self_vt):
        self.ccvt = ccvt
        self.self_vt = self_vt
        super(IncompatibleTypesCaseClassException, self).__init__(
            'Trying to deserialize incompatible types: {} vs {}'.format(ccvt, self_vt))


class MigrationFunctionCaseClassException(CaseClassException):
    def __init__(self, intermediate_instance, from_version, to_version, e):
        self.intermediate_instance = intermediate_instance
        self.from_version = from_version
        self.to_version = to_version
        self.e = e
        super(MigrationFunctionCaseClassException, self).__init__(
            'Exception while applying migration function on instance {} from version {} to version {}. Original exception is {}'.format(
                intermediate_instance, from_version, to_version, e))


class MigrationPathNotFoundCaseClassException(CaseClassException):
    def __init__(self, ccvt, self_vt):
        self.ccvt = ccvt
        self.self_vt = self_vt
        super(MigrationPathNotFoundCaseClassException, self).__init__(
            'Could not convert case class {} to {} during read'.format(ccvt, self_vt))


class ExternalVersionProviderCaseClassException(CaseClassException):
    def __init__(self, msg):
        super(ExternalVersionProviderCaseClassException, self).__init__(msg)


class CaseClassInvalidParameterException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassInvalidParameterException, self).__init__(msg)


class CaseClassTypeCheckException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassTypeCheckException, self).__init__(msg)


class CaseClassSubTypeException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassSubTypeException, self).__init__(msg)


class CaseClassSubTypeCannotBeNullException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassSubTypeCannotBeNullException, self).__init__(msg)


class CaseClassTypeAsStringException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassTypeAsStringException, self).__init__(msg)


class CaseClassCannotBeFoundException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassCannotBeFoundException, self).__init__(msg)


class CaseClassFieldTypeException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassFieldTypeException, self).__init__(msg)


class CaseClassUnexpectedFieldException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassUnexpectedFieldException, self).__init__(msg)


class CaseClassDefinitionException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassDefinitionException, self).__init__(msg)


class CaseClassUnexpectedTypeException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassUnexpectedTypeException, self).__init__(msg)


class CaseClassUnknownFieldException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassUnknownFieldException, self).__init__(msg)


class CaseClassInvalidVersionedTypeException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassInvalidVersionedTypeException, self).__init__(msg)


class CaseClassCreationException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassCreationException, self).__init__(msg)


class CaseClassFieldMismatchException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassFieldMismatchException, self).__init__(msg)


class CaseClassUnexpectedFieldTypeException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassUnexpectedFieldTypeException, self).__init__(msg)


class CaseClassImmutabilityException(CaseClassException):
    def __init__(self, msg):
        super(CaseClassImmutabilityException, self).__init__(msg)
