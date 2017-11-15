serium
======

A serialization library that inherently provides resiliency to data
structure evolution over time.

This kind of resiliency is achieved by providing case classes that are
inherently serializable in a way that preserves version information, and
seamlessly migrating old data structures on-the-fly while performing
deserialization.

The approach that this library takes towards data structure evolution is
different than many other serialization formats. Instead of defining
evolution at the protocol-level (e.g. adding new fields which might be
empty, deprecating fields, converting types, etc.), it defines evolution
at the domain-level. Developers explicitly define conversion functions
between versions, and the infrastructure uses these functions in order
to provide the application code with the current version of each object.
This approach allows to change the data structures according to real
bussiness/development needs, and not be limited to protocol-level
changes.

A related concept to this approach is that the codebase itself acts as
the “schema repository”, holding the structures of all “live versions”.
This, combined with the conversion functions, allows to manage the
evolution of the data using standard code tools and practices.

This initial implementation of the library is in python, which is
dynamically typed. This required creating full support for strictly
typed case classes, a feature which in other languages might have been
provided by the language itself.

Main Features
-------------

-  Strictly typed, immutable, nested case classes (including recursive
   definitions)
-  Support for case class version management and powerful schema
   evolution inside the codebase
-  Inherent serialization capabilities (currently json only)
-  On-the-fly data migration on read
-  Support for subtypes - A method for mimicking inheritance in
   serialized data. Supertype can contain a “selector field” which
   denotes the actual type of another field, fully integrating with the
   version management capabilities of the library.

Design assumptions
------------------

-  CPU/Memory is cheaper than developer time and time-to-market of new
   features
-  Decoupling feature release from any maintenance/migration work is a
   good thing
-  Logical evolution of the data strcutures is required in many real
   world use cases
-  The codebase and the programming language can serve as an accurate
   “distributed schema repository”, taking advantage of standard code
   management tools
-  In many cases, the migration logic is relatively simple, and the cost
   of applying it during read (cpu+latency) is worth it if it means less
   roadblocks to production

Due to these design assumptions, the library is currently optimized
mainly for ease of development and iteration, and for decoupling between
the developer’s work and devops work. Obviously, once the concepts
stabilize enough, speed/space optimizations will get into focus.

Future plans
------------

-  At least one strictly-typed implementation (e.g. Scala)
-  Other serialization formats
-  Higher-level types (e.g. url, phone-number, etc.)
-  Higher-level constraints on the data as part of the type definitions
   (e.g. valid-url, positive-value, not-empty, in-range, etc.)
-  Dynamic search scope of subtypes
-  Create IDL or reuse existing IDL such as protobuf
-  Typed enums (currently just regular strings)
-  Typed timestamps (currently just ints or longs)
-  Less verbose syntax

Library Status
==============

While already being used in one production setting, the library is still
considered to be in alpha status. Any feedback regarding the concept and
the direction this needs to take will be greatly appreciated.

Installation
============

``pip install serium``

Examples
========

Basic Example
-------------

.. code:: python

    # BASIC_EXAMPLE_START

    from collections import OrderedDict
    from uuid import uuid4

    from serium.caseclasses import CaseClass, cc_to_json_str, cc_from_json_str
    from serium.caseclasses import SeriumEnv, CaseClassSerializationContext, CaseClassDeserializationContext, CaseClassJsonSerialization
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
    {"title": "A tale of Love and Darkness", "_ccvt": "Book/1", "book_id": "e3cb81c0-6555-45e6-8615-85fae4729bf1", "author": {"author_id": 500, "name": "Amos Oz", "_ccvt": "Author/1"}}
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

Data Migration Example
----------------------

.. code:: python

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

Finer control over serialization using SeriumEnv
------------------------------------------------

