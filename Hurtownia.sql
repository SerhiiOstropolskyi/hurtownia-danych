USE hurtownia;

DELIMITER //
CREATE PROCEDURE create_dim_date()
BEGIN
    CREATE TABLE IF NOT EXISTS dim_date (
        date_key DATE PRIMARY KEY,
        day INT,
        month INT,
        month_name VARCHAR(20),
        quarter INT,
        year INT
    );
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE insert_dim_date()
BEGIN
    INSERT INTO dim_date (date_key, day, month, month_name, quarter, year)
    SELECT DISTINCT 
        Date,
        DAY(Date),
        MONTH(Date),
        MONTHNAME(Date),
        QUARTER(Date),
        YEAR(Date)
    FROM sales;
END //
DELIMITER ;

-- ***********************
-- Tabela wymiaru klienta
-- ***********************
-- Wymiar klienta oparty jest na atrybutach: Customer_Age, Age_Group, Customer_Gender, Country, State

DELIMITER //
CREATE PROCEDURE create_dim_customer()
BEGIN
    CREATE TABLE IF NOT EXISTS dim_customer (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_age INT,
        age_group VARCHAR(50),
        customer_gender CHAR(1),
        country VARCHAR(50),
        state VARCHAR(50)
    );
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE insert_dim_customer()
BEGIN
    INSERT INTO dim_customer (customer_age, age_group, customer_gender, country, state)
    SELECT DISTINCT 
        Customer_Age, Age_Group, Customer_Gender, Country, State
    FROM sales;
END //
DELIMITER ;

-- ***********************
-- Tabela wymiaru produktu
-- ***********************
-- Wymiar produktu oparty jest na: Product, Product_Category oraz Sub_Category

DELIMITER //
CREATE PROCEDURE create_dim_product()
BEGIN
    CREATE TABLE IF NOT EXISTS dim_product (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product VARCHAR(100),
        product_category VARCHAR(100),
        sub_category VARCHAR(100)
    );
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE insert_dim_product()
BEGIN
    INSERT INTO dim_product (product, product_category, sub_category)
    SELECT DISTINCT 
        Product, Product_Category, Sub_Category
    FROM sales;
END //
DELIMITER ;

-- ***********************
-- Tabela faktów sprzedaży
-- ***********************
-- Tabela faktów łączy datę, klienta i produkt z miarami sprzedaży

DELIMITER //
CREATE PROCEDURE create_fact_sales()
BEGIN
    CREATE TABLE IF NOT EXISTS fact_sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        date_key DATE,
        customer_id INT,
        product_id INT,
        order_quantity INT,
        unit_cost DECIMAL(10,2),
        unit_price DECIMAL(10,2),
        profit DECIMAL(10,2),
        cost DECIMAL(10,2),
        revenue DECIMAL(10,2),
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
        FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
        FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
    );
END //
DELIMITER ;

DELIMITER //
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
DELIMITER ;

-- ***********************
-- Wywołanie procedur
-- ***********************

CALL create_dim_date();
CALL insert_dim_date();

CALL create_dim_customer();
CALL insert_dim_customer();

CALL create_dim_product();
CALL insert_dim_product();

CALL create_fact_sales();
CALL insert_fact_sales();
