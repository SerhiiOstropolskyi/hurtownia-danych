SET GLOBAL local_infile = 1;
USE hurtownia;

DROP TABLE IF EXISTS sales;
CREATE TABLE sales (
    Date DATE,                   -- Data zamówienia
    Day INT,                     -- Dzień
    Month VARCHAR(20),           -- Nazwa miesiąca (lub można INT, jeśli wolisz)
    Year INT,                    -- Rok
    Customer_Age INT,            -- Wiek klienta
    Age_Group VARCHAR(50),       -- Grupa wiekowa
    Customer_Gender CHAR(1),     -- Płeć klienta (M/F)
    Country VARCHAR(50),         -- Kraj
    State VARCHAR(50),           -- Stan/region
    Product_Category VARCHAR(100), -- Kategoria produktu
    Sub_Category VARCHAR(100),   -- Podkategoria
    Product VARCHAR(100),        -- Nazwa produktu
    Order_Quantity INT,          -- Ilość zamówiona
    Unit_Cost DECIMAL(10,2),     -- Koszt jednostkowy
    Unit_Price DECIMAL(10,2),    -- Cena jednostkowa
    Profit DECIMAL(10,2),        -- Zysk
    Cost DECIMAL(10,2),          -- Łączny koszt
    Revenue DECIMAL(10,2)        -- Łączny przychód
);

LOAD DATA LOCAL INFILE 'C:/Users/Sergi/Downloads/sales_data.csv'
INTO TABLE sales
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
