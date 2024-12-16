from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from models import PropertyFilter, ExportRequest
from database import get_db_connection
from export_utils import format_excel_worksheet, prepare_export_dataframe
import json
from datetime import datetime
from io import BytesIO
import pandas as pd
from models import PropertyFilter, ExportRequest
from export_utils import format_excel_worksheet, prepare_export_dataframe, add_export_info_sheet

router = APIRouter(prefix="/api")

@router.get("/properties")
async def get_properties(
    state: Optional[str] = None,
    city: Optional[str] = None,
    county: Optional[str] = None,
    zip_codes: Optional[str] = None,
    property_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = Query(None, regex="^(asc|desc)$")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                p.PropertyID,
                p.Property_Address,
                p.Property_Name,
                p.PropertyType,
                p.Building_Class,
                p.Secondary_Type,
                p.Market_Name,
                p.Submarket_Name,
                p.City,
                p.State,
                p.Zip,
                p.County_Name,
                p.Last_Sale_Date,
                p.Last_Sale_Price,
                p.Percent_Leased,
                p.Year_Built,
                p.Anchor_Tenants,
                p.Architect_Name,
                p.[Avg_Asking/SF],
                p.[Avg_Effective/SF],
                p.Building_Operating_Expenses,
                p.Cap_Rate,
                p.Ceiling_Ht,
                p.Constr_Status,
                p.Construction_Material,
                p.Developer_Name,
                p.Flood_Risk_Area,
                p.Land_Area__AC_,
                p.Land_Area__SF_,
                p.Latitude,
                p.Longitude,
                p.Market_Segment,
                p.Max_Building_Contiguous_Space,
                p.Number_Of_Stories,
                p.Operation_Type,
                p.Property_Location,
                p.Taxes_Total,
                p.Total_Buildings,
                p.Zoning,
                c.name as contact_name,
                c.phone,
                c.email
            FROM [dbo].[property] p
            LEFT JOIN [dbo].[relationship] r ON p.PropertyID = r.PropertyID
            LEFT JOIN [dbo].[contact] c ON r.contact_id = c.contact_id
            WHERE 1=1
        """
        params = []
        
        if state:
            query += " AND p.State = ?"
            params.append(state)
            
        if city:
            query += " AND p.City = ?"
            params.append(city)
            
        if county:
            query += " AND p.County_Name = ?"
            params.append(county)
            
        if zip_codes:
            zip_list = [z.strip() for z in zip_codes.split(',')]
            placeholders = ','.join('?' * len(zip_list))
            query += f" AND p.Zip IN ({placeholders})"
            params.extend(zip_list)
            
        if property_type:
            query += " AND p.PropertyType = ?"
            params.append(property_type)
            
        # Add sorting
        if sort_by:
            query += f" ORDER BY {sort_by} {sort_direction or 'ASC'}"
        else:
            query += " ORDER BY p.PropertyID"
            
        # Add pagination
        offset = (page - 1) * page_size
        query += f" OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
        
        print(f"Executing query: {query}")  # Debug print
        print(f"With parameters: {params}")  # Debug print
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(DISTINCT p.PropertyID)
            FROM [dbo].[property] p
            WHERE 1=1
        """
        # Add the same WHERE conditions
        if state:
            count_query += " AND p.State = ?"
        if city:
            count_query += " AND p.City = ?"
        if county:
            count_query += " AND p.County_Name = ?"
        if zip_codes:
            count_query += f" AND p.Zip IN ({placeholders})"
        if property_type:
            count_query += " AND p.PropertyType = ?"
            
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        return {
            "data": results,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        
    except Exception as e:
        print(f"Error executing query: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/filters")
async def get_filter_options():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get unique property types
        cursor.execute("SELECT DISTINCT PropertyType FROM [dbo].[property] WHERE PropertyType IS NOT NULL")
        property_types = [row[0] for row in cursor.fetchall()]
        
        # Get unique states
        cursor.execute("SELECT DISTINCT State FROM [dbo].[property] WHERE State IS NOT NULL")
        states = [row[0] for row in cursor.fetchall()]
        
        # Get unique cities
        cursor.execute("SELECT DISTINCT City FROM [dbo].[property] WHERE City IS NOT NULL")
        cities = [row[0] for row in cursor.fetchall()]
        
        # Get unique counties
        cursor.execute("SELECT DISTINCT County_Name FROM [dbo].[property] WHERE County_Name IS NOT NULL")
        counties = [row[0] for row in cursor.fetchall()]
        
        # Get unique zipcodes
        cursor.execute("SELECT DISTINCT Zip FROM [dbo].[property] WHERE Zip IS NOT NULL")
        zipcodes = [row[0] for row in cursor.fetchall()]
        
        return {
            "property_types": property_types,
            "states": states,
            "cities": cities,
            "counties": counties,
            "zipcodes": zipcodes
        }
        
    except Exception as e:
        print(f"Error fetching filters: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.get("/properties/export")
async def export_properties(
    format: str = Query(..., regex="^(csv|excel)$"),
    selected_ids: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    county: Optional[str] = None,
    zip_codes: Optional[str] = None,
    property_type: Optional[str] = None,
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build the base query with all needed fields
        query = """
            SELECT DISTINCT
                p.PropertyID,
                p.Property_Name,
                p.Property_Address,
                p.City,
                p.State,
                p.Zip,
                p.County_Name,
                p.PropertyType,
                p.Building_Class,
                p.Secondary_Type,
                p.Market_Name,
                p.Submarket_Name,
                p.Last_Sale_Date,
                p.Last_Sale_Price,
                p.Percent_Leased,
                p.Year_Built,
                p.Anchor_Tenants,
                p.Architect_Name,
                p.[Avg_Asking/SF],
                p.[Avg_Effective/SF],
                p.Building_Operating_Expenses,
                p.Cap_Rate,
                p.Ceiling_Ht,
                p.Constr_Status,
                p.Construction_Material,
                p.Developer_Name,
                p.Flood_Risk_Area,
                p.Land_Area__AC_,
                p.Land_Area__SF_,
                p.Latitude,
                p.Longitude,
                p.Market_Segment,
                p.Max_Building_Contiguous_Space,
                p.Number_Of_Stories,
                p.Operation_Type,
                p.Property_Location,
                p.Taxes_Total,
                p.Total_Buildings,
                p.Zoning,
                c.name as contact_name,
                c.phone,
                c.email
            FROM [dbo].[property] p
            LEFT JOIN [dbo].[relationship] r ON p.PropertyID = r.PropertyID
            LEFT JOIN [dbo].[contact] c ON r.contact_id = c.contact_id
            WHERE 1=1
        """
        
        params = []
        filters = {}
        
        # Add filters
        if selected_ids:
            try:
                id_list = json.loads(selected_ids)
                if id_list:
                    placeholders = ','.join('?' * len(id_list))
                    query += f" AND p.PropertyID IN ({placeholders})"
                    params.extend(id_list)
                    filters['Selected Properties'] = f"{len(id_list)} properties"
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid selected_ids format")
            
        if state:
            query += " AND p.State = ?"
            params.append(state)
            filters['State'] = state
            
        if city:
            query += " AND p.City = ?"
            params.append(city)
            filters['City'] = city
            
        if county:
            query += " AND p.County_Name = ?"
            params.append(county)
            filters['County'] = county
            
        if zip_codes:
            zip_list = [z.strip() for z in zip_codes.split(',')]
            placeholders = ','.join('?' * len(zip_list))
            query += f" AND p.Zip IN ({placeholders})"
            params.extend(zip_list)
            filters['ZIP Codes'] = zip_codes
            
        if property_type:
            query += " AND p.PropertyType = ?"
            params.append(property_type)
            filters['Property Type'] = property_type
            
        # Debug print
        print(f"Executing export query: {query}")
        print(f"With parameters: {params}")
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        if not results:
            raise HTTPException(status_code=404, detail="No data found matching the criteria")
        
        print(f"Found {len(results)} records to export")
        
        # Prepare DataFrame
        df = prepare_export_dataframe(results)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'csv':
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            filename = f'properties_export_{timestamp}.csv'
            media_type = 'text/csv'
            print(f"Created CSV export with {len(df)} rows")
            
        else:  # excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write main data sheet
                df.to_excel(writer, sheet_name='Properties', index=False)
                format_excel_worksheet(df, writer)
                
                # Add export info sheet
                add_export_info_sheet(writer, filters, len(df))
            
            output.seek(0)
            filename = f'properties_export_{timestamp}.xlsx'
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            print(f"Created Excel export with {len(df)} rows")
        
        return StreamingResponse(
            output,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": media_type
            }
        )
        
    except HTTPException as e:
        print(f"HTTP Exception in export: {str(e)}")
        raise e
    except Exception as e:
        print(f"Unexpected error in export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#test endpoint
@router.get("/test-connection")
async def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT TOP 1 * FROM [dbo].[contact]")
        result = cursor.fetchone()
        
        return {
            "status": "success",
            "message": "Database connection successful",
            "sample_data": dict(zip([column[0] for column in cursor.description], result)) if result else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()