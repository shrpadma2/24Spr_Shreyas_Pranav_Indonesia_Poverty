import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import pandas as pd




# Load datasets
df_2019 = pd.read_csv('my_data.csv')
df_2020 = pd.read_csv('my_data1.csv')

# Standardize column names for both datasets
df_2019.rename(columns={'r101n': 'Province', 'r403': 'FuelType', 'r404': 'WaterSource', 'r405a': 'DefecationFacility','r502ak2': 'NumberOfHospitals', 'r502ak3': 'AvgDistanceToHospital', 'r1302': 'ComputerStatus', 'r701a': 'TransportType', 'r703a': 'CableTelephone', 'r703b': 'CellPhoneUsage', 'r1201': 'BUMDesBusinessUnits', 'r1203': 'VillageMarkets', 'r1204': 'BoatMooring'}, inplace=True)
df_2020.rename(columns={'R101N': 'Province', 'R503B': 'FuelType', 'R508': 'WaterSource', 'R507A': 'DefecationFacility','R603AK2': 'NumberOfHospitals', 'R603AK3': 'AvgDistanceToHospital', 'R806A': 'ComputerStatus', 'R801A': 'TransportType', 'R803A': 'CableTelephone', 'R803B': 'CellPhoneUsage', 'R1202': 'BUMDesBusinessUnits', 'R1203': 'VillageMarkets', 'R1204': 'BoatMooring'}, inplace=True)


# Assuming 'i' iterates over school types and 'j' over data types
column_rename_2019 = {f'r501{"abcdefghij"[i]}k{j}': f'EduType{i}_{j}' for i in range(10) for j in range(2, 6)}
column_rename_2020 = {f'R601{"ABCDEFGHIJ"[i]}K{j}': f'EduType{i}_{j}' for i in range(10) for j in range(2, 6)}

# Apply renaming
df_2019.rename(columns=column_rename_2019, inplace=True)
df_2020.rename(columns=column_rename_2020, inplace=True)

transport_mapping = {   
    1: 'Land',
    2: 'Land/Water',
    3: 'Land and Water',
    4: 'Air'
}

def process_transport_data(df, mapping):
    # Map the numerical responses to the defined categories
    df['TransportType'] = df['TransportType'].map(mapping)

    # Group by Province and TransportType, then count the occurrences
    transport_grouped = df.groupby(['Province', 'TransportType']).size().unstack(fill_value=0)
    transport_grouped = transport_grouped.apply(lambda x: (x / x.sum()) * 100, axis=1)  # Percentage per province

    return transport_grouped

transport_data_2019 = process_transport_data(df_2019, transport_mapping)
transport_data_2020 = process_transport_data(df_2020, transport_mapping)

# Function to process cable telephone data
def process_cable_telephone_data(df):
    # Normalize per 1000 families
    df['CableTelephone_per_1000'] = df['CableTelephone'] / df['Total Families'] * 1000
    return df.groupby('Province')['CableTelephone_per_1000'].mean().reset_index()

cell_phone_usage_mapping = {
    1: 'Most of the citizens',
    2: 'A small portion of citizens',
    3: 'None'
}

df_2019['CellPhoneUsage'] = df_2019['CellPhoneUsage'].map(cell_phone_usage_mapping)
df_2020['CellPhoneUsage'] = df_2020['CellPhoneUsage'].map(cell_phone_usage_mapping)

def process_cell_phone_data(df):
    # Group by Province and calculate the percentage of each cell phone usage category
    cell_phone_data = df.groupby(['Province', 'CellPhoneUsage']).size().unstack(fill_value=0)
    cell_phone_data = cell_phone_data.apply(lambda x: (x / x.sum()) * 100, axis=1)  # Convert counts to percentages
    return cell_phone_data

# Process the data for each year
cable_telephone_data_2019 = process_cable_telephone_data(df_2019)
cable_telephone_data_2020 = process_cable_telephone_data(df_2020)

