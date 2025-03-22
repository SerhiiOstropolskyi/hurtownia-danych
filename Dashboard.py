import pandas as pd
from sqlalchemy import create_engine, text
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

# Ustawienie połączenia z bazą danych
DATABASE_URI = "mysql+pymysql://Sergiusz:Ost-MySQL123@localhost:3306/hurtownia"
engine = create_engine(DATABASE_URI, echo=False)

def query_db(query, params=None):
    """Wykonuje zapytanie SQL z opcjonalnymi parametrami i zwraca wynik jako DataFrame."""
    with engine.connect() as conn:
        if params:
            df = pd.read_sql(text(query), conn, params=params)
        else:
            df = pd.read_sql(text(query), conn)
    return df

def get_total_sales(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT SUM(f.revenue) as total_sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause};
    """
    df = query_db(query, params)
    if df.empty or pd.isna(df.iloc[0]['total_sales']):
        return 0
    return df.iloc[0]['total_sales']

def get_transaction_count(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT COUNT(*) as transaction_count
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause};
    """
    df = query_db(query, params)
    if df.empty or pd.isna(df.iloc[0]['transaction_count']):
        return 0
    return df.iloc[0]['transaction_count']

def get_average_order_value(date_from=None, date_to=None):
    total = get_total_sales(date_from, date_to)
    count = get_transaction_count(date_from, date_to)
    return total / count if count else 0

