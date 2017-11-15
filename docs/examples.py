#!/usr/bin/env python

import sys,os
sys.path.insert(0, os.path.join(sys.path[0], '..'))

# BASIC_EXAMPLE_START

from collections import OrderedDict
from uuid import uuid4

from serium.caseclasses import CaseClass, cc_to_json_str, cc_from_json_str
from serium.types import cc_list, cc_uuid


# Let's define the first case class.

# In order to define a case class, just create a basic value-object class definition, 
# accepting all parameters in the constructor. There are three things to note here:
# 1. The class should inherit from CaseClass
# 2. There is a static field called CC_TYPES. This is an ordered dict between field names 
#    and types. This is a placeholder for a full fledged IDL which will exist in the future 
#    (or reuse existing serialization format IDLs).
#    Also, when we provide implementations for statically typed languages, the language's
#    type system will be used
# 3. There's another static field called CC_V which denotes the version of the class. 
#    For now it's just 1 (and essentially could have been omitted).
class Author(CaseClass):
    CC_TYPES = OrderedDict([
        ('author_id', int),
        ('name', unicode)
    ])
    CC_V = 1

    def __init__(self, author_id, name):
        self.author_id = author_id
        self.name = name


# Now let's create another class called Book. Two things to note here:
# 1. The book_id field is of type cc_uuid. This is essentially a UUID field that the system 
#    knows how to serialize and deserialize into strings. More about it later
# 2. The author field is of type Author - The case class we've defined above.
class Book(CaseClass):
    CC_TYPES = OrderedDict([
        ('book_id', cc_uuid),
        ('title', unicode),
        ('author', Author)
    ])
    CC_V = 1

    def __init__(self, book_id, title, author):
        self.book_id = book_id
        self.title = title
        self.author = author


# Let's create an instance of Author
a = Author(500, u'Amos Oz')
# and an instance of book. Notice that it gets a as the author field. We won't show it 
# here, but passing the wrong types when creating an instance would throw an exception
b = Book(uuid4(), u'A tale of Love and Darkness', a)

# Now let's serialize the book to a json string.
serialized_book = cc_to_json_str(b)
print serialized_book
'''
{
  "_ccvt": "Book/1",
  "author": {
    "_ccvt": "Author/1",
    "author_id": 500,
    "name": "Amos Oz"
  },
  "book_id": "1f028cef-0540-4c98-b8f6-c55a3c324c44",
  "title": "A tale of Love and Darkness"
}
'''

# You can notice two things:
# * There's a field called _ccvt in each level, storing the "versioned type" of the instance. 
#   This will allow automatic migration, as we'll see later on. Notice that that library 
#   can provide "pure serialization of case classes" as well, to support writing/sending 
#   to legacy systems. See SeriumEnv in the docs for details.
# * The book_id has been serialized into a string. This is accomplished by the cc_uuid type, 
#   which essentially states that this is a UUID value when in memory, but has a string 
#   representation when serialized.

# Let's deserialize this string back into an object
new_book_instance = cc_from_json_str(serialized_book, Book)
print new_book_instance
'''
Book(book_id=UUID('c9814b3f-fea0-4494-a828-0d66b50336c1'),title=u'A tale of Love and Darkness',
     author=Author(author_id=500,name=u'Amos Oz'))
'''

# The variable new_book_instance now contains a Book instance with the proper info. 
# Notice that book_id is a UUID again, and that author has been deserialized into an object as well.

# One last thing to notice is that the string representation of the case classes is "executable". 
# This means that you can copy-paste the output as code, and recreate the relevant object.

## Immutability

# Case classes are immutable, meaning that once created, you cannot change any of the fields, 
# or recreate new fields. Trying to do so will cause an exception. In order to modify an 
# instance, use the copy() method on the case class, and pass keyword arguments with the 
# new values
modified_book = b.copy(title=u'A new title')
print modified_book
'''
Book(book_id=UUID('f0115f3b-d8e8-4424-97bd-6541323b3427'),title=u'A new title',
     author=Author(author_id=500,name=u'Amos Oz'))
'''


