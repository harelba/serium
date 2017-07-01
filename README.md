
# pycase
This is an initial attempt to provide case classes in python, which have the following properties:
1. Strictly typed
2. Nested as needed, including recursive definitions
3. Immutable
4. Support for regular dicts as fields
5. Serializable to/from dict/json
6. Support subtyping (e.g. a "routing" field containing the key to the structure of another field).
7. Fields easily discoverable by the IDE

Not production grade yet. Will be soon I hope. Please provide any feedback you think about.

"API" is still to be modified in terms of naming and such.

lots of stuff to do:
0. Make it production grade
1. IDL for case classes will be taken from a protobuf definition or similar.
2. Make "API" less verbose
3. Generalize serialization to other formats

## Installation
no pip install yet. Will be done soon.

## Usage Example


```
#!/usr/bin/env python

from pycase.caseclasses import CaseClass
from pycase.caseclasses import cc_to_json_str, cc_from_json_str, CaseClassListType, CaseClassDictType
from collections import OrderedDict


class AnotherCaseClass(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a', str),
        ('b', str)
    ])

    def __init__(self, a, b):
        self.a = a
        self.b = b


class SomeCaseClass(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('x', str),
        ('y', int),
        ('z', float),
        ('nested', AnotherCaseClass),
        ('list_of_ints', CaseClassListType(int)),
        ('dict_of_strings_to_case_classes', CaseClassDictType(str, AnotherCaseClass))
    ])

    def __init__(self, x, y, z, nested, list_of_ints, dict_of_strings_to_case_classes):
        self.x = x
        self.y = y
        self.z = z
        self.nested = nested
        self.list_of_ints = list_of_ints
        self.dict_of_strings_to_case_classes = dict_of_strings_to_case_classes


v = SomeCaseClass('string1', 200, 300.0, AnotherCaseClass('a1', 'b1'), [10, 20, 30], {'key1': AnotherCaseClass('a2', 'b2'), 'key2': AnotherCaseClass('a3', 'b3')})

serialized_v = cc_to_json_str(v)

print serialized_v
# {
#   "dict_of_strings_to_case_classes": {
#     "key2": {
#       "a": "a3",
#       "b": "b3"
#     },
#     "key1": {
#       "a": "a2",
#       "b": "b2"
#     }
#   },
#   "nested": {
#     "a": "a1",
#     "b": "b1"
#   },
#   "list_of_ints": [
#     10,
#     20,
#     30
#   ],
#   "y": 200,
#   "x": "string1",
#   "z": 300.0
# }
reconstructed_v = cc_from_json_str(serialized_v, SomeCaseClass)

print reconstructed_v
# SomeCaseClass(x='string1', y=200, z=300.0, nested=AnotherCaseClass(a='a1', b='b1'), list_of_ints=[10, 20, 30],
#               dict_of_strings_to_case_classes={'key2': AnotherCaseClass(a='a3', b='b3'), 'key1': AnotherCaseClass(a='a2', b='b2')})
```