def get_monthly_sales(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT d.year, d.month, d.month_name, SUM(f.revenue) as sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY d.year, d.month, d.month_name
    ORDER BY d.year, d.month;
    """
    return query_db(query, params)

def get_top_products(date_from=None, date_to=None, limit=10):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT p.product as product_name, SUM(f.revenue) as total_sales
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY p.product
    ORDER BY total_sales DESC
    LIMIT {limit};
    """
    return query_db(query, params)

def get_sales_by_location(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT c.country, c.state, SUM(f.revenue) as total_sales
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY c.country, c.state;
    """
    return query_db(query, params)

def get_customer_segmentation(date_from=None, date_to=None):
    """
    Segmentacja klientów metodą RFM:
    - Recency: liczba dni od ostatniego zakupu
    - Frequency: liczba transakcji
    - Monetary: suma przychodów
    """
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT c.customer_id, MAX(d.date_key) as last_purchase, COUNT(*) as frequency, SUM(f.revenue) as monetary
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY c.customer_id;
    """
    df = query_db(query, params)
    df['last_purchase'] = pd.to_datetime(df['last_purchase'])
    today = pd.Timestamp.today()
    df['recency'] = (today - df['last_purchase']).dt.days
    return df

def get_recent_transactions(date_from=None, date_to=None, limit=10):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT f.sale_id, d.date_key as sale_date, c.country, c.state, p.product, f.order_quantity, f.revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_product p ON f.product_id = p.product_id
    {where_clause}
    ORDER BY d.date_key DESC
    LIMIT {limit};
    """
    return query_db(query, params)

def get_dealsize_analysis(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT CASE 
             WHEN f.order_quantity < 10 THEN 'Small'
             WHEN f.order_quantity < 20 THEN 'Medium'
             ELSE 'Large'
           END as dealsize_category,
           SUM(f.revenue) as total_sales
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY dealsize_category;
    """
    return query_db(query, params)

def get_total_quantity(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT SUM(f.order_quantity) as total_quantity
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause};
    """
    df = query_db(query, params)
    if df.empty or pd.isna(df.iloc[0]['total_quantity']):
        return 0
    return df.iloc[0]['total_quantity']

def get_unique_customers(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT COUNT(DISTINCT f.customer_id) as unique_customers
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause};
    """
    df = query_db(query, params)
    if df.empty or pd.isna(df.iloc[0]['unique_customers']):
        return 0
    return df.iloc[0]['unique_customers']

def get_top_category(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT p.product_category as product_category, SUM(f.order_quantity) as total_quantity
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY p.product_category
    ORDER BY total_quantity DESC
    LIMIT 1;
    """
    df = query_db(query, params)
    if df.empty:
        return "Brak danych"
    return df.iloc[0]['product_category']

def get_customer_ranking(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT c.customer_id, c.customer_age, c.country, 
           COUNT(*) as order_count, 
           SUM(f.revenue) as total_sales, 
           AVG(f.revenue) as avg_order
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause}
    GROUP BY c.customer_id, c.customer_age, c.country
    ORDER BY total_sales DESC
    LIMIT 10;
    """
    return query_db(query, params)

def get_customer_locations(date_from=None, date_to=None):
    where_clause = ""
    params = {}
    if date_from and date_to:
        where_clause = "WHERE d.date_key BETWEEN :date_from AND :date_to"
        params = {"date_from": date_from, "date_to": date_to}
    query = f"""
    SELECT DISTINCT c.customer_id, c.country, c.state
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    JOIN dim_date d ON f.date_key = d.date_key
    {where_clause};
    """
    return query_db(query, params)

# Inicjalizacja aplikacji Dash z wykorzystaniem Bootstrapa
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Nowa struktura layoutu przy użyciu kontenera, wierszy i kolumn
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(html.H1("📊 Dashboard Hurtowni Danych", className="text-center my-4"), width=12)
    ),
    dbc.Row(
        dbc.Col(
            html.Div([
                html.Label("Zakres dat:"),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date_placeholder_text="Data początkowa",
                    end_date_placeholder_text="Data końcowa"
                )
            ]),
            width=12
        ),
        className="mb-4"
    ),
    dbc.Row(id='kpi-cards', className="mb-4"),
    
    dbc.Row(
        dbc.Col(html.H2("Trend przychodu w czasie", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(dcc.Graph(id='monthly-sales-graph'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Ranking 10 najlepiej sprzedających się produktów", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(dcc.Graph(id='top-products-graph'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Zaawansowana segmentacja klientów (RFM)", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(dcc.Graph(id='customer-segmentation-graph'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Przychód według lokalizacji - mapa choropleth", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(dcc.Graph(id='sales-geo-map'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Ostatnie transakcje", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(html.Div(id='recent-transactions'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Ranking klientów", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(html.Div(id='customer-ranking'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Lokalizacje klientów", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(dcc.Graph(id='customer-location-map'), width=12),
        className="mb-4"
    ),
    
    dbc.Row(
        dbc.Col(html.H2("Analiza wielkości zamówień", className="my-3"), width=12)
    ),
    dbc.Row(
        dbc.Col(dcc.Graph(id='dealsize-analysis'), width=12),
        className="mb-4"
    )
], fluid=True)

# Callbacky

@app.callback(
    Output('kpi-cards', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_kpi(start_date, end_date):
    total = get_total_sales(start_date, end_date)
    count = get_transaction_count(start_date, end_date)
    avg_order = get_average_order_value(start_date, end_date)
    total_quantity = get_total_quantity(start_date, end_date)
    unique_customers = get_unique_customers(start_date, end_date)
    top_category = get_top_category(start_date, end_date)
    
    cards = dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Całkowity przychód", className="card-title"),
                    html.P(f"${total:,.2f}", className="card-text")
                ])
            ),
            md=4, className="mb-3"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Liczba transakcji", className="card-title"),
                    html.P(f"{count}", className="card-text")
                ])
            ),
            md=4, className="mb-3"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Średnia wartość zamówienia", className="card-title"),
                    html.P(f"${avg_order:,.2f}", className="card-text")
                ])
            ),
            md=4, className="mb-3"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Ilość sprzedanych produktów", className="card-title"),
                    html.P(f"{total_quantity}", className="card-text")
                ])
            ),
            md=4, className="mb-3"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Liczba unikalnych klientów", className="card-title"),
                    html.P(f"{unique_customers}", className="card-text")
                ])
            ),
            md=4, className="mb-3"
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5("Najczęściej sprzedawana kategoria", className="card-title"),
                    html.P(f"{top_category}", className="card-text")
                ])
            ),
            md=4, className="mb-3"
        )
    ])
    return cards

