import requests
import pprint
import sys


class Item(object):
    def __init__(self):
        pass


class Menu(object):
    def __init__(self):
        self.items = {}

    def addItem(self, item):
        self.items[item['ProductId']] = item


class Dominos(object):
    def __init__(self):
        self.sess = requests.session()
        self.base_url = 'https://www.dominos.co.uk/'
        self.stores = []
        self.menu = Menu()

    def search_stores(self, postcode):
        url = self.base_url + ('storelocatormap/storenamesearch?search=%s' % postcode)
        print url
        results = self.sess.get(url).json()

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
        query = ('Journey/Initialize?fulfilmentmethod=1'
                 '&storeId=%s&postcode=%s' % (store['Id'], postcode))
        url = self.base_url + query
        print url
        r = self.sess.get(url)
        print r.status_code, self.sess.headers, self.sess.cookies

    def get_store_context(self):
        url = self.base_url + 'ProductCatalog/GetStoreContext'
        print url
        r = self.sess.get(url)
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
        for item in r.json():
            print '----------------------'
            for i in item:
                pprint.pprint(i)
            return
            self.menu.addItem(item)



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
    if not d.get_store_context():
        sys.exit(0)
    d.get_menu(store)
'''
    gets cookie:
    https://www.dominos.co.uk/Journey/Initialize?fulfilmentmethod=1&storeId=2816

    get item ids:
    https://www.dominos.co.uk/ProductCatalog/GetStoreCatalog?collectionOnly=false&menuVersion=635603832000000000&storeId=28162

    list menu:
    https://www.dominos.co.uk/Tracking/ListingProductsDisplayed?productIds=12%7C
'''
