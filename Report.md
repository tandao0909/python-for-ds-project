# Table of contents

- [Table of contents](#table-of-contents)
- [I. Data Crawling and Preprocessing](#i-data-crawling-and-preprocessing)
  - [Chuyển đổi dữ liệu](#chuyển-đổi-dữ-liệu)
    - [Mục tiêu](#mục-tiêu)
    - [Xử lý định dạng của Data Frame](#xử-lý-định-dạng-của-data-frame)
    - [Trích xuất dữ liệu từ cột `Description` và `Title`](#trích-xuất-dữ-liệu-từ-cột-description-và-title)
      - [Tổng quan, ý tưởng](#tổng-quan-ý-tưởng)
      - [Xử lý các dữ liệu số](#xử-lý-các-dữ-liệu-số)
      - [Tạo ra các cột dữ liệu mới hữu ích cho bài toán](#tạo-ra-các-cột-dữ-liệu-mới-hữu-ích-cho-bài-toán)
- [II. EDA và Feature Engineering](#ii-eda-và-feature-engineering)
  - [3 Xử lý và làm sạch dữ liệu](#3-xử-lý-và-làm-sạch-dữ-liệu)
    - [3.1. `DataCleaner` class](#31-datacleaner-class)
      - [3.1.1. Chức năng chính của `DataCleaner`](#311-chức-năng-chính-của-datacleaner)
      - [3.1.2. Các phương thức chính của `DataCleaner`](#312-các-phương-thức-chính-của-datacleaner)
    - [3.2. Các hàm khác](#32-các-hàm-khác)

# I. Data Crawling and Preprocessing

## Chuyển đổi dữ liệu

### Mục tiêu

Sau khi mà cào dữ liệu từ web xong, chúng tôi tiến hành chuyển hóa dữ liệu thô thế này:

| Unnamed: 0 | Date       | Type       | ID     | Title                                         | Location1          | Location2                       | Description                                   | Area | Bedrooms | Legal          | WC   | House orientation | Furniture | Price         |
|------------|------------|------------|--------|-----------------------------------------------|--------------------|---------------------------------|-----------------------------------------------|------|----------|----------------|------|-------------------|-----------|---------------|
| 2          | 22/07/2024 | Tin Thường | 115827 | Bán nhà 2.6 tỷ Lý Thường Kiệt Q10, NHÀ ĐẸP 3 Tầng | Quận 10, Hồ Chí Minh | Đường Lý Thường Kiệt, 14       | + Kết cấu: Nhà 3 tầng, 3WC, có thể ở ngay.   | 16   | 4.0      | Sổ đỏ/ Sổ hồng | 3.0  | NaN               | NaN       | 2 tỷ 600 triệu |
| 3          | 22/07/2024 | Tin Thường | 115833 | Nhà Quận 6 Chỉ 3 Tỷ - DTSD >150m² - 5 TẦNG BTC | Quận 6, Hồ Chí Minh | Phường 14, Quận 6, Hồ Chí Minh | Nhà Quận 6 Chỉ 3 Tỷ - DTSD >150m² - 5 TẦNG BTC | 32   | 4.0      | Sổ đỏ/ Sổ hồng | NaN  | NaN               | NaN       | 3 tỷ          |
| 4          | 22/07/2024 | Tin Thường | 115834 | Bán nhà HẺM XE HƠI TRÁNH TÂN HOÁ, chỉ 4.6 TỶ,  | Quận 6, Hồ Chí Minh | Đường Tân Hóa, 10              | Bán nhà HẺM XE HƠI TRÁNH TÂN HOÁ, chỉ 4.6 TỶ, | 38   | NaN      | Sổ đỏ/ Sổ hồng | 4.0  | NaN               | NaN       | 4 tỷ 600 triệu |


Thành một dữ liệu sạch, sử dụng tốt như thế này:

| id     | price | area | bedrooms | wc   | n_floors | car_place | house_orientation | furniture | facade | legal            | street           | district | type        | date       |
|--------|-------|------|----------|------|----------|-----------|-------------------|-----------|--------|------------------|------------------|----------|-------------|------------|
| 115827 | 2.6   | 16   | 4.0      | 3.0  | 3.0      | False     | NaN               | NaN       | False  | sổ đỏ/ sổ hồng   | lý thường kiệt   | quận 10  | tin thường  | 22/07/2024 |
| 115833 | 3.0   | 32   | 4.0      | NaN  | 5.0      | True      | NaN               | NaN       | False  | sổ đỏ/ sổ hồng   | NaN              | quận 6   | tin thường  | 22/07/2024 |
| 115834 | 4.6   | 38   | 3.0      | 4.0  | 3.0      | True      | NaN               | NaN       | False  | sổ đỏ/ sổ hồng   | tân hóa          | quận 6   | tin thường  | 22/07/2024 |

### Xử lý định dạng của Data Frame

Đầu tiên ta đập vào mắt ta là một cột vô dụng mang tên `Unnamed: 0`, nó là một cột index dư thừa, nên sẽ được loại bỏ ngay trong bước đầu tiên. Sau đó thì ta tiến hành xử lý chuẩn hóa tên các cột trong Data Frame, đưa các tên về chữ thường và nếu có 2 từ trở lên sẽ được nối với nhau bằng `_`. Hơn nữa, với mỗi cột ta đều chuẩn hóa dữ liệu không phải số thành chữ thường hết. Tất cả các bước sau được gói gọn trong hàm:

```python
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
```

### Trích xuất dữ liệu từ cột `Description` và `Title`

#### Tổng quan, ý tưởng

Đối với bài toán hồi quy dự đoán giá nhà dựa vào các đặc trưng phổ biến như *diện tích, số phòng ngủ, số phòng tắm, số tầng,...* nhưng trong bộ dữ liệu thô lại thiếu đi quá nhiều do tính chất của trang web. Một vài post sẽ cho người đăng viết mô tả về căn nhà (trong đó có thể gồm các thông tin trên), nhưng người dùng lại không hề nhập tay vào ô *số phòng ngủ, số toilet, ...*. Từ đó dẫn tới việc thiếu đi dữ liệu trong quá trình cào.

Ta quan sát một số ví dụ:

| Unnamed: 0 | Date       | Type       | ID     | Title                                         | Location1          | Location2                       | Description                                   | Area | Bedrooms | Legal          | WC   | House orientation | Furniture | Price         |
|------------|------------|------------|--------|-----------------------------------------------|--------------------|---------------------------------|-----------------------------------------------|------|----------|----------------|------|-------------------|-----------|---------------|
| 4          | 22/07/2024 | Tin Thường | 115834 | Bán nhà HẺM XE HƠI TRÁNH TÂN HOÁ, chỉ 4.6 TỶ,  | Quận 6, Hồ Chí Minh | Đường Tân Hóa, 10              | Bán nhà HẺM XE HƠI TRÁNH TÂN HOÁ, chỉ 4.6 TỶ, | 38   | NaN      | Sổ đỏ/ Sổ hồng | 4.0  | NaN               | NaN       | 4 tỷ 600 triệu |

Ta thấy cột `Bedrooms` là NaN nhưng hãy cùng quan sát phần `Description` của dữ liệu này:

```
Bán nhà HẺM XE HƠI TRÁNH TÂN HOÁ, chỉ 4.6 TỶ, KHU AN NINH, YÊN TĨNH, DÂN TRÍ CAO

- Diện tích : 3.95mx9.5m

-Kết cấu 3 tầng với 3 PN , 3WC.

-Hẻm nhựa 6m xe hơi tránh, thông qua Đặng Nguyên Cẩn

Ms Tuyền 0909.738.688 - Zalo 24/24 - Tư vấn pháp lý - Hỗ trợ miễn phí
```

Ta tìm được thông tin "3 PN" trong phần mô tả này, nên từ đó ta cố gắng trích xuất chúng và giảm thiểu số lượng dữ liệu NaN nhất có thể. Chính vì vậy dữ liệu sau khi xử lý mới có số phòng ngủ là 3:

| id     | price | area | bedrooms | wc   | n_floors | car_place | house_orientation | furniture | facade | legal            | street           | district | type        | date       |
|--------|-------|------|----------|------|----------|-----------|-------------------|-----------|--------|------------------|------------------|----------|-------------|------------|
| 115834 | 4.6   | 38   | 3.0      | 4.0  | 3.0      | True      | NaN               | NaN       | False  | sổ đỏ/ sổ hồng   | tân hóa          | quận 6   | tin thường  | 22/07/2024 |

Trước hết ta cần hiểu được một cách tổng quan về **Regex**:

**Regex (Regular Expressions)** là một công cụ mạnh mẽ dùng để tìm kiếm, khớp mẫu (pattern matching), và xử lý chuỗi văn bản. Regex thường được sử dụng trong xử lý dữ liệu, kiểm tra chuỗi, và trích xuất thông tin từ dữ liệu không cấu trúc.

Ở phần sau, ta sẽ áp dụng toàn bộ phương pháp để trích xuất thông tin từ cả `Description` và `Title`.

#### Xử lý các dữ liệu số

Ta cần xem qua hai hàm phụ trợ chính trong việc trích xuất này là hàm `process_number` và `process_boolean` trong đó:
- `process_number` được sử dụng để tìm kiếm số đầu tiên phù hợp với mẫu regex. Đầu tiên nó kiểm tra nếu chuỗi đầu vào là dữ liệu khuyết nó sẽ trả về khuyết luôn. Sau đó, tìm kiếm mẫu regex trong chuỗi mô tả, nếu có trả về số đầu tiên.
    ```python
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
    ```
- `process_boolean` xác định xem một chuỗi mô tả có chứa mẫu regex cụ thể hay không. Tương tự cũng sẽ có bước kiểm tra dữ liệu khuyết. Sau đó, trả về `True` nếu có sự tồn tại của mẫu regex trong chuỗi, ngược lại trả về `False`.
    ```python
    def process_boolean(description: str, pattern: str) -> bool:
    """
    Check if the input string matches the given pattern.
    """
    if pd.isnull(description):
        return pd.NA
    return bool(re.search(pattern, description))
    ```

Từ đó các hàm xử lý dữ liệu khuyết sẽ có một "workflow" tương tự nhau như sau: *thiết kế regex pattern* $\to$ *tìm kiếm* $\to$ *điền vào dữ liệu khuyết*.

1. Xử lý số phòng ngủ

    Hàm chính của chúng ta là `process_bedroom`, trong đó regex pattern được thiết kế để bắt gặp được các trường hợp phổ biến đã được ta kiểm tra bằng thực nghiệm với bộ dữ liệu thô như sau:
    - 2pn
    - 3 phòng ngủ
    - 5 ngủ
    - ...

    Vì là tiếng Việt phong phú, nên các ví dụ trên còn có thể viết dưới dạng không dấu nên cuối cùng regex pattern mà ta thiết kế cho trường hợp này sẽ là như sau:

    ```python
    pattern = r"\d+\s?(pn|phòng ngủ|phong ngu|phòng ngu|phong ngủ|phòng ngũ|ngủ)"
    ```

2. Xử lý số nhà vệ sinh

    Tương tự với cách làm việc như trên, hàm chính cho việc này sẽ là `process_bathroom`, và các trường hợp phổ biến trong dữ liệu thô là:

    - 2wc
    - 3 toilet
    - 1 vệ sinh
    - ...

    Từ đó ta có regex pattern sau cho trường hợp này là:

    ```python
    pattern = r"\d+\s?(wc|toilet|vs|vệ sinh|ve sinh|nhà vệ sinh|nhà vs)"
    ```

3. Xử lý số tầng

    Số tầng là theo chúng tôi nghĩ là một đặc trưng rất quan trọng trong bài toán hồi quy tiên đoán giá nhà này, và trên web không hề có thuộc tính này. Nhưng may mắn thay, trong phần mô tả các người đăng rất hay mô tả đặc điểm này, nên chúng tôi cũng cố gắng sử dụng Regex để trích xuất được.

    Xét ví dụ đã thấy ở trên:

    ```
    Bán nhà HẺM XE HƠI TRÁNH TÂN HOÁ, chỉ 4.6 TỶ, KHU AN NINH, YÊN TĨNH, DÂN TRÍ CAO

    - Diện tích : 3.95mx9.5m

    -Kết cấu 3 tầng với 3 PN , 3WC.

    -Hẻm nhựa 6m xe hơi tránh, thông qua Đặng Nguyên Cẩn

    Ms Tuyền 0909.738.688 - Zalo 24/24 - Tư vấn pháp lý - Hỗ trợ miễn phí
    ```

    Ta rõ ràng biết được rằng số tầng là 3 và thông qua kiểm tra thực nghiệm, chúng tôi cũng thấy được cách mô tả phổ biến là:

    - 2 lầu
    - 3 tầng
    - 4 tấm
    - ...

    Vì vậy để bao quát được các mẫu đó, chúng tôi đã thiết kế regex pattern cho trường hợp này như sau:

    ```python
    pattern = r"\d+\s?(lầu|tầng|tấm|tang|lau|tam)"
    ```

    Ngoài ra, chúng tôi thấy được có nhiều phần mô tả không đề cập tới vấn đề số tầng, nhưng lại có một mô tả về căn nhà là "nhà cấp 4", mà đó nghĩa là nhà 1 tầng. Nên chúng tôi thiết kế một mảng các từ có thể là mô tả nhà cấp 4 như sau:

    ```python
    level4 = ["cấp 4", "c4", "cap 4", "cap4"]
    ```

    Bất cứ từ nào nằm trong phần mô tả thì sẽ trả về số tầng là 1 ngay.

4. Xử lý mức giá

    Ta xem qua hàm `process_price` được thiết kế để xử lý và chuẩn hóa dữ liệu giá bất động sản từ chuỗi mô tả dạng tự do sang dạng số thực.

    ```python
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
    ```

    Hàm này chủ yếu tập trung vào việc trích xuất giá trị từ các định dạng giá phổ biến như:

    - "2 tỷ 500 triệu"
    - "3 tỷ"
    - "400 triệu"
    - ...

    **Cách hoạt động:** Đầu tiên, kiểm tra các giá trị NaN hay các giá trị rác không phải mô tả về mức giá. Tiếp theo, sử dụng regex `re.findall(r"\d+", price)` để trích xuất tất cả các số trong chuỗi. Hàm kiểm tra các từ khóa quan trọng như "tỷ" và "triệu" để xử lý giá theo hai trường hợp chính:

    - **Trường hợp 1:** Giá trị chứa từ "tỷ"

        a) Cấu trúc phổ biến:
        - x tỷ: Chỉ có số nguyên tỷ (vd: "3 tỷ").
        - x tỷ y triệu: Bao gồm cả tỷ và triệu (vd: "2 tỷ 500 triệu").

        b) Xử lý:
        - Nếu chỉ có x tỷ, giá trị được chuyển đổi trực tiếp thành float từ số nguyên tỷ.
        - Nếu có cả x tỷ và y triệu, giá trị được tính bằng công thức:
        ```python
        float(numbers[0]) + float(numbers[1]) / 1000
        ```
            (1 triệu = 0.001 tỷ).
    - **Trường hợp 2:** Giá trị không chứa "tỷ" nhưng có "triệu"

        a) Cấu trúc phổ biến:
        - x triệu: Chỉ có giá trị triệu (vd: "400 triệu").

        b) Xử lý:
        - Số được chia cho 1000 để chuyển đổi từ triệu sang tỷ:
            ```python
            number / 1000
            ```
        - Nếu giá trị triệu quá nhỏ ($\leq$ 500), giả định đây không phải là giá bán hợp lệ và trả về `pd.NA`.

#### Tạo ra các cột dữ liệu mới hữu ích cho bài toán

Ngoài việc chuẩn hóa giá cả và thông tin cơ bản như số phòng ngủ, phòng vệ sinh, và số tầng, các hàm dưới đây được thiết kế để trích xuất thông tin chi tiết hơn về các đặc điểm liên quan đến vị trí, tiện ích, và tính năng của bất động sản. Điều này giúp cải thiện khả năng phân tích và đánh giá giá trị tài sản.

Trong phần này, chúng tôi vẫn cố gắng khai thác tối đa thông tin từ cột `Description` và `Title` để lấy ra được những đặc trưng mà chúng tôi thấy hữu ích trong bài toán hồi quy tiến đoán này. Quy trình làm việc vẫn là cố gắng thiết kế các regex pattern mà có thể thể hiện được "sự tồn tại" của biến sắp được tạo ra trong `Description` hay `Title`.

1. Xử lý không gian đỗ xe hơi:

    Hàm `process_car_place` được thiết kế để kiểm tra xem bất động sản có không gian dành cho đỗ xe hoặc gara hay không, một yếu tố quan trọng trong việc đánh giá sự tiện nghi.

    **Cách hoạt động:** 
    - Sử dụng regex để nhận diện các từ khóa liên quan đến đỗ xe trong chuỗi mô tả, bao gồm:
    - "gara", "đỗ ô tô", "xe hơi", "hầm xe", "sân đỗ", "hẻm xe hơi", "hẻm xe tải", "oto", v.v.
    - Trả về `True` nếu tìm thấy từ khóa trong mô tả, `False` nếu không tìm thấy.

    Sau đây là pattern đầy đủ:

    ```python
    pattern = r"gara|đỗ ô tô|xe hơi|ô tô tránh|hầm xe|hầm|nhà xe|đỗ|ô tô|ôtô|sân đỗ|hẻm xe hơi|hxh|oto|hẻm xe tải"
    ```

    **Ý nghĩa:** Hàm này giúp nhận diện bất động sản phù hợp với người mua có yêu cầu về đỗ xe, đặc biệt ở các khu vực thành phố lớn nơi không gian đỗ xe là một yếu tố ưu tiên.

2. Xử lý thông tin mặt tiền:

    Chúng tôi sử dụng hai hàm để có thể trích xuất được thông tin mặt tiền là `process_facade_step1` và `process_facade_step2`. Hai hàm này được sử dụng để xác định vị trí của bất động sản liên quan đến mặt tiền, với hai trường hợp cụ thể:

    - 2.1. Hàm `process_facade_step1`

        Sử dụng regex để tìm kiếm các cụm từ mô tả trực tiếp mặt tiền như: "mặt tiền", "mặt phố", "mặt đường", "mat tien". Trả về `True` nếu bất động sản nằm trực tiếp trên mặt tiền đường, ngược lại trả vè `False`

        Ví dụ:

        ```python
        description = "Nhà nằm ở mặt tiền đường lớn, thích hợp kinh doanh."
        result = process_facade_step1(description)
        print(result)  # Output: True
        ```

    - 2.2. Hàm `process_facade_step2`

        Hàm này sẽ nhận dạng các từ khóa mô tả việc bất động sản có khoảng cách gần mặt tiền như: "cách mặt tiền", "sát mặt tiền", "cách mặt phố", "sát mặt phố". Trả về `True` nếu bất động sản gần mặt tiền, ngược lại trả về `False`.

        Ví dụ:

        ```python
        description = "Nhà cách mặt tiền đường 10m, thuận tiện di chuyển."
        result = process_facade_step2(description)
        print(result)  # Output: True
        ```

    Sau cùng chúng tôi sẽ lấy giao của `process_facade_step1` và phủ định của `process_facade_step2`, từ đó xác định được việc bất động sản có phải tọa lạc ở mặt tiền hay không.

    **Ý nghĩa:** Những hàm này cho phép phân tích tự động các đặc điểm chi tiết của bất động sản dựa trên mô tả tự do. Khi kết hợp với các hàm xử lý khác (giá cả, số phòng ngủ, phòng vệ sinh), hệ thống có thể:
    - Đưa ra các đánh giá tổng quan và chi tiết hơn về bất động sản.
    - Tăng khả năng lọc và tìm kiếm bất động sản phù hợp với nhu cầu cụ thể của người dùng (ví dụ: ưu tiên mặt tiền, có gara).
    - Cải thiện độ chính xác trong định giá và phân tích giá trị tài sản.


# II. EDA và Feature Engineering

## 3 Xử lý và làm sạch dữ liệu

Ở phần này, tôi sẽ sử dụng file `DataProcessing.py` có chứa `DataCleaner` class để xử lý và làm sạch dữ liệu.

Trước tiên, tôi sẽ giới thiệu đôi chút về `DataCleaner` class.

### 3.1. `DataCleaner` class

```python
class DataCleaner:
    """
    A class for cleaning and processing datasets, including outlier removal, 
    imputing missing values, address geocoding, and handling feature correlations.
    """

    # ... (code here) ...
```

`DataCleaner` là một lớp (class) được thiết kế nhằm hỗ trợ quá trình tiền xử lý và làm sạch dữ liệu. Mục tiêu chính của lớp này là đơn giản hóa và tự động hóa các bước chuẩn hóa dữ liệu cho trường hợp bài toán dự đoán giá nhà của chúng ta. Sau đó, dữ liệu đã được làm sạch sẽ được lưu lại dưới dạng DataFrame để tiếp tục sử dụng cho các bước quan trọng kết đến.

#### 3.1.1. Chức năng chính của `DataCleaner`
- Xử lý dữ liệu thô, loại bỏ những giá trị ngoại lai (outliers).
- Chuẩn hoá lại dữ liệu đầu vào, bao gồm việc chuyển đổi và điền khuyết giá trị thiếu (missing values) thông qua các mô hình học máy.
- Chuẩn hoá dạng dữ liệu, ví dụ như chuyển đổi dữ liệu boolean sang dạng số.
- Trích xuất thông tin vị trí (latitude, longitude) từ địa chỉ thông qua API geocoding.
- Cho phép thực hiện các thao tác biến đổi phân phối dữ liệu, như log transformation, để điều chỉnh độ lệch và giảm tác động của outliers lên mô hình.

#### 3.1.2. Các phương thức chính của `DataCleaner`

- `__init__(self, api_key: str)`: Phương thức khởi tạo `__init__` trong lớp `DataCleaner` đảm nhiệm vai trò thiết lập ban đầu cho đối tượng. Khi tạo một đối tượng `DataCleaner`, chúng ta cần truyền vào `api_key` - đây là API dùng để tương tác với dịch vụ geocoding của OpenCageData. Thông qua `api_key`, class có thể tự động gọi API, chuyển đổi địa chỉ thành tọa độ kinh độ (longitude) và vĩ độ (latitude).
    ```python
        def __init__(self, api_key: str):
            """
            Initialize the DataCleaner class.

            Parameters:
            - api_key: str. The API key for the OpenCageData geocoding service.
            """

            self.api_key = api_key
    ```

- `def drop_outliers(self, df: pd.DataFrame, ...)`: Phương thức `drop_outliers` trong lớp `DataCleaner` tập trung vào các cột numeric giúp loại bỏ những điểm dữ liệu ngoại lai (outliers) dựa trên chỉ số Interquartile Range (IQR). Việc loại bỏ ngoại lai sẽ giúp dữ liệu trở nên "clean" và ổn định hơn, từ đó giảm thiểu ảnh hưởng tiêu cực của các điểm dữ liệu bất thường đến quá trình huấn luyện mô hình dự báo.
    ![IQR](https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Boxplot_vs_PDF.svg/1200px-Boxplot_vs_PDF.svg.png)
    _Hình 1: Minh họa cách tính IQR và xác định ngoại lai trong boxplot_

    ```python
        def drop_outliers(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
            """
            Remove outliers from the specified columns based on the interquartile range (IQR).

            Parameters:
            - df: pd.DataFrame. The dataset.
            - columns: list of str. The columns from which to remove outliers.

            Returns:
            - pd.DataFrame. The dataset without outliers.
            """
            for field_name in columns:
                if df[field_name].dtype != 'int64' and df[field_name].dtype != 'float64':
                    continue
                Q1 = df[field_name].quantile(0.25)
                Q3 = df[field_name].quantile(0.75)
                IQR = Q3 - Q1
                df = df[(df[field_name] >= (Q1 - 1.5 * IQR)) & (df[field_name] <= (Q3 + 1.5 * IQR))]

            return df
    ```

- `process_addresses_into_coordinations(self, df: pd.DataFrame)`: Phương thức này thực hiện việc chuyển đổi địa chỉ thành tọa độ địa lý (longitude và latitude) thông qua việc sử dụng OpenCage API. Đây là một bước quan trọng khi làm việc với dữ liệu liên quan đến vị trí địa lý để phân tích không gian và hiển thị dữ liệu trên bản đồ. Quy trình chính của phương thức này như sau:

  1. **`cache`** là một dictionary dùng để lưu trữ các kết quả geocoding đã xử lý trước đó. Mục đích:
       - Giảm số lần gọi API không cần thiết.
       - Tăng hiệu suất khi cùng một địa chỉ xuất hiện nhiều lần trong dữ liệu.

  2. **Hàm nội bộ `get_coordinates`:**
     - Đây là một hàm nhỏ bên trong phương thức chính, thực hiện công việc chính:
       - Kiểm tra nếu địa chỉ đã tồn tại trong `cache`.
       - Nếu không, gửi yêu cầu API đến OpenCage để lấy tọa độ.
     - Cách hoạt động:
       - Sử dụng `requests.get` để gửi yêu cầu đến API của OpenCage.
       - Kết quả trả về được trích xuất từ JSON, lưu tọa độ (`latitude`, `longitude`) vào `cache` để sử dụng lại (nếu cần).
       - Nếu xảy ra lỗi, hàm sẽ xử lý ngoại lệ (`RequestException`) và trả về `(None, None)`.

  3. **Xử lý song song với `concurrent.futures.ThreadPoolExecutor`:**
     - **`ThreadPoolExecutor`**:
       - Đây là một lớp từ thư viện `concurrent.futures`, được thiết kế để thực hiện các tác vụ song song bằng cách sử dụng nhiều luồng (threads).
       - Trong trường hợp này, nó được sử dụng để tăng tốc việc gọi API geocoding, cho phép xử lý nhiều địa chỉ cùng lúc (cụ thể là 5 địa chỉ mỗi lần).
     - **Tại sao dùng `ThreadPoolExecutor`?**
       - Gọi API thường là một tác vụ I/O-bound, nghĩa là thời gian chờ phản hồi từ máy chủ chiếm phần lớn thời gian xử lý.
       - Bằng cách chạy các yêu cầu API đồng thời (concurrently), tổng thời gian xử lý sẽ giảm đáng kể so với việc xử lý tuần tự (sử dụng một luồng duy nhất).
     - Cách hoạt động:
       - `executor.map` thực thi hàm `get_coordinates` cho từng địa chỉ trong cột `address`.
       - Mỗi địa chỉ được gửi đi như một yêu cầu API riêng biệt. Trong trường hợp này, `address` sẽ có dạng `"<street>, <district>, Ho Chi Minh"`.
       - Kết quả trả về là danh sách các tuple `(latitude, longitude)` tương ứng với từng địa chỉ.

    4. Mục đích của phương thức `process_addresses_into_coordinations`:
       - Xử lý dữ liệu địa chỉ phục vụ cho việc phân tích không gian và hiển thị trên bản đồ.
       - Tạo ra các feature mới `latitude` và `longitude` trong DataFrame để lưu trữ tọa độ vị trí và phục vụ cho việc xây dựng mô hình dự báo.
       ```python
            def process_addresses_into_coordinations(self, df: pd.DataFrame) -> pd.DataFrame:
                """
                Convert addresses into latitude and longitude coordinates using the OpenCage API.

                Parameters:
                - df: pd.DataFrame. The dataset with 'address' column.

                Returns:
                - pd.DataFrame. The dataset with added 'latitude' and 'longitude' columns.
                """
                cache = {}

                def get_coordinates(address: str) -> tuple:
                    """
                    Get the latitude and longitude coordinates of an address.

                    Parameters:
                    - address: str. The address to geocode.

                    Returns:
                    - tuple. The latitude and longitude coordinates of the address.
                    """
                    # Check if the address is already in the cache
                    if address in cache:
                        return cache[address]
                    # Make the API call if not in the cache
                    url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={self.api_key}"
                    try:
                        response = requests.get(url)
                        response.raise_for_status() # Raise an exception for 4xx/5xx status codes
                        data = response.json() # Parse the JSON response
                        if data['results']:
                            location = data['results'][0]['geometry']
                            cache[address] = (location['lat'], location['lng'])
                            return location['lat'], location['lng']
                        else:
                            cache[address] = (None, None)
                            return None, None
                    except requests.RequestException as e:
                        print(f"Error fetching data for {address}: {e}")
                        return None, None

                # Process addresses concurrently
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = list(executor.map(lambda x: get_coordinates(f"{x}, Ho Chi Minh"), df['address']))

                df['latitude'], df['longitude'] = zip(*results)
                return df
         ```

- `convert_boolean_to_numeric(self, df: pd.DataFrame)`: Phương thức này chuyển đổi dữ liệu boolean thành dạng số (0 và 1) để phục vụ cho việc xây dựng mô hình học máy. Trong một số trường hợp, dữ liệu boolean không thể trực tiếp sử dụng trong mô hình học máy, do đó việc chuyển đổi sang dạng số sẽ giúp mô hình hiểu được dữ liệu hơn.
    ```python
        def convert_boolean_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
            """
            Convert boolean columns to numeric (0 and 1).

            Parameters:
            - df: pd.DataFrame. The dataset.

            Returns:
            - pd.DataFrame. The dataset with boolean columns converted to numeric.
            """
            for col in df.columns:
                if df[col].dtype == bool:
                    df[col] = df[col].astype(int)

            return df
    ```

- `handle_missing_values_by_using_models(self, df: pd.DataFrame, ...)`: Phương thức này được thiết kế để xử lý giá trị thiếu (`missing values`) trong dữ liệu bằng cách sử dụng các mô hình học máy (Machine Learning Models). Đây là một cách tiếp cận tiên tiến và hiệu quả so với việc sử dụng các phương pháp đơn giản như điền giá trị trung bình, trung vị, hoặc mode. Quy trình xử lý bao gồm:

  1. Nhập các tham số đầu vào:
     - `df`: DataFrame chứa dữ liệu cần xử lý.
     - `input_cols`: Danh sách các cột đầu vào, được sử dụng làm đặc trưng (features) để xây dựng mô hình dự đoán.
     - `cols_to_impute`: Danh sách các cột có giá trị bị thiếu cần được điền khuyết.

  2. **Hàm `myWeight`**: Hàm này được định nghĩa để cung cấp trọng số tùy chỉnh cho mô hình KNN (`KNeighborsClassifier`). Trọng số này giảm dần theo khoảng cách giữa các điểm dữ liệu:
    $$
    w_i = \exp \left( \frac{-||\mathbf{x} - \mathbf{x}_i||_2^2}{\sigma^2} \right)
    $$
    **Ý nghĩa của trọng số**:
       - Dựa trên công thức \( w = e^{-\frac{\text{distances}^2}{\sigma^2}} \), khoảng cách càng xa thì trọng số càng nhỏ.
       - Giá trị \( \sigma^2 \) kiểm soát tốc độ giảm của trọng số. Trong trường hợp này, \( \sigma^2 = 0.4 \).
       - Đảm bảo không có trọng số bằng 0 bằng cách thay thế giá trị nhỏ nhất bằng \( 10^{-5} \).

        Tham khảo thêm tại https://machinelearningcoban.com/2017/01/08/knn/.

  3. **Các mô hình được sử dụng**: Các mô hình Machine Learning khác nhau được chuẩn bị trong dictionary `models`:
     - **KNeighborsClassifier (KNN)**: Sử dụng thuật toán tìm $k$ lân cận với trọng số tùy chỉnh.
     - **LinearRegression**: Hồi quy tuyến tính.
     - **DecisionTreeRegressor**: Cây quyết định (Decision Tree) cho bài toán hồi quy.
     - **RandomForestRegressor**: Rừng ngẫu nhiên với nhiều cây quyết định.
     - **GradientBoostingRegressor**: Gradient Boosting, một thuật toán mạnh mẽ cho các bài toán hồi quy và là một cải thiện của thuật toán Random Forest.

  4. **Quy trình xử lý cho mỗi cột trong `cols_to_impute`:**
     1. **Tách dữ liệu**:
          - `df_known`: Các dòng không có giá trị thiếu trong cột đang xử lý.
          - `df_unknown`: Các dòng có giá trị thiếu trong cột đang xử lý. Nếu `df_unknown` rỗng (không có giá trị thiếu), bỏ qua cột này.

     2. **Xây dựng tập dữ liệu**:
          - `X_known` và `y_known`: Tập dữ liệu đầu vào và nhãn từ các dòng không bị thiếu.
          - Sử dụng `train_test_split` để chia `X_known` và `y_known` thành tập huấn luyện và kiểm tra.

     3. **Chuẩn hóa dữ liệu**: Dùng `StandardScaler` để chuẩn hóa các đặc trưng trong tập `X_known` và `X_unknown`.

     4. **Huấn luyện và chọn mô hình tốt nhất**:
          - Huấn luyện tất cả các mô hình trên tập huấn luyện.
          - Dự đoán trên tập kiểm tra và tính toán Mean Squared Error (MSE):
            $$
            \text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2
            $$
          - Lựa chọn mô hình có MSE nhỏ nhất làm mô hình tốt nhất.

     5. **Điền giá trị thiếu**:
          - Huấn luyện mô hình tốt nhất trên toàn bộ `X_known` và `y_known`.
          - Dự đoán giá trị cho `X_unknown` (dòng có giá trị thiếu).
          - Điền các giá trị dự đoán vào cột tương ứng trong DataFrame ban đầu.

     6. Phương thức trả về DataFrame với các giá trị bị thiếu trong `cols_to_impute` đã được điền khuyết bằng các giá trị dự đoán từ mô hình tốt nhất.

  5. **Tại sao sử dụng cách này?**
     1. **Ưu điểm so với các phương pháp truyền thống**:
        - Các giá trị bị thiếu được điền dựa trên mối quan hệ giữa các đặc trưng khác, không phải chỉ dùng các giá trị trung bình hoặc mode.
        - Phương pháp này đặc biệt hữu ích với dữ liệu phức tạp hoặc dữ liệu có mối quan hệ phi tuyến tính giữa các đặc trưng.

     2. **Tính linh hoạt**: Có thể sử dụng nhiều loại mô hình khác nhau (KNN, Random Forest, Gradient Boosting, v.v.) để phù hợp với bản chất dữ liệu.

     3. **Tự động chọn mô hình tốt nhất** bằng cách tính toán MSE trên tập kiểm tra, phương thức đảm bảo rằng mô hình được sử dụng có hiệu suất tốt nhất cho dữ liệu hiện tại.
    ```python
        def handle_missing_values_by_using_models(self, df: pd.DataFrame, input_cols: list = [], cols_to_impute: list = []) -> pd.DataFrame:
            """
            Impute missing values in specified columns using predictive models (KNN, Linear Regression, etc.).

            Parameters:
            - df: pd.DataFrame. The dataset.
            - input_cols: list of str. The input columns for building predictive models.
            - cols_to_impute: list of str. Columns to impute missing values.

            Returns:
            - pd.DataFrame. The dataset with missing values imputed.
            """
            def myWeight(distances: np.array) -> np.array:
                """
                Custom weight function for KNN model.
                
                Parameters:
                - distances: np.array. The distances between points.

                Returns:
                - np.array. The weights for the distances.
                """
                sigma2 = .4
                weights = np.exp(-distances**2 / sigma2)
                return np.where(weights == 0, 1e-5, weights)  # Ensure no zero weights

            models = {
                'knn': KNeighborsClassifier(n_neighbors=12, p=2, weights=myWeight),
                'linear_reg': LinearRegression(),
                'decision_tree': DecisionTreeRegressor(max_depth=5),
                'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
            }

            for col in cols_to_impute:
                print(f"Imputing for column: {col}")
                df_impute = df[input_cols].copy()
                df_impute[col] = df[col]

                df_known = df_impute.dropna(subset=[col])
                df_unknown = df_impute[df_impute[col].isnull()]

                if df_unknown.empty:
                    continue

                X_known = df_known.drop(columns=[col])
                y_known = df_known[col]

                X_train, X_test, y_train, y_test = train_test_split(X_known, y_known, test_size=0.2, random_state=42)

                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)

                best_model = None
                lowest_error = float('inf')

                for model_name, model in models.items():
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    error = mean_squared_error(y_test, y_pred)

                    if error < lowest_error:
                        best_model = model
                        lowest_error = error

                    print(f"{model_name} MSE for {col}: {error:.4f}")

                print(f"Best model for {col}: {best_model} with MSE: {lowest_error:.4f}")
                print("-----------------------------------")

                best_model.fit(scaler.fit_transform(X_known), y_known)
                X_unknown_scaled = scaler.transform(df_unknown.drop(columns=[col]))
                y_unknown_pred = best_model.predict(X_unknown_scaled)

                df.loc[df[col].isnull(), col] = y_unknown_pred

            return df
    ```

- `apply_log_transformation(self, df: pd.DataFrame, columns: list)`: Phương thức này thực hiện việc biến đổi log lên các cột có phân phối lệch (skewed). Mục đích chính của việc này là giảm mức độ ảnh hưởng của các outliers và làm cho phân phối dữ liệu trở nên “near normal” hơn, giúp các mô hình học máy hoặc các phân tích thống kê hoạt động hiệu quả hơn. Quy trình xử lý bao gồm:

  1. **Xác định độ lệch (skewness)**:
     - Bên trong phương thức có một hàm nội bộ `find_skewness` dùng để tính toán độ lệch của một cột thông qua phương thức `skew()` của `pandas`.
     - Skewness đo lường độ bất đối xứng của phân phối dữ liệu.  
       - Giá trị `skewness > 0`: Phân phối lệch phải (right-skewed).
       - Giá trị `skewness < 0`: Phân phối lệch trái (left-skewed).
       - Giá trị tuyệt đối càng lớn, dữ liệu càng lệch mạnh so với phân phối chuẩn.
     - Một ngưỡng điển hình là `skewness > 0.75` được coi là lệch cao và cần được điều chỉnh.

  2. **Áp dụng biến đổi log**:
     - Nếu độ lệch của một cột vượt quá 0.75, phương thức sẽ áp dụng hàm `np.log1p` lên cột đó.
     - `np.log1p(x)` tương đương với `log(x+1)`, điều này giúp tránh lỗi khi dữ liệu có giá trị bằng 0 (log(0) không xác định được).
     - Sau biến đổi log, phân phối dữ liệu thường trở nên cân bằng hơn, giảm độ lệch, và hạn chế ảnh hưởng của ngoại lai.

  3. **Hạn chế áp dụng lên kiểu dữ liệu không phù hợp**:
     - Phương thức chỉ áp dụng log transform với các cột dạng số (`int64` hoặc `float64`).
     - Điều này đảm bảo không thực hiện biến đổi không phù hợp với dữ liệu dạng chuỗi, danh mục, hoặc kiểu boolean.

    ![Log transform](https://upload.wikimedia.org/wikipedia/commons/c/cc/Relationship_between_mean_and_median_under_different_skewness.png)
    _Hình 2: Minh họa sự thay đổi giữa trung bình và trung vị khi dữ liệu lệch phải và sau khi áp dụng log transform_
    
    Lợi ích chính của việc làm này là giảm độ lệch giúp nâng cao hiệu suất mô hình hồi quy hoặc mô hình tuyến tính, vốn thường giả định dữ liệu gần với phân phối chuẩn. Ngoài ra, log transform còn giúp tăng tính ổn định và độ tin cậy của các phép thống kê, đặc biệt trong phân tích dữ liệu định lượng.
    ```python
        def apply_log_transformation(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
            """
            Apply log transformation to skewed columns to reduce the effect of outliers.

            Parameters:
            - df: pd.DataFrame. The dataset.
            - columns: list of str. The columns to apply log transformation.

            Returns:
            - pd.DataFrame. The dataset with log transformation applied to skewed columns.
            """
            def find_skewness(col: pd.Series) -> float:
                """
                Calculate the skewness of a column.

                Parameters:
                - col: pd.Series. The column to calculate skewness.

                Returns:
                - float. The skewness of the column.
                """
                return col.skew()  # Skewness > 0.75 is considered highly skewed

            for col in columns:
                if df[col].dtype == 'int64' or df[col].dtype == 'float64':
                    skewness = find_skewness(df[col])
                    if skewness > 0.75:
                        df[col] = np.log1p(df[col])

            return df
    ```

- `clean_data(self, df: pd.DataFrame, ...)`: Phương thức `clean_data` trong lớp `DataCleaner` đóng vai trò là hàm xử lý tổng thể (pipeline) cho quá trình làm sạch và chuẩn hóa dữ liệu. Phương thức này gói gọn nhiều bước xử lý quan trọng thành một quy trình liên tục, giúp người dùng dễ dàng tiền xử lý dữ liệu mà không phải lặp lại nhiều bước thủ công.

    Cụ thể, khi gọi đến `clean_data`, người dùng cung cấp một DataFrame cùng với một số thông tin và tham số liên quan (cột mục tiêu `target_col`, danh sách cột cần xóa nếu thiếu dữ liệu `drop_na_cols`, cột dùng cho việc điền giá trị thiếu `input_cols`, và các cột cần điền khuyết `cols_to_impute`). Quy trình xử lý dữ liệu sẽ được thực hiện theo các bước sau:

    1. **Loại bỏ ngoại lai**: Áp dụng quy tắc dựa trên IQR để loại trừ các điểm dữ liệu nằm quá xa phân vị thứ nhất và thứ ba.
    2. **Xử lý địa chỉ**: Ghép các trường thông tin (như `street` và `district`) để tạo thành địa chỉ đầy đủ, sau đó chuyển đổi địa chỉ này thành tọa độ vĩ độ và kinh độ thông qua API geocoding.
    3. **Xử lý dữ liệu trùng lặp và thiếu**: 
       - Loại bỏ các dòng trùng lặp.
       - Loại bỏ các dòng thiếu dữ liệu ở những cột quan trọng.
       - Chuyển đổi dữ liệu Boolean thành dạng số.
       - Sử dụng các mô hình học máy để dự đoán và điền giá trị thiếu cho những cột cần thiết.
    4. **Tiếp tục loại bỏ ngoại lai**: Sau khi dữ liệu được bổ sung, tiến hành loại bỏ ngoại lai một lần nữa để dữ liệu trở nên sạch hơn.
    5. **Biểu diễn dữ liệu**: Tạo biểu đồ histogram để quan sát sự phân bố dữ liệu, giúp xác định xem có cột nào cần áp dụng log transform để giảm độ skew hay không.
    6. **Xử lý cột phân phối lệch (skewed)**: Nếu người dùng xác nhận sự tồn tại của các cột lệch, tiến hành log transform để làm giảm ảnh hưởng của ngoại lai và cải thiện phân phối dữ liệu.

    Tóm lại, `clean_data` là nơi “điều phối” hầu hết các bước tiền xử lý dữ liệu, từ lọc nhiễu, xử lý thiếu dữ liệu, đến biến đổi đặc trưng, giúp dữ liệu trở nên “sẵn sàng” hơn cho giai đoạn phân tích, mô hình hóa tiếp theo.

    ```python
        def clean_data(self, df: pd.DataFrame, target_col: str, drop_na_cols: list = [], input_cols: list = [], cols_to_impute: list = []) -> pd.DataFrame:
            """
            Clean the dataset by removing outliers, imputing missing values, 
            and processing addresses into coordinates.

            Parameters:
            - df: pd.DataFrame. The dataset to clean.
            - target_col: str. The target column used for outlier detection.
            - input_cols: list of str. Columns used as input for imputing missing values.
            - cols_to_impute: list of str. Columns where missing values will be imputed.

            Returns:
            - pd.DataFrame. The cleaned dataset.
            """
            df = self.drop_outliers(df, [target_col])

            # Merge 'street' and 'district' columns, handling NaN values
            df['address'] = df['street'].fillna('') + ', ' + df['district'].fillna('')
            df['address'] = df['address'].str.replace('^, |, $', '', regex=True)

            df = self.process_addresses_into_coordinations(df)
            df = df.drop_duplicates()

            drop_na_cols.extend(["latitude", "longitude"])
            df = df.dropna(subset=drop_na_cols)

            df = self.convert_boolean_to_numeric(df)
            input_cols.extend(["latitude", "longitude"])
            df = self.handle_missing_values_by_using_models(df, input_cols, cols_to_impute)
            df = self.drop_outliers(df, df.columns)

            df.hist(bins=50, figsize=(12, 8))
            plt.show()

            answer_for_skewed_cols = input("Are there any skewed columns that need log transformation? (y/n): ")
            if answer_for_skewed_cols.lower() == 'y':
                skewed_cols = input("Enter the names of the skewed columns separated by commas: ").split(',')
                skewed_cols = [col.strip() for col in skewed_cols]  # Remove leading/trailing whitespaces
                
                df = self.apply_log_transformation(df, skewed_cols)

                for col in df.columns:
                    if df[col].dtype == float:
                        df[col] = df[col].replace([np.inf, -np.inf], np.nan)

            return df
    ```

### 3.2. Các hàm khác

- `del_col(df: pd.DataFrame, columns: list)`: Hàm `del_col` là một hàm dùng để xóa một số cột ra khỏi DataFrame. Việc loại bỏ cột thường cần thiết khi chúng ta muốn tinh gọn dữ liệu, loại bỏ dữ liệu không liên quan, hoặc chuẩn bị dữ liệu (tùy ý) cho các bước phân tích tiếp theo. Quy trình xử lý bao gồm:

    1. **Xóa các cột dạng object (chuỗi, ký tự, v.v.)**: Đầu tiên, hàm sẽ duyệt qua tất cả các cột trong DataFrame.  
       - Nếu phát hiện cột có kiểu dữ liệu là `object` (thường là dạng chuỗi, văn bản), hàm sẽ xóa cột đó ngay lập tức.  
       - Mục đích: Trong nhiều trường hợp, dữ liệu dạng object có thể không cần thiết cho quá trình phân tích hoặc mô hình hoá, hoặc có thể cần được xử lý riêng (như mã hoá thành số) trước khi sử dụng.

    2. **Xóa các cột trong danh sách truyền vào**: Sau khi loại bỏ các cột dạng object, hàm tiếp tục xóa những cột được chỉ định trong tham số `columns`.  
       - Người dùng có thể truyền vào danh sách tên các cột muốn xóa.  
       - Hàm sẽ xóa từng cột trong danh sách đó, nếu chúng tồn tại trong DataFrame.

    3. Cuối cùng, hàm trả về DataFrame sau khi đã loại bỏ các cột object và các cột do người dùng yêu cầu.  

    Tóm lại, `del_col` hỗ trợ bạn nhanh chóng loại bỏ các cột không mong muốn, giúp tập dữ liệu trở nên dễ quản lý hơn và phù hợp với mục đích phân tích, tiền xử lý hoặc mô hình hoá tiếp theo.
