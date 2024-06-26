import pytz

from multiprocessing import Process
from datetime import datetime, timedelta

from utils import *

class AnaSloData:
    process = []
    
    def get_all_datas(self, type):
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        start_date = now - timedelta(days=1)
        start_date = start_date.strftime("%Y-%m-%d")
        
        # get date of previous operation
        prev_date = get_date_of_previous_operation()
        print(prev_date)
        
        # get page data to get region info
        print('================start===============')
        print(now.strftime("%H:%M:%S"))
        
        response = send_request('https://ana-slo.com/', 'get', {}, {})
        
        page_data = None
        
        if response != '':
            page_data = parse_html_to_element(response)
        else:
            return {'msg': 'net error', 'data': response}
        
        # get region info from page data
        region_data = get_region_data(page_data)
        print('==================region data===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))
        
        for region in region_data:
            print(f"start => {region}")
            self.get_store_info(region, start_date, prev_date, type)
            # self.process.append(Process(target=self.get_store_info, args=(region, start_date, prev_date, type)).start())
        
        return "Finished"
    
    def get_store_info(self, region, start_date, prev_date, type):
        # get a list of stores in region
        store_list = get_list_of_stores(region)
        print('==================store list===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))

        # save data in database
        save_data_in_database(type, start_date, 'store_list')
        print('==================save data ind database===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))
        
        # get store data by date
        cur_date = start_date.split('-')
        cur_date = datetime(int(cur_date[0]), int(cur_date[1]), int(cur_date[2]))
        
        store_data = get_store_data_by_date(prev_date, cur_date, type)
        print('==================get store data by date===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))

        # save data in database
        save_data_in_database(type, start_date, 'store_data')
        print('==================save data ind database===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))
        
        # get store sub data by date
        store_sub_data = get_store_sub_data_by_date()
        print('==================get store sub data by date===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))

        # #  export json file
        # export_txt_file()
        # print('==================json export===============')
        # now = datetime.now()
        # print(now.strftime("%H:%M:%S"))
        
        # # export json file
        # export_json_file()
        # print('==================json export===============')
        # now = datetime.now()
        # print(now.strftime("%H:%M:%S"))
        
        # save data in database
        save_data_in_database(type, start_date, 'history')
        print('==================save data ind database===============')
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))
        
        # # export xlsx file
        # export_xlsx_file()
        # print('==================excel export===============')
        # now = datetime.now()
        # print(now.strftime("%H:%M:%S"))
        
    # def run(self):
    #     results = asyncio.run(self.main())
    #     return results