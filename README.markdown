
# serium

A serialization library that inherently provides resiliency to data structure evolution over time

This kind of resiliency is achieved by providing case classes that are inherently serializable in a way that preserves version information, and seamlessly migrates old data structures on read (e.g. during deserialization).

To clarify the underlying concepts, follow the concrete data migration example below.

While already being used in one production setting, the library is still in alpha status, so please send me any feedback and comments you might have.

# Installation
`pip install serium`

# Data migration example
``` python
#!/usr/bin/env python

from serium.caseclasses import CaseClass, cc_to_json_str, cc_from_json_str
from serium.types import cc_list
from collections import OrderedDict

# Let's define an address case-class, very simplistic, just a text field.
class Address(CaseClass):
        CC_TYPES = OrderedDict([
                ('address_text',unicode)
        ])
        CC_V = 1

        def __init__(self,address_text):
                self.address_text = address_text

# Let's define a customer case-class. Notice that it has an address field, which has the type Address
class Customer(CaseClass):
        CC_TYPES = OrderedDict([
                ('customer_id',int),
                ('name',unicode),
                ('address',Address)
        ])
        CC_V = 1

        def __init__(self,customer_id,name,address):
                self.customer_id = customer_id
                self.name = name
                self.address = address

# Let's create a Customer instance
c = Customer(1000,u'John Smith',Address(u'1st Smith Road, SF, CA'))

# Now let's serialize it to a json string
serialized_c = cc_to_json_str(c)
print serialized_c
'''
{
  "_ccvt": "Customer/1", 
  "address": {
    "_ccvt": "Address/1", 
    "address_text": "1st Smith Road, SF, CA"
  }, 
  "customer_id": 1000, 
  "name": "John Smith"
}
'''
# Let's assume that we're storing this (and other similar) jsons somewhere over time.

# Now let's say that at some point, we've decided to support multiple addresses per customer.
# In order to do that, we need to do the following:

# 1. Rename the Customer case class so it becomes Customer__v1
class Customer__v1(CaseClass):
        CC_TYPES = OrderedDict([
                ('customer_id',int),
                ('name',unicode),
                ('address',Address)
        ])
        CC_V = 1

        def __init__(self,customer_id,name,address):
                self.customer_id = customer_id
                self.name = name
                self.address = address

# 2. Create a new Customer class, with the modified structure. We'll explain the changes below.
class Customer(CaseClass):
        CC_TYPES = OrderedDict([
                ('customer_id',int),
                ('name',unicode),
                ('addresses',cc_list(Address))
        ])
        CC_V = 2
        CC_MIGRATIONS = {
            1: lambda old: Customer(customer_id=old.customer_id,name=old.name,addresses=[old.address])
        }

        def __init__(self,customer_id,name,addresses):
                self.customer_id = customer_id
                self.name = name
                self.addresses = addresses
# So, several things to notice here:
# 1. The CC_V field has changed to 2
# 2. The field is now named "addresses" to reflect the fact that it's a list
# 3. The type of the field is now a list of addresses (cc_list(t) just means a list of elements of type t)
# 4. We've added a "migration definition" through the CC_MIGRATIONS dictionary. This dictionary is a mapping
#    between a source version (1 in this case) and a function which gets an old instance and returns a new one 
#    after conversion. In this case, we're taking the old address and just put it in the new "addresses" field
#    as a single element inside a list. Obviously, any kind of conversion logic could have worked here.
# 5. We haven't touched the Address class itself

# The rest of the code is totally unaware of the Customer__v1 class - The application code continues to 
# use the Customer class only, expecting multiple addresses per customer.

# So, what happens when we read an old serialized Customer? Let's take the serialized c we had before:
old_serialized_c = '''
{
  "_ccvt": "Customer/1",
  "address": {
    "_ccvt": "Address/1",
    "address_text": "1st Smith Road, SF, CA"
  },
  "customer_id": 1000,
  "name": "John Smith"
}
'''
# And deserialize this string into a Customer. Notice that the cc_from_json_str takes a second argument saying we
# expect a Customer instance:
new_c = cc_from_json_str(serialized_c,Customer)
# This is the newly constructed customer instsance:
print new_c
'''
Customer(customer_id=1000,name=u'John Smith',addresses=[Address(address_text=u'1st Smith Road, SF, CA')])
'''
# Notice that it has an addresses field containing the previous 'address' value of the old customer instance.
# This means that it's a version 2 customer. When the deserialization happened, the library detected the 
# fact that we're reading an old customer instance, and automatically migrated it to a version 2 customer on-the-fly,
# before returning the deserialized object. If there existed multiple versions, the library would find the shortest
# migration path automatically, performing multiple successive migrations as needed in order to provide the app with
# a proper "current" Customer instance.

# It's important to note that this kind of auto-migration happens behind the scenes on each object level separately. For example, if we created a version-2 Address as well, the auto-migration for it would have been performed on-the-fly
# as well.

# This demonstrates one of the main concepts behind this library - Being able to explicitly provide the migration logic on a per object basis, while hiding the burden of managing the versioning from most of the application code.

# Another important concept is the fact that the on-the-fly migration allows to decouple the release of a new feature from the database/storage migration phase. Even in cases where a complete data migration would be necessary, it's would still be possible to release the feature early, and perform the complete migration in some other time, or incrementally, without hurting the delivery schedules.
```
