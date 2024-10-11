import pandas as pd
import re

def process_number(description, pattern):
    if pd.isnull(description):
        return pd.NA
    match = re.search(pattern, description)
    if match:
        return sum([float(num) for num in re.findall(r"\d+", match.group())])
    return pd.NA

def process_boolean(description, pattern):
    if pd.isnull(description):
        return pd.NA
    return bool(re.search(pattern, description))

def process_price(price):
    if pd.isnull(price):
        return pd.NA
    numbers = re.findall(r"\d+", price)
    if "tỷ" in price:
        if len(numbers) == 1:
            return float(numbers[0])
        elif len(numbers) == 2:
            return float(numbers[0]) + float(numbers[1])/1000
    elif len(numbers) == 1:
        return float(numbers[0]) / 1000  # Dành cho trường hợp giá trị dưới 1 tỷ
    return pd.NA

def process_bedroom(description):
    pattern = r"\d+\s?(pn|phòng ngủ|phong ngu|phòng ngu|phong ngủ|phòng ngũ|ngủ)"
    return process_number(description, pattern)

def process_bathroom(description):
    pattern = r"\d+\s?(wc|toilet|vs|vệ sinh|ve sinh)"
    return process_number(description, pattern)

def process_nfloor(description):
    pattern = r"\d+\s?(lầu|tầng|tấm)"
    return process_number(description, pattern)

def process_rentable(description):
    pattern = r"triệu/tháng|tr/tháng|dòng tiền|đang cho thuê|doanh thu"
    return process_boolean(description, pattern)

def process_car_place(description):
    pattern = r"gara|đỗ ô tô|xe hơi|ô tô tránh|hầm xe|hầm|nhà xe|đỗ|ô tô|ôtô|sân đỗ|hẻm xe hơi|hxh|oto|hẻm xe tải"
    return process_boolean(description, pattern)

def process_facade_step1(description):
    pattern = r"mặt tiền|mặt phố|mặt đường"
    return process_boolean(description, pattern)

def process_facade_step2(description):
    pattern = r"cách mặt tiền|cách mặt phố|sát mặt tiền"
    return process_boolean(description, pattern)



path = "data/raw_data.csv"
df = pd.read_csv(path, sep='\t')

# TASK
    # drop unnamed -> x
    # lower column names and join with _ -> x
    # process price -> x
    # bedroom pattern -> x
    # bathroom pattern -> x
    # n_floor pattern -> x
    # car_place -> x
    # rentable -> x
    # facade -> x
    # get street, district ->
    # coordinator ->

df = df.drop(columns='Unnamed: 0', axis=1)
transfrom_column = lambda col: "_".join(col.split()).lower()
df.columns = [transfrom_column(col) for col in df.columns]

# lower content
object_columns = df.select_dtypes(include='object').columns.tolist()
lower_lambda = lambda content: content.lower() if pd.notnull(content) else content

for col in object_columns:
    df[col] = df[col].apply(lower_lambda)

df['price'] = df['price'].apply(process_price)
df['new_bedrooms'] = df['description'].apply(process_bedroom)
df['new_bathrooms'] = df['description'].apply(process_bathroom)
df['n_floors'] = df['description'].apply(process_nfloor)
df['rentable'] = df['description'].apply(process_rentable)
df['car_place'] = df['description'].apply(process_car_place)
facade_step1 = df['description'].apply(process_facade_step1)
facade_step2 = df['description'].apply(process_facade_step2)
df['facade'] = (facade_step1 == True) & (facade_step2 == False)

# df['bedrooms'] = df['bedrooms'].fillna(df['new_bedrooms'])
# df['wc'] = df['wc'].fillna(df['new_bathrooms'])

# columns_to_drop = ['new_bedrooms', 'new_bathrooms']
# df = df.drop(columns=columns_to_drop, axis=1)

def test_with_description(df, columns):
    print(f"There are {len(df)} instances!")
    start = int(input("Start from: "))
    for i in range(start, len(df)):
        print(f"-------{i}-------")
        des = df['description'][i]
        print(des)
        print("-"*50)
        for col in columns:
            print(f"{col}: {df[col][i]}")
        next_instance = input("Complete?")
        if next_instance == "n":
            break
        print("\n"*20)

test_columns = ['bedrooms', 'new_bedrooms', 'wc', 'new_bathrooms', 'n_floors', 'rentable', 'car_place', 'facade']
test_with_description(df, columns=test_columns)