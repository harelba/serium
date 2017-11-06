
# serium

A serialization library that inherently provides resiliency to data structure evolution over time

This kind of resiliency is achieved by providing case classes that are inherently serializable in a way that preserves version information, and seamlessly migrates old data structures on read (e.g. during deserialization).

To clarify the underlying concepts, follow the concrete data migration example below.

While already being used in one production setting, the library is still in alpha status, so please send me any feedback and comments you might have.

# Installation
`pip install serium`

# Basic Example

[embedmd]:# (./examples.py python /BASIC_EXAMPLE_START/ /BASIC_EXAMPLE_END/)

# Data Migration Example

[embedmd]:# (./examples.py python /DATA_MIGRATION_EXAMPLE_START/ /DATA_MIGRATION_EXAMPLE_END/)

