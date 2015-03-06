Structures
----------

This section shows some example return data. All server
responses are in JSON, but they are mapped into Python objects, so
fields can be accessed in a simpler way. For example:

    >>> stores = d.search_stores('ng2')
    >>> stores[0].Postcode
    u'NG24 1TN'
    >>> stores[0].StoreName
    u'Newark

Shown below however is the raw JSON data, to show both the field names
and the data in those fields.

Results for ``search_store``
============================

    >>> results = d.search_stores('ng2')
    >>> pprint(results)
    [{u'CompanyName': u'',
      u'Distance': 0.0,
      u'FranchiseeName': u'',
      u'Id': 28513,
      u'IsCollectionAvailable': True,
      u'IsOpen': False,
      u'IsPreOrder': True,
      u'Latitude': u'53.073927',
      u'Longitude': u'-0.808936',
      u'Name': u'NG24 1TN - Newark',
      u'Postcode': u'NG24 1TN',
      u'RegionId': u'4',
      u'StoreName': u'Newark',
      u'StoreStatusMessage': u''},
     {u'CompanyName': u'',
      u'Distance': 0.0,
      u'FranchiseeName': u'',
      u'Id': 28858,
      u'IsCollectionAvailable': True,
      u'IsOpen': False,
      u'IsPreOrder': True,
      u'Latitude': u'52.918675',
      u'Longitude': u'-1.152726',
      u'Name': u'NG2 7RS - Nottingham - Silverdale',
      u'Postcode': u'NG2 7RS',
      u'RegionId': u'4',
      u'StoreName': u'Nottingham - Silverdale',
      u'StoreStatusMessage': u''},
     {u'CompanyName': u'',
      u'Distance': 0.0,
      u'FranchiseeName': u'',
      u'Id': 28232,
      u'IsCollectionAvailable': True,
      u'IsOpen': False,
      u'IsPreOrder': True,
      u'Latitude': u'52.937948',
      u'Longitude': u'-1.132982',
      u'Name': u'NG2 5FF - Nottingham - West Bridgford',
      u'Postcode': u'NG2 5FF',
      u'RegionId': u'4',
      u'StoreName': u'Nottingham - West Bridgford',
      u'StoreStatusMessage': u''}]

Results for ``get_store_context``
=================================

The return for this is used internally. There is no need to
deal with this outside of the Dominos class. This function will return 
``True`` if successful, or ``False`` if there was an error.

Results for ``get_cookie``
==========================

The return for this is used internallty. This will return ``True`` on success
and ``False`` on error.

Results for ``get_basket``
==========================

    >>> basket = d.get_basket()
    >>> pprint.pprint(basket)
    {u'TotalSavingInBasket': 0.0, u'FormattedDealSaving': u'\xa30.00',
    u'FulfilmentMethod': u'Delivery',
    u'Success': False,
    u'HasDealSaving': False,
    u'IsSuccess': True,
    u'Version': u'44bf297c-e187-457e-847e-65662e559e78',
    u'TotalItemCount': 0,
    u'CanCheckOut': True,
    u'FormattedOriginalPrice': u'\xa30.00',
    u'CheckOutUrl': u'/basketdetails/show',
    u'WizardOn': True,
    u'DealName': None,
    u'TotalPrice': 0.0,
    u'OriginalBasketPrice': 0.0,
    u'ErrorMessage': None,
    u'IsLoaded': True,
    u'Discount': None,
    u'RecentBasketId': 0,
    u'FormattedTotalPrice': u'\xa30.00',
    u'Items': [],
    u'LastItemCustomiseUrl': None,
    u'CanCheckOutMessage': None}

Results for ``get_store_context``
=================================

Only needed to get the ``menuVersion`` field for later queries. Will
return ``True`` on success and ``False`` on Failure.

Results for ``get_menu``
========================

The ``Menu`` object contains a dictionary of items. There are two keys
``Side`` and ``Pizza``. Each containing a list of ``Items`` of the category


Structure of an Item
====================

    >>> print(u'%s' % menu.items['Side'])
    {u'CustomizeUrl': None,
     u'Description': u'A 6\u201d base topped with 100% Mozzarella Cheese & Domino\u2019s own Tomato Sauce. Calories per half portion: 274 kcal',
     u'DisplayOrder': 3,
     u'DisplayPrice': u'\xa33.99',
     u'ImageUrl': u'https://www.dominos.co.uk/Content/images/Products/GB/Side/256x256/garlic-bread.png?v=fbe05c6fea79956a8f51b38dab4cd589',
     u'IsAlcohol': False,
     u'IsDeliveryOnly': False,
     u'IsGlutenFree': False,
     u'IsHot': False,
     u'IsVegetarian': True,
     u'IsVirtual': False,
     u'Name': u'Garlic Pizza Bread',
     u'Price': 3.99,
     u'ProductId': 1,
     u'ProductSkus': [{u'AvailableQuantities': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                       u'ComplimentaryProducts': [],
                       u'DisplayDoubleUpPrice': u'',
                       u'DisplayPrice': u'\xa33.99',
                       u'DisplayPriceByRelativeSize': u'',
                       u'ExternalAllergenUrl': None,
                       u'HasAllergenInformation': True,
                       u'HasDefaultRecipe': True,
                       u'IconUrl': u'/Content/Images/Site/icons/garlic-bread.png',
                       u'Ingredients': [],
                       u'Movies': [],
                       u'Name': u'Garlic Pizza Bread',
                       u'PackagingRebate': None,
                       u'Price': 3.99,
                       u'ProductCode': u'GPB',
                       u'ProductId': 1,
                       u'ProductSkuId': 225,
                       u'Quantity': 1,
                       u'QuantityInBasket': 0,
                       u'UnitDescription': None}],
     u'QuantityInBasket': 0,
     u'Title': u'Add Garlic Pizza Bread to your order',
     u'Type': u'Side',
     'idx': 17}
    
Each ``ProductSkus`` entry defines one size of pizza.


