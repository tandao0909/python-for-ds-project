from selenium import webdriver
import re
import numpy as np
import pandas as pd
import threading
from queue import Queue
from time import sleep
from selenium.common.exceptions import TimeoutException
import os

from selenium.webdriver.chrome.options import Options


os.environ['PATH'] = r"/usr/local/bin/"
path = os.getcwd()

#Số trang bắt đầu cào dữ liệu trong từng luồng
num_pages = [470,475,480,485,490]
# Số trang cần phải cào trong từng lường (step của numpages ở trên)
n_iter = 5

url = "https://batdongsan.vn/filter?options=on&gia_tri_tinh_chon=1&priceMin=0&priceMax=400&areaMin=0&areaMax=500&"


def openMultiBrowser(n):
    drivers = []
    for i in range(n):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(8) #Mếu muốn đảm bảo sẽ crawl được thông tin ở trừng trang thì set thời gian cao hơn nhưng bù lại quá trình cào sẽ diễn ra lâu hơn
        drivers.append(driver)
    return drivers


def loadMultiPages(driver,i):
    try:
        print(f"Loading thread")
        driver.get(f"{url}page={i}")
    except TimeoutException:
        print("Timeout loading thread")
        pass

def loadMultiBrowsers(drivers_rx): 
    '''
    Vai trò: Tiến hành chạy đa luồng với danh sách các driver đã khởi tạo
    Arg:
        - drivers_rx: danh sách các driver đã khởi tạo ở hàm openMultiBrowser
    Return: None
    '''
    for i,driver in enumerate(drivers_rx):
        '''
        target - là hàm muốn chạy trong luồng
        args là các đối số cần thiết cho hàm đó - ở đây là driver tương ứng với luồng,
                                                num_pages[i] là số trang bắt đầu cào dữ liệu như đã đề cập trước đó
        '''
        t = threading.Thread(target=loadMultiPages,args=(driver,num_pages[i]))
        t.start()

def get_params(text):
    reg_pattern = {"Area":"Diện tích\s+(\d+)",
                "Bedroom":"Số phòng ngủ\s+(\d+)",
                "Legal":"Pháp lý\s+([^\n]+)",
                'WC':"Số toilet\s+(\d+)",
                'House orientation':"Hướng nhà\n+(.+)",
                "Furniture":"Nội thất\n(.+)",
                "Price":"Mức giá\n+(.+)"}
    params = []
    for name in reg_pattern:
        try:
            params.append(re.search(r"{}".format(reg_pattern[name]),text).group(1))
        except:
            params.append(np.nan)
            
            
    return params

def get_info_post(text):
    reg_pattern = {"Date":"Ngày đăng\n(.*?)\n",
                "Type":"Loại tin\n(.*?)\n",
                "ID":"Mã tin\n(\d+)"}
    
    info = []
    for name in reg_pattern:
        try:
            info.append(re.search(r"{}".format(reg_pattern[name]),text).group(1))
        except:
            info.append(np.nan)
            
    return info


def get_data(driver,start_page):
    '''
    Vai trò: thực hiện cào dữ liệu trong từng luồng
    Arg:
        - driver : driver tương ứng trong từng luồng
        - start_page: số trang bắt đầu cào dữ liệu trong luồng này (ex: 1,5,10,15,20...etc)
    Return: trả về một dataframe là dữ liệu thu thập được sao khi duyệt qua n_page ứng với mỗi luồng
    '''
    report =  pd.DataFrame(columns=['Date','Type','ID','Title','Location1','Location2','Description','Area','Bedrooms','Legal','WC','House orientation','Furniture','Price'])

    for i in range(start_page,start_page+n_iter):
        print(f"------Start crawl page {i}------")
        try:
            # Lấy element là các item trong một page
            print("\t------Getting links------")
            elements = driver.find_elements('xpath','//*[@id="danhmuc"]/div[2]/div[1]/div[2]/a')
            location1 = driver.find_elements('css selector','.card-content .description')
        except:
            continue
        
        # Trích xuất dẫn đến mô tảchi tiết của từng item
        links = [element.get_attribute('href') for element in elements]
        location1 = [item.text for item in location1]
        # Duyệt qua từng item
        n = len(links)
        data = []
        print("\t------Start extracting information------")
        for j in range(n):
            # Mở link dẫn đến item
            try:
                driver.get(links[j])
            except TimeoutException:
                print("Timeout access post's link")
                continue
            # Lấy ra những thông tin cần thiết (Title, Price, Số Phòng ngủ, Số WC, Diện tích, Description...etc)
            try:
                sleep(3)
                tmp = []
                title = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div[2]/h1').text
                location2 = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div[3]').text.split('\n')[0]
                driver.find_element('xpath','//*[@id="myBtn"]').click()
                description = driver.find_element('xpath','//*[@id="more1"]').text
                params = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[3]/div[3]')
                params = get_params(params.text)
                post_info = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[4]/div/div')
                post_info = get_info_post(post_info.text)
                tmp = post_info+[title,location1[j],location2,description]+params
            except:
                print("Error")
                continue
    
            data.append(tmp)
        
        if len(data) > 0:
            # Xếp chồng các phần tử trong list data trước đó để tạo thành ma trận với mỗi hàng là một mẫu trong bộ dữ liệu
            matrix_data = np.vstack([item for item in data]) 
            # Tạo ra data_page là dataframe chứa dữ liệu của một trang và concat vào dataframe report
            data_page = pd.DataFrame(matrix_data,columns=report.columns)
            
            report = pd.concat([report,data_page],axis=0)
            report.set_index(np.arange(len(report)),inplace=True)
            # Sao lưu lại data vào file output.csv tránh trường hợp bị mất dữ liệu trong quá trình cào
            report.to_csv(f'data/page{i}.csv',sep="\t",index=False)
            print(f"------Page{i} - Done!------\n\n")
        # Chuyển sang trang kế tiếp
        try:
            driver.get(f"{url}page={i+1}")
        except TimeoutException:
            pass

    return report


def runInParallel(func,drivers_rx):
    '''
    Vai trò: Tiến hành chạy đa luồng
    Arg:
        -func: hàm để crawl data - ở đây sẽ là get_data
        - drivers_rx : danh sách các driver được khai báo trước đó để tiến hành chạy đa luồng
    Return: trả về một danh sách n dataframe (n là số luồng)
    '''
    # Hàng đợi để lưu trữ kết quả từ hàm get_data
    que = Queue()
    for i,driver in enumerate(drivers_rx):
        '''
        target: hàm sẽ thực hiện việc push các dataframe thu được từ get_data vào hàng đợi q
        args:
            - q = que - hàng đợi đã khai báo trước đó
            - arg1 = driver - driver của luồng thứ i
            - start_page = num_page[i] - số trang bắt đầu cào dữ liệu ứng với luồng thứ i
        '''
        t1 = threading.Thread(target= lambda q,arg1,start_page:q.put(func(arg1,start_page)),args=(que,driver,num_pages[i]))
        t1.start()
    ans = []
    for i in range(len(drivers_rx)):
        try:
            tmp = que.get()
            ans.append(tmp)
        except:
            continue
    print("------Done!------")
    return ans

if __name__ == '__main__':
    driver_r5 = openMultiBrowser(5)
    loadMultiBrowsers(driver_r5)
    sleep(5)
    list_report = runInParallel(get_data,driver_r5)
    df = pd.concat([report for report in list_report],axis=0)
    df.to_csv('raw_data1.csv',sep='\t')