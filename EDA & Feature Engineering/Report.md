# Table of contents

- [Table of contents](#table-of-contents)
- [II. EDA và Feature Engineering](#ii-eda-và-feature-engineering)
  - [3 Xử lý và làm sạch dữ liệu](#3-xử-lý-và-làm-sạch-dữ-liệu)
    - [3.1. `DataCleaner` class](#31-datacleaner-class)
      - [3.1.1. Chức năng chính của `DataCleaner`](#311-chức-năng-chính-của-datacleaner)
      - [3.1.2. Các phương thức chính của `DataCleaner`](#312-các-phương-thức-chính-của-datacleaner)

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

- `clean_data(self, df: pd.DataFrame, ...)`: Phương thức `clean_data` trong lớp `DataCleaner` đóng vai trò là hàm xử lý tổng thể (pipeline) cho quá trình làm sạch và chuẩn hóa dữ liệu. Phương thức này gói gọn nhiều bước xử lý quan trọng thành một quy trình liên tục, giúp người dùng dễ dàng tiền xử lý dữ liệu mà không phải lặp lại nhiều bước thủ công.

    Cụ thể, khi gọi đến `clean_data`, người dùng cung cấp một DataFrame cùng với một số thông tin và tham số liên quan (cột mục tiêu `target_col`, danh sách cột cần xóa nếu thiếu dữ liệu `drop_na_cols`, cột dùng cho việc điền giá trị thiếu `input_cols`, và các cột cần điền khuyết `cols_to_impute`). Quy trình xử lý dữ liệu sẽ được thực hiện theo các bước sau:

    1. **Loại bỏ ngoại lai**: Áp dụng quy tắc dựa trên IQR để loại trừ các điểm dữ liệu nằm quá xa phân vị thứ nhất $Q_1$ và thứ ba $Q_3$.
    ![IQR](https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Boxplot_vs_PDF.svg/1200px-Boxplot_vs_PDF.svg.png)
    _Hình 1: Minh họa cách tính IQR và xác định ngoại lai trong boxplot_
    2. **Xử lý địa chỉ**: Ghép các trường thông tin (như `street` và `district`) để tạo thành địa chỉ đầy đủ, sau đó chuyển đổi địa chỉ này thành tọa độ vĩ độ và kinh độ thông qua API geocoding.
    3. **Xử lý dữ liệu trùng lặp và thiếu**: 
       - Loại bỏ các dòng trùng lặp.
       - Loại bỏ các dòng thiếu dữ liệu ở những cột quan trọng.
       - Chuyển đổi dữ liệu Boolean thành dạng số.
       - Sử dụng các mô hình học máy để dự đoán và điền giá trị thiếu cho những cột cần thiết.
    4. **Tiếp tục loại bỏ ngoại lai**: Sau khi dữ liệu được bổ sung, tiến hành loại bỏ ngoại lai một lần nữa để dữ liệu trở nên sạch hơn.
    5. **Biểu diễn dữ liệu**: Tạo biểu đồ histogram để quan sát sự phân bố dữ liệu, giúp xác định xem có cột nào cần áp dụng log transform để giảm độ skew hay không.
    6. **Xử lý cột phân phối lệch (skewed)**: Nếu người dùng xác nhận sự tồn tại của các cột lệch, tiến hành log transform để làm giảm ảnh hưởng của ngoại lai và cải thiện phân phối dữ liệu.
    ![Log transform](https://upload.wikimedia.org/wikipedia/commons/c/cc/Relationship_between_mean_and_median_under_different_skewness.png)
    _Hình 2: Minh họa sự thay đổi giữa trung bình và trung vị khi dữ liệu lệch phải và sau khi áp dụng log transform_

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

- `def drop_outliers(self, df: pd.DataFrame, ...)`:


