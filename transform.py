import pandas as pd
import re
import os

RAW_DATA_PATH = "data/raw_data.csv"
OUTPUT_PATH = "data/housing.csv"

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
    pattern = r"\d+\s?(wc|toilet|vs|vệ sinh|ve sinh)"
    return process_number(description, pattern)

def process_nfloor(description: str) -> pd.NA:
    """
    Extract the number of floors from the description string.

    Parameters:
    description (str): The input string to search in.

    Returns:
    pd.NA or int: The number of floors, or pd.NA if no match is found.
    """
    pattern = r"\d+\s?(lầu|tầng|tấm)"
    return process_number(description, pattern)

def process_rentable(description: str) -> bool:
    """
    Check if the property is rentable based on the description string.

    Parameters:
    description (str): The input string to search in.

    Returns:
    bool or pd.NA: Returns True if the property is rentable (matches certain keywords), 
                   False otherwise. Returns pd.NA if input is null.
    """
    pattern = r"triệu/tháng|tr/tháng|dòng tiền|đang cho thuê|doanh thu"
    return process_boolean(description, pattern)

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
    pattern = r"mặt tiền|mặt phố|mặt đường"
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
    pattern = r"cách mặt tiền|cách mặt phố|sát mặt tiền"
    return process_boolean(description, pattern)


if __name__ == "__main__":
    pass
