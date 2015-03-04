#!/usr/bin/env python2.7

import requests
import pprint
import sys
import time
import calendar
import unicodedata

class Item(object):
    def __init__(self):
        pass


class Basket(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
         return self.__dict__


class Menu(object):
    def __init__(self):
        self.items = {}

    def addItem(self, item):
        self.items[item['ProductId']] = item


class Dominos(object):
    def __init__(self):
        self.sess = requests.session()
        print self.sess
        self.base_url = 'https://www.dominos.co.uk/'
        self.stores = []
        self.menu = Menu()

        url = self.base_url + '/Home/SessionExpire'
        r = self.sess.get(url)
        print 'expire ', r.status_code

    def get_epoch(self):
        return calendar.timegm(time.gmtime())

    def search_stores(self, postcode):
        url = self.base_url + ('storelocatormap/storenamesearch')
        payload = {'search': postcode}
        results = self.sess.get(url, params=payload).json()
        print url

        if len(results) < 1:
            print 'No stores found near', postcode
            if len(postcode) > 3:
                print 'Try a less specific postcode'

        for result in results:
            self.stores.append(result)

        return self.stores

    def select_store(self, idx):
        try:
            return self.stores[idx]
        except IndexError:
            print 'Invalid store selected'
            return None


    def get_cookie(self, store, postcode):
        url = self.base_url + 'Journey/Initialize'
        payload = {'fulfilmentmethod':'1',
                   'storeId' : store['Id'],
                   'postcode' : postcode}
        print payload
        print self.sess.cookies
        r = self.sess.get(url, params=payload)

    def get_basket(self):
        url = self.base_url + '/Basket/GetBasket'
        r = self.sess.get(url)
        print r.status_code
        try:
            self.basket = Basket(**(r.json()))
        except:
            print 'Failed to get basket'
            return False
        return True


    def get_store_context(self):
        url = self.base_url + 'ProductCatalog/GetStoreContext'
        payload = {'_' : self.get_epoch()}
        print self.sess.cookies
        r = self.sess.get(url, params=payload)
        print r.status_code

        try:
            context = r.json()
        except:
            print 'Unable to get context'
            return False

        self.menu_version = context['sessionContext']['menuVersion']
        return True

    def get_menu(self, store):
        url = (self.base_url + '/ProductCatalog/GetStoreCatalog?'
                'collectionOnly=false&menuVersion=%s&storeId=%s' %
                (self.menu_version, store['Id']))
        print url
        r = self.sess.get(url)
        item_num = 0
        for item in r.json():
            print '----------------------'
            for i in item['Subcategories']:
                print i['Name']
                for p in i['Products']:
                    name = unicodedata.normalize('NFKD', p['Name']).encode('ascii','ignore')
                    print '[%d] %s (%s)' % (item_num, name, p['ProductId'])
                    item_num += 1

    def add_margarita(self):
        url = self.base_url + '/Basket/AddPizza/'
        payload = {"basketItemId":None,"stepId":0,"saveName":None,"quantity":1,"sizeId":3,"productId":12,"ingredients":[42,36],"productIdHalfTwo":0,"ingredientsHalfTwo":[],"recipeReferrer":0,"recipeReferralCode":None}

        r = self.sess.post(url, data=payload)
        print r.status_code
        print r.text

        self.get_basket()
        pprint.pprint(self.basket)


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

    if not d.get_basket():
        sys.exit(0)

    if not d.get_store_context():
        sys.exit(0)
    d.get_menu(store)

    #d.add_margarita()
'''
    gets cookie:
    https://www.dominos.co.uk/Journey/Initialize?fulfilmentmethod=1&storeId=2816

    get item ids:
    https://www.dominos.co.uk/ProductCatalog/GetStoreCatalog?collectionOnly=false&menuVersion=635603832000000000&storeId=28162

    list menu:
    https://www.dominos.co.uk/Tracking/ListingProductsDisplayed?productIds=12%7C
'''