# BASIC_EXAMPLE_END

# DATA_MIGRATION_EXAMPLE_START

# Let's assume that we're storing this (and other similar) jsons somewhere over time.

# Now let's say that at some point, we've decided to support multiple authors per book.
# In order to do that, we need to do the following:

# 1. Rename the Book case class so it becomes Book__v1
class Book__v1(CaseClass):
    CC_TYPES = OrderedDict([
        ('book_id', cc_uuid),
        ('title', unicode),
        ('author', Author)
    ])
    CC_V = 1

    def __init__(self, book_id, title, author):
        self.book_id = book_id
        self.title = title
        self.author = author


# 2. Create a new Book class, with the modified structure. We'll explain the changes below.
class Book(CaseClass):
    CC_TYPES = OrderedDict([
        ('book_id', cc_uuid),
        ('title', unicode),
        ('authors', cc_list(Author))
    ])
    CC_V = 2
    CC_MIGRATIONS = {
        1: lambda old: Book(book_id=old.book_id, title=old.title, authors=[old.author] if old.author is not None else [])
    }

    def __init__(self, book_id, title, authors):
        self.book_id = book_id
        self.title = title
        self.authors = authors


# So, several things to notice in the modified Book definition:
# 1. The CC_V field has changed to 2
# 2. The field is now named "authors" to reflect the fact that it's a list
# 3. The type of the field is now a list of authors (cc_list(t) just means a list of 
#    elements of type t)
# 4. We've added a "migration definition" through the CC_MIGRATIONS dictionary. This 
#    dictionary is a mapping between a source version (1 in this case) and a function 
#    which gets an old instance and returns a new one after conversion. In this case, 
#    we're taking the old author and just put it in the new "author" field as a single 
#    element inside a list.
# 5. We haven't touched the Author class itself

# The rest of the code is totally unaware of the Book__v1 class - The application code 
# continues to use the Book class only, expecting multiple authors per customer.

# So, what happens when we read an old serialized Book? Let's take the serialized book 
# we had before (assume it's been stored somewhere):
some_old_serialized_book = '''
{
  "_ccvt": "Book/1",
  "author": {
    "_ccvt": "Author/1",
    "author_id": 500,
    "name": "Amos Oz"
  },
  "book_id": "1f028cef-0540-4c98-b8f6-c55a3c324c44",
  "title": "A tale of Love and Darkness"
}
'''

# And deserialize this string into a Book. Notice that the cc_from_json_str takes a 
# second argument saying we expect a Book instance:
deserialized_book = cc_from_json_str(some_old_serialized_book, Book)
# This is the newly constructed book instance:
print deserialized_book
'''
Book(book_id=UUID('1f028cef-0540-4c98-b8f6-c55a3c324c44'),title=u'A tale of Love and Darkness',
     authors=[Author(author_id=500,name=u'Amos Oz')])
'''

# Notice that it has an authors field containing the previous 'author' value of the old 
# book instance. This means that it's a version 2 book. When the deserialization happened, 
# the library detected the fact that we're reading an old customer instance, and 
# automatically migrated it to a version 2 customer on-the-fly, before returning the 
# deserialized object. If there existed multiple versions, the library would find the 
# shortest migration path automatically, performing multiple successive migrations as 
# needed in order to provide the app with a proper "current" Customer instance.

# It's important to note that this kind of auto-migration happens behind the scenes on 
# each object level separately. For example, if we created a version-2 Author as well, 
# the auto-migration for it would have been performed on-the-fly as well, providing the
# app with a version-2 book with a version-2 author inside it.

# This demonstrates one of the main concepts behind this library - Being able to 
# explicitly provide the migration logic on a per object basis, while hiding the burden 
# of managing the versioning from most of the application code.

# Another important concept is the fact that the on-the-fly migration allows to decouple 
# the release of a new feature from the database/storage migration phase. Even in cases 
# where a complete data migration would be necessary, it's would still be possible to
# release the feature early, and perform the complete migration in some other time, or 
# incrementally, without hurting the delivery schedules.

# DATA_MIGRATION_EXAMPLE_END

