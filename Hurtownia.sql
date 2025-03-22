USE hurtownia;

DROP PROCEDURE IF EXISTS create_dim_date;
DROP PROCEDURE IF EXISTS create_dim_customer;
DROP PROCEDURE IF EXISTS create_dim_product;
DROP PROCEDURE IF EXISTS create_fact_sales;
DROP PROCEDURE IF EXISTS insert_dim_date;
DROP PROCEDURE IF EXISTS insert_dim_product;
DROP PROCEDURE IF EXISTS insert_dim_customer;
DROP PROCEDURE IF EXISTS insert_fact_sales;
DROP PROCEDURE IF EXISTS insert_dim_date_delta;
DROP PROCEDURE IF EXISTS insert_dim_customer_delta;
DROP PROCEDURE IF EXISTS insert_dim_product_delta;
DROP PROCEDURE IF EXISTS insert_fact_sales_delta;

DELIMITER //

-- ***********************
-- Tworzenie tabel wymiarowych
-- ***********************
CREATE PROCEDURE create_dim_date()
BEGIN
    CREATE TABLE IF NOT EXISTS dim_date (
        date_key DATE PRIMARY KEY,
        day INT NOT NULL,
        month INT NOT NULL,
        month_name VARCHAR(20) NOT NULL,
        quarter INT NOT NULL,
        year INT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX (year, month, day)
    );
END //

CREATE PROCEDURE create_dim_customer()
BEGIN
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_age INT NOT NULL,
        age_group VARCHAR(50) NOT NULL,
        customer_gender CHAR(1) NOT NULL,
        country VARCHAR(50) NOT NULL,
        state VARCHAR(50) NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY (customer_age, age_group, customer_gender, country, state)
    );
END //

CREATE PROCEDURE create_dim_product()
BEGIN
    CREATE TABLE IF NOT EXISTS dim_product (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product VARCHAR(100) NOT NULL,
        product_category VARCHAR(100) NOT NULL,
        sub_category VARCHAR(100) NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY (product, product_category, sub_category)
    );
END //

-- ***********************
-- Tworzenie tabeli faktów
-- ***********************
CREATE PROCEDURE create_fact_sales()
BEGIN
    CREATE TABLE IF NOT EXISTS fact_sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        date_key DATE NOT NULL,
        customer_id INT NOT NULL,
        product_id INT NOT NULL,
        order_quantity INT NOT NULL,
        unit_cost DECIMAL(12,4) NOT NULL,
        unit_price DECIMAL(12,4) NOT NULL,
        profit DECIMAL(12,4) NOT NULL,
        cost DECIMAL(12,4) NOT NULL,
        revenue DECIMAL(12,4) NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
        FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
        FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
        INDEX (date_key),
        INDEX (customer_id),
        INDEX (product_id)
    );
END //

-- ***********************
-- Procedury wstawiania danych do tabel wymiarowych (pełne ładowanie)
-- ***********************
CREATE PROCEDURE insert_dim_date()
BEGIN
    INSERT INTO dim_date (date_key, day, month, month_name, quarter, year)
    SELECT *
    FROM (
        SELECT DISTINCT 
            Date AS date_key,
            DAY(Date) AS day,
            MONTH(Date) AS month,
            MONTHNAME(Date) AS month_name,
            QUARTER(Date) AS quarter,
            YEAR(Date) AS year
        FROM sales
    ) AS new
    ON DUPLICATE KEY UPDATE
        day = new.day,
        month = new.month,
        month_name = new.month_name,
        quarter = new.quarter,
        year = new.year,
        last_updated = CURRENT_TIMESTAMP;
END //

CREATE PROCEDURE insert_dim_customer()
BEGIN
    INSERT INTO dim_customer (customer_age, age_group, customer_gender, country, state)
    SELECT DISTINCT 
        Customer_Age, Age_Group, Customer_Gender, Country, State
    FROM sales
    ON DUPLICATE KEY UPDATE
        last_updated = CURRENT_TIMESTAMP;
END //

CREATE PROCEDURE insert_dim_product()
BEGIN
    INSERT INTO dim_product (product, product_category, sub_category)
    SELECT DISTINCT 
        Product, Product_Category, Sub_Category
    FROM sales
    ON DUPLICATE KEY UPDATE
        last_updated = CURRENT_TIMESTAMP;
END //

