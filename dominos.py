import requests


class Dominos(object):

    def __init__(self):
        self.sess = requests.session()

    def search_stores(self, postcode):
        url = 'https://www.dominos.co.uk/storelocatormap/storenamesearch?search=%s' % postcode
        results = self.sess.get(url).json()

        if len(results) < 1:
            print 'No stores found near', postcode
            if len(postcode) > 3:
                print 'Try a less specific postcode'

        stores = []
        for result in results:
            stores.append(result['Name'])

        return stores


if __name__ == '__main__':
    d = Dominos()
    stores = d.search_stores('ig8')

    print 'Select a store:'
    for i, s in enumerate(stores):
        print '[%d] %s' % (i, s)
