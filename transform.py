import pandas as pd # for DataFrame
import re # for regular expression
from dotenv import load_dotenv # for load environment variables
from openai import OpenAI 
import os

RAW_DATA_PATH = "raw_data.csv"
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

def process_street(address):
    """
    Extracts the street name from a given address string using OpenAI's GPT model.
    This function processes an address string to extract only the street name, excluding house numbers, wards, districts, and cities. It uses OpenAI's GPT model to perform the extraction based on specific rules.
    
    Parameters:
    address (str): The address string to be processed.
    
    Returns:
    str or None: The extracted street name, or None if the address does not contain a street name or contains disallowed content.
    """

    if pd.isnull(address):
        return pd.NA
        
    env_openai_key = os.getenv("OPENAI_API_KEY") # get API_KEY

    system_input = """
    Hãy đóng vai là một người phân tích dữ liệu chuyên nghiệp và hoàn thành các yêu cầu sau của tôi. 

    Tôi sẽ đưa cho bạn một chuỗi chứa nội dung có thể về địa chỉ, nhiệm vụ của bạn là lấy duy nhất tên đường trong địa chỉ đó (không bao gồm số nhà, phường, quận, thành phố). Sẽ có những yêu cầu cụ thể sau: 
    - Đường có thể có số, ví dụ "đường số 8", thì bạn phải trả về "đường số 8".
    - Một vài chuỗi sẽ có số nhà, bạn cần loại bỏ, ví dụ "1928 đường phan văn trị" hoặc "1928 phan văn trị" thì trả về "đường phan văn trị"
    - Chuỗi chỉ có thông tin phường, quận, thành phố mà không có tên đường thì trả về None
    - Chuỗi không đề cập gì hết thì trả về None
    - Chuỗi chứa từ "mức giá" thì trả về None

    Trả về đoạn chuỗi duy nhất thể hiện tên đường, không giải thích gì thêm"""

    user_input = f"Đoạn chuỗi là: {address}"
    
    client = OpenAI(api_key = env_openai_key)

    completion = client.chat.completions.create(
        model = "gpt-4o-mini",
        temperature = 0.2, # precision > creation
        max_tokens = 15, # for about 10 words
        n=1, # number of answers
        messages = [
            {
                "role": "system",
                "content": system_input
            },
            {
                "role": "user",
                "content":user_input
            }
        ]
    )
    
    if completion.choices:
        extracted_street = completion.choices[0].message['content']
        return extracted_street.strip() or None  # Return None if empty string
    return None  # Return None if no choices available

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all process function to input DataFrame, and drop useless column.

    Parameters:
    df (pd.DataFrame): The input DataFrame to be transformed.

    Returns:
    pd.DataFrame: Returns transformed DataFrame.
    """
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
            df[new_column] = df[process_column].apply(func)
        except Exception as e:
            print(f"Error in function '{func}' on column '{process_column}': {e}")

    # make facade column
    try:
        df['facade'] = (df['facade_step1'] == True) & (df['facade_step2'] == False)
    except Exception as e:
        print(f"Error calculating 'facade': {e}")

    df['bedrooms'] = df['bedrooms'].fillna(df['new_bedrooms'])
    df['wc'] = df['wc'].fillna(df['new_bathrooms'])

    # create tmp column
    df['street'] = pd.NA

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
    return df


if __name__ == "__main__":
    load_dotenv()
    df = pd.read_csv(RAW_DATA_PATH, sep='\t')
    df = transform(df)
    print(df.head())
    print(df.columns)