
# serium

A serialization library that inherently provides resiliency to data structure evolution over time.

This kind of resiliency is achieved by providing case classes that are inherently serializable in a way that preserves version information, and seamlessly migrating old data structures on-the-fly while performing deserialization.

The approach that this library takes towards data structure evolution is different than many other serialization formats. Instead of defining evolution at the protocol-level (e.g. adding new fields which might be empty, deprecating fields, converting types, etc.), it defines evolution at the domain-level. Developers explicitly define conversion functions between versions, and the infrastructure uses these functions in order to provide the application code with the current version of each object. This approach allows to change the data structures according to real bussiness/development needs, and not be limited to protocol-level changes.

A related concept to this approach is that the codebase itself acts as the "schema repository", holding the structures of all "live versions". This, combined with the conversion functions, allows to manage the evolution of the data using standard code tools and practices.

This initial implementation of the library is in python, which is dynamically typed. This required creating full support for strictly typed case classes, a feature which in other languages might have been provided by the language itself.

## Main Features
* Strictly typed, immutable, nested case classes (including recursive definitions)
* Support for case class version management and powerful schema evolution inside the codebase
* Inherent serialization capabilities (currently json only)
* On-the-fly data migration on read
* Support for subtypes - A method for mimicking inheritance in serialized data. Supertype can contain a "selector field" which denotes the actual type of another field, fully integrating with the version management capabilities of the library.

## Design assumptions
* CPU/Memory is cheaper than developer time and time-to-market of new features
* Decoupling feature release from any maintenance/migration work is a good thing
* Logicl evolution of the data strcutures is required in many real world use cases
* The codebase and the programming language can serve as an accurate "distributed schema repository", taking advantage of standard code management tools

Due to these design assumptions, the library is currently optimized mainly for ease of development and iteration, and for decoupling between the developer's work and devops work. Obviously, once the concepts stabilize enough, speed/space optimizations will get into focus.

## Future plans
* At least one strictly-typed implementation (e.g. Scala)
* Other serialization formats
* Higher-level types (e.g. url, phone-number, etc.)
* Higher-level constraints on the data as part of the type definitions (e.g. valid-url, positive-value, not-empty, in-range, etc.)
* Dynamic search scope of subtypes
* Create IDL or reuse existing IDL such as protobuf
* Typed enums (currently just regular strings)
* Typed timestamps (currently just ints or longs)
* Less verbose syntax

# Library Status
While already being used in one production setting, the library is still considered to be in alpha status. Any feedback regarding the concept and the direction this needs to take will be greatly appreciated.

# Installation
`pip install serium`

# Basic Example

[embedmd]:# (./examples.py python /# BASIC_EXAMPLE_START/ /# BASIC_EXAMPLE_END/)

# Data Migration Example

[embedmd]:# (./examples.py python /# DATA_MIGRATION_EXAMPLE_START/ /# DATA_MIGRATION_EXAMPLE_END/)

# Reference for case class definitions

## Basic structure for defining a case class
```python
class MyClass(CaseClass):
	CC_TYPES = OrderedDict([ <pairs of field-name/field-type> ])
	CC_V = <version>
	CC_MIGRATIONS = {
		<old-version-number>: lambda old: <construct a new MyClass using old>,
		...
	}
	def __init__(self,<field-names>):
		self.field_name1 = field_name1
		...
```

## Supported types
```python
	from serium.types import cc_self_type, cc_list, cc_dict, cc_decimal, cc_uuid
	...
	CC_TYPES = OrderedDict([
		('my_int',int),
		('my_long',long),
		('my_float',float),
		('my_bool',bool),
		('my_str',str),	
		('my_unicode',unicode),	
		('my_uuid',cc_uuid),
		('my_decimal',cc_decimal),
		('my_raw_dict',dict),
		('my_list_of_ints',cc_list(int)),
		('my_typed_dict',cc_dict(str,int)),
		('my_sibling_node',cc_self_type),
		('my_other_case_class',<case-class-name>)
	])
```

## Basic conversion to/from dict
* `cc_to_dict(x)` - Convert case class instance `x` to a dictionary
* `cc_from_dict(d,cc_type)` - Convert dict `d` back into a case class of type `cc_type`

## Basic conversion to/from json string
* `cc_to_json_str(x)` - Conver case class instance `x` to a json string
* `cc_from_json_str(s, cc_type)` - Convert json string `s` back into a case class instance of type `cc_type`

## Simple type checking
* `cc_check(x, cc_type)` - Throws an exception if case class instance x is not of type `cc_type`

## Advanced serialization and deserialization control
The module-level functions in `serium.caseclasses` provide a simple out-of-the-box experience, with several behaviour defaults regarding controlling the serde process. When you need more control over these, you can create a `SeriumEnv` instance and run the same functions defined above, as methods of this instance. Here's an example:
```python
from serium.caseclasses import SeriumEnv

env = SeriumEnv(...)

env.cc_from_dict(...)
env.cc_to_json_str(...) 
```

SeriumEnv gets three parameters:

* `serialization_ctx` - An instance of `CaseClassSerializationContext`. Params:

  * `force_unversioned_serialization` - A boolean flag. When true, the serialized output will be plain - It will not include versioning info. This can be used in order to send data to external systems, for example, which cann't tolerate extra fields. Default to False, meaning that output will include versioning info.
* `deserialization_ctx` - An instance of `CaseClassDeserializationContext`. Params:

  * `fail_on_unversioned_data` - A boolean, defaults to True, which means that if there's no version information in the serialized data, an exception will be thrown. If set to False, the "current version" case class will be used in order to attempt to deserialize the data without errors.
  * `fail_on_incompatible_types` - A boolean, defaults to True. When set to False, the deserializer will attempt to forcefully deserialize a non-matching type into the requested type. This will succeed only if both types happen to share the same field names and types
  * `external_version_provider_func` - A function `f(cc_type, d)` where cc_type is a case class type, and d is a dictionary. The function should return a version number for the relevant params. This allows to effectively inject specific versions during deserialization, whenever they don't exist in the data itself (e.g. data from external system, initial migration to this library, etc.).

