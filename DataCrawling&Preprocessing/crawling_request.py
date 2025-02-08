import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd
from time import sleep
from concurrent.futures import ThreadPoolExecutor
import time

# URL to crawl data from
url = "https://batdongsan.vn/filter?options=on&gia_tri_tinh_chon=1&priceMin=0&priceMax=400&areaMin=0&areaMax=500&"

# List of starting pages for each thread
num_pages = [1,51,101,151,201,251,301,351,401,451]
# Number of iterations (pages) to crawl per thread
n_iter = 50

def get_params(text):
    """
    Extract parameters from the given text using regular expressions.

    Args:
        text (str): The text to extract parameters from.

    Returns:
        list: A list of extracted parameters (Area, Bedroom, Legal, WC, House orientation, Furniture, Price).
    """
    # Regular expressions pattern for extracting parameters
    reg_pattern = {
        "Area": "Diện tích\s+(\d+)",
        "Bedroom": "Số phòng ngủ\s+(\d+)",
        "Legal": "Pháp lý\s+([^\n]+)",
        'WC': "Số toilet\s+(\d+)",
        'House orientation': "Hướng nhà\n+\s+(.+)",
        "Furniture": "Nội thất\n+\s+(.+)",
        "Price": "Mức giá\n+\s+(.+)"
    }
    # Perform the search for information according to the given pattern, if not found, return np.nan
    params = []
    for name in reg_pattern:
        try:
            params.append(re.search(r"{}".format(reg_pattern[name]), text).group(1))
        except:
            params.append(np.nan)
    return params

def get_data(start_page):
    """
    Crawl data from the website starting from the given page.

    Args:
        start_page (int): The starting page number.

    Returns:
        DataFrame: A DataFrame containing the crawled data from a specific page.
    """
    # Define the structure of the DataFrame
    # Location 1 is taken from the main page post interface, Location 2 is taken from the detailed post
    report = pd.DataFrame(columns=['Date', 'Type', 'ID', 'Title', 'Location1', 'Location2', 'Description', 'Area', 'Bedrooms', 'Legal', 'WC', 'House orientation', 'Furniture', 'Price'])

    # Perform data crawling from start_page to start_page + n_iter
    for i in range(start_page, start_page + n_iter):
        print(f"------Start crawl page {i}------")
        # Get basic information of 25 posts on the interface of page i
        try:
            response = requests.get(f"{url}page={i}")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Select the elements containing the links to the posts
            elements = soup.select('#danhmuc > div:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(2) > a')
            # Extract and clean the location1 information from the selected elements (location 1 includes district and city names)
            location1 = [item.text.replace('\n', '').strip() for item in soup.select('.card-content .description')]
            location1 = [' '.join(item.split()) for item in location1]
        except requests.RequestException as e:
            print(f"Error fetching page {i}: {e}")
            continue
        # Extract the links of the posts from elements
        links = [element['href'] for element in elements]
        n = len(links)
        data = []
        # Crawl data from each post
        for j in range(n):
            try:
                post_response = requests.get(links[j])
                post_response.raise_for_status()
                post_soup = BeautifulSoup(post_response.text, 'html.parser')
                # Extract the title
                title = post_soup.select_one('h1').text
                # Extract the location 2 (street name, ward)
                location2 = post_soup.select_one('.footer').text.strip().split('\n')[0]
                # Extract the description of the post
                description = post_soup.select_one('#more1').text.strip()
                # Extract the params (Area, Bedroom, Legal, WC, House orientation, Furniture, Price) of the post
                params = get_params(post_soup.select_one('.box-characteristics').text)
                # Extract the post information (Date, Type, ID)
                post_info = [item.text.strip() for item in post_soup.select('.row.mat-42 .box-text .col .value')]
                # Concatenate all extracted information into a single list
                tmp = post_info + [title, location1[j], location2, description] + params
                print(f"\tCrawled post {j+1}/{n} on page {i}")
            except requests.RequestException as e:
                print(f"Error fetching post {links[j]}: {e}")
                continue
            except Exception as e:
                print(f"Error extracting data from post {links[j]}: {e}")
                continue
            # Append the extracted information to the data list
            data.append(tmp)
        # If data is not empty, convert it to a DataFrame and save it to a CSV file
        if data:
            # Convert list data of a page to a DataFrame and save it to a CSV file
            matrix_data = np.vstack([item for item in data])
            data_page = pd.DataFrame(matrix_data, columns=report.columns)
            data_page.to_csv(f'data/page{i}.csv', sep="\t", index=False)
            # Concatenate the data of the page to the report
            report = pd.concat([report, data_page], axis=0)
            report.set_index(np.arange(len(report)), inplace=True)
            print(f"------Page{i} - Done!------\n\n")

    return report

if __name__ == '__main__':
    start_time = time.time()
    # Create a ThreadPoolExecutor with 10 threads to crawl data faster
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks to the executor
        futures = [executor.submit(get_data, start_page) for start_page in num_pages]
        # Collect results from the futures
        list_report = [future.result() for future in futures]
    print("------All done!------")
    # Concatenate all results into a single DataFrame
    df = pd.concat(list_report, axis=0)
    # Save the final DataFrame to a CSV file
    df.to_csv('./data/raw_data.csv', sep='\t')
    # Print the total time taken to crawl data
    print(f"Total time: {time.time() - start_time} seconds")