# Define mappings outside of the callback
fuel_mapping = {
    1: 'Gas Kota', 2: 'LPG 3kg', 3: 'LPG more than 3kg', 4: 'Kerosene', 5: 'Firewood', 6: 'Other'
}
water_mapping = {
    1: 'Branded bottled water', 2: 'Refill', 3: 'Plumbing with meter (PAM/PDAM)',
    4: 'Plumber without meter', 5: 'Wells or pumps', 6: 'Well', 
    7: 'Water springs', 8: 'River/lake/pond/reservoir/situ/embung/dam',
    9: 'Rainwater', 10: 'Others'
}
defecation_facility_mapping = {
    1: 'Own toilet', 2: 'Toilet together', 3: 'Public toilet', 4: 'Not a latrine'
}

computer_status_mapping = {
    1: 'Used',
    2: 'Rarely used',
    3: 'Not used',
    4: 'None'
}

def aggregate_education_data(df):
    # Define column patterns to sum and average
    sum_column_patterns = [f'EduType{i}_{j}' for i in range(10) for j in [2, 3]]
    mean_column_patterns = [f'EduType{i}_4' for i in range(10)]

    # Check if columns exist in the dataframe and select them
    sum_columns = [col for col in sum_column_patterns if col in df.columns]
    mean_columns = [col for col in mean_column_patterns if col in df.columns]

    # Perform the aggregation
    df['Sum_23'] = df[sum_columns].sum(axis=1) if sum_columns else 0
    df['Mean_4'] = df[mean_columns].mean(axis=1) if mean_columns else 0

    # Group by Province first before normalizing
    grouped_df = df.groupby('Province').agg({
        'Sum_23': 'sum',
        'Mean_4': 'mean',
        'Total Families': 'sum'  # Aggregate the total families to get a correct sum for each province
    }).reset_index()

    # Normalize per 1000 families after aggregating
    grouped_df['Sum_23_per_1000'] = (grouped_df['Sum_23'] / grouped_df['Total Families']) * 1000
    grouped_df['Mean_4_per_1000'] = (grouped_df['Mean_4'] / grouped_df['Total Families']) * 1000

    return grouped_df



# Process data for each year
education_data_2019 = aggregate_education_data(df_2019)
education_data_2020 = aggregate_education_data(df_2020)

def process_hospital_data(df):
    hospital_df = df.groupby('Province').agg({
        'NumberOfHospitals': 'sum', 
        'AvgDistanceToHospital': 'mean',
        'Total Families': 'sum'  # Sum the 'Total Families' for each province
    }).reset_index()
    
    # Now we calculate the number of hospitals per 100,000 families correctly
    hospital_df['NumberOfHospitalsPer100000'] = (hospital_df['NumberOfHospitals'] / hospital_df['Total Families']) * 100000
    
    return hospital_df


# ... (previous code remains the same)

# Create Dash app
app = dash.Dash(__name__)

# Define custom colors
colors = {
    'background': '#f2f2f2',
    'text': '#333333',
    'primary': '#ff5722',
    'secondary': '#ffc107',
    'accent': '#8bc34a'
}

from PIL import Image
# Open the logo image using PIL
pil_image = Image.open("logo.png")
import base64
import io

# Convert the PIL image to bytes
buffer = io.BytesIO()
pil_image.save(buffer, format='PNG')
buffer.seek(0)

# Encode the bytes as base64
image_url = base64.b64encode(buffer.getvalue()).decode()

app.layout = html.Div(style={'backgroundColor': colors['background'], 'padding': '20px', 'fontFamily': 'Arial, sans-serif'}, children=[
    html.Div(style={'textAlign': 'center', 'marginBottom': '30px'}, children=[
        html.H1("Indonesia Poverty and Equity Program Dashboard", style={'color': colors['text'], 'fontSize': '36px', 'fontWeight': 'bold'}),
        html.Img(src=f'data:image/png;base64,{image_url}', style={'width': '400px', 'height': '400px', 'marginTop': '10px'})
    ]),
    html.Div(style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '20px'}, children=[
        dcc.Dropdown(
            id='year-dropdown',
            options=[
                {'label': '2019', 'value': '2019'},
                {'label': '2020', 'value': '2020'}
            ],
            value='2020',
            style={'width': '200px', 'marginRight': '20px', 'borderRadius': '10px', 'backgroundColor': '#ffffff'}
        ),
        dcc.Dropdown(
            id='province-dropdown',
            options=[{'label': 'Select All', 'value': 'ALL'}] +
                    [{'label': province, 'value': province} for province in sorted(df_2020['Province'].unique())],
            value='ALL',  # Select all provinces by default
            multi=True,
            style={'width': '500px', 'borderRadius': '10px', 'backgroundColor': '#ffffff'}
        )
    ]),
    html.Div(className='row', children=[
        html.Div(className='col-md-6', children=[
            dcc.Graph(id='electricity-users-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='fuel-type-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='water-source-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='defecation-facility-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='hospital-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'})
        ]),
        html.Div(className='col-md-6', children=[
            dcc.Graph(id='computer-status-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='education-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='transportation-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='cable-telephone-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'}),
            dcc.Graph(id='cell-phone-usage-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'})
        ])
    ]),
    dcc.Graph(id='province-aggregate-graph', style={'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'})
])


# ... (callbacks and other code remain the same)

global hospital_df_all, province_stats_all
hospital_df_all = None
province_stats_all = None