.. code:: python

    # USING_SERIUM_ENV_EXAMPLE_START

    # Let's see how we can modify the behaviour of serium by using a SeriumEnv. In this 
    # example, we'll just make the json serialization more pretty:
    from serium.caseclasses import cc_pretty_json_serialization, cc_compact_json_serialization
    env = SeriumEnv(CaseClassSerializationContext(), CaseClassDeserializationContext(), cc_pretty_json_serialization)

    # (cc_pretty_json_serialization is just a shortcut for specifying a CaseClassJsonSerialization() 
    #  instance with some standard json-module parameters. You can just create your own instance
    #  any parameters you'd like). 
    # There's also a cc_compact_json_serialization which provides a standard compact json
    # presentation.

    # Now let's use the env we created in order to serialize the original book instance b:
    print env.cc_to_json_str(b)
    '''
    {
      "_ccvt": "Book/1",
      "author": {
        "_ccvt": "Author/1",
        "author_id": 500,
        "name": "Amos Oz"
      },
      "book_id": "c56675d3-10e0-42e9-af9a-b8462c4e1104",
      "title": "A tale of Love and Darkness"
    }
    '''

    # CaseClassSerializationContext and CaseClassDeserializationContext contain additional
    # parameters that can control the ser/de process, mostly related to supporting writing
    # to and reading from other systems which do not support versioning. See the docs
    # for details on each of the params.

    # USING_SERIUM_ENV_EXAMPLE_END

Reference for case class definitions
====================================

Basic structure for defining a case class
-----------------------------------------

.. code:: python

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

Supported types
---------------

.. code:: python

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
            ('my_type_as_string',cc_type_as_string(t)),  # Assumes t is a type which can serialize itself to string using str() and deserialize itself from string using a one-parameter constructor. For example, cc_uuid is actualy cc_type_as_string(UUID).
            ('my_other_case_class',<case-class-name>)
        ])

Basic conversion to/from dict
-----------------------------

-  ``cc_to_dict(x)`` - Convert case class instance ``x`` to a dictionary
-  ``cc_from_dict(d,cc_type)`` - Convert dict ``d`` back into a case
   class of type ``cc_type``

Basic conversion to/from json string
------------------------------------

-  ``cc_to_json_str(x)`` - Conver case class instance ``x`` to a json
   string
-  ``cc_from_json_str(s, cc_type)`` - Convert json string ``s`` back
   into a case class instance of type ``cc_type``

Simple type checking
--------------------

-  ``cc_check(x, cc_type)`` - Throws an exception if case class instance
   x is not of type ``cc_type``

Advanced serialization and deserialization control
--------------------------------------------------

The module-level functions in ``serium.caseclasses`` provide a simple
out-of-the-box experience, with several behaviour defaults regarding
controlling the serde process. When you need more control over these,
you can create a ``SeriumEnv`` instance and run the same functions
defined above, as methods of this instance. Here’s an example:

.. code:: python

    from serium.caseclasses import SeriumEnv

    env = SeriumEnv(...)

    env.cc_from_dict(...)
    env.cc_to_json_str(...) 

SeriumEnv gets three parameters:

-  ``serialization_ctx`` - An instance of
   ``CaseClassSerializationContext``. Params:

   -  ``force_unversioned_serialization`` - A boolean flag. When true,
      the serialized output will be plain - It will not include
      versioning info. This can be used in order to send data to
      external systems, for example, which cann’t tolerate extra fields.
      Default to False, meaning that output will include versioning
      info.

-  ``deserialization_ctx`` - An instance of
   ``CaseClassDeserializationContext``. Params:

   -  ``fail_on_unversioned_data`` - A boolean, defaults to True, which
      means that if there’s no version information in the serialized
      data, an exception will be thrown. If set to False, the “current
      version” case class will be used in order to attempt to
      deserialize the data without errors.
   -  ``fail_on_incompatible_types`` - A boolean, defaults to True. When
      set to False, the deserializer will attempt to forcefully
      deserialize a non-matching type into the requested type. This will
      succeed only if both types happen to share the same field names
      and types
   -  ``external_version_provider_func`` - A function ``f(cc_type, d)``
      where cc_type is a case class type, and d is a dictionary. The
      function should return a version number for the relevant params.
      This allows to effectively inject specific versions during
      deserialization, whenever they don’t exist in the data itself
      (e.g. data from external system, initial migration to this
      library, etc.).
   -  ``fail_on_null_subtypes`` - A boolean denoting whether or not to
      fail on deserialization if a subtype value field is null. Defaults
      to False, meaning that null values for subtype object is allowed.

Building
========

Run ``make init`` after initial checkout.

Run ``make create-doc`` to compile docs/README.md into README.rst (Don’t
forget to checkin the rst file afterwards). The rst file content becomes
the pypi long description for the package.

Run ``make test`` to run tests.

Run ``make prepare-dist`` to Prepare the distribution packages. Make
sure to change the versions in setup.py before doing it.

Run ``make upload-to-testpypy`` to upload to the *test* pypi repository.
