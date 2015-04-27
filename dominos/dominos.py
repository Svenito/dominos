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
        self.set_skus()

    def set_skus(self):
        skus = self.ProductSkus
        self.ProductSkus = []

        for sku in skus:
            s = self.Sku(**sku)
            self.ProductSkus.append(s)


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


class Address(object):
    '''
    Delivery address structure. Contains the
    required fields to set the delivery address on
    the site
    '''
    def __init__(self):
        self.first_name = ''
        self.last_name = ''
        self.contact_number = ''
        self.email = ''
        self.id = ''
        self.address_line = ''
        self.postcode = ''

    def __repr__(self):
        out = ('Name: %s %s\nAddress:[%s] %s %s\nPhone:%s\nEmail:%s' %
               (self.first_name, self.last_name, self.id, self.address_line,
                self.postcode, self.contact_number, self.email))
        return out


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
        self.reset_store()

    def reset_session(self):
        '''
        Clear out a session by calling SessionExpire on the remote.
        Also clears out the local session and creates a new requests.session
        '''
        url = self.base_url + '/Home/SessionExpire'
        self.sess.get(url)
        self.sess = requests.session()

    def reset_store(self):
        '''
        Clears out the current store and gets a cookie
        '''
        url = self.base_url + 'Store/Reset'
        self.sess.get(url)

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

        results = self.sess.get(url, params=payload, headers=headers)
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
        payload = {'fulfilmentmethod': 'Delivery',
                   'storeid': store.Id,
                   'postcode': postcode}

        xsrf = self.sess.cookies['XSRF-TOKEN']
        headers = {'content-type': 'application/json; charset=utf-8',
                'X-XSRF-TOKEN': xsrf}

        r = self.sess.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code != 200:
            return False

        try:
            context = r.json()
        except:
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
        r = self.sess.get(url, params=payload)#, headers=headers)

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

        xsrf = self.sess.cookies['XSRF-TOKEN']
        headers = {'content-type': 'application/json; charset=utf-8',
                'X-XSRF-TOKEN': xsrf}
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
        self.get_basket()

        url = self.base_url + '/fulfilment/yourdetails'
        r = self.sess.get(url)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text)
        try:
            address_ids = soup.find(id='AddressId').children
        except:
            return {}

        addresses = {}
        for field in address_ids:
            try:
                if field['value']:
                    addresses[field['value']] = field.text
            except:
                pass

        return addresses

    def set_address(self, address):
        '''
        Given and idx returned from `get_addresses` will
        set that as the delivery address. Automatically
        set marketing preferences to False.
        address.firstname
        address.last_name
        address.contact_number
        address.email
        address.postcode
        '''
        url = self.base_url + '/fulfilment/yourdetails'
        payload = {'FirstName': address.first_name,
                   'LastName': address.last_name,
                   'ContactNumber': address.contact_number,
                   'EmailAddress': address.email,
                   'DeliveryAddress.Postcode': address.postcode,
                   'AddressId': address.id,
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
        '''
        Verifies if the selected store allows cash on delivery.
        The current implementation only support cash on delivery, so
        it is used to make sure we can actually order. Before this
        call will succeed you must add something to the basket.
        Returns True if supported, False if not
        '''
        url = self.base_url + '/PaymentOptions/GetPaymentDetailsData'

        xsrf = self.sess.cookies['XSRF-TOKEN']
        headers = {'content-type': 'application/json; charset=utf-8',
                   'X-XSRF-TOKEN': xsrf}

        r = self.sess.post(url, headers=headers)
        result = None
        try:
            result = r.json()
        except:
            print "ERROR"
            return False

        if (result['isCashOptionAvailable'] == True and
                result['isCashOptionAllowed'] == True):
            return True
        else:
            return False
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

    def set_payment_method(self):
        '''
        Set the payment method to Cash On Delivery, the only
        method currently supported.

        POST /PaymentOptions/SetPaymentMethod
        {"paymentMethod":0}
        '''
        url = self.base_url + '/PaymentOptions/SetPaymentMethod'
        payload = {'paymentMethod': 0}
        xsrf = self.sess.cookies['XSRF-TOKEN']
        headers = {'content-type': 'application/json; charset=utf-8',
                   'X-XSRF-TOKEN': xsrf}

        r = self.sess.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code != 200:
            return False

        try:
            r.json()
            return True
        except:
            return False

    def proceed_payment(self):
        '''
        *UNTESTED IN REAL LIFE*
        Complete payment and submit to store. Brace for delivery
        POST /paymentoptions/proceed (yes, lowercase)
        no args
        '''
        # Comment out next line to enable payments
        return False

        url = self.base_url + 'paymentoptions/proceed'

        xsrf = self.sess.cookies['XSRF-TOKEN']
        headers = {'content-type': 'application/json; charset=utf-8',
                   'X-XSRF-TOKEN': xsrf}
        payload = {'__RequestVerificationToken': self.sess.cookies,
                   'method': 'submit'}

        r = self.sess.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code != 200:
            return False

        return True

    def get_confirmation(self):
        '''
        *UNTESTED IN THE WILD*
        Returns the delivery details for tracking and
        confirmation.
        GET /tracking/pageload
        {"pageType": "CheckoutComplete",
         "dataLayerFormat": "ConfirmationThankYou"}
        '''
        url = self.base_url + 'tracking/pageload'
        payload = {"pageType": "CheckoutComplete",
                   "dataLayerFormat": "ConfirmationThankYou"}

        r = self.sess.get(url, params=payload)
        try:
            return r.json()
        except:
            return ''

        '''
        window.dataLayer.push({
  "site": {
    "environment": "07",
    "versionNo": "9.1.0.1610",
    "versionName": "Beta"
  },
  "user": {
    "id": "anon",
    "loginState": "false",
    "loginType": "anon",
    "existingCustomer": "false",
    "language": "en-GB"
  },
  "page": {
    "type": "Confirmation Thank You",
    "subType": "checkout-page",
    "url": ""
  },
  "store": {
    "id": 281,
    "name": "London",
    "city": "London Region",
    "postcode": "XX8 XX8"
  },
  "transaction": {
    "id": "XXXXXXXXX",
    "affiliation": "London",
    "subTotal": "36.97",
    "total": "22.48",
    "shipping": "0.00",
    "paymentType": "Cash",
    "currency": "GBP",
    "shippingMethod": "Delivery",
    "noOfProducts": "3.00",
    "deliveryTime": "01/01/0001 00:00:00",
    "quantity": "3.00"
  },
  "transactionProducts": [
    {
      "id": "3174179",
      "name": "BOGOF",
      "nameParent": "BOGOF",
      "category": "MealDeal",
      "originalPrice": "28.98",
      "price": "14.49",
      "offerName": "BOGOF",
      "offerSaving": "14.49",
      "upsellType": "",
      "currency": "GBP",
      "quantity": 1,
      "dealType": "MealDeal",
      "partOfDeal": "deal",
      "productIds": "50|50",
      "productNames": "Create Your Own|Create Your Own"
    },
    {
      "id": "1443",
      "variantId": "1655",
      "name": "14 Chicken Kickers",
      "nameParent": "14 Chicken Kickers",
      "image": "CHICKEN_KICKERS_14.jpg",
      "thumbnail": "icons/chicken.png",
      "category": "Side",
      "subCategory": "Chicken",
      "price": "7.99",
      "offerSaving": "0.00",
      "upsellType": "",
      "currency": "GBP",
      "quantity": 1,
      "flavourDietry": "",
      "size": "",
      "dealType": "",
      "partOfDeal": "false",
      "numberPassed": "1443"
    },
    {
      "id": "999",
      "variantId": "50",
      "name": "Medium (8 slices) Create Your Own",
      "nameParent": "Create Your Own",
      "image": "create-your-own.jpg",
      "thumbnail": "icons/pizza.png",
      "category": "Pizza",
      "subCategory": "CreateYourOwnPizza",
      "price": "11.99",
      "offerSaving": "14.49",
      "upsellType": "",
      "currency": "GBP",
      "quantity": 1,
      "flavourDietry": "gluten-Free",
      "size": "Medium (8 slices)",
      "pizzaCrust": "Italian Style",
      "pizzaSauce": "Domino's Own Tomato Sauce",
      "pizzaCheese": "Mozzarella Cheese",
      "pizzaToppings": "Anchovies|Olives",
      "dealType": "MealDeal",
      "partOfDeal": "true",
      "partOfDealId": "3174179",
      "numberPassed": "999"
    },
    {
      "id": "999",
      "variantId": "50",
      "name": "Medium (8 slices) Create Your Own",
      "nameParent": "Create Your Own",
      "image": "create-your-own.jpg",
      "thumbnail": "icons/pizza.png",
      "category": "Pizza",
      "subCategory": "CreateYourOwnPizza",
      "price": "11.99",
      "offerSaving": "0.00",
      "upsellType": "",
      "currency": "GBP",
      "quantity": 1,
      "flavourDietry": "gluten-Free",
      "size": "Medium (8 slices)",
      "pizzaCrust": "Italian Style",
      "pizzaSauce": "Domino's Own Tomato Sauce",
      "pizzaCheese": "Mozzarella Cheese",
      "pizzaToppings": "Olives|Pepperoni",
      "dealType": "MealDeal",
      "partOfDeal": "true",
      "partOfDealId": "3174179",
      "numberPassed": "999"
    }
  ]
});

window.pageContext= {pageType : 'CheckoutComplete', dataLayerFormat:
'ConfirmationThankYou'} ;
'''

if __name__ == '__main__':
    pass