@app.callback(
    Output('monthly-sales-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_monthly_sales(start_date, end_date):
    df = get_monthly_sales(start_date, end_date)
    fig = px.line(df, x='month_name', y='sales', color='year', markers=True,
                  title="Przychód miesięczny")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('top-products-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_top_products(start_date, end_date):
    df = get_top_products(start_date, end_date)
    fig = px.bar(df, x='product_name', y='total_sales',
                 title="Najlepiej sprzedające się produkty")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('customer-segmentation-graph', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_customer_segmentation(start_date, end_date):
    df = get_customer_segmentation(start_date, end_date)
    fig = px.scatter(df, x='frequency', y='monetary', size='recency',
                     hover_data=['customer_id'],
                     title="Segmentacja klientów - Frequency vs Monetary (rozmiar: recency)")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('sales-geo-map', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_geo_map(start_date, end_date):
    df = get_sales_by_location(start_date, end_date)
    fig = px.choropleth(df, locations='country', locationmode='country names',
                        color='total_sales', hover_name='country',
                        title="Przychód według krajów")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('recent-transactions', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_recent_transactions(start_date, end_date):
    df = get_recent_transactions(start_date, end_date)
    table = html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in df.columns])
        ),
        html.Tbody([
            html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
            for i in range(len(df))
        ])
    ], style={'width': '100%', 'border': '1px solid black', 'borderCollapse': 'collapse'})
    return table

@app.callback(
    Output('customer-ranking', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_customer_ranking(start_date, end_date):
    df = get_customer_ranking(start_date, end_date)
    
    def compute_age_group(age):
        if age < 30:
            return "<30"
        elif age < 50:
            return "30-50"
        else:
            return "50+"
    
    df['age_group'] = df['customer_age'].apply(compute_age_group)
    table = html.Table([
        html.Thead(
            html.Tr([
                html.Th("Klient"),
                html.Th("Country"),
                html.Th("Grupa wiekowa"),
                html.Th("Liczba zamówień"),
                html.Th("Wartość sprzedaży"),
                html.Th("Średnia wartość zamówienia")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(row['customer_id']),
                html.Td(row['country']),
                html.Td(row['age_group']),
                html.Td(row['order_count']),
                html.Td(f"${row['total_sales']:,.2f}"),
                html.Td(f"${row['avg_order']:,.2f}")
            ]) for _, row in df.iterrows()
        ])
    ], style={'width': '100%', 'border': '1px solid black', 'borderCollapse': 'collapse'})
    return table

@app.callback(
    Output('customer-location-map', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_customer_location_map(start_date, end_date):
    df = get_customer_locations(start_date, end_date)
    df_grouped = df.groupby(['country', 'state']).agg(num_customers=('customer_id', 'nunique')).reset_index()
    df_grouped['location'] = df_grouped.apply(
        lambda row: f"{row['state']}, {row['country']}" if pd.notnull(row['state']) and row['state'] != '' else row['country'], 
        axis=1
    )
    fig = px.scatter_geo(
        df_grouped, 
        locations='country', 
        locationmode='country names',
        size='num_customers',
        hover_name='location',
        hover_data={'num_customers': True, 'state': True, 'country': True},
        title="Lokalizacje klientów",
        projection="natural earth"
    )
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(
    Output('dealsize-analysis', 'figure'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_dealsize_analysis(start_date, end_date):
    df = get_dealsize_analysis(start_date, end_date)
    fig = px.pie(df, names='dealsize_category', values='total_sales',
                 title="Analiza wielkości zamówień")
    fig.update_layout(template="plotly_white")
    return fig

if __name__ == '__main__':
    app.run(debug=True)
    # Pod linkiem: http://localhost:8050/
