#!/usr/bin/env python2.7

import cmd
import time
from dominos import Dominos, Address
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

    def do_locate_store(self, postcode):
        store = self.d.search_nearest_store(postcode)
        if store:
            print '[OK] Found nearest store that delivers:', store.Name
            self.current_store = store
            self.postcode = postcode
        else:
            print '[Warn] Looks like no stores near you deliver'

    def help_locate_store(self):
        print('Search for a Dominos that delivers to the specified postcode.')

    def help_set_store(self):
        print('Select a store by number. Use `locate_store` to get a list '
              'of stores based on a search term.')

    def do_init_delivery(self, postcode):
        if not self.current_store or not self.postcode:
            print('[Error] locate_store needs to be run successfully first.')
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
            tries += 1

        if tries >= 3:
            print '[Error] Failed to get basket'
            return
        else:
            print '[OK] Context and basket initialised'

        #if self.d.check_cash_on_delivery():
        #    self.d.set_payment_method()

    def help_deliver_to(self):
        print('Do the required set up for a delivery from the previously '
              'selected store. Will error if no store has been set. '
              'Requires the delivery postcode as an argument.')

    def get_menu(self):
        if not self.current_store:
            print '[Error] No store set. Run `set_store` first'
            return

        menu = self.d.get_menu(self.current_store)
        for cat, items in menu.items.iteritems():
            for item in items:
                self.items[item.idx] = item

        return menu

    def do_menu(self, s):
        menu = self.get_menu()
        if not menu:
            print '[Error] Unable to get menu. Store context set?'
            return

        print 'Menu for ', self.current_store.Name

        for cat, items in menu.items.iteritems():
            print '---------------------------------'
            print cat
            for item in items:
                print(u'[%s] %s - %s ' %
                      (item.idx, item.Name, item.DisplayPrice)),
                if item.IsVegetarian:
                    print(u'\u24cb '),
                if item.IsHot:
                    print(u'\u2668'),

                print

    def help_menu(self):
        print('Shows the menu for the currently selected store. '
              'Will error if no store is set and requires '
              '`init_delivery` to have been run.')

    def do_info(self, item_idx):
        if not self.items:
            self.get_menu()

        item_idx = int(item_idx)
        if item_idx not in self.items.keys():
            print '[Error] Item with idx %s not found' % item_idx
            return

        item = self.items[item_idx]

        print u'%s - %s' % (item.Name, item.DisplayPrice)
        print u'%s' % item.Description
        print 'Sizes available:'
        for i, sku in enumerate(item.ProductSkus):
            print (u'\t[%d] %s - %s' %
                   (i, sku.Name, sku.DisplayPrice))

    def help_info(self):
        print('Show detailed info for item of given index. '
              'Will include available sizes to use when adding an item to '
              'basket')

    def do_add(self, s):
        if not self.items:
            menu = self.get_menu()

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

        try:
            item_name = self.items[item_idx].Name
            if self.d.add_item(self.items[item_idx], size_idx):
                print('[OK] One %s added to basket' % item_name)
            else:
                print('[Error] Failed to add %s to basket' % item_name)
        except:
            print('[Error] Invalid selection')

    def help_add(self):
        print('Add an item to the basket. Must provide item Id as '
              'specified when viewing `menu`, followed by size index. '
              'Size index can be obtained by running `info <item_idx>` '
              'where item_idx is the menu index of the item.')

    def do_remove(self, s):
        self.d.remove_item(int(s))

    def help_remove(self):
        print('Remove item from basket. Provide basket index of item. This '
              'is the number by the item when viewing basket contents.')

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

    def help_basket(self):
        print('Show the contents of the basket')

    def do_exit(self, s):
        return True

    def do_get_address(self, s):
        self.addresses = self.d.get_addresses()
        if not self.addresses:
            print(u'[Error] Unable to get address lists. Try again')
            return

        for idx, address in enumerate(self.addresses.values()):
            print '[%d] %s' % (idx, address)

    def do_set_address(self, s):
        details = s.split()
        if len(details) < 5:
            print(u'[Error] Please provide AddressIdx FirstName LastName PhoneNumber email')
            return
        self.address = Address()
        self.address.first_name = details[1]
        self.address.last_name = details[2]
        self.address.contact_number = details[3]
        self.address.email = details[4]
        self.address.postcode = self.postcode

        try:
            idx = int(details[0])
        except:
            print(u'Invalid index')
            return

        key = self.addresses.keys()[idx]
        self.address.id = key
        self.address.address_line = self.addresses[key]

        print(u'Delivery details are: %s' % self.address)

    def do_debug_payment(self, s):
        print 'COD', self.d.check_cash_on_delivery()
        print 'SET?', self.d.set_payment_method()

    def do_debug_item(self, s):
        pprint.pprint(self.items[int(s)])

    def do_debug_basket(self, s):
        pprint.pprint(self.d.basket)

if __name__ == '__main__':
    x = DominosCLI()
    print('Welcome to Dominos CLI. Order your pizza from the comfort of '
          'your command line. Use `help` for help on the commands.')
    x.cmdloop()
