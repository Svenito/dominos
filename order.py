#!/usr/bin/env python2.7

import cmd
import sys
import time
from dominos import Dominos

import pprint

class DominosCLI(cmd.Cmd):
    def __init__(self):
        # super(DominosCLI, self).__init__()
        cmd.Cmd.__init__(self)
        self.prompt = 'Pizza> '
        self.d = Dominos()
        self.postcode = None
        self.current_store = None
        self.items = {}

    def do_locate_store(self, s):
        stores = self.d.search_stores(s)
        if not stores:
            print '[Warn] No stores found with search term ', s
            return

        for i, store in enumerate(stores):
            print '[%s] %s' % (i, store['Name'])

    def help_locate_store(self):
        print('Search for a Dominos by postcode/location name. Returns '
              'a list of stores that match the given search term')

    def do_set_store(self, store_idx):
        store_idx = int(store_idx)
        try:
            self.current_store = self.d.select_store(store_idx)
            print '[OK] Selected store: %s' % self.current_store['Name']
        except IndexError:
            print '[Error] Invalid selection.'

    def help_set_store(self):
        print('Select a store by number. Use `locate_store` to get a list '
              'of stores based on a search term.')

    def do_deliver_to(self, postcode):
        self.postcode = postcode
        if not self.current_store or not self.postcode:
            print '[Error] A current store and delivery postcode must be set'
            return

        self.d.get_cookie(self.current_store, self.postcode)
        time.sleep(1)
        if not self.d.get_store_context():
            print('[Error] Failed to get store context. '
                  'Try setting the store again.')
            self.d.reset_session()
            return

        tries = 0
        while not self.d.get_basket() and tries < 2:
            print '.',
            tries += 1

        if tries >= 2:
            print '[Error] Failed to get basket'
            return
        else:
            print '[OK] Context and basket initialised'

    def help_deliver_to(self):
        print('Do the required set up for a delivery from the previously '
              'selected store. Will error if no store has been set. '
              'Requires the delivery postcode as an argument.')

    def do_menu(self, s):
        if not self.current_store:
            print '[Error] No store set. Run `set_store` first'
            return

        menu = self.d.get_menu(self.current_store)
        print 'Menu for ', self.current_store['Name']
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

        # pprint.pprint(self.items[12])

    def help_menu(self):
        print('Shows the menu for the currently selected store. '
              'Will error if no store is set and requires '
              '`init_delivery` to have been run.')

    def do_info(self, item_idx):
        if not self.items:
            print '[Error] Please run `menu` before this cmd'

        item_idx = int(item_idx)
        if not item_idx in self.items.keys():
            print '[Error] Item with idx %s not found' % item_idx
            return

        item = self.items[item_idx]

        print u'%s - %s' % (item.Name, item.DisplayPrice)
        print u'%s' % item.Description
        print 'Sizes available:'
        for i, sku in enumerate(item.ProductSkus):
            print (u'\t[%d] %s - %s' %
                   (i, sku['Name'], sku['DisplayPrice']))

        # print self.items[item_idx]

    def do_add(self, s):
        if not self.items:
            print '[Error] Please run `menu` before this cmd'

        details = s.split()
        if len(details) < 2:
            print('[Error] Specify item ID and a size. '
                  'Use `info` cmd to see sizes for each item.')

        try:
            item_idx = int(details[0])
            size_idx = int(details[1])
        except TypeError:
            print('[Error] Invalid item ID or size')
            return

        item_name = self.items[item_idx].Name
        if self.d.add_item(self.items[item_idx], size_idx):
            print('[OK] One %s added to basket' % item_name)
        else:
            print('[Error] Failed to add %s to basket' % item.name)

    def do_basket(self, s):
        if not self.d.basket:
            print('[Error] No basket yet. Run `deliver_to` first')
            return

        basket = self.d.basket
        print('Current basket:\n')
        for i, item in enumerate(basket.Items):
            print(u'%d. %s - %s' % (i, item['Title'], item['FormattedPrice']))

        print(u'\nItem count:\t\t%s' % basket.TotalItemCount)
        print(u'-------------------------------')
        print(u'Total:\t\t\t%s' % basket.FormattedTotalPrice)
        print(u'Deal Savings:\t\t%s' % self.d.basket.FormattedDealSaving)

    def do_exit(self, s):
        return True

    def do_debug_item(self, s):
        pprint.pprint(self.items[int(s)])

    def do_debug_basket(self, s):
        pprint.pprint(self.d.basket)

if __name__ == '__main__':
    x = DominosCLI()
    x.cmdloop()