@app.callback(
    [Output('electricity-users-graph', 'figure'),
     Output('fuel-type-graph', 'figure'),
     Output('water-source-graph', 'figure'),
     Output('defecation-facility-graph', 'figure'),
     Output('hospital-graph', 'figure'),
     Output('computer-status-graph', 'figure'),
     Output('education-graph', 'figure'),
     Output('transportation-graph', 'figure'),
     Output('cable-telephone-graph', 'figure'),
     Output('cell-phone-usage-graph', 'figure'),
     Output('province-aggregate-graph', 'figure')],
    [Input('year-dropdown', 'value'),
     Input('province-dropdown', 'value')]
)
def update_graph(selected_year, selected_provinces):
    global hospital_df_all, province_stats_all
    try:
        
        # Check if 'ALL' is selected and adjust the province list accordingly
        if 'ALL' in selected_provinces:
            if selected_year == '2019':
                selected_provinces = df_2019['Province'].unique()
            else:
                selected_provinces = df_2020['Province'].unique()

        

        df_selected = df_2019.copy() if selected_year == '2019' else df_2020.copy()

        
        df_selected = df_selected[df_selected['Province'].isin(selected_provinces)]
        
        df_selected['ComputerStatus'] = df_selected['ComputerStatus'].map(computer_status_mapping)
        computer_status_data = df_selected.groupby(['Province', 'ComputerStatus']).size().unstack(fill_value=0)
        computer_status_data = computer_status_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        computer_status_fig = px.bar(
            computer_status_data.reset_index(),
            x='Province',
            y=computer_status_data.columns,
            title="Computer Status per 1000 Offices by Province",
            labels={'value': 'Number of Offices', 'variable': 'Computer Status'},
            barmode='stack'
        )
        computer_status_fig.update_layout(
            title="Computer Status per 1000 Offices by Province",
            xaxis_title="Province",
            yaxis_title="Number of Offices",
            legend_title="Computer Status"
        )

        # Process hospital data for the selected year
        hospital_df = process_hospital_data(df_selected)
        national_average = hospital_df['NumberOfHospitalsPer100000'].mean()

        # Create the Plotly graph for hospital data
        hospital_fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add bar plot for the number of hospitals per 100,000 families
        hospital_fig.add_trace(
            go.Bar(
                x=hospital_df['Province'],
                y=hospital_df['NumberOfHospitalsPer100000'],
                name='Number of Hospitals per 100000 Families',
                marker_color='lightblue'
            ),
            secondary_y=False,
        )

        hospital_fig.add_trace(
            go.Scatter(
                x=hospital_df['Province'],
                y=hospital_df['AvgDistanceToHospital'],
                name='Average Distance to Nearest Hospital',
                mode='lines+markers',
                marker_color='darkorange',
                line=dict(width=2)
            ),
            secondary_y=True,
        )

        hospital_fig.add_trace(
            go.Scatter(
                x=hospital_df['Province'],
                y=[national_average]*len(hospital_df['Province']),
                name='National Average',
                mode='lines',
                line=dict(color="red", width=2, dash="dot"),
                hoverinfo='skip'
            ),
            secondary_y=False,
        )

        # Set titles, axes labels, and legend positioning
        hospital_fig.update_layout(
            title_text="Hospital Data Analysis",
            yaxis_title='Number of Hospitals per 100000 Families',
            legend=dict(
                x=0,
                y=1.0,
                traceorder='normal',
                bgcolor='rgba(255,255,255,0)',
                bordercolor='rgba(255,255,255,0)'
            )
        )

        hospital_fig.update_yaxes(title_text="Number of Hospitals per 100000 Families", secondary_y=False)
        hospital_fig.update_yaxes(title_text="Average Distance to Nearest Hospital (km)", secondary_y=True)


        # Process electricity data
        # Assuming you have columns 'PLN users by 1000' and 'Non-PLN users by 1000' in your dataframe
        grouped_electricity = df_selected.groupby('Province').agg({
            'PLN users by 1000': 'mean',
            'Non-PLN users by 1000': 'mean'
        }).reset_index()
        electricity_fig = px.bar(
            grouped_electricity,
            x='Province',
            y=['PLN users by 1000', 'Non-PLN users by 1000'],
            title="Electricity Usage by Province for 1000 Families",
            labels={'value': 'Number of Families', 'variable': 'Type of Electricity User'},
            barmode='stack'
        )
        electricity_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Number of Families",
            legend_title="Type of Electricity User"
        )

        # Process fuel data
        df_selected['FuelType'] = df_selected['FuelType'].map(fuel_mapping)
        fuel_data = df_selected.groupby(['Province', 'FuelType']).size().unstack(fill_value=0)
        fuel_data = fuel_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        fuel_fig = px.bar(
            fuel_data.reset_index(),
            x='Province',
            y=fuel_data.columns,
            title="Fuel Used for Cooking per 1000 Families by Province",
            labels={'value': 'Number of Families', 'variable': 'Fuel Type'},
            barmode='stack'
        )
        fuel_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Number of Families",
            legend_title="Fuel Type"
        )

        # Process water source data
        df_selected['WaterSource'] = df_selected['WaterSource'].map(water_mapping)
        water_data = df_selected.groupby(['Province', 'WaterSource']).size().unstack(fill_value=0)
        water_data = water_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        water_fig = px.bar(
            water_data.reset_index(),
            x='Province',
            y=water_data.columns,
            title="Water Source per 1000 Families by Province",
            labels={'value': 'Number of Families', 'variable': 'Water Source'},
            barmode='stack'
        )
        water_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Number of Families",
            legend_title="Water Source"
        )

        df_selected['DefecationFacility'] = df_selected['DefecationFacility'].map(defecation_facility_mapping)
        defecation_data = df_selected.groupby(['Province', 'DefecationFacility']).size().unstack(fill_value=0)
        defecation_data = defecation_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        defecation_facility_fig = px.bar(
            defecation_data.reset_index(),
            x='Province',
            y=defecation_data.columns,
            title="Defecation Facilities per 1000 Families by Province",
            labels={'value': 'Number of Families', 'variable': 'Defecation Facility'},
            barmode='stack'
        )
        defecation_facility_fig.update_layout(title="Defecation Facility Usage by Province for 1000 Families",
                                                xaxis_title="Province",
                                                yaxis_title="Number of Families",
                                                legend_title="Defecation Facility")
        
        education_data = education_data_2019 if selected_year == '2019' else education_data_2020
        education_data = education_data[education_data['Province'].isin(selected_provinces)]
        national_average_mean = education_data['Mean_4_per_1000'].mean()

        education_fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add bar plot for summed '2' and '3' columns
        education_fig.add_trace(
            go.Bar(
                x=education_data['Province'], 
                y=education_data['Sum_23_per_1000'],
                name='Sum of Public and Private Education Levels per 10000 Families'
            ),
            secondary_y=False
        )

        # Add line plot for averaged '4' columns
        education_fig.add_trace(
            go.Scatter(
                x=education_data['Province'], 
                y=education_data['Mean_4_per_1000'],
                name='Average Distance to Educational Facility',
                mode='lines+markers',
                marker_color='orange'
            ),
            secondary_y=True
        )

        education_fig.add_trace(
            go.Scatter(
                x=education_data['Province'], 
                y=[national_average_mean]*len(education_data),
                mode='lines',
                line=dict(color='blue', dash='dash'),
                name='National Avg Distance to Educational Institution'
            ),
            secondary_y=True
        )

        education_fig.update_layout(
            title_text='Educational Facilities and Distance Data by Province',
            yaxis_title='Total Educational Facilities per 10000 Families',
            yaxis2_title='Average Distance to Facilities (km)',
            legend_title='Legend'
        )

        transport_data = transport_data_2019 if selected_year == '2019' else transport_data_2020
        transport_data = transport_data[transport_data.index.isin(selected_provinces)]

        # Create the Plotly graph for transportation data
        transport_fig = px.bar(
            transport_data.reset_index(),
            x='Province',
            y=transport_data.columns,
            title="Means of Transportation per Province",
            labels={'value': 'Percentage of Responses', 'variable': 'Means of Transportation'},
            barmode='group'
        )
        transport_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Percentage of Responses",
            legend_title="Means of Transportation"
        )

        cable_telephone_data = cable_telephone_data_2019 if selected_year == '2019' else cable_telephone_data_2020
        cable_telephone_data = cable_telephone_data[cable_telephone_data['Province'].isin(selected_provinces)]
        cable_telephone_fig = px.bar(
        cable_telephone_data,
        x='Province',
        y='CableTelephone_per_1000',
        title='Cable Telephone Subscriptions per 1000 Families'
    )

        # Select the appropriate year's data for cell phone usage
        cell_phone_data = process_cell_phone_data(df_selected)
        cell_phone_data = cell_phone_data[cell_phone_data.index.isin(selected_provinces)]
        cell_phone_usage_fig = px.bar(
            cell_phone_data.reset_index(),
            x='Province',
            y=cell_phone_data.columns,
            title='Cell Phone Usage Distribution',
            labels={'value': 'Percentage of Citizens', 'variable': 'Cell Phone Usage'}
    )
        
        province_stats = df_selected.groupby('Province').agg({
            'BUMDesBusinessUnits': 'sum',
            'VillageMarkets': 'sum',
            'BoatMooring': 'sum',
            'Total Families':'sum'
        }).reset_index()



        province_statistics_fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add bar plots for BUMDes Business Units, Village Markets, and Boat Mooring
        province_statistics_fig.add_trace(
            go.Bar(name='BUMDes Business Units', x=province_stats['Province'], y=province_stats['BUMDesBusinessUnits']), secondary_y=False
        )

        province_statistics_fig.add_trace(
            go.Bar(name='Village Markets', x=province_stats['Province'], y=province_stats['VillageMarkets']), secondary_y=False
        )

        province_statistics_fig.add_trace(
            go.Bar(name='Boat Mooring', x=province_stats['Province'], y=province_stats['BoatMooring']), secondary_y=False
        )

        # Add a line plot for Total Families
        province_statistics_fig.add_trace(
            go.Scatter(name='Total Families', x=province_stats['Province'], y=province_stats['Total Families'], mode='lines+markers', line=dict(color='red', width=2)), secondary_y=True
        )

        # Set titles, axes labels, and legend positioning
        province_statistics_fig.update_layout(
            title='Provincial Statistics with Total Families',
            xaxis_title='Province',
            legend_title='Indicator',
            barmode='group'
        )

        # Set y-axes titles
        province_statistics_fig.update_yaxes(title_text='Count per Province', secondary_y=False)
        province_statistics_fig.update_yaxes(title_text='Total Families', secondary_y=True)
 


        return electricity_fig, fuel_fig, water_fig, defecation_facility_fig, hospital_fig, computer_status_fig, education_fig, transport_fig, cable_telephone_fig, cell_phone_usage_fig, province_statistics_fig
    except Exception as e:
        print(f"An error occurred: {e}")
        # Return blank figures in case of an error
        return {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

if __name__ == '__main__':
    app.run_server(debug=True)