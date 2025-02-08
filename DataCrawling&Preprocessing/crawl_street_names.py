import requests
from bs4 import BeautifulSoup
import json

def get_street_names(verify_ssl=True):
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
        req = requests.get(link, verify=verify_ssl)
        soup = BeautifulSoup(req.text, 'html.parser')
        if district in ["củ chi", "bình chánh", "hóc môn"]:
            tables = soup.find_all("tbody")
            street_table = tables[1]
            for row in street_table.find_all("tr"):
                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    if i % 2 == 1:
                        street_name = ' '.join(cell.text.strip().lower().split())  # Remove extra spaces
                    if not street_name:  # empty string
                        continue
                    if "đường" in street_name:
                        street_name = street_name.replace("đường", "").strip()
                        if len(street_name) <= 1:  # just 1 character
                            continue
                    street_names[district].append(street_name)
        else:
            table = soup.find("tbody")
            for td in table.find_all("td"):
                street_name = ' '.join(td.text.strip().lower().split())  # Remove extra spaces
                if not street_name or len(street_name) == 1:
                    continue
                if "đường" in street_name:
                    street_name = street_name.replace("đường", "").strip()
                    if len(street_name) == 1:  # just 1 character
                        continue
                street_names[district].append(street_name)

    return street_names

if __name__ == "__main__":
    street_names = get_street_names(verify_ssl=False)
    with open('street_names.json', 'w', encoding='utf-8') as f:
        json.dump(street_names, f, ensure_ascii=False, indent=4)
