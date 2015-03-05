#!/usr/bin/env python2.7

import requests
import sys
import time
import calendar


class Item(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return str(self.__dict__)


class Basket(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return str(self.__dict__)


class Menu(object):
    def __init__(self):
        self.items = {}

    def addItem(self, category, item):
        self.items.setdefault(category, [])
        self.items[category].append(item)


class Dominos(object):
    def __init__(self):
        self.sess = requests.session()
        # print self.sess
        self.base_url = 'https://www.dominos.co.uk/'
        self.stores = []
        self.menu_version = None
        self.menu = Menu()

        self.reset_session()

    def reset_session(self):
        url = self.base_url + '/Home/SessionExpire'
        self.sess.get(url)
        self.sess = requests.session()

    def get_epoch(self):
        return calendar.timegm(time.gmtime())

    def search_stores(self, postcode):
        self.stores = []
        url = self.base_url + ('storelocatormap/storenamesearch')
        payload = {'search': postcode}
        results = self.sess.get(url, params=payload).json()

        for result in results:
            self.stores.append(result)

        return self.stores

    def select_store(self, idx):
        return self.stores[idx]

    def get_cookie(self, store, postcode):
        url = self.base_url + 'Journey/Initialize'
        payload = {'fulfilmentmethod': '1',
                   'storeId': store['Id'],
                   'postcode': postcode}

        r = self.sess.get(url, params=payload)

    def get_store_context(self):
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
        url = self.base_url + '/Basket/GetBasket?'
        r = self.sess.get(url)

        try:
            self.basket = Basket(**(r.json()))
        except:
            return False
        return True

    def print_basket(self):
        print self.basket

    def get_menu(self, store):
        self.menu = Menu()
        if not self.menu_version:
            return None

        url = (self.base_url + '/ProductCatalog/GetStoreCatalog?'
               'collectionOnly=false&menuVersion=%s&storeId=%s' %
               (self.menu_version, store['Id']))
        r = self.sess.get(url)

        idx = 0
        for item in r.json():
            for i in item['Subcategories']:
                for p in i['Products']:
                    p['idx'] = idx
                    self.menu.addItem(i['Type'], Item(**p))
                    idx += 1

        print item['Subcategories'][0]
        return self.menu

    def show_menu(self, s=None):
        self.menu.print_menu(s)

    def add_item(self, item):
        # url = self.base_url + '/Basket/AddPizza/'
        pass

    def add_margarita(self):
        url = self.base_url + '/Basket/AddPizza/'
        payload = {"basketItemId": 'null',
                   "stepId": 0,
                   "saveName": 'null',
                   "quantity": 1,
                   "sizeId": 3,
                   "productId": 12,
                   "ingredients[]": [42, 36],
                   "productIdHalfTwo": 0,
                   "ingredientsHalfTwo[]": [],
                   "recipeReferrer": 0,
                   "recipeReferralCode": 'null'}

        headers = {'content-type': 'application/json; charset=utf-8'}

        r = self.sess.post(url, params=payload, headers=headers)


if __name__ == '__main__':
    d = Dominos()
    stores = d.search_stores(sys.argv[1])

    valid = False
    store = 0
    while(not valid):
        print 'Select a store:'
        for i, s in enumerate(stores):
            print '[%d] %s' % (i, s['Name'])

            store = int(raw_input('Store: '))
            store = d.select_store(store)
            if store:
                valid = True

    postcode = raw_input('Enter your postcode: ')
    d.get_cookie(store, postcode)
    time.sleep(2)

    doit = True
    while not d.get_store_context() and doit:
        a = raw_input('carry on?')
        if a == 'n':
            doit = False
        d.reset_session()

    doit = True
    while not d.get_basket() and doit:
        a = raw_input('carry on?')
        if a == 'n':
            doit = False

    d.get_menu(store)

    d.show_menu()

    '''

    gets cookie:
    https://www.dominos.co.uk/Journey/Initialize?fulfilmentmethod=1&storeId=2816

    get item ids:
    https://www.dominos.co.uk/ProductCatalog/GetStoreCatalog?collectionOnly=false&menuVersion=635603832000000000&storeId=28162

    list menu:
    https://www.dominos.co.uk/Tracking/ListingProductsDisplayed?productIds=12%7C
    '''
