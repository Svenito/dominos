Usage
-----

The main purpose of this API is a learning experience for myself. The reason
it has docs, unit tests and all other stuff, is because I wanted to have a
go at setting something up that didn't really exist.

The main issue with the API is that certain steps need to be followed in a
certain order for it to work. It uses an undocumented REST API, so I had to
jump through a few hoops to get it work in the first place.

The CLI example project will provide a good demo of the API usage to complement
this doc.

General
~~~~~~~

The API will return objects that represent the JSON objects returned from
the Domino's site. The structure and members of these objects are documented in
the ``object definitions`` section.

Placing orders
~~~~~~~~~~~~~~~~~~~~

Getting the store
=================

As mentioned before, there's a certain order that things need to happen in. So
after creating a new instance of Dominos

    >>> d = Dominos()

you need to locate your nearest store. This is achieved by passing the
delivery postcode (the postcode where you want items to be delivered) to
``search_nearest_store``. This will return either one or none ``Store`` objects.
The returned object will be the closest store that delivers to that postcode.
Alternatively you can call ``search_stores`` with a more vague term (like the
town or area name) and retrieve a list of stores. However a specific store
must be selected from this list.

Setting up session data
=======================

Session data needs to be set up for the next steps. This involves getting some
cookies and a ``Basket``. For this we need to call ``get_cookie`` followed
by ``get_store_context`` and then ``get_basket``. The latter two calls may
error at times due to some rate limiting, but trying again usually resolves the
issue. The ``get_cookie`` call needs the store and the postcode to deliver to.

    >>> d.get_cookie(stores[0], 'BG9 7TH')
    True

Once the cookie has been set, the context for the store needs to be retrieved
using

    >>> d.get_store_context()
    True

Getting the menu
================

Having initialised the session we can now retrieve the menu. Having selected
a store, we need to pass that to the ``get_menu`` function in order
to get the ``Menu`` object

    >>> menu = d.get_menu(stores[0])

Iterating the menu
==================

The menu is a bit awkward to iterate over, for example if you wanted to
print it out. It contains a dictionary of items with the category as keys.
Currently there seem to be only two categories, ``Side`` and ``Pizza``.
I use something like this to get a list of entries:

.. code-block:: python

    for cat, items in menu.items.iteritems():
        print '---------------------------------'
        print cat
        for item in items:
            self.items[item.idx] = item
            print(u'[%s] %s - %s ' %
                  (item.idx, item.Name, item.DisplayPrice)),
            if item.IsVegetarian:
                print(u'\u24cb '),
            if item.IsHot:
                print(u'\u2668'),

            print

Which also prints vegetarian and spiciness icons.

Getting available item sizes
============================

Dominos uses a ``ProductSkus`` list to define item sizes. For example:

.. code-block:: python

    print 'Sizes available:'
    for i, sku in enumerate(item.ProductSkus):
        print (u'\t[%d] %s - %s' %
               (i, sku.Name, sku.DisplayPrice))

This will list all available size options for the given product.

Adding an item to the basket
============================

Once you have the menu, you can index into the item list and use
that item instance to add it to the basket, along with a ``size_idx``.
The ``size_idx`` is the index into the ``ProductSkus`` list. If all
went well a new basket object is returned.

Removing an item from the basket
================================

Items need to be removed from the basket via their ``basket_index``.
This is the index into the list of items in the basket, which is returned
from ``get_basket``.

Getting the delivery address
============================

Internally Dominos uses an id to identify specific addresses which are
resolved from the postcode. In order to get the ID for an address you call
``get_addresses``. This will return a dictionary of all addresses for the
provided postcode. The address is used as the key and the address line as
the values.

    The basket must contain some items for this call to succeed.

Setting the delivery address
============================

To finalise delivery details, a complete address must be set.
For convenience an ``Address`` class is provided, which wraps all the
required fields:

.. code-block:: python

    self.first_name = ''
    self.last_name = ''
    self.contact_number = ''
    self.email = ''
    self.id = ''
    self.address_line = ''
    self.postcode = ''

These items must be set manually and the object passed to ``set_address``. The
``id`` value is obtained from the keys of the dictionary retruned from ``get_addresses``

Setting Cash On Delivery
========================

Currently only cash on delivery is supported. To check if the selected store supports
COD call ``check_cash_on_delivery``, which will return True or False.

    The basket must contain some items for this call to succeed.

If the store supports COD, then a call to ``set_payment_method`` will set the order
as COD.

Payment
=======

* THIS IS UNTESTED *

To complete payment call ``proceed_payment`` which will return True on success
or False on error. This is followed by a call to ``get_confirmation`` which
will return a structure summing up the order details.

So far this has been determined via session capture but not been tested in this
API.
