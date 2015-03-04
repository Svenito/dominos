#!/usr/bin/env python2.7

import cmd
import time
from dominos import Dominos


class DominosCLI(cmd.Cmd):
    def __init__(self):
        # super(DominosCLI, self).__init__()
        cmd.Cmd.__init__(self)
        self.prompt = 'Pizza> '
        self.d = Dominos()
        self.postcode = None
        self.current_store = None

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
                print(u'[%s] %s - %s' %
                      (item.idx, item.Name, item.DisplayPrice))

    def help_menu(self):
        print('Shows the menu for the currently selected store. '
              'Will error if no store is set and requires '
              '`init_delivery` to have been run.')

    def do_basket(self, s):
        basket = self.d.basket
        for i, item in enumerate(basket.Items):
            print u'%d. %s' % (i, item)

        print u'\nItem count: %s' % basket.TotalItemCount
        print u'-------------------------------'
        print u'Total: %s' % basket.FormattedTotalPrice
        print u'Deal Savings: %s' % self.d.basket.FormattedDealSaving


if __name__ == '__main__':
    x = DominosCLI()
    x.cmdloop()
