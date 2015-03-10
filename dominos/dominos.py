#!/usr/bin/env python2.7

import requests
import time
import calendar
import json
import pprint
from bs4 import BeautifulSoup


class Base(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return pprint.pformat(self.__dict__)


class Item(Base):
    '''
    Wrapper around a menu Item. Basically provides
    class like interface to the Item dictionary.
    '''
    class Sku(Base):
        pass

    def __init__(self, **entries):
        self.__dict__.update(entries)
        self.skus = []
        self.set_skus()

    def set_skus(self):
        for skus in self.ProductSkus:
            sku = self.Sku(**skus)
            self.skus.append(sku)


class Basket(Base):
    '''
    Wrapper around the Basket dictionary returned from
    server. Provides class like access to Basket.
    '''
    pass


class Store(Base):
    '''
    Wrapper around the Store dictionary returned from server.
    Provides class like access to Store details.
    '''
    pass


class Menu(object):
    '''
    Menu is a container for Items.
    '''
    def __init__(self):
        self.items = {}

    def addItem(self, category, item):
        '''
        Add an item of category to this menu.

        :param category: The category of this item. Usually item.Type
        :param item: The item to add

        '''

        self.items.setdefault(category, [])
        self.items[category].append(item)

    def itemsInCategory(self, category):
        try:
            return self.items[category]
        except:
            return []

    def __repr__(self):
        out = ''
        for cat, items in self.items.iteritems():
            out += cat + '\n'
            for item in items:
                out += item.Name + '\n'
        return out


class DeliveryAddress(object):
    def __init__(self):
        self.first_name = ''
        self.last_name = ''
        self.contact_number = ''
        self.email = ''
        self.address_id = ''
        self.postcode = ''


class Dominos(object):
    '''
    Main class to interact with the dominos.co.uk
    site
    '''
    def __init__(self):
        self.sess = requests.session()
        self.base_url = 'https://www.dominos.co.uk/'
        self.stores = []
        self.menu_version = None
        self.menu = Menu()

        self.reset_session()

    def reset_session(self):
        '''
        Clear out a session by calling SessionExpire on the remote.
        Also clears out the local session and creates a new requests.session
        '''
        url = self.base_url + '/Home/SessionExpire'
        self.sess.get(url)
        self.sess = requests.session()

    def get_epoch(self):
        '''
        Utility function used to get current epoch time. Required for some
        calls to the remote.
        '''
        return calendar.timegm(time.gmtime())

    def search_stores(self, term):
        '''
        Given a search query returns all matching store objects.
        These are then stored in the stores list.
        Returns a list of stores as dictionaries. If no stores
        match ``term`` an empty list is returned.
        '''
        self.stores = []
        url = self.base_url + ('storelocatormap/storenamesearch')
        payload = {'search': term}
        results = self.sess.get(url, params=payload).json()

        for result in results:
            store = Store(**result)
            self.stores.append(store)

        return self.stores

    def search_nearest_store(self, postcode):
        '''
        Given a postcode will return the nearest Dominos that
        delivers to that postcode.
        Returns a Store object if one is found, otherwise returns
        None
        '''
        self.stores = []
        url = self.base_url + ('storelocatormap/storesearch')

        payload = {'SearchText': postcode}
        headers = {'content-type': 'application/json; charset=utf-8'}

        results = self.sess.post(url, data=json.dumps(payload), headers=headers)
        try:
            stores = results.json()
        except:
            return None

        store = None
        if stores['LocalStore']:
            store = Store(**stores['LocalStore'])

        return store

    def select_store(self, idx):
        '''
        Return a store at the given index.
        '''
        return self.stores[idx]

    def get_cookie(self, store, postcode):
        '''
        Set local cookies by initialising the delivery system on the
        remote. Requires a store ID and a delivery postcode. This
        must be called once a store ID is known, as the generated cookies
        are needed for future calls.
        Returns True on success and False on error.
        '''
        url = self.base_url + 'Journey/Initialize'
        payload = {'fulfilmentmethod': '1',
                   'storeId': store.Id,
                   'postcode': postcode}

        r = self.sess.get(url, params=payload)
        if r.status_code != 200:
            return False
        return True

    def get_store_context(self):
        '''
        Get the required context for the store. This must be called at
        some point after get_cookie and before you are able to get a
        basket. This might fail due to possible rate limiting on the remote
        end. Sometimes waiting a little and retrying will make it succeed.
        '''
        url = self.base_url + 'ProductCatalog/GetStoreContext'
        payload = {'_': self.get_epoch()}
        headers = {'content-type': 'application/json; charset=utf-8'}
        r = self.sess.get(url, params=payload, headers=headers)

        try:
            context = r.json()
        except:
            return False

        self.menu_version = context['sessionContext']['menuVersion']
        return True

    def get_basket(self):
        '''
        Get the current basket object. get_store_context must be called first.
        May also fail, but will usually succeed if retried.
        '''
        url = self.base_url + '/Basket/GetBasket?'
        r = self.sess.get(url)

        try:
            self.basket = Basket(**(r.json()))
        except:
            return None
        return self.basket

    def get_menu(self, store):
        '''
        Retrieve the menu for the currently set store. get_basket and
        get_store_context must be called successfully before this can be
        called.
        '''
        self.menu = Menu()
        if not self.menu_version:
            return None

        url = (self.base_url + '/ProductCatalog/GetStoreCatalog?'
               'collectionOnly=false&menuVersion=%s&storeId=%s' %
               (self.menu_version, store.Id))
        r = self.sess.get(url)

        idx = 0
        for item in r.json():
            for i in item['Subcategories']:
                for p in i['Products']:
                    p['idx'] = idx
                    self.menu.addItem(i['Type'], Item(**p))
                    idx += 1

        return self.menu

    def add_item(self, item, size_idx):
        '''
        Add an item to the basket. Provide the item object and
        a size index. Will overwrite the basket with the new basket.
        The size index is the index into the item's ``ProductSkus`` list.

        Will return an updated basket on success or ``None`` on failure.

        '''

        url = self.base_url

        if item.Type == 'Pizza':
            url += '/Basket/AddPizza/'
            ingredients = item.ProductSkus[size_idx].Ingredients

            # always cheese and tomato sauce
            ingredients += [42, 36]

            payload = {"stepId": 0,
                       "quantity": 1,
                       "sizeId": size_idx,
                       "productId": item.ProductId,
                       "ingredients": ingredients,
                       "productIdHalfTwo": 0,
                       "ingredientsHalfTwo": [],
                       "recipeReferrer": 0}
        elif item.Type == 'Side':
            url += '/Basket/AddProduct/'
            sku_id = item.ProductSkus[size_idx].ProductSkuId

            payload = {"ProductSkuId": sku_id,
                       "Quantity": 1,
                       "ComplimentaryItems": []}

        headers = {'content-type': 'application/json; charset=utf-8'}
        r = self.sess.post(url, data=json.dumps(payload), headers=headers)

        if r.status_code != 200:
            return None

        try:
            self.basket = Basket(**r.json())
        except:
            return None

        return self.basket

    def remove_item(self, basket_item_idx):
        '''
        Remove an item at basket position item_idx from the basket
        '''
        item = Item(**self.basket.Items[basket_item_idx])

        url = self.base_url + '/Basket/RemoveBasketItem'
        payload = {'basketItemId': item.BasketItemId,
                   'wizardItemDelete': False}

        r = self.sess.get(url, params=payload)
        if r.status_code != 200:
            return None

        try:
            self.basket = Basket(**r.json())
        except:
            return None

        return self.basket

    def get_addresses(self):
        '''
        Gets a list of possible addresses based on the postcode
        passed to ``get_cookie``. Returns a dictionary with AddressIds
        as keys and the address line as value.
        The AddressId is passed onto the ordering system.
        Returns an empty dictionary if no addresses can be found.
        '''

        url = self.base_url + '/fulfilment/yourdetails'
        r = self.sess.get(url)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text)
        try:
            address_ids = soup.find(id='AddressId').children
        except:
            print r.text
            return {}

        print(u'Select delivery address')

        addresses = {}
        for field in address_ids:
            try:
                if field['value']:
                    addresses[field['value']] = field.text
            except:
                pass

        return addresses

    def set_address(self, address):
        url = self.base_url + '/fulfilment/yourdetails'
        payload = {'FirstName': address.first_name,
                   'LastName': address.last_name,
                   'ContactNumber': address.contact_number,
                   'EmailAddress': address.email,
                   'DeliveryAddress.Postcode': address.postcode,
                   'AddressId': '1515951',
                   'DeliveryAddress.AdditionalInformation': '',
                   'AddAddressToCustomer': False,
                   'DeliveryTime': 'ASAP',
                   'MarketingPreferenceEmail': True,
                   'MarketingPreferenceEmail': False,
                   'MarketingPreferenceSMS': True,
                   'MarketingPreferenceSMS': False
                   }

        headers = {'content-type': 'application/json; charset=utf-8'}
        r = self.sess.post(url, data=json.dumps(payload), headers=headers)

        if r.status_code != 200:
            return None

    def check_cash_on_delivery(self):
        pass
        # rl = self.base_url + '/PaymentOptions/GetPaymentDetailsData'
        '''
        GET
        returns:
        {
          "isCashOptionAvailable": true,
          "cashOptionText": "Cash on Delivery",
          "isCardOptionAvailable": true,
          "isPayPalOptionAvailable": true,
          "cashNotAllowedText": null,
          "cardNotAllowedText": null,
          "payPalStatusText": null,
          "cardUrl": "https://hps.datacash.com/hps/?HPS_SessionID=214853777",
          "totalPrice": "18.99",
          "isCashOptionAllowed": true,
          "savePaymentCardOption": true,
          "paymentMethodSelected": 1,
          "canShowSavedCards": false,
          "canShowPayPal": true,
          "isSavePaymentCardAvailable": false,
          "isMaximumSavedCardsReached": false,
          "savedPaymentCards": null
        }
'''

    def submit_detail_summary(self):
        '''
        Might not be neccessary
        '''
        # https://www.dominos.co.uk/fulfilment/yourdetailssummarysubmit
        # POST
        # Body	Items%5B0%5D.item.BasketItemId	2
        # Body	Items%5B0%5D.item.BasketItemId	3

    def set_payment_menthod(self):
        '''
        POST /PaymentOptions/SetPaymentMethod
        {"paymentMethod":0}
        '''

        pass


if __name__ == '__main__':
    pass
