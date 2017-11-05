
# serium

A serialization library that inherently provides resiliency to data structure evolution over time

This kind of resiliency is achieved by providing case classes that are inherently serializable in a way that preserves version information, and seamlessly migrates old data structures on read (e.g. during deserialization).

To clarifying the underlying concepts, let's take a concrete example:

``` python
#!/usr/bin/env python

from serium.caseclasses import CaseClass, cc_to_json_str, cc_from_json_str

# Let's define an address case-class, very simplistic, just a text field.
class Address(CaseClass):
	CC_TYPES = OrderedDict([
		('address_text',unicode)
	])
	def __init__(self,address_text):
		self.address_text = address_text

# Let's define a customer case-class. Notice that it has an address field, which has the type Address
class Customer(CaseClass):
	CC_TYPES = OrderedDict([
		('customer_id',int),
		('name',unicode),
		('address',Address)
	])
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
'''



```


