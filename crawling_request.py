import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd
from time import sleep
from concurrent.futures import ThreadPoolExecutor
import time

url = "https://batdongsan.vn/filter?options=on&gia_tri_tinh_chon=1&priceMin=0&priceMax=400&areaMin=0&areaMax=500&"

num_pages = [1,51,101,151,201,251,301,351,401,451]
n_iter = 50

def get_params(text):
    reg_pattern = {
        "Area": "Diện tích\s+(\d+)",
        "Bedroom": "Số phòng ngủ\s+(\d+)",
        "Legal": "Pháp lý\s+([^\n]+)",
        'WC': "Số toilet\s+(\d+)",
        'House orientation': "Hướng nhà\n+\s+(.+)",
        "Furniture": "Nội thất\n+\s+(.+)",
        "Price": "Mức giá\n+\s+(.+)"
    }
    params = []
    for name in reg_pattern:
        try:
            params.append(re.search(r"{}".format(reg_pattern[name]), text).group(1))
        except:
            params.append(np.nan)
    return params

def get_data(start_page):
    report = pd.DataFrame(columns=['Date', 'Type', 'ID', 'Title', 'Location1', 'Location2', 'Description', 'Area', 'Bedrooms', 'Legal', 'WC', 'House orientation', 'Furniture', 'Price'])

    for i in range(start_page, start_page + n_iter):
        print(f"------Start crawl page {i}------")
        try:
            response = requests.get(f"{url}page={i}")
            sleep(1)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select('#danhmuc > div:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(2) > a')
            location1 = [item.text.replace('\n', '').strip() for item in soup.select('.card-content .description')]
            location1 = [' '.join(item.split()) for item in location1]
        except requests.RequestException as e:
            print(f"Error fetching page {i}: {e}")
            continue

        links = [element['href'] for element in elements]
        n = len(links)
        data = []
        # print("\t------Start extracting information------")
        for j in range(n):
            try:
                post_response = requests.get(links[j])
                post_response.raise_for_status()
                post_soup = BeautifulSoup(post_response.text, 'html.parser')
                title = post_soup.select_one('h1').text
                location2 = post_soup.select_one('.footer').text.strip().split('\n')[0]

                description = post_soup.select_one('#more1').text.strip()
                params = get_params(post_soup.select_one('.box-characteristics').text)
                post_info = [item.text.strip() for item in post_soup.select('.row.mat-42 .box-text .col .value')]
                tmp = post_info + [title, location1[j], location2, description] + params
                print(f"\tCrawled post {j+1}/{n} on page {i}")
            except requests.RequestException as e:
                print(f"Error fetching post {links[j]}: {e}")
                continue
            except Exception as e:
                print(f"Error extracting data from post {links[j]}: {e}")
                continue

            data.append(tmp)

        if data:
            matrix_data = np.vstack([item for item in data])
            data_page = pd.DataFrame(matrix_data, columns=report.columns)
            report = pd.concat([report, data_page], axis=0)
            report.set_index(np.arange(len(report)), inplace=True)
            report.to_csv(f'data/page{i}.csv', sep="\t", index=False)
            print(f"------Page{i} - Done!------\n\n")

    return report

if __name__ == '__main__':
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_data, start_page) for start_page in num_pages]
        list_report = [future.result() for future in futures]
    print("------All done!------")
    df = pd.concat(list_report, axis=0)
    df.to_csv('raw_data.csv', sep='\t')
    print(f"Total time: {time.time() - start_time} seconds")
