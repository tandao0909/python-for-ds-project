import pandas as pd # for DataFrame
import re # for regular expression
import os
import json
from crawl_street_names import get_street_names

RAW_DATA_PATH = "9882.csv"
OUTPUT_PATH = "housing.csv"

def process_df_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame by converting column names to snake_case and converting 
    all string values in object columns to lowercase.
    
    Parameters:
    df (pd.DataFrame): The DataFrame to process.

    Returns:
    pd.DataFrame: The processed DataFrame with transformed column names and 
                  lowercase object columns.
    """
    if "Unnamed: 0" in df.columns: # drop Unnamed column if it exists
        df = df.drop(columns='Unnamed: 0', axis=1)
    # convert columns name to snake_case style and lower it
    df.columns = df.columns.str.replace(' ', '_').str.lower()
    # lower all rows of object columns
    object_columns = df.select_dtypes(include='object').columns
    df[object_columns] = df[object_columns].apply(lambda col: col.str.lower())
    return df

def process_number(description: str, pattern: str) -> pd.NA:
    """
    Extract the first number found in the string that matches the given pattern.
    
    Parameters:
    description (str): The input string to search in.
    pattern (str): The regular expression pattern to search for.
    
    Returns:
    pd.NA or int: Returns the first matching number as an integer if found,
                  otherwise returns pd.NA.
    """
    if pd.isnull(description): # if input is null return pd.NA
        return pd.NA
    match = re.search(pattern, description)
    if match: 
        return int(re.findall(r"\d+", match.group())[0]) # if match return the number before matched value
    return pd.NA

def process_boolean(description: str, pattern: str) -> bool:
    """
    Check if the input string matches the given pattern.

    Parameters:
    description (str): The input string to search in.
    pattern (str): The regular expression pattern to search for.
    
    Returns:
    bool or pd.NA: Returns True if the pattern matches the input string, 
                   False otherwise. Returns pd.NA if input is null.
    """
    if pd.isnull(description):
        return pd.NA
    return bool(re.search(pattern, description)) # if pattern in description return True, otherwise return False

def process_price(price: str) -> float:
    """
    Convert a price string to a float value based on the format "x tỷ y triệu" or similar.
    
    Parameters:
    price (str): The string describing the price of a house.
    
    Returns:
    float or pd.NA: The float value of the price in billions (tỷ), or pd.NA if the format is invalid.
    """
    if pd.isnull(price): # if input is null return pd.NA
        return pd.NA
    numbers = re.findall(r"\d+", price) # find all digits in price. ex: 12 tỷ 500 triệu -> [12, 5]
    if "tỷ" in price:
        if len(numbers) == 1:
            return float(numbers[0])
        elif len(numbers) == 2:
            return float(numbers[0]) + float(numbers[1]) / 1000  # ex: 12 tỷ 500 triệu = 12.5
    elif len(numbers) == 1:
        return float(numbers[0]) / 1000  # ex: 800 triệu = 0.8 tỷ
    return pd.NA

def process_bedroom(description: str) -> pd.NA:
    """
    Extract the number of bedrooms from the description string.

    Parameters:
    description (str): The input string to search in.

    Returns:
    pd.NA or int: The number of bedrooms, or pd.NA if no match is found.
    """
    pattern = r"\d+\s?(pn|phòng ngủ|phong ngu|phòng ngu|phong ngủ|phòng ngũ|ngủ)"
    return process_number(description, pattern)

def process_bathroom(description: str) -> pd.NA:
    """
    Extract the number of bathrooms from the description string.

    Parameters:
    description (str): The input string to search in.

    Returns:
    pd.NA or int: The number of bathrooms, or pd.NA if no match is found.
    """
    pattern = r"\d+\s?(wc|toilet|vs|vệ sinh|ve sinh|nhà vệ sinh|nhà vs)"
    return process_number(description, pattern)

def process_nfloor(description: str) -> pd.NA:
    """
    Extract the number of floors from the description string.

    Parameters:
    description (str): The input string to search in.

    Returns:
    pd.NA or int: The number of floors, or pd.NA if no match is found.
    """
    pattern = r"\d+\s?(lầu|tầng|tấm|tang|lau|tam)"
    return process_number(description, pattern)

def process_car_place(description: str) -> bool:
    """
    Check if there is space for a car based on the description string.

    Parameters:
    description (str): The input string to search in.

    Returns:
    bool or pd.NA: Returns True if the property has space for a car, False otherwise. 
                   Returns pd.NA if input is null.
    """
    pattern = r"gara|đỗ ô tô|xe hơi|ô tô tránh|hầm xe|hầm|nhà xe|đỗ|ô tô|ôtô|sân đỗ|hẻm xe hơi|hxh|oto|hẻm xe tải"
    return process_boolean(description, pattern)

def process_facade_step1(description: str) -> bool:
    """
    Check if the property has a facade directly facing the street.

    Parameters:
    description (str): The input string to search in.

    Returns:
    bool or pd.NA: Returns True if the property has a facade facing the street, 
                   False otherwise. Returns pd.NA if input is null.
    """
    pattern = r"mặt tiền|mặt phố|mặt đường|mat tien"
    return process_boolean(description, pattern)

def process_facade_step2(description: str) -> bool:
    """
    Check if the property is near a street facade (but not directly on it).

    Parameters:
    description (str): The input string to search in.

    Returns:
    bool or pd.NA: Returns True if the property is near a street facade, 
                   False otherwise. Returns pd.NA if input is null.
    """
    pattern = r"cách mặt tiền|cách mặt phố|sát mặt tiền|sát mặt phố"
    return process_boolean(description, pattern)

def process_district(text: str) -> str:
    """
    Extract district information from text input, the text will has format like: "Quận x , Hồ Chí Minh".
    Then this function will split the text by delimiter "," after that get the first element and remove 
    " " at last string's position

    Parameters:
    text (str): The input string to be extracted.

    Returns:
    string or pd.NA: Returns the extracted district if text is not null,
                     Returns pd.NA if input is null.
    """
    if pd.isnull(text):
        return pd.NA
    district = text.split(",")[0]
    if district[-1] == " ":
        district = district[:-1] # remove last space
    return district

def process_legal(text: str) -> str:
    """
    Transform invalid value to pd.NA, valid values is ["sổ đỏ/ sổ hồng", "hợp đồng mua bán"]. If input text not in this list
    return pd.NA

    Parameters:
    text (str): The input string to be checked.

    Returns:
    string or pd.NA: Returns the text if it is valid,
                     Returns pd.NA if the input is null or the text is invalid.
    """
    if pd.isnull(text):
        return pd.NA
    valid_case = ["sổ đỏ/ sổ hồng", "hợp đồng mua bán"]
    if text != valid_case[0] and text != valid_case[1]:
        return pd.NA
    else:
        return text


def insert_so(match): # Insert "số" between "đường" and "x", x is (0, 1, 2, ... 9)
    return f"đường số {match.group(1)}"


def insert_so_into_street(address):
    # Find and replace "đường x" by "đường số x"
    return re.sub(r'đường (\d+)', insert_so, address)

def process_street(address, district, street_names):
    """
    Processes the given address to extract the street name.

    Parameters:
        address (str): The full address string.
        district (str): The district name to check within the street_names dictionary.
        street_names (dict): A dictionary where keys are district names and values are lists of street names.

    Returns:
        str or pd.NA: The extracted street name if found, otherwise pd.NA if the address is null or contains certain keywords.
    """

    test_case = ["quận", "huyện", "xã", "phường", "thành phố", "tphcm", district, "mức giá", "dự án", "hồ chí minh"]
    if pd.isnull(address):
        return pd.NA
    else:
        address = insert_so_into_street(address)

    flag = 0
    # Check if district is in street_names dictionary
    if district in street_names:
        for street in street_names[district]:
            if street in address:
                return street
    if flag == 0:  # still can't find
        street = address.split(",")[0]
        for word in test_case:
            if word in street:
                return pd.NA

    return street

def transform(df: pd.DataFrame, to_save = False, OUTPUT_PATH="data/housing.csv") -> pd.DataFrame:
    """
    Apply all process function to input DataFrame, and drop useless column.

    Parameters:
    df (pd.DataFrame): The input DataFrame to be transformed.

    Returns:
    pd.DataFrame: Returns transformed DataFrame.
    """
    print("Formating data ...")
    df = process_df_format(df)

    # make a list contains functions, columns to be processed and new columns ill be called
    # format: (process_function, process_column, new_column)
    processes = [
        (process_price, 'price', 'price'),
        (process_bedroom, 'description', 'new_bedrooms'),
        (process_bathroom, 'description', 'new_bathrooms'),
        (process_nfloor, 'description', 'n_floors'),
        (process_car_place, 'description', 'car_place'),
        (process_facade_step1, 'description', 'facade_step1'),
        (process_facade_step2, 'description', 'facade_step2'),
        (process_district, 'location1', 'district'),
        (process_legal, 'legal', 'legal')
    ]
    # loop through processes list and apply
    for func, process_column, new_column in processes:
        try:
            print(f"Processing {new_column}")
            df[new_column] = df[process_column].apply(func)
        except Exception as e:
            print(f"Error in function '{func}' on column '{process_column}': {e}")

    # make facade column
    try:
        print("Processing facade")
        df['facade'] = (df['facade_step1'] == True) & (df['facade_step2'] == False)
    except Exception as e:
        print(f"Error calculating 'facade': {e}")

    df['bedrooms'] = df['bedrooms'].fillna(df['new_bedrooms'])
    df['wc'] = df['wc'].fillna(df['new_bathrooms'])

    # process street
    if not os.path.exists('street_names.json'): # check if json file is existed
        print("street_names.json not found, calling get_street_names")
        street_names = get_street_names()
        with open('street_names.json', 'w', encoding='utf-8') as f:
            json.dump(street_names, f, ensure_ascii=False, indent=4)
    else:
        with open('street_names.json', 'r', encoding='utf-8') as f:
            street_names = json.load(f)
    print("Processing street")
    df['street'] = df.apply(lambda row: process_street(row['location2'], row['district'], street_names), axis=1)

    columns_to_use = [
        "id",
        "price",
        "area",
        "bedrooms",
        "wc",
        "n_floors",
        "car_place",
        "house_orientation",
        "furniture",
        "facade",
        "legal",
        "street",
        "district",
        "type",
        "date"
    ]
    df = df[columns_to_use]
    if to_save:
        df.to_csv(OUTPUT_PATH, sep='\t', index=False)
        print(f"Saved to {OUTPUT_PATH}")
    print("Done!")
    return df


if __name__ == "__main__":
    df = pd.read_csv(RAW_DATA_PATH, sep='\t')
    df = transform(df, to_save=True)
    print(df.head())
    print(f"Transformed data has {len(df)} rows")