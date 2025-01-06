"""
This script processes and transforms a housing dataset by applying various data cleaning and feature extraction functions.
Modules:
    pandas (pd): For handling DataFrame operations.
    re: For regular expression operations.
    os: For interacting with the operating system.
    json: For handling JSON data.
    crawl_street_names: Custom module to get street names.
Functions:
    process_df_format(df: pd.DataFrame) -> pd.DataFrame:
    process_number(description: str, pattern: str) -> pd.NA:
    process_boolean(description: str, pattern: str) -> bool:
    process_price(price: str) -> float:
    process_bedroom(description: str) -> pd.NA:
    process_bathroom(description: str) -> pd.NA:
    process_nfloor(description: str) -> pd.NA:
    process_car_place(description: str) -> bool:
    process_facade_step1(description: str) -> bool:
    process_facade_step2(description: str) -> bool:
    process_district(text: str) -> str:
        Extract district information from text input.
    process_legal(text: str) -> str:
        Transform invalid value to pd.NA, valid values are ["sổ đỏ/ sổ hồng", "hợp đồng mua bán"].
    insert_so(match):
        Insert "số" between "đường" and "x", where x is a digit.
    insert_so_into_street(address):
        Find and replace "đường x" by "đường số x".
    process_street(address, district, street_names):
    transform(df: pd.DataFrame, to_save=False, OUTPUT_PATH="data/housing.csv") -> pd.DataFrame:
        Apply all process functions to input DataFrame, and drop useless columns.
Usage:
    Run the script directly to process the housing dataset from "9882.csv" and save the transformed data to "data/housing.csv".
"""

import pandas as pd
import re
import os
import json
from crawl_street_names import get_street_names