CREATE PROCEDURE insert_fact_sales()
BEGIN
    INSERT INTO fact_sales (
        date_key, customer_id, product_id,
        order_quantity, unit_cost, unit_price, profit, cost, revenue
    )
    SELECT 
        s.Date,
        c.customer_id,
        p.product_id,
        s.Order_Quantity,
        s.Unit_Cost,
        s.Unit_Price,
        s.Profit,
        s.Cost,
        s.Revenue
    FROM sales s
    JOIN dim_customer c 
      ON s.Customer_Age = c.customer_age 
     AND s.Age_Group = c.age_group 
     AND s.Customer_Gender = c.customer_gender 
     AND s.Country = c.country 
     AND s.State = c.state
    JOIN dim_product p 
      ON s.Product = p.product 
     AND s.Product_Category = p.product_category 
     AND s.Sub_Category = p.sub_category;
END //

-- ***********************
-- Procedury metody delty
-- ***********************
CREATE PROCEDURE insert_dim_date_delta()
BEGIN
    INSERT INTO dim_date (date_key, day, month, month_name, quarter, year)
    SELECT DISTINCT 
        s.Date,
        DAY(s.Date),
        MONTH(s.Date),
        MONTHNAME(s.Date),
        QUARTER(s.Date),
        YEAR(s.Date)
    FROM sales s
    LEFT JOIN dim_date d ON s.Date = d.date_key
    WHERE d.date_key IS NULL;
END //

CREATE PROCEDURE insert_dim_customer_delta()
BEGIN
    INSERT INTO dim_customer (customer_age, age_group, customer_gender, country, state)
    SELECT DISTINCT 
        s.Customer_Age, s.Age_Group, s.Customer_Gender, s.Country, s.State
    FROM sales s
    LEFT JOIN dim_customer dc 
      ON s.Customer_Age = dc.customer_age 
     AND s.Age_Group = dc.age_group 
     AND s.Customer_Gender = dc.customer_gender 
     AND s.Country = dc.country 
     AND s.State = dc.state
    WHERE dc.customer_id IS NULL;
END //

CREATE PROCEDURE insert_dim_product_delta()
BEGIN
    INSERT INTO dim_product (product, product_category, sub_category)
    SELECT DISTINCT 
        s.Product, s.Product_Category, s.Sub_Category
    FROM sales s
    LEFT JOIN dim_product dp 
      ON s.Product = dp.product 
     AND s.Product_Category = dp.product_category 
     AND s.Sub_Category = dp.sub_category
    WHERE dp.product_id IS NULL;
END //

CREATE PROCEDURE insert_fact_sales_delta()
BEGIN
    INSERT INTO fact_sales (
        date_key, customer_id, product_id,
        order_quantity, unit_cost, unit_price, profit, cost, revenue
    )
    SELECT 
        s.Date,
        c.customer_id,
        p.product_id,
        s.Order_Quantity,
        s.Unit_Cost,
        s.Unit_Price,
        s.Profit,
        s.Cost,
        s.Revenue
    FROM sales s
    JOIN dim_date d ON s.Date = d.date_key
    JOIN dim_customer c 
      ON s.Customer_Age = c.customer_age 
     AND s.Age_Group = c.age_group 
     AND s.Customer_Gender = c.customer_gender 
     AND s.Country = c.country 
     AND s.State = c.state
    JOIN dim_product p 
      ON s.Product = p.product 
     AND s.Product_Category = p.product_category 
     AND s.Sub_Category = p.sub_category
    WHERE NOT EXISTS (
        SELECT 1 FROM fact_sales fs
        WHERE fs.date_key = s.Date
          AND fs.customer_id = c.customer_id
          AND fs.product_id = p.product_id
          AND fs.order_quantity = s.Order_Quantity
          AND fs.unit_cost = s.Unit_Cost
          AND fs.unit_price = s.Unit_Price
          AND fs.profit = s.Profit
          AND fs.cost = s.Cost
          AND fs.revenue = s.Revenue
    );
END //

DELIMITER ;

-- ***********************
-- Wywołanie procedur
-- ***********************

-- Pełne załadowanie danych (pierwsze uruchomienie)
CALL create_dim_date();
CALL create_dim_customer();
CALL create_dim_product();
CALL create_fact_sales();

CALL insert_dim_date();
CALL insert_dim_customer();
CALL insert_dim_product();
CALL insert_fact_sales();

-- Delta (dla aktualizacji)
CALL insert_dim_date_delta();
CALL insert_dim_customer_delta();
CALL insert_dim_product_delta();
CALL insert_fact_sales_delta();
