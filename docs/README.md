
# serium

A serialization library that inherently provides resiliency to data structure evolution over time

This kind of resiliency is achieved by providing case classes that are inherently serializable in a way that preserves version information, and seamlessly migrates old data structures on read (e.g. during deserialization).

This initial implementation of the library is in python, which is dynamically typed. This required creating full support for strictly typed case classes, a feature which in other languages might have been provided by the language itself.

## Main Features
* Strictly typed, immutable, nested case classes (including recursive definitions)
* Support for case class version management and schema evolution inside the codebase
* Inherent serialization capabilities (currently json only)
* On-the-fly data migration on read

The library is currently optimized mainly for ease of development and iteration, and for decoupling between the developer's work and devops work. The main design guideline is that in many cases, the cost of more CPU/RAM is small relative to the cost of slow development processes. 

## Future plans
* At least one strictly-typed implementation (e.g. Scala)
* Other serialization formats
* Higher-level constraints on the data as part of the type definitions (e.g. valid-url, positive-value, not-empty, etc.)
* Create IDL or reuse existing IDL such as protobuf

# Library Status
While already being used in one production setting, the library is still considered to be in alpha status. Any feedback regarding the concept and the direction this needs to take will be greatly appreciated.

# Installation
`pip install serium`

# Basic Example

[embedmd]:# (./examples.py python /# BASIC_EXAMPLE_START/ /# BASIC_EXAMPLE_END/)

# Data Migration Example

[embedmd]:# (./examples.py python /# DATA_MIGRATION_EXAMPLE_START/ /# DATA_MIGRATION_EXAMPLE_END/)

# Reference for case class definitions

* Case class definition:
```python
class MyClass(CaseClass):
	CC_TYPES = OrderedDict([ <pairs of field-name/field-type> ])
	CC_V = <version>
	CC_MIGRATIONS = {
		<old-version-number>: lambda old: <construct a new MyClass using old>,
		...
	}
```

* 
	
