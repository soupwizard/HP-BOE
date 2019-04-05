
import requests
from bs4 import BeautifulSoup
from decimal import *

class HpOutletItem:

    def __init__(self):
        self.model              = None
        self.part_num           = None
        self.price              = None
        self.promo_bonus        = None

        self.soup = None # beautiful soup's html parser

    def setPrice(self, std_price_str, sale_price_str):
        self.price = Decimal(std_price_str.strip('$'))
        if sale_price_str:
            sale_price = Decimal(sale_price_str.strip('$'))
            if sale_price < self.price:
                self.price = sale_price

    def csv_string(self):
        string = '"%s","%s","$%s","%s"' % (self.model, self.part_num, self.price, self.promo_bonus) 
        return string

    def __str__(self):
        string = "%s : %s : $%s : %s" % (self.model, self.part_num, self.price, self.promo_bonus) 
        return string

    ### method for making this class sortable

    def _get_comparison_tuple(self):
        model = self.model.upper()
        price = self.price
        return (price, model)

    def __lt__(self, other):
        return ( self._get_comparison_tuple() < other._get_comparison_tuple() )

    def __eq__(self, other):
        #return self.model.upper() == other.model.upper()
        return ( self._get_comparison_tuple() == other._get_comparison_tuple() )

class HpOutletExtractor:

    def __init__(self):
        self.items = {}

    def load_page(self, url):
        page = requests.get(url)
        if page.status_code == requests.codes.ok:
            #print("%d, Retrieved web page from %s" % (page.status_code, url))
            self.soup = BeautifulSoup(page.text, 'html.parser')
        else:
            print("%d, Failed to retrieve web page from %s" % (page.status_code, url))
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

    def print_items(self):
        headers = 'Model,Part#,Price,Promo bonus'
        item_types = sorted(self.items.keys())
        for item_type in item_types:
            print(item_type)
            print(headers)
            items = sorted(self.items[item_type])
            for item in items:
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
        for row in rows:
            item = HpOutletItem()
            columns = row.findAll('td')
            # column header = 'Model', 'Part#', 'Outlet std price', 'Outlet sale price', 'Promo bonus'
            item.model       = self.get_item_column_contents(columns[0].contents)
            item.part_num    = self.get_item_column_contents(columns[1].contents)
            std_price        = self.get_item_column_contents(columns[2].contents)
            sale_price       = self.get_item_column_contents(columns[3].contents)
            item.promo_bonus = self.get_item_column_contents(columns[4].contents)
            item.setPrice(std_price, sale_price)
            items.append(item)
        return items

HP_OUTLET_URL= 'https://h41369.www4.hp.com/pps-offers.php'

hoe = HpOutletExtractor()
hoe.load_page(HP_OUTLET_URL)
hoe.parse_items()
hoe.print_items()


