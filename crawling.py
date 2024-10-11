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

path = '/home/tiamo/Documents/code/Python for DS Project'


#Số trang bắt đầu cào dữ liệu trong từng luồng
num_pages = [1,3,5]
# Số trang cần phải cào trong từng lường (step của numpages ở trên)
n_iter = 2

url = "https://batdongsan.vn/ban-nha/"

path = '/home/tiamo/Documents/code/Python for DS Project'

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
        print(f"Loading thread {i}")
        driver.get(f"{url}p{i+2}")
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
    report =  pd.DataFrame(columns=['Date','Type','ID','Title','Location','Description','Area','Bedrooms','Legal','WC','House orientation','Furniture','Price'])

    for i in range(start_page,start_page+n_iter):
        print(f"------Start crawl page {i}------")
        
        try:
            # Lấy ra element để tiến sang trang tiếp theo - sử dụng ở cuối vòng lặp
            next = driver.find_element('xpath','//*[@id="danhmuc"]/div[2]/div[1]/div[2]/div/nav/ul/div/ul/li[15]/a').get_attribute('href')
            # Lấy element là các item trong một page (20 items)
            print("\t------Getting links to 24 items------")
            elements = driver.find_elements('xpath','//*[@id="danhmuc"]/div[2]/div[1]/div[2]/a')
        except:
            continue
        
        # Trích xuất dẫn đến mô tảchi tiết của từng item
        links = [element.get_attribute('href') for element in elements]
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
                sleep(5)
                tmp = []
                title = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div[2]/h1').text
                location = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[2]/div[1]/div[3]').text.split('\n')[0]
                description = driver.find_element('xpath','//*[@id="more"]').text
                params = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[3]/div[3]')
                params = get_params(params.text)
                post_info = driver.find_element('xpath','/html/body/div[2]/div[1]/div[1]/div[4]/div/div')
                post_info = get_info_post(post_info.text)
                tmp = post_info+[title,location,description]+params
            except:
                print("Error")
                continue
    
            data.append(tmp)
        
        # Xếp chồng các phần tử trong list data trước đó để tạo thành ma trận với mỗi hàng là một mẫu trong bộ dữ liệu
        matrix_data = np.vstack([item for item in data]) 
        # Tạo ra data_page là dataframe chứa dữ liệu của một trang và concat vào dataframe report
        data_page = pd.DataFrame(matrix_data,columns=report.columns)
        
        report = pd.concat([report,data_page],axis=0)
        report.set_index(np.arange(len(report)),inplace=True)
        # Sao lưu lại data vào file output.csv tránh trường hợp bị mất dữ liệu trong quá trình cào
        report.to_csv(f'page{i}.csv',sep="\t",index=False)
        print(f"------Page{i} - Done!------\n\n")
        # Chuyển sang trang kế tiếp
        try:
            driver.get(next)
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
    driver_r5 = openMultiBrowser(3)
    loadMultiBrowsers(driver_r5)
    sleep(5)
    list_report = runInParallel(get_data,driver_r5)
    df = pd.concat([report for report in list_report],axis=0)
    df.to_csv('raw_data.csv',sep='\t')
    
    
