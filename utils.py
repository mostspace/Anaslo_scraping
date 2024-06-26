import json
import pytz
import requests
import xlsxwriter
import pathlib
import mysql.connector

import conf

from datetime import datetime
from mysql.connector import errorcode
from bs4 import BeautifulSoup
import time

region_list_data = []
store_list_data = []
store_data_by_date = []
store_sub_data = []

tuple_region_list_data = []
tuple_store_list_data = []
tuple_store_data_by_date = []
tuple_store_sub_data = []

# send request
def send_request(url, request_type, header, param):
    headers = {
        'Content-Type': 'application/json',
        "Accept": "application/json",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    }
    
    response = None
    if request_type == 'get':
        try:
            response = requests.get(url, params=param, headers=headers)
        except:
            return ''
    else:
        try:
            response = requests.post(url, params=param, headers=headers)
        except:
            return ''
    
    if response.status_code == 200:
        return response.text
    else:
        return ''

# get date of previous operation
def get_date_of_previous_operation():
    cnx = None
    date = ''
    try:
        cnx = mysql.connector.connect(host=conf.DB_HOST, user=conf.DB_USER, password=conf.DB_PWD, database=conf.DB_NAME)
        cursor = cnx.cursor()
        query = """SELECT date FROM tbl_scraping_history ORDER BY id DESC LIMIT 1"""
        cursor.execute(query)
        date = cursor.fetchone()
        
        if date is None or len(date) == 0:
            return ''
        
        date = date[0].strftime('%Y-%m-%d')
        prev_date = date.split('-')
        prev_date = datetime(int(prev_date[0]), int(prev_date[1]), int(prev_date[2]))
        return prev_date
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    finally:
        if cnx != None:
            cnx.close()

