import requests
from bs4 import BeautifulSoup
import json

if __name__ == "__main__":
    street_links = [
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-binh-tan-thanh-pho-ho-chi-minh-37336.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-tan-phu-thanh-pho-ho-chi-minh-37335.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-tan-binh-thanh-pho-ho-chi-minh-37334.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-phu-nhuan-thanh-pho-ho-chi-minh-37333.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-go-vap-thanh-pho-ho-chi-minh-37332.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-thu-duc-thanh-pho-ho-chi-minh-37331.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-binh-thanh-thanh-pho-ho-chi-minh-37330.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-12-thanh-pho-ho-chi-minh-37329.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-11-thanh-pho-ho-chi-minh-37328.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-10-thanh-pho-ho-chi-minh-37327.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-9-thanh-pho-ho-chi-minh-37326.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-8-thanh-pho-ho-chi-minh-37325.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-7-thanh-pho-ho-chi-minh-37324.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-6-thanh-pho-ho-chi-minh-37323.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-5-thanh-pho-ho-chi-minh-37322.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-4-thanh-pho-ho-chi-minh-37321.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-3-thanh-pho-ho-chi-minh-37320.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-2-thanh-pho-ho-chi-minh-37319.html",
    "https://nguyenhopphat.vn/danh-sach-ten-duong-tp.hcm/danh-sach-cac-ten-duong-tai-quan-1-thanh-pho-ho-chi-minh-37318.html",
    "https://displaysolution.vn/tin-tuc/danh-sach-nhung-ten-duong-thuoc-huyen-cu-chi-41046.html",
    "https://displaysolution.vn/tin-tuc/danh-sach-nhung-ten-duong-thuoc-huyen-binh-chanh-41049.html",
    "https://displaysolution.vn/tin-tuc/danh-sach-nhung-ten-duong-thuoc-huyen-hoc-mon-34093.html"
    ]

    street_names = {
        "bình tân": [],
        "tân phú": [],
        "tân bình": [],
        "phú nhuận": [],
        "gò vấp": [],
        "thủ đức": [],
        "bình thạnh": [],
        "quận 12": [],
        "quận 11": ["3/2"],
        "quận 10": ["3/2"],
        "quận 9": [],
        "quận 8": [],
        "quận 7": [],
        "quận 6": [],
        "quận 5": [],
        "quận 4": [],
        "quận 3": [],
        "quận 2": [],
        "quận 1": [],
        "củ chi": [],
        "bình chánh": [],
        "hóc môn": []
    }

    for district, link in zip(street_names.keys(), street_links):
        print(f"Crawling {district}...")
        req = requests.get(link)
        soup = BeautifulSoup(req.text, 'html.parser')
        if district in ["củ chi", "bình chánh", "hóc môn"]:
            tables = soup.find_all("tbody")
            table = tables[1]
            tr_tags = table.find_all("tr")
            for tr in tr_tags:
                td_tags = table.find_all("td")
                for i, td in enumerate(td_tags):
                    if i % 2 == 1:
                        tmp = td.text.strip().lower()
                        if tmp == "":  # empty string
                            continue
                        if "đường" in tmp:
                            tmp = tmp.replace("đường", "").strip()
                            if len(tmp) == 1:  # just 1 character
                                continue
                        street_names[district].append(tmp)
        else:
            table = soup.find("tbody")
            td_tags = table.find_all("td")
            for td in td_tags:
                tmp = td.text.strip().lower()
                if tmp == "": # empty string 
                    continue
                if "đường" in tmp:
                    tmp = tmp.replace("đường", "").strip()
                    if len(tmp) == 1: # just 1 character
                        continue
                street_names[district].append(tmp)

    with open('street_names.json', 'w', encoding='utf-8') as f:
        json.dump(street_names, f, ensure_ascii=False, indent=4)