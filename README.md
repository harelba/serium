
# pycase
This is an initial attempt to provide case classes in python, which have the following properties:
1. Strictly typed
2. Nested as needed, including recursive definitions
3. Immutable
4. Serializable to/from dict/json
5. Versioned - Support automatic migration-on-read when deserializing a different version
6. Support subtyping (e.g. a "routing" field containing the key to the structure of another field).
7. Fields easily discoverable by the IDE
8. Support for regular dicts as fields

Not production grade yet. Will be soon I hope. Please provide any feedback you think about.

"API" is still to be modified in terms of naming and such.

lots of stuff to do:
0. Make it production grade
1. Make "API" less verbose, perhaps make use of python type hinting
2. Generalize serialization to other formats
3. IDL for case classes will be taken from a protobuf definition or similar.

## Installation
no pip install yet. Will be done soon. 

## Dev envrionment
1. Clone
2. Run `dev/prepare-dev-env` (one time only, creates a virtualenv called pycase)
3. Run `source pycase-activate` every time you wanna meddle with the project
4. pycase module will be part of the venv. You can write python code that uses `from pycase... import`


## Basic Tutorial
Make sure you have ipython installed on the virtualenv. To do that, run `pip install ipython` after running `source pycase-activate`.

Run ipython in order to follow the tutorial and copy-paste stuff into its REPL.

If you get any syntax errors inside ipython, it means that for some reason, ipython thinks you have python 3 installed...


```python
#!/usr/bin/env python

# This tutorial is meant to be executable. `print` output has been put inside multi-line strings immediately following the print statement.

import logging
import sys
from collections import OrderedDict
from uuid import uuid4

from pycase.caseclasses import CaseClass, CaseClassException, cc_to_json_str, cc_from_json_str, cc_to_dict, cc_from_dict, CaseClassListType, CaseClassSubTypeKey, CaseClassSubTypeValue, \
    CaseClassSelfType
from pycase.types import cc_uuid

# Define logging level as INFO. Change to DEBUG to see pycase logs
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


# Let's define a case class for a user. The CASE_CLASS_EXPECTED_TYPES is used to define the types and their order.
# In the future we'll perhaps use python type hinting or something.

# The type for a field can be any python type, such as an int or a float, or special "smarter" types as we'll see later.
# The user_id field is using such field definition "cc_uuid". It's effectively a uuid type, which will be serialized as
# strings automatically, as we'll see later on
class User(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('user_id', cc_uuid),
        ('name', unicode),
        ('address', unicode)
    ])

    def __init__(self, user_id, name, address):
        self.user_id = user_id
        self.name = name
        self.address = address


# Let's create an instance of it:
u = User(uuid4(), u'my name', u'my address')
print u
"""
User(user_id=UUID('b2a7a31d-1d68-4516-af0e-ca038a598fb4'),name=u'my name',address=u'my address')
"""

# As you can see, the output of printing the object is actually a constructor-call, allowing to recreate the object in code
# by copy-pasting it.

# If we try to create a User object with the wrong parameter types, an exception will be thrown during creation:
try:
    bad_u = User(uuid4(), 100, u'my address')
except CaseClassException, e:
    print "User creation failed {}".format(e)
"""
User creation failed For caseclass <class '__main__.User'> - Expected type for parameter name is <type 'unicode'>. Got value of type <type 'int'>. Value is 100
"""

# Now let's serialize the user object. We'll use a function called cc_to_json_str to do that.
serialized_u = cc_to_json_str(u)
print serialized_u
"""
{
  "user_id": "b2a7a31d-1d68-4516-af0e-ca038a598fb4",
  "name": "my name",
  "_ccvt": "User/1",
  "address": "my address"
}
"""

# Notice that the uuid has been serialized to a string.
# You can also notice that there's a _ccvt field added to the serialized output. We'll go back to that later.

# Accessing fields is done using standard python field access
print u.user_id
"""UUID('b2a7a31d-1d68-4516-af0e-ca038a598fb4')"""

# The object is immutable - After creation, you can't change the value of any of the fields, or create/access other ones.
try:
    u.address = u'new address'
except CaseClassException, e:
    print "Address change failed {}".format(e)
"""
Address change failed Caseclass is immutable - cannot update after creation. Use copy() to create a modified instance User(user_id=UUID('2f887090-c553-48bf-8805-e4d0fe4479c6'),name=u'my name',address=u'my address'). field name address field value u'new address'
"""

# In order to create a modified object, use the .copy() method. This will create a new instance which will include the modified fields
u2 = u.copy(address=u'new address')
print u2
"""
User(user_id=UUID('1a62a52e-d0b3-4003-8ae0-bd87affd210b'),name=u'my name',address=u'new address')
"""

# Case classes can be compared for equality based on the data they contain:
some_uuid = uuid4()
o1 = User(some_uuid, u'name1', u'address 1')
o2 = User(some_uuid, u'name1', u'address 1')
print o1 == o2
"""
True
"""
o3 = o2.copy(name=u'new name')
print o1 == o3
"""
False
"""

# Now let's deserialize the json back into a user object. This can be done using cc_from_json_str, which gets the json string, and the name of the class to deserialize into
recreated_user = cc_from_json_str(serialized_u, User)
print recreated_user
"""
User(user_id=UUID('1a62a52e-d0b3-4003-8ae0-bd87affd210b'),name=u'my name',address=u'my address')
"""

# pycase also includes the methods cc_to_dict and cc_from_dict, which serialize/deserialize objects into a dictionary. This is extremely useful when passing case class objects
# into libraries which expect dictionaries, or doing the serialization themselves.
user_as_dict = cc_to_dict(u)
"""
{'user_id': '44ec583a-3501-4468-890f-cb4c623fb654', 'name': u'my name', '_ccvt': 'User/1', 'address': u'my address'}
"""
recreated_user_from_dict = cc_from_dict(user_as_dict, User)
"""
User(user_id=UUID('44ec583a-3501-4468-890f-cb4c623fb654'),name=u'my name',address=u'my address')
"""


# Now let's see how we can use the User definition in other case classes.

# This is an example of a click case class. Notice that the user field type is the "User" case class

class Click(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('click_id', cc_uuid),
        ('timestamp', long),
        ('url', unicode),
        ('user', User)
    ])

    def __init__(self, click_id, timestamp, url, user):
        self.click_id = click_id
        self.timestamp = timestamp
        self.url = url
        self.user = user


# We'll now create a click instance, with the user u as its user
c = Click(uuid4(), 10000L, u'https://url1', u)

# Let's serialize it
serialized_c = cc_to_json_str(c)
print serialized_c
"""
{
  "click_id": "d03f8bc9-1088-4ab3-a53d-2c6cde2a34dc",
  "url": "https://url1",
  "user": {
    "user_id": "1a62a52e-d0b3-4003-8ae0-bd87affd210b",
    "name": "my name",
    "_ccvt": "User/1",
    "address": "my address"
  },
  "_ccvt": "Click/1",
  "timestamp": 10000
}
"""

# Notice that the user object has been serialized as a subobject of the serialized click object

# Deserializing the json brings us back to a Click object, which has a User object inside it:

recreated_click = cc_from_json_str(serialized_c, Click)

print recreated_click
"""
Click(click_id=UUID('d03f8bc9-1088-4ab3-a53d-2c6cde2a34dc'),timestamp=10000L,url=u'https://url1',user=User(user_id=UUID('1a62a52e-d0b3-4003-8ae0-bd87affd210b'),name=u'my name',address=u'my address'))
"""

print recreated_click.user
"""
User(user_id=UUID('1a62a52e-d0b3-4003-8ae0-bd87affd210b'),name=u'my name',address=u'my address')
"""


# Now we'll see an example of how standard python types can be used to define a case class field. The WithDict class below
# defines a field called d, and it's type is a regular python dict.
class WithDict(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('val', int),
        ('d', dict)
    ])
    CC_V = 1

    def __init__(self, val, d):
        self.val = val
        self.d = d


# Let's create an instance. We'll use keyword args here for clarity.
w = WithDict(val=100, d={"x": "aa", "y": "bb"})

# Now let's serialize the object
serialized_w = cc_to_json_str(w)
print serialized_w
"""
{
  "_ccvt": "WithDict/1",
  "d": {
    "y": "bb",
    "x": "aa"
  },
  "val": 100
}
"""

# You can see that the dict inside d has naturally become a subobject of the key d in the json output

# Deserializing the object returns us to the original object
recreated_w = cc_from_json_str(serialized_w, WithDict)
print recreated_w
"""
WithDict(val=100,d={u'y': u'bb', u'x': u'aa'})
"""


# Now let's create a case class with a field that contains a list.
class A(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1', int),
        ('a2', CaseClassListType(int))
    ])
    CC_V = 1

    def __init__(self, a1, a2):
        self.a1 = a1
        self.a2 = a2


# The CaseClassListType(t) means that a2 is a list of elements of type t. t can be any type, including other case classes
# Also, you'll notice that we've added a CC_V field with the value of 1. This denotes the version of the class. We'll get back to that later on.

# Let's create an instance of a:
a = A(200, [10, 20, 30])
print a
"""
A(a1=200,a2=[10, 20, 30])
"""


# Serializing and deserializing it works as expected

# Now we'll see how to construct trees of case classes. The special type "CaseClassSelfType" is a self-reference to the same case class, allowing to create trees and graphs
class TreeNode(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('value', float),
        ('children', CaseClassListType(CaseClassSelfType()))
    ])

    def __init__(self, value, children):
        self.value = value
        self.children = children


# children is a list of "self-type". Let's create a tree:
t = TreeNode(100.0, [TreeNode(200.0, []), TreeNode(300.0, [TreeNode(400.0, [])])])
serialized_t = cc_to_json_str(t)
print serialized_t
"""
{
  "_ccvt": "TreeNode/1",
  "children": [
    {
      "_ccvt": "TreeNode/1",
      "children": [],
      "value": 200.0
    },
    {
      "_ccvt": "TreeNode/1",
      "children": [
        {
          "_ccvt": "TreeNode/1",
          "children": [],
          "value": 400.0
        }
      ],
      "value": 300.0
    }
  ],
  "value": 100.0
}
"""

recreated_t = cc_from_json_str(serialized_t, TreeNode)
print recreated_t
"""
TreeNode(value=100.0,children=[TreeNode(value=200.0,children=[]), TreeNode(value=300.0,children=[TreeNode(value=400.0,children=[])])])
"""


# Now let's move on to a concept called "subtyping". pycase has the capability to encapsulate multiple types of "submessages" inside the definition of one "supermessage"

# Let's create the "supermessage" type. We'll call it "Envelope". This class is a "wrapper" around multiple submessages, which will reside under the "msg" field.
# In order to be able to determine which msg is contained inside msg (and hence know its schema), there's another field called "msg_type", which denotes the specific type
# of the submessage. pycase requires you to declare this relationship between msg_type and msg. This is done by the special-types CaseClassSubTypeKey and CaseClassSubTypeValue
# Naming and syntax for this will be improved at some point
class Envelope(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('message_id', cc_uuid),
        ('timestamp', long),
        ('msg_type', CaseClassSubTypeKey('msg')),
        ('msg', CaseClassSubTypeValue('msg_type'))
    ])

    def __init__(self, message_id, timestamp, msg_type, msg):
        self.message_id = message_id
        self.timestamp = timestamp
        self.msg_type = msg_type
        self.msg = msg


# Let's define two submessages, one called ClickMessage and the other ImpressionMessage. Click and impression are concepts from the adtech
# world, but you shouldn't care. It's just to different types of messages
class ClickMessage(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('click_id', cc_uuid),
        ('url', unicode)
    ])

    def __init__(self, click_id, url):
        self.click_id = click_id
        self.url = url


class ImpressionMessage(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('impression_id', cc_uuid),
        ('url', unicode),
        ('whatever', unicode)
    ])

    def __init__(self, impression_id, url, whatever):
        self.impression_id = impression_id
        self.url = url
        self.whatever = whatever


# Let's create an impression message
impression = ImpressionMessage(uuid4(), u'url1', u'whatever1')
# And "wrap" it with an Envelope message.
# Notice that the field "msg_type" is essentially just a string field with the value "ImpressionMessage". We're using ImpressionMessage.__name__ just as a convenience
# so the IDE can detect these locations with "Find Usages".
m = Envelope(uuid4(), 150000L, ImpressionMessage.__name__, impression)

# Now let's serialize it and see the result:
serialized_impression = cc_to_json_str(m)
print serialized_impression
"""
{
  "timestamp": 150000,
  "_ccvt": "Envelope/1",
  "message_id": "8d79106e-cac8-411f-a7f3-92c3153f6905",
  "msg_type": "ImpressionMessage",
  "msg": {
    "impression_id": "d1f86d00-2282-4554-9873-0a8c8c249dbd",
    "url": "url1",
    "_ccvt": "ImpressionMessage/1",
    "whatever": "whatever1"
  }
}
"""

# Now let's deserialize it back to an Envelope with a message:
recreated_impression = cc_from_json_str(serialized_impression, Envelope)
print recreated_impression
"""
Envelope(message_id=UUID('8d79106e-cac8-411f-a7f3-92c3153f6905'),timestamp=150000L,msg_type='ImpressionMessage',msg=ImpressionMessage(impression_id=UUID('d1f86d00-2282-4554-9873-0a8c8c249dbd'),url=u'url1',whatever=u'whatever1'))
"""


# The msg_type field in the envelope can be used in order to determine the actual type inside msg, and perform actions or access field in msg which belong to a specific subtype

# Now, let's take another look at the class A we've defined before:
class A(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1', int),
        ('a2', CaseClassListType(int))
    ])
    CC_V = 1

    def __init__(self, a1, a2):
        self.a1 = a1
        self.a2 = a2


# As we briefly mentioned before, CC_V denotes the version of A, which is currently 1.
# Let's say that after a while, we need to change A so it contains another field called s, which contains the
# sum of the elements in the list a2. This kind of logical change is not supported in most schema evolution schemes, as they
# only support "protocol-level evolution", such as adding a new field with a default value, promoting an int to a float, etc.
#
# In pycase such a change is supposed to be a first-class-citien. Let's see how. We'll describe the changes that the developer
# should be doing in the code as part of this change.

# We take the original A class and change its name to its A__v1. The rest of it remain identical to before:
class A__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1', int),
        ('a2', CaseClassListType(int))
    ])
    CC_V = 1

    def __init__(self, a1, a2):
        self.a1 = a1
        self.a2 = a2


# We now create a new A case class, with the following changes:
# 1. We add the s field definition
# 2. We set the CC_V value to 2 instead of 1, hence saying that it's version 2
# 3. We create a dictionary called CC_MIGRATIONS on the class, which describes the migration from version 1 to version 2. We'll explain this below.
class A(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1', int),
        ('a2', CaseClassListType(int)),
        ('s', int)
    ])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: A(old.a1, old.a2, sum(old.a2))
    }

    def __init__(self, a1, a2, s):
        self.a1 = a1
        self.a2 = a2
        self.s = s


# The CC_MIGRATIONS dictionary is a dictionary of migrations between some version (1 in the case above) and the version of the class (2 in the case above).
# The migration itself takes the form of a function getting an old version instance (old) and returning a newly created instance of the new version. In this case,
# The old version parameters a1 and a2 are just passed along, and the "s" field is filled by summing the ints over the old a2. Any other logic could be applied here, providing
# for any required logical migration of the data.

# Now, let's take a serialized "old" v1 A instance (assuming it was written to some db/file/queue earlier), and deserialize it:
serialized_a_v1 = """
{
  "a1": 200,
  "a2": [
    10,
    20,
    30
  ],
  "_ccvt": "A/1"
}
"""
# Now let's deserialize it to an A instance (which is of version 2).
new_a = cc_from_json_str(serialized_a_v1, A)
print new_a
"""
A(a1=200,a2=[10, 20, 30],s=60)
"""

# We can see that the new_a instance contains the s field with the proper sum. Behind the scenes, pycase would notice that the serialized a was of version 1 (due to the _ccvt='A/1' field),
# and would trigger an auto-conversion during the deserialization phase.

# Let's see how the new_a looks like after it's serialized:
print cc_to_json_str(new_a)
"""
{
  "a1": 200,
  "s": 60,
  "a2": [
    10,
    20,
    30
  ],
  "_ccvt": "A/2"
}
"""


# Notice the _ccvt value is now A/2 and not A/1 anymore. If we decide to write the new_a to our storage, then it will store the new version, and no migration would be
# needed anymore when reading the data again. Otherwise, the migration logic would happen again every time we read the data.

# Another thing to notice is that this means that the actual code which uses the deserialized A instance always uses the newest version, allowing the code to go
# forward without requiring full data migration on the storage layer.

# Full data migration might still be needed in some of the cases, in order to prevent having too many versions in parallel. However the way pycase works allows to decouple
# the delivery of changes from performing the data migration. The data migration can be done after delivery, or only once in a while, and would only require reading all the
# entries and just writing them back. The auto-migration would take care of the rest.

# Let's see another version-bump of A. Let's say we decide to give up the s field, and we want all the values in a1 and a2 to be doubled. This will "require" changing the field names
# so the new meaning will be evident from them.
# The way we do this is as follows:
# 1. We rename the class A of version 2 to A__v2.
# 2. We create a new A class with the new structure, and change its CC_V field to 3 instead of 2
# 3. We add a new migration from version 2 to version 3 in this new A class.
#
# Let's see how the entire class set would appear after the changes:
class A__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1', int),
        ('a2', CaseClassListType(int))
    ])
    CC_V = 1

    def __init__(self, a1, a2):
        self.a1 = a1
        self.a2 = a2


class A__v2(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1', int),
        ('a2', CaseClassListType(int)),
        ('s', int)
    ])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: A__v2(old.a1, old.a2, sum(old.a2))
    }

    def __init__(self, a1, a2, s):
        self.a1 = a1
        self.a2 = a2
        self.s = s


class A(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('a1_doubled', int),
        ('a2_doubled', CaseClassListType(int))
    ])
    CC_V = 3
    CC_MIGRATIONS = {
        2: lambda old: A(old.a1 * 2, [x * 2 for x in old.a2])
    }

    def __init__(self, a1_doubled, a2_doubled):
        self.a1_doubled = a1_doubled
        self.a2_doubled = a2_doubled


# The version 2 A has been renamed to A__v2, and effectively remained the same. The only other change you can see is that the migration lambda in it now returns
# A__v2 instead of A.

# The new A class with CC_V=3 has been created, and it contains a migration lambda from version 2 to version 3. This lambda doubles the values of the fields of the version 2 instance.

# Notice that since the lambda creates a new instance in code, then there's no problem in changing the field names as we did in that case.

# Let's now take an already serialized A of version 1:
serialized_really_old_a = """
{
  "a1": 200,
  "a2": [
    10,
    20,
    30
  ],
  "_ccvt": "A/1"
}
"""

# ... and deserialize it into an A instance (which is essentially in version 3):
new_a = cc_from_json_str(serialized_really_old_a, A)
print new_a
"""
A(a1_doubled=400,a2_doubled=[20, 40, 60])
"""

# Let's see its serialized form:
print cc_to_json_str(new_a)
"""
{
  "a1_doubled": 400,
  "_ccvt": "A/3",
  "a2_doubled": [
    20,
    40,
    60
  ]
}
"""


# Notice that the resulting new_a instance is of version A/3, and that it has been automatically migrated from version 1. The important thing here
# is that there was no need to actually provide the lambda for the migration of A/1 to A/3. pycase has found a path of migration from 1 to 2 and then to 3,
# applying it automatically. If you wanted you could provide a direct migration lambda from version 1 inside A/3's CC_MIGRATIONS, and it would have been used
# without resorting to a double migration. From the end-user's viewpoint, this doesn't matter though - The end result is a valid A/3 instance that can be used
# around the code.

# The auto-migration applies to nested and sub-type case classes as well. Let's consider the previous Envelope/ClickMessage/ImpressionMessage classes.
# Assume that at some point, ImpressionMessage has evolved. Similar to before, we move the old ImpressionMessage to become ImpressionMessage__v1, and we
# create a new ImpressionMessage class with the changes:
class ImpressionMessage__v1(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('impression_id', cc_uuid),
        ('url', unicode),
        ('whatever', unicode)
    ])
    CC_V = 1

    def __init__(self, impression_id, url, whatever):
        self.impression_id = impression_id
        self.url = url
        self.whatever = whatever


class ImpressionMessage(CaseClass):
    CASE_CLASS_EXPECTED_TYPES = OrderedDict([
        ('impression_id', cc_uuid),
        ('url', unicode),
        ('whatever', unicode),
        ('my_int_value', int)
    ])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: ImpressionMessage(old.impression_id, old.url, old.whatever, 42)
    }

    def __init__(self, impression_id, url, whatever, my_int_value):
        self.impression_id = impression_id
        self.url = url
        self.whatever = whatever
        self.my_int_value = my_int_value


# The new ImpressionMessage contains a new field called my_int_value, which is initialized to 42 in the migration lambda.

# Now let's take an already serialized Envelope+ImpressionMessage, where the ImpressionMessage version is 1:
serialized_old_impression = """
{
  "timestamp": 150000,
  "_ccvt": "Envelope/1",
  "message_id": "b9158e31-8709-4038-99eb-a9f953cb6ded",
  "msg_type": "ImpressionMessage",
  "msg": {
    "impression_id": "24c94d16-1cd4-428d-af74-024d5ee42787",
    "url": "url1",
    "_ccvt": "ImpressionMessage/1",
    "whatever": "whatever1"
  }
}
"""

# Notice that the _ccvt of msg is ImpressionMessage/1.

# Now let's deserialize it back into objects:
m = cc_from_json_str(serialized_old_impression, Envelope)
print m
"""
Envelope(message_id=UUID('b9158e31-8709-4038-99eb-a9f953cb6ded'),timestamp=150000L,msg_type='ImpressionMessage',msg=ImpressionMessage(impression_id=UUID('24c94d16-1cd4-428d-af74-024d5ee42787'),url=u'url1',whatever=u'whatever1',my_int_value=42))
"""

# Let's see the json serialization of the new object:
"""
{
  "timestamp": 150000,
  "_ccvt": "Envelope/1",
  "message_id": "b9158e31-8709-4038-99eb-a9f953cb6ded",
  "msg_type": "ImpressionMessage",
  "msg": {
    "impression_id": "24c94d16-1cd4-428d-af74-024d5ee42787",
    "url": "url1",
    "my_int_value": 42,
    "_ccvt": "ImpressionMessage/2",
    "whatever": "whatever1"
  }
}
"""

# As you can see the msg object has been automatically migrated to the current version. This can be seen in the object output above - The msg field contains an ImpressionMessage object,
# which is essentially of version 2.
```


