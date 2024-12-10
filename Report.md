# Table of contents

- [Table of contents](#table-of-contents)
- [II. EDA và Feature Engineering](#ii-eda-và-feature-engineering)
  - [3 Xử lý và làm sạch dữ liệu](#3-xử-lý-và-làm-sạch-dữ-liệu)
    - [3.1. `DataCleaner` class](#31-datacleaner-class)
      - [3.1.1. Chức năng chính của `DataCleaner`](#311-chức-năng-chính-của-datacleaner)
      - [3.1.2. Các phương thức chính của `DataCleaner`](#312-các-phương-thức-chính-của-datacleaner)
    - [3.2. Các hàm khác](#32-các-hàm-khác)

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