def process_df_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame by converting column names to snake_case and converting 
    all string values in object columns to lowercase.
    """
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns='Unnamed: 0', axis=1)
    df.columns = df.columns.str.replace(' ', '_').str.lower()
    object_columns = df.select_dtypes(include='object').columns
    df[object_columns] = df[object_columns].apply(lambda col: col.str.lower())
    return df

def process_number(description: str, pattern: str) -> pd.NA:
    """
    Extract the first number found in the string that matches the given pattern.
    """
    if pd.isnull(description):
        return pd.NA
    match = re.search(pattern, description)
    if match:
        return int(re.findall(r"\d+", match.group())[0])
    return pd.NA

def process_boolean(description: str, pattern: str) -> bool:
    """
    Check if the input string matches the given pattern.
    """
    if pd.isnull(description):
        return pd.NA
    return bool(re.search(pattern, description))

def process_price(price: str) -> float:
    """
    Convert a price string to a float value based on the format "x tỷ y triệu" or similar.
    """
    if pd.isnull(price) or "tháng" in price:
        return pd.NA
    numbers = re.findall(r"\d+", price)
    if "tỷ" in price:
        if len(numbers) == 1:
            return float(numbers[0])
        elif len(numbers) == 2:
            return float(numbers[0]) + float(numbers[1]) / 1000
    elif len(numbers) == 1:
        number = float(numbers[0])
        if number <= 500:
            return pd.NA
        return number / 1000
    return pd.NA

def process_bedroom(description: str) -> pd.NA:
    """
    Extract the number of bedrooms from the description string.
    """
    pattern = r"\d+\s?(pn|phòng ngủ|phong ngu|phòng ngu|phong ngủ|phòng ngũ|ngủ)"
    return process_number(description, pattern)

def process_bathroom(description: str) -> pd.NA:
    """
    Extract the number of bathrooms from the description string.
    """
    pattern = r"\d+\s?(wc|toilet|vs|vệ sinh|ve sinh|nhà vệ sinh|nhà vs)"
    return process_number(description, pattern)

def process_nfloor(description: str) -> pd.NA:
    """
    Extract the number of floors from the description string.
    """
    level4 = ["cấp 4", "c4", "cap 4", "cap4"]
    if any(word in description for word in level4):
        return 1
    pattern = r"\d+\s?(lầu|tầng|tấm|tang|lau|tam)"
    return process_number(description, pattern)

def process_car_place(description: str) -> bool:
    """
    Check if there is space for a car based on the description string.
    """
    pattern = r"gara|đỗ ô tô|xe hơi|ô tô tránh|hầm xe|hầm|nhà xe|đỗ|ô tô|ôtô|sân đỗ|hẻm xe hơi|hxh|oto|hẻm xe tải"
    return process_boolean(description, pattern)

def process_facade_step1(description: str) -> bool:
    """
    Check if the property has a facade directly facing the street.
    """
    pattern = r"mặt tiền|mặt phố|mặt đường|mat tien"
    return process_boolean(description, pattern)

def process_facade_step2(description: str) -> bool:
    """
    Check if the property is near a street facade (but not directly on it).
    """
    pattern = r"cách mặt tiền|cách mặt phố|sát mặt tiền|sát mặt phố"
    return process_boolean(description, pattern)

def process_district(text: str) -> str:
    """
    Extract district information from text input.
    """
    if pd.isnull(text):
        return pd.NA
    district = text.split(",")[0].strip()
    return district

def process_legal(text: str) -> str:
    """
    Transform invalid value to pd.NA, valid values are ["sổ đỏ/ sổ hồng", "hợp đồng mua bán"].
    """
    if pd.isnull(text):
        return pd.NA
    valid_cases = ["sổ đỏ/ sổ hồng", "hợp đồng mua bán"]
    return text if text in valid_cases else pd.NA

def insert_so(match):
    return f"đường số {match.group(1)}"

def insert_so_into_street(address):
    return re.sub(r'đường (\d+)', insert_so, address)

def check_chars_ratio(string1, string2):
    splited_string1 = string1.split()
    two_words = len(splited_string1) == 2
    splited_string2 = string2.split()
    prev_index = -1
    for char in splited_string1:
        if char in splited_string2:
            current_index = splited_string2.index(char)
            if current_index < prev_index:
                return 0
            prev_index = current_index
    ratio = len([char for char in splited_string1 if char in splited_string2]) / len(splited_string1)
    return int(ratio) if two_words else ratio

def check_sliding_window(string1, string2):
    """
    Create a sliding window of the same length as string1 and check if string1 matches any window in string2.
    """
    len1, len2 = len(string1), len(string2)
    return any(string2[i:i+len1] == string1 for i in range(len2 - len1 + 1))

def process_street(address, district, street_names):
    """
    Processes the given address to extract the street name.
    """
    if pd.isnull(address):
        return pd.NA
    if "múc giá" in address or "sao chép liên kết" in address:
        return pd.NA
    address = insert_so_into_street(address).split(",")[0]
    first_5_letters_address = " ".join(address.split()[:5])
    if district in street_names:
        best_ratio, return_street = 0, None
        for street in street_names[district]:
            if check_sliding_window(street, first_5_letters_address):
                return street
            ratio = check_chars_ratio(street, first_5_letters_address)
            if ratio > 0.5 and ratio > best_ratio:
                return_street, best_ratio = street, ratio
        return return_street if best_ratio > 0.5 else pd.NA
    return pd.NA

def transform(df: pd.DataFrame, to_save=False, OUTPUT_PATH="data/housing.csv") -> pd.DataFrame:
    """
    Apply all process functions to input DataFrame, and drop useless columns.
    """
    print("Formating data ...")
    df = process_df_format(df)

    processes = [
        (process_price, 'price', 'price'),
        (process_bedroom, 'description', 'new_bedrooms'),
        (process_bathroom, 'description', 'new_bathrooms'),
        (process_bedroom, 'title', 'new_bedrooms2'),
        (process_bathroom, 'title', 'new_bathrooms2'),
        (process_nfloor, 'description', 'n_floors'),
        (process_nfloor, 'title', 'n_floors2'),
        (process_car_place, 'description', 'car_place1'),
        (process_car_place, 'title', 'car_place2'),
        (process_facade_step1, 'description', 'facade1_step1'),
        (process_facade_step2, 'description', 'facade1_step2'),
        (process_facade_step1, 'title', 'facade2_step1'),
        (process_facade_step2, 'title', 'facade2_step2'),
        (process_district, 'location1', 'district'),
        (process_legal, 'legal', 'legal')
    ]

    for func, process_column, new_column in processes:
        try:
            print(f"Processing {new_column}")
            df[new_column] = df[process_column].apply(func)
        except Exception as e:
            print(f"Error in function '{func}' on column '{process_column}': {e}")

    try:
        print("Processing facade")
        df['facade1'] = df['facade1_step1'] & ~df['facade1_step2']
        df['facade2'] = df['facade2_step1'] & ~df['facade2_step2']
        df['facade'] = df['facade1'] | df['facade2']
        print("Processing car_place")
        df['car_place'] = df['car_place1'] | df['car_place2']
    except Exception as e:
        print(f"Error processing 'facade' and 'car_place': {e}")

    df['bedrooms'] = df['bedrooms'].fillna(df['new_bedrooms']).fillna(df['new_bedrooms2'])
    df['wc'] = df['wc'].fillna(df['new_bathrooms']).fillna(df['new_bathrooms2'])
    df['n_floors'] = df['n_floors'].fillna(df['n_floors2'])

    if not os.path.exists('street_names.json'):
        print("street_names.json not found, calling get_street_names")
        street_names = get_street_names(verify_ssl=False)
        with open('street_names.json', 'w', encoding='utf-8') as f:
            json.dump(street_names, f, ensure_ascii=False, indent=4)
    else:
        with open('street_names.json', 'r', encoding='utf-8') as f:
            street_names = json.load(f)
    print("Processing street")
    try:
        df['street'] = df.apply(lambda row: process_street(row['location2'], row['district'], street_names), axis=1)
    except Exception as e:
        print(f"Error when processing 'street': {e}")

    columns_to_use = [
        "id", "price", "area", "bedrooms", "wc", "n_floors", "car_place",
        "house_orientation", "furniture", "facade", "legal", "street",
        "district", "type", "date"
    ]
    df = df[columns_to_use].dropna(subset=["price"]).reset_index(drop=True)
    if to_save:
        df.to_csv(OUTPUT_PATH, sep='\t', index=False)
        print(f"Saved to {OUTPUT_PATH}")
    print("Done!")
    return df

if __name__ == "__main__":
    RAW_DATA_PATH = "9882.csv"
    df = pd.read_csv(RAW_DATA_PATH, sep='\t')
    df = transform(df, to_save=True)
    print(df.head())
    print(f"Transformed data has {len(df)} rows")