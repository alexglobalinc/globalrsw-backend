# export_utils.py
import pandas as pd
from typing import Dict, List
from datetime import datetime

def format_excel_worksheet(df: pd.DataFrame, writer: pd.ExcelWriter) -> None:
    """Format Excel worksheet with proper styling and column widths"""
    worksheet = writer.sheets['Properties']
    
    # Define formats
    header_format = writer.book.add_format({
        'bold': True,
        'fg_color': '#4B5563',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    # Currency format for price fields
    currency_format = writer.book.add_format({
        'num_format': '$#,##0',
        'align': 'right'
    })
    
    # Percentage format
    percent_format = writer.book.add_format({
        'num_format': '0.00%',
        'align': 'right'
    })
    
    # Date format
    date_format = writer.book.add_format({
        'num_format': 'mm/dd/yyyy',
        'align': 'center'
    })
    
    # Number format
    number_format = writer.book.add_format({
        'num_format': '#,##0',
        'align': 'right'
    })

    # Auto-adjust column widths and apply formats
    for idx, col in enumerate(df.columns):
        series = df[col]
        # Get maximum length of the column data
        max_len = max(
            series.astype(str).map(len).max(),
            len(str(series.name))
        ) + 2
        
        # Set column width (cap at 50 for readability)
        worksheet.set_column(idx, idx, min(max_len, 50))
        
        # Write header with formatting
        worksheet.write(0, idx, col, header_format)
        
        # Apply conditional formatting based on column content
        if 'price' in col.lower() or 'cost' in col.lower() or 'value' in col.lower():
            worksheet.set_column(idx, idx, None, currency_format)
        elif 'percent' in col.lower() or 'rate' in col.lower():
            worksheet.set_column(idx, idx, None, percent_format)
        elif 'date' in col.lower():
            worksheet.set_column(idx, idx, None, date_format)
        elif 'number' in col.lower() or 'count' in col.lower() or 'total' in col.lower():
            worksheet.set_column(idx, idx, None, number_format)

    # Freeze panes to keep headers visible
    worksheet.freeze_panes(1, 0)
    
    # Add autofilter
    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

def prepare_export_dataframe(data: List[Dict]) -> pd.DataFrame:
    """Prepare DataFrame for export with proper column naming and ordering"""
    df = pd.DataFrame(data)
    
    # Define column mappings with desired order
    column_mappings = {
        'PropertyID': 'Property ID',
        'Property_Name': 'Property Name',
        'Property_Address': 'Address',
        'City': 'City',
        'State': 'State',
        'Zip': 'ZIP Code',
        'County_Name': 'County',
        'PropertyType': 'Property Type',
        'Building_Class': 'Building Class',
        'Secondary_Type': 'Secondary Type',
        'Market_Name': 'Market',
        'Submarket_Name': 'Submarket',
        'Last_Sale_Date': 'Last Sale Date',
        'Last_Sale_Price': 'Last Sale Price',
        'Percent_Leased': 'Percent Leased',
        'Year_Built': 'Year Built',
        'Anchor_Tenants': 'Anchor Tenants',
        'Architect_Name': 'Architect',
        'Avg_Asking/SF': 'Average Asking Rate/SF',
        'Avg_Effective/SF': 'Average Effective Rate/SF',
        'Building_Operating_Expenses': 'Operating Expenses',
        'Cap_Rate': 'Cap Rate',
        'Ceiling_Ht': 'Ceiling Height',
        'Constr_Status': 'Construction Status',
        'Construction_Material': 'Construction Material',
        'Developer_Name': 'Developer',
        'Flood_Risk_Area': 'Flood Risk Area',
        'Land_Area__AC_': 'Land Area (Acres)',
        'Land_Area__SF_': 'Land Area (SF)',
        'Latitude': 'Latitude',
        'Longitude': 'Longitude',
        'Market_Segment': 'Market Segment',
        'Max_Building_Contiguous_Space': 'Max Contiguous Space',
        'Number_Of_Stories': 'Number of Stories',
        'Operation_Type': 'Operation Type',
        'Property_Location': 'Property Location',
        'Taxes_Total': 'Total Taxes',
        'Total_Buildings': 'Total Buildings',
        'Zoning': 'Zoning',
        'contact_name': 'Contact Name',
        'phone': 'Contact Phone',
        'email': 'Contact Email'
    }
    
    # Rename columns and reorder
    df = df.rename(columns=column_mappings)
    
    # Reorder columns based on mapping order
    ordered_columns = [col for col in column_mappings.values() if col in df.columns]
    df = df[ordered_columns]
    
    # Convert data types
    type_conversions = {
        'Last Sale Date': 'datetime64[ns]',
        'Year Built': 'Int64',
        'Number of Stories': 'Int64',
        'Total Buildings': 'Int64',
        'Latitude': 'float64',
        'Longitude': 'float64',
        'Cap Rate': 'float64',
        'Percent Leased': 'float64'
    }
    
    for col, dtype in type_conversions.items():
        if col in df.columns:
            try:
                if dtype == 'datetime64[ns]':
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
            except Exception as e:
                print(f"Error converting {col} to {dtype}: {str(e)}")
    
    return df

def add_export_info_sheet(writer: pd.ExcelWriter, filters: Dict, total_records: int) -> None:
    """Add an information sheet to the Excel export"""
    info_sheet = writer.book.add_worksheet('Export Info')
    
    # Define format for headers
    header_format = writer.book.add_format({
        'bold': True,
        'font_size': 12,
        'bottom': 1
    })
    
    # Add export information
    info_sheet.write(0, 0, 'Export Information', header_format)
    info_sheet.write(1, 0, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    info_sheet.write(2, 0, f'Total Records: {total_records}')
    
    # Add filter information
    info_sheet.write(4, 0, 'Applied Filters:', header_format)
    row = 5
    for key, value in filters.items():
        if value:
            info_sheet.write(row, 0, key)
            info_sheet.write(row, 1, str(value))
            row += 1
    
    # Adjust column widths
    info_sheet.set_column(0, 0, 20)
    info_sheet.set_column(1, 1, 50)