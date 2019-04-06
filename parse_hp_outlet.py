#!/usr/bin/python3

import requests, argparse, sys
from bs4 import BeautifulSoup
from decimal import *

class HpBusinessOutletItem:

    def __init__(self):
        # externally set attributes
        self.description    = None
        self.part_num       = None
        self.promo_bonus    = None

        # internally set attributes
        self.price          = None
        self.model          = None
        self.os             = None
        self.cpu_name       = None
        self.cpu_speed      = None
        self.storage        = None
        self.memory         = None
        self.misc           = None

        self.soup = None # beautiful soup's html parser

    def setPrice(self, std_price_str, sale_price_str):
        self.price = Decimal(std_price_str.strip('$'))
        if sale_price_str:
            sale_price = Decimal(sale_price_str.strip('$'))
            if sale_price < self.price:
                self.price = sale_price

    def parseModel(self):
        # Examples to parse:
        # HP ZBook x2 G4 W10P-64 i7 8650U 1.9GHz 1TB NVME 32GB(2x16GB) DDR4 2133 14.0UHD WLAN BT BL Quadro M62
        # HP Elite x2 1013 G3 W10P-64 i5 8250U 1.6GHz 256GB NVME 16GB 13.0 3K2K WWAN(VZW) WLAN BT No-GPS BL FP
        # HP ProBook 640 G4 W10P-64 i3 8130U 2.2GHz 500GB SATA 8GB(1x8GB) 14.0HD No-Wireless No-NFC No-FPR No-
        # HP ProBook 640 G4 W10P-64 i5 8250U 1.6GHz 256GB NVME 1TB SATA 16GB(1x16GB) 14.0FHD WLAN BT No-FPR No

        #print('%%% ' + self.description)
        parts = self.description.split(' ')

        #
        ### Find OS
        #
        self.os = None
        for os_index in range(0, len(parts)):
            if parts[os_index].startswith('W10'):
                self.os = parts[os_index]
                break

        if self.os == None:
            print("ERROR: No OS found:", os_index, self.description)
            sys.exit(1)

        next_index = os_index + 1

        #
        ### Find Model - is all parts before OS
        #
        self.model = ' '.join(parts[0:os_index])

        #
        ### Find CPU name & CPU speed
        #
        cpu_index_start = next_index
        cpu_index_end   = None
        for x in range(cpu_index_start, len(parts)):
            if parts[x].upper().endswith('GHZ'):
                cpu_index_end = x
                break

        if cpu_index_end == None:
            print("ERROR: No cpu end index:", self.description)
            sys.exit(1)
        else:
            self.cpu_name  = ' '.join(parts[cpu_index_start : cpu_index_end])
            self.cpu_speed = parts[cpu_index_end] 

        next_index = cpu_index_end + 1

        ### one row had extra "Ghz" after cpu, need to skip that if there
        if parts[next_index].upper() == 'GHZ':
            next_index += 1 # ok, just skip it

        #
        ### Find Storage (hd or ssd)
        #
        # one or more storage devices
        #   each storage devices is in format of 'size type(s)'
        # 
        # Example with 2 storage devices:
        #   HP ProBook 640 G4 W10P-64 i5 8250U 1.6GHz 256GB NVME 1TB SATA 16GB(1x16GB) 14.0FHD WLAN BT No-FPR No
        
        self.storage = ''
        storage_devices = []
        storage_index = next_index
        keep_going = True
        while keep_going:

            # find storage size
            if parts[storage_index].upper().endswith('GB'):
                storage_size = parts[storage_index]
            elif parts[storage_index].upper().endswith('TB'):
                storage_size = parts[storage_index]
            else:
                # this part is not a storage size, must be memory size instead
                # leave storage_index where is it so that we can check if that part is a memory size
                keep_going = False
                continue

            # all storage devices have one or more descriptors
            storage_desc = ''
            for x in range(storage_index+1, len(parts)):
                if parts[x].upper() in ['NVME', 'SATA', 'SSD']:
                    storage_desc += ' ' + parts[x]
                else:
                    # done with storage descriptors for this device
                    break

            if storage_desc == '':
                # whoops didn't find any desciptors for storage size, that must be memory size instead
                # leave storage_index where is it so that we can check if that part is a memory size
                keep_going = False
            else:
                # ok found storage size and descriptors
                storage_device = storage_size + storage_desc
                storage_devices.append(storage_device)
                storage_index = x

        self.storage = ' '.join(storage_devices)
        if self.storage == '':
            print("ERROR: storage info not found:", self.description)
            sys.exit(1)

        next_index = storage_index

        #
        ### Find Memory 
        #
        # 32GB(2x16GB) DDR4 2133 14.0UHD WLAN BT BL Quadro M62
        # 16GB 13.0 3K2K WWAN(VZW) WLAN BT No-GPS BL FP
        # 8GB(1x8GB) 14.0HD No-Wireless No-NFC No-FPR No-

        memory_index = next_index 
        if 'GB' in parts[memory_index].upper():
            self.memory = parts[memory_index]
            if '(' in self.memory:
                self.memory = self.memory.replace('(', ' (')
        else:
            print("ERROR: memory size not found:", parts[memory_index], ':',  self.description)
            sys.exit(1)
        next_index = memory_index + 1

        #
        ### Find Misc (and particular stuff from misc)
        #
        self.misc = ''
        self.screen = ''

        screen_resolutions = ['HD', 'FHD', 'QHD', 'UHD', 'WXGA', '3K2K']
        screen_sizes = ['11', '12', '13', '14', '15', '17']

        for part in parts[next_index:]:
            if any(s in part.upper() for s in screen_resolutions):
                # this part contains a keyword from screen_resolutions
                self.screen += ' ' + part
            elif any(part.startswith(s) for s in screen_sizes):
                # this part starts with a keyword from screen_sizes
                self.screen += ' ' + part
            else:
                self.misc += ' ' + part
                
        self.screen = self.screen.strip()
        self.misc = self.misc.strip()


    ### Methods for outputting data

    def get_csv_headers(self):
        return ['Model','CPU Name','CPU Speed','OS','Storage','Memory','Screen','Misc','Part#','Price','Promo bonus']

    def _get_output_attributes(self):
        return [self.model, self.cpu_name, self.cpu_speed, self.os, self.storage, self.memory, self.screen, self.misc, self.part_num, '$'+str(self.price), '"'+self.promo_bonus+'"']

    def csv_string(self):
        string = ','.join(self._get_output_attributes())
        return string

    def __str__(self):
        string = ' : '.join(self._get_output_attributes())
        return string

    ### methods for making this class sortable

    def _get_comparison_tuple(self):
        # sort by price then model
        price = self.price
        model = self.model.upper()
        return (price, model)

    def __lt__(self, other):
        return ( self._get_comparison_tuple() < other._get_comparison_tuple() )

    def __eq__(self, other):
        return ( self._get_comparison_tuple() == other._get_comparison_tuple() )

class HpBusinessOutletExtractor:

    def __init__(self, url):
        self.url = url
        self.items = {}

        self.load_page()
        self.parse_items()

    def load_page(self):
        try:
            page = requests.get(self.url)
        except requests.ConnectionError as ex:
            print(ex)
            print("ERROR: Connection Error when loading web page from %s" % (self.url))
            sys.exit(1)

        if page.status_code == requests.codes.ok:
            #print("%d, Retrieved web page from %s" % (page.status_code, self.url))
            self.soup = BeautifulSoup(page.text, 'html.parser')
        else:
            print("%d, Failed to retrieve web page from %s" % (page.status_code, self.url))
            sys.exit(1)

    def parse_items(self):
        #self.items['Clearance']                 = self.parse_items_by_css('#clearance')
        #self.items['Tablets']                   = self.parse_items_by_css('#tablet_pcs')
        self.items['Notebooks']                 = self.parse_items_by_css('#notebook_pcs')
        #self.items['Notebook & Tablet Options'] = self.parse_items_by_css('#notebook_-_tablet_options')
        #self.items['Desktops']                  = self.parse_items_by_css('#desktop_pcs')
        #self.items['Desktop Options']           = self.parse_items_by_css('#desktop_options')
        #self.items['Workstations']              = self.parse_items_by_css('#workstations')
        #self.items['Workstation Options']       = self.parse_items_by_css('#workstation_options')
        #self.items['Thin Clients']              = self.parse_items_by_css('#thin_clients')
        #self.items['Monitors']                  = self.parse_items_by_css('#monitors')

    def print_items_csv(self):
        headers = None
        item_types = sorted(self.items.keys())
        for item_type in item_types:
            print(item_type)
            print(headers)
            items = sorted(self.items[item_type])
            for item in items:
                if not headers:
                    headers = ','.join(item.get_csv_headers())
                    print(headers)
                print(item.csv_string())
            print

    def get_item_column_contents(self, column_contents):
        if len(column_contents) > 0:
            contents = column_contents[0]
        else:
            contents = ''
        return contents

    def parse_items_by_css(self, item_type_css_selector):
        section_div = self.soup.select(item_type_css_selector)[0]
        item_table = section_div.find('table',{'class':'pps-table'})
        rows = item_table.findAll('tr',{'class':'data'})
        items = []
        x = 0 # debug only
        for row in rows:
            #if x > 3: return items
            item = HpBusinessOutletItem()
            columns = row.findAll('td')
            # column header = 'Model', 'Part#', 'Outlet std price', 'Outlet sale price', 'Promo bonus'
            item.description = self.get_item_column_contents(columns[0].contents)
            item.part_num    = self.get_item_column_contents(columns[1].contents)
            std_price        = self.get_item_column_contents(columns[2].contents)
            sale_price       = self.get_item_column_contents(columns[3].contents)
            item.promo_bonus = self.get_item_column_contents(columns[4].contents)
            item.setPrice(std_price, sale_price)
            item.parseModel()
            items.append(item)
            x += 1
        return items

################################################
### Main
################################################

def main(**kwargs):
    url         = kwargs['url']
    output_file = kwargs['output_file']

    hboe = HpBusinessOutletExtractor(url)
    hboe.print_items_csv()

################################################

if __name__ == '__main__':

    HP_BUSINESS_OUTLET_URL = 'https://h41369.www4.hp.com/pps-offers.php'

    parser = argparse.ArgumentParser(description='Parse items for sale at HP Business Outlet web page')
    parser.add_argument('-u', '--url', type=str, default=HP_BUSINESS_OUTLET_URL, help='Output csv file to store processed results')
    parser.add_argument('-o', '--output_file', type=str, default='', help='Output csv file to store processed results')
    args = parser.parse_args()

    main(**vars(args))