# convert html to element format
def parse_html_to_element(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup

# get region data from page data
def get_region_data(page_data):
    global tuple_region_list_data
    tuple_region_list_data = []
    parent_elements = page_data.find_all('div', {'class': 'pref_list'})
    parent_element = parent_elements[1]
    region_data = []
    child_elements = parent_element.find_all('a')
    
    for i in range(len(child_elements)):
        if(i == 1):
            data = [(i + 8), child_elements[i]['href'], child_elements[i].text]
            region_data.append(data)
            tuple_region_list_data.append(tuple(data))
    
    global region_list_data
    region_list_data = region_data
    return region_data

# get a list of stores from region data
# def get_list_of_stores():
def get_list_of_stores(region):
    global tuple_store_list_data
    global store_list_data

    tuple_store_list_data = []
    all_store_list = []
    cnt = 0
    
    # for region in region_data:
    response = send_request(region[1], 'get', {}, {})
    page_data = None
    
    if response != '':
        page_data = parse_html_to_element(response)
    else:
        return all_store_list
    
    table_data = page_data.find('div', {'class': 'hall-list-table'})
    table_body = table_data.find('div', {'class': 'table-body'})
    table_rows = table_body.find_all('div', {'class': 'table-row'})
    
    i = 0
    for i in range(len(table_rows)):
        num = (int(region[0]) - 8) * 10000000
        table_data = table_rows[i].find_all('div', {'class': 'table-data-cell'})
        data = [(cnt + i + 1 + num), region[0], table_data[0].find('a')['href'], table_data[0].text, table_data[1].text]
        all_store_list.append(data)
        tuple_store_list_data.append(tuple(data))
    
    region[1] = ''
    cnt += (i + 1)
        
    store_list_data = all_store_list
    return all_store_list

# get store data by date
def get_store_data_by_date(prev_date, start_date, type):
    global store_list_data
    global store_data_by_date
    global tuple_store_data_by_date
    tuple_store_data_by_date = []
    store_list = store_list_data
    
    cnt = 0
    store_data = []
    for store in store_list:
        num = (int(store[1]) - 8) * 10000000
        print(f"cur store data by date => {store[2]}")
        response = send_request(store[2], 'get', {}, {})
    
        page_data = None
        if response != '':
            page_data = parse_html_to_element(response)
        else:
            continue
        
        table_data = page_data.find_all('div', {'class': 'table-row'})

        for i in range(len(table_data)):
            table_cell_data = table_data[i].find_all('div', {'class': 'table-data-cell'})
            if i == 0:
                continue
            
            if type == False:
                data_date = table_cell_data[0].text
                data_date = data_date.split('(')[0]
                data_date = data_date.split('/')
                data_date = datetime(int(data_date[0]), int(data_date[1]), int(data_date[2]))

                if prev_date == '' or data_date == '':
                    break
                
                if data_date <= prev_date:
                    break
                
            if table_cell_data[0].find('a') != None:
                data = [
                    (cnt + i + 1 + num), 
                    store[0], 
                    table_cell_data[0].find('a')['href'],
                    table_cell_data[0].text,
                    table_cell_data[1].text,
                    table_cell_data[2].text,
                    table_cell_data[3].text,
                    table_cell_data[4].text
                ]
                store_data.append(data)
                tuple_store_data_by_date.append(tuple(data))
            else:
                break

        cnt += (i + 1)
        store[2] = ''

        # save_data_in_database(type, '', 'store_data')
        # time.sleep(3)
        # tuple_store_data_by_date = []

    store_data_by_date = store_data
    return store_data_by_date

# get sub data from data by date
def get_store_sub_data_by_date():
    global store_data_by_date
    global tuple_store_sub_data
    tuple_store_sub_data = []
    temp_store_data_by_date = store_data_by_date
    header_type = ["機種名", "台番号", "G数", "差枚", "BB", "RB", "ART", "合成確率", "BB確率", "RB確率", "ART確率"]
    
    cnt = 0
    count = 0
    sub_data = []
    empty_position = []
    for store_data in temp_store_data_by_date:
        num = (int(store_data[1]) / 10000000) * 10000000
        print('start =================================')
        print(store_data[2])
        response = send_request(store_data[2], 'get', {}, {})

        page_data = None
        if response != '':
            page_data = parse_html_to_element(response)
        else:
            continue
        
        print('get page ==============================')
        table = page_data.find('table', {'id': 'all_data_table'})
        table_header = page_data.find('thead')
        header_item = []
        for item in table_header.find_all('th'):
            header_item.append(item.text)
        position = 0
        for i in range(len(header_type)):
            adjusted_index = i - position
            if 0 <= adjusted_index < len(header_item):
                if header_item[adjusted_index] is not None:
                    if header_type[i] != header_item[adjusted_index]:
                        empty_position.append(i)
                        position += 1
                else:
                    empty_position.append(i)
            else:
                empty_position.append(i)
        table_body = table.find('tbody')
        table_row_data = table_body.find_all('tr')
        
        for j in range(len(table_row_data)):
            table_td_data = table_row_data[j].find_all('td')
            data = []
            data.append((cnt + j + 1 + num))
            data.append(store_data[0])
            
            for i in range(len(table_td_data)):
                data.append(table_td_data[i].text)
            length = len(data)
            
            for i in empty_position:
                if((i + 2) < length):
                    data.insert((i + 2), '')
                else:
                    data.append('')
            sub_data.append(data)
            tuple_store_sub_data.append(tuple(data))
        cnt += (j + 1)
        empty_position = []
        store_data[2] = ''
        count += 1
        print(count)
        if(count == 100):
            print(tuple_store_sub_data)
            count = 0
            save_data_in_database(type, '', 'subdata')
            time.sleep(3)
            tuple_store_sub_data = []
    
    global store_sub_data
    store_sub_data = sub_data
    return store_sub_data

# export json file
def export_json_file():
    hour = datetime.now(pytz.timezone('Asia/Tokyo')).hour
    minute = datetime.now(pytz.timezone('Asia/Tokyo')).minute
    seconds = datetime.now(pytz.timezone('Asia/Tokyo')).second

    document_folder = pathlib.Path.home() / "Documents"
    filename = f'Anaslo_data_{hour}_{minute}_{seconds}.json'
    filepath = document_folder / filename
    
    with open(filepath, 'wb') as file:
        total_data = {}
        for region in region_list_data:
            if region[2] not in total_data:
                print(region[2])
                total_data[region[0]] = {'region_name': region[2], 'store_list': [], 'store_data': [], 'sub_data': []}
            for store in store_list_data:
                if store[1] == region[0]:
                    total_data[region[0]]['store_list'].append(store)
                    
                    for store_data in store_data_by_date:
                        if store_data[1] == store[0]:
                            temp = []
                            for i in range(len(store_data)):
                                if i < (len(store_data) - 3):
                                    temp.append(store_data[i + 3])
                            total_data[region[0]]['store_data'].append(temp)
                        
                            print(f"sub data => {len(store_sub_data)}")
                            for sub_data in store_sub_data:
                                if sub_data[1] == store_data[0]:
                                    temp1 = []
                                    for i in range(len(sub_data)):
                                        if i < (len(sub_data) - 2):
                                            temp1.append(sub_data[i + 2])
                                    total_data[region[0]]['sub_data'].append(temp1)
        data = json.dumps(total_data, indent=2)
        file.write(data.encode('utf-8'))
    return

# export txt file
def export_txt_file():
    global region_list_data
    global store_list_data
    global store_data_by_date
    global store_sub_data

    document_folder = pathlib.Path.home() / "Documents"
    filename = f'Anaslo_data_region.txt'
    filepath = document_folder / filename
    
    with open(filepath, 'w') as file:
        for region in region_list_data:
            for i in range(len(region)):
                print(str(region[i]))
                file.write(str(region[i]))
                file.write('\t')
            file.write('\n')
    
    filename = f'Anaslo_data_store_list.txt'
    filepath = document_folder / filename
    with open(filepath, 'wb') as file:
        for store in store_list_data:
            for i in range(len(store)):
                file.write(str(store))
                file.write('\t')
            file.write('\n')
    
    filename = f'Anaslo_data_store_data.txt'
    filepath = document_folder / filename
    with open(filepath, 'wb') as file:
        for store_data in store_data_by_date:
            for i in range(len(store_data)):
                file.write(str(store_data))
                file.write('\t')
            file.write('\n')

    filename = f'Anaslo_data_store_model_data.txt'
    filepath = document_folder / filename
    with open(filepath, 'wb') as file:
        for model_data in store_sub_data:
            for i in range(len(model_data)):
                file.write(str(model_data))
                file.write('\t')
            file.write('\n')


# export excel file
def export_xlsx_file():
    hour = datetime.now(pytz.timezone('Asia/Tokyo')).hour
    minute = datetime.now(pytz.timezone('Asia/Tokyo')).minute
    seconds = datetime.now(pytz.timezone('Asia/Tokyo')).second

    document_folder = pathlib.Path.home() / "Documents"
    filename = f'Anaslo_data_{hour}_{minute}_{seconds}.xlsx'
    filepath = document_folder / filename
    
    wbk = xlsxwriter.Workbook(filepath)
    sheet = wbk.add_worksheet()
    count = 0
    if count >= 1000000:
        wbk.save(filepath)
        return
    
    for region in region_list_data:
        sheet.write(count, 0, region[2])
        count += 1
        for store in store_list_data:
            if store[1] == region[0]:
                sheet.write(count, 0, store[3])
                sheet.write(count, 1, store[4])
                count += 1
                
                for store_data in store_data_by_date:
                    if store_data[1] == store[0]:
                        for i in range(len(store_data)):
                            if i < (len(store_data) - 3):
                                sheet.write(count, i, store_data[i + 3])
                        count += 1
                    
                        print(f"sub data => {count}")
                        for sub_data in store_sub_data:
                            if sub_data[1] == store_data[0]:
                                for i in range(len(sub_data)):
                                    if i < (len(sub_data) - 2):
                                        sheet.write(count, i, str(sub_data[i + 2]))
                                count += 1
    wbk.close()
    return

# save data in database
def save_data_in_database(flag, start_date, save_type):
    cnx = None
    try:
        cnx = mysql.connector.connect(host=conf.DB_HOST, user=conf.DB_USER, password=conf.DB_PWD, database=conf.DB_NAME)
        cursor = cnx.cursor()
        if flag == True:
            cursor.execute("TRUNCATE TABLE tbl_store_list")
            cursor.execute("TRUNCATE TABLE tbl_store_data_by_date")
            cursor.execute("TRUNCATE TABLE tbl_model_data")
        
        if(save_type == 'store_list'):
            print('tbl_store_list')
            query = """INSERT INTO tbl_store_list (id, region_id, url, name, city) VALUES (%s, %s, %s, %s, %s)"""
            cursor.executemany(query, tuple_store_list_data)
            cnx.commit()

        if(save_type == 'store_data'):
            print('tbl_store_data')
            query = """INSERT INTO tbl_store_data_by_date (id, store_id, url, date, total_diff, avg_diff, avg_g_number, winning_rate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(query, tuple_store_data_by_date)
            cnx.commit()
        
        if(save_type == 'subdata'):
            print('tbl_subdata')
            query = """INSERT INTO tbl_model_data (id, store_data_id, model_name, machine_number, g_number, extra_sheet, bb, rb, art, composite_probability, bb_probability, rb_probability, art_probability) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(query, tuple_store_sub_data)
            cnx.commit()
        
        if(save_type == 'history'):
            print('tbl_history')
            query = """INSERT INTO tbl_scraping_history (id, date) VALUES (%s, %s)"""
            cursor.execute(query, (0, start_date))
            cnx.commit()
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    finally:
        print('end ========')
        if cnx != None:
            cnx.close()
