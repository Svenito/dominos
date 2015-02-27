import requests


class Dominos(object):

    def __init__(self):
        self.sess = requests.session()
        self.stores = []

    def search_stores(self, postcode):
        url = 'https://www.dominos.co.uk/storelocatormap/storenamesearch?search=%s' % postcode
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
            return store[int(idx)]
        except IndexError:
            print 'Invalid store selected'
            return None


if __name__ == '__main__':
    d = Dominos()
    stores = d.search_stores('ig6')

    valid = False
    while(not valid):
        print 'Select a store:'
        for i, s in enumerate(stores):
            print '[%d] %s' % (i, s['Name'])

            store = raw_input('Store: ')
            selected_store = d.select_store(store)
            if selected_store:
                valid = True

'''
    gets cookie:
    https://www.dominos.co.uk/Journey/Initialize?fulfilmentmethod=1&storeId=2816

    get item ids:
    https://www.dominos.co.uk/ProductCatalog/GetStoreCatalog?collectionOnly=fals

    list menu:
    https://www.dominos.co.uk/Tracking/ListingProductsDisplayed?productIds=12%7C
'''
