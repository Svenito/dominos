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

you need to locate your nearest store. The site expects you to search for it 
by some part of the address, so you can provide a partial postcode, or a 
town, or street name. Bear in mind that the more general you are, the more
results you will get.

    >>> stores = d.search_stores('Birmingham')    
    >>> len(stores)
    11

Once a list of stores has been obtained you need to select one to use when 
setting up the order process. Specifically its ``Id``. 

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

Dominos use a ``ProductSkus`` list to define item sizes. For example:

.. code-block:: python

    print 'Sizes available:'
    for i, sku in enumerate(item.ProductSkus):
        print (u'\t[%d] %s - %s' %
               (i, sku['Name'], sku['DisplayPrice']))

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
