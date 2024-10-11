from bs4 import BeautifulSoup
import requests
from tenacity import retry, wait_fixed, stop_after_attempt
import numpy as np
from time import sleep
import datetime
import pandas as pd
import re
import threading
import os

USE_KEY = ['Diện tích', 'Mức giá', 'Hướng nhà', 'Số phòng ngủ', 'Số toilet', 'Pháp lý', 'Tên bài viết', 'Thông tin mô tả', 'Địa chỉ chung', 'Địa chỉ đường', 'Ngày đăng', 'Mã tin']
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CSV_FOLDER = os.path.join(CURRENT_DIRECTORY, 'csv_files')
LOG_FOLDER = os.path.join(CURRENT_DIRECTORY, 'log_files')
BATCH_SIZE = 20
FROM_PAGE = 1
TO_PAGE = 1
BASE_URL = 'https://batdongsan.vn/filter?options=on&gia_tri_tinh_chon=1&priceMin=0&priceMax=400&areaMin=0&areaMax=500&page='

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

def send_log(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    today_time = datetime.datetime.now().strftime('%Y-%m-%d')
    today_file = os.path.join(LOG_FOLDER, 'log'+today_time+'.txt')
    with open(f'{today_file}', 'a') as f:
        f.write(timestamp + ' ' + message + '\n')

def checkNone(value):
    if value is None:
        return np.nan
    return value.text.strip()

@retry(wait=wait_fixed(5), stop=stop_after_attempt(20))  # Retry after 5 seconds if there is a failure, stop after 20 attempts
def make_request(URL):
    try:
        response = requests.get(URL, timeout=30)  # Increase timeout as needed
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        send_log("Request failed, retrying...")
        return None

def get_links(PAGE_NUMBER):
    URL = BASE_URL + str(PAGE_NUMBER)
    response = make_request(URL)
    if response is None:
        return None, None
    soup = BeautifulSoup(response.text, 'html.parser')
    list_div = soup.find('div', class_='gap-24 d-flex flex-column card-container')
    if list_div is None:
        return None, None
    links = list_div.find_all('a', class_='card-cm')
    address_city = list_div.find_all('div', class_='description')
    return links, address_city

def get_data(URL):
    data_dict = {}
    response = make_request(URL)
    if response is None:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    cols = soup.find_all('div', class_='col')
    for col in cols:
        label = col.find('div', class_ = 'line-label')
        content = col.find('div', class_ = 'line-text')
        if label is not None and content is not None:
            data_dict[label.text.strip()] = content.text.strip()
    title = soup.find('h1')
    data_dict['Tên bài viết'] = checkNone(title)
    desc = soup.find('div', id='more1')
    data_dict['Thông tin mô tả'] = checkNone(desc)
    address = soup.find('div', class_='footer')
    data_dict['Địa chỉ đường'] = checkNone(address)
    footer = soup.find('div', class_='row mat-42').find_all('div', class_='value')
    upload_date = footer[0]
    data_dict['Ngày đăng'] = checkNone(upload_date)
    id_post = footer[2]
    data_dict['Mã tin'] = checkNone(id_post)
    print(data_dict['Mã tin'])
    return data_dict

def extract(START_PAGE, END_PAGE, THREAD_NUMBER=1):
    send_log(f'Extracting from page {START_PAGE} to page {END_PAGE}')
    for i in range(START_PAGE, END_PAGE):
        links, address_city = get_links(i)
        if links is None:
            continue
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d')
        today_file = os.path.join(CSV_FOLDER, 'data'+timestamp+'.tsv')
        if not os.path.exists(today_file):
            header = ""
            for key in USE_KEY:
                header += key + '\t' if key != USE_KEY[-1] else key
            with open(f'{today_file}', 'w') as f:
                f.write(header + '\n')
        with open(f'{today_file}', 'a') as f:
            for j in range(len(links)):
                url = links[j]['href']
                data_dict = get_data(url)
                if data_dict is None:
                    continue
                data_dict['Địa chỉ chung'] = re.sub(r'\s+', ' ', address_city[j].text.strip())
                new_dict = {key: data_dict.get(key, np.nan) for key in USE_KEY}
                new_df = pd.DataFrame(new_dict, index=[0])
                f.write(new_df.to_csv(sep='\t', index=False, header=False))
                sleep(1.5)
        send_log(f"Page {i} done, Thread {THREAD_NUMBER} completed {i - START_PAGE + 1}/{END_PAGE - START_PAGE}")

def extract_with_threading(FROM_PAGE, TO_PAGE, NUMBER_OF_THREADS):
    threads = []

    send_log('Extracting data from batdongsan.vn ...')
    BATCH_SIZE = (TO_PAGE - FROM_PAGE + 1) // NUMBER_OF_THREADS
    for i in range(NUMBER_OF_THREADS):
        start_page = FROM_PAGE + i * BATCH_SIZE
        end_page = FROM_PAGE + (i + 1) * BATCH_SIZE if i != NUMBER_OF_THREADS - 1 else TO_PAGE
        send_log(f'Starting thread {i} to extract data from page {start_page} to page {end_page}')
        thread = threading.Thread(target=extract, args=(start_page, end_page, i))
        threads.append(thread)
        thread.start()
        sleep(1)


    for thread in threads:
        thread.join()

    send_log(f'Done extracting data from page {FROM_PAGE} to page {TO_PAGE} with {NUMBER_OF_THREADS} threads')

if __name__ == '__main__':
    print("Extraction")
    FROM_PAGE = int(input('From page: '))
    TO_PAGE = int(input('To page: '))
    NUMBER_OF_THREADS = int(input('Number of threads: '))
    if NUMBER_OF_THREADS > 1:
        extract_with_threading(FROM_PAGE, TO_PAGE, NUMBER_OF_THREADS)
    else:
        extract(FROM_PAGE, TO_PAGE)
