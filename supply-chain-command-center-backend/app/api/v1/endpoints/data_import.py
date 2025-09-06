"""
Data Import Endpoints

This module provides endpoints for:
1. File upload (CSV, Excel)
2. Data cleaning using paraphrase models
3. Preview cleaned data
4. Import data to inventory collection
"""

import io
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import pandas as pd
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_database
# from app.models.inventory import InventoryItem, InventoryItemCreate  # Not needed for this implementation
from app.services.ml_services_simple import (
    paraphrase_service, 
    detect_file_encoding, 
    standardize_column_names
)

router = APIRouter()
logger = logging.getLogger(__name__)

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    upload_id: str
    file_info: Dict[str, Any]
    preview_data: List[Dict[str, Any]]
    column_mapping: Dict[str, str]

class DataCleaningResponse(BaseModel):
    """Response model for data cleaning"""
    success: bool
    message: str
    upload_id: str
    cleaned_data: List[Dict[str, Any]]
    changes_summary: Dict[str, Any]

class ImportDataRequest(BaseModel):
    """Request model for data import"""
    upload_id: str
    confirmed_data: List[Dict[str, Any]]
    import_options: Dict[str, Any] = {}

class ImportDataResponse(BaseModel):
    """Response model for data import"""
    success: bool
    message: str
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[str] = []

# In-memory storage for upload sessions (in production, use Redis)
upload_sessions: Dict[str, Dict[str, Any]] = {}

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> FileUploadResponse:
    """Upload and preview CSV/Excel file"""
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['csv', 'xlsx', 'xls']:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Please upload CSV or Excel files."
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Generate upload ID
        import uuid
        upload_id = str(uuid.uuid4())
        
        # Detect encoding for CSV files
        encoding = 'utf-8'
        if file_extension == 'csv':
            encoding = detect_file_encoding(content)
        
        # Parse file based on type
        try:
            if file_extension == 'csv':
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            else:  # Excel files
                df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
        
        # Basic validation
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(df) > 10000:  # Limit to 10k rows for performance
            df = df.head(10000)
            logger.warning(f"File truncated to 10000 rows for processing")
        
        # Standardize column names
        original_columns = df.columns.tolist()
        df = standardize_column_names(df)
        standardized_columns = df.columns.tolist()
        
        # Create column mapping for user reference
        column_mapping = dict(zip(original_columns, standardized_columns))
        
        # Get preview data (first 10 rows)
        preview_data = df.head(10).fillna("").to_dict('records')
        
        # Store session data
        upload_sessions[upload_id] = {
            'original_data': df.to_dict('records'),
            'file_info': {
                'filename': file.filename,
                'size': len(content),
                'rows': len(df),
                'columns': len(df.columns),
                'encoding': encoding
            },
            'column_mapping': column_mapping,
            'status': 'uploaded',
            'created_at': pd.Timestamp.now().isoformat()
        }
        
        logger.info(f"File uploaded successfully: {upload_id}")
        
        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            upload_id=upload_id,
            file_info=upload_sessions[upload_id]['file_info'],
            preview_data=preview_data,
            column_mapping=column_mapping
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/clean/{upload_id}", response_model=DataCleaningResponse)
async def clean_data(
    upload_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> DataCleaningResponse:
    """Clean data using paraphrase model"""
    
    # Validate upload session
    if upload_id not in upload_sessions:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    session = upload_sessions[upload_id]
    
    if session['status'] != 'uploaded':
        raise HTTPException(status_code=400, detail="Data has already been processed")
    
    try:
        # Get original data
        df = pd.DataFrame(session['original_data'])
        
        # Initialize paraphrase service
        if not paraphrase_service._initialized:
            await paraphrase_service.initialize()
        
        # Track changes
        changes_summary = {
            'total_rows': len(df),
            'cleaned_fields': 0,
            'text_fields_processed': []
        }
        
        # Define text columns to clean
        text_columns = ['name', 'category', 'supplier']
        
        # Clean text columns
        for column in text_columns:
            if column in df.columns:
                logger.info(f"Cleaning column: {column}")
                original_values = df[column].tolist()
                
                # Clean each value in the column
                for idx, value in enumerate(original_values):
                    if pd.notna(value) and str(value).strip():
                        # For demo purposes, use basic cleaning instead of full paraphrasing
                        # This is faster and more predictable
                        cleaned_value = paraphrase_service.clean_text(str(value))
                        df.iloc[idx, df.columns.get_loc(column)] = cleaned_value
                        changes_summary['cleaned_fields'] += 1
                
                changes_summary['text_fields_processed'].append(column)
        
        # Additional data validation and cleaning
        
        # Clean numeric fields
        if 'current_stock' in df.columns:
            df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce').fillna(0).astype(int)
        
        if 'unit_price' in df.columns:
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce').fillna(0.0)
        
        # Generate SKUs if missing or invalid
        if 'sku' in df.columns:
            df['sku'] = df['sku'].astype(str).str.strip()
            # Replace empty or 'nan' SKUs with generated ones
            mask = (df['sku'] == '') | (df['sku'] == 'nan') | df['sku'].isna()
            df.loc[mask, 'sku'] = ['AUTO_' + str(i).zfill(6) for i in range(1, mask.sum() + 1)]
        
        # Update session with cleaned data
        cleaned_data = df.fillna("").to_dict('records')
        session['cleaned_data'] = cleaned_data
        session['changes_summary'] = changes_summary
        session['status'] = 'cleaned'
        
        logger.info(f"Data cleaned successfully: {upload_id}")
        
        return DataCleaningResponse(
            success=True,
            message="Data cleaned successfully",
            upload_id=upload_id,
            cleaned_data=cleaned_data[:10],  # Return first 10 rows for preview
            changes_summary=changes_summary
        )
        
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning data: {str(e)}")


@router.post("/import", response_model=ImportDataResponse)
async def import_data(
    request: ImportDataRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ImportDataResponse:
    """Import cleaned data to inventory collection"""
    
    # Validate upload session
    if request.upload_id not in upload_sessions:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    session = upload_sessions[request.upload_id]
    
    try:
        # Get data to import
        data_to_import = request.confirmed_data
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        # Process each record
        for i, record in enumerate(data_to_import):
            try:
                # Validate required fields
                if not record.get('sku') or not record.get('name'):
                    errors.append(f"Row {i+1}: Missing required fields (sku or name)")
                    error_count += 1
                    continue
                
                # Check for duplicate SKU
                existing = await db.inventory.find_one({"sku": record['sku']})
                if existing:
                    if request.import_options.get('skip_duplicates', True):
                        skipped_count += 1
                        continue
                    else:
                        # Update existing record
                        update_data = {k: v for k, v in record.items() if v != ""}
                        await db.inventory.update_one(
                            {"sku": record['sku']},
                            {"$set": {**update_data, "updated_at": pd.Timestamp.now().isoformat()}}
                        )
                        imported_count += 1
                        continue
                
                # Create new inventory item
                inventory_data = {
                    "sku": record.get('sku', ''),
                    "name": record.get('name', ''),
                    "category": record.get('category', 'General'),
                    "current_stock": int(record.get('current_stock', 0)),
                    "unit_price": float(record.get('unit_price', 0.0)),
                    "supplier": record.get('supplier', 'Unknown'),
                    "warehouse_location": record.get('warehouse_location', 'Main'),
                    "reorder_point": int(record.get('reorder_point', 10)),
                    "max_stock": int(record.get('max_stock', 1000)),
                    "created_at": pd.Timestamp.now().isoformat(),
                    "updated_at": pd.Timestamp.now().isoformat()
                }
                
                # Insert into database
                await db.inventory.insert_one(inventory_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
                error_count += 1
                continue
        
        # Update session status
        session['status'] = 'imported'
        session['import_results'] = {
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'errors': errors
        }
        
        logger.info(f"Data import completed: {request.upload_id} - {imported_count} imported, {skipped_count} skipped, {error_count} errors")
        
        return ImportDataResponse(
            success=True,
            message=f"Import completed: {imported_count} records imported",
            imported_count=imported_count,
            skipped_count=skipped_count,
            error_count=error_count,
            errors=errors[:10]  # Return first 10 errors
        )
        
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")


@router.get("/session/{upload_id}")
async def get_upload_session(upload_id: str):
    """Get upload session details"""
    if upload_id not in upload_sessions:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    session = upload_sessions[upload_id]
    
    # Return session info without full data
    return {
        "upload_id": upload_id,
        "file_info": session['file_info'],
        "column_mapping": session['column_mapping'],
        "status": session['status'],
        "created_at": session['created_at'],
        "changes_summary": session.get('changes_summary'),
        "import_results": session.get('import_results')
    }


@router.delete("/session/{upload_id}")
async def delete_upload_session(upload_id: str):
    """Delete upload session"""
    if upload_id not in upload_sessions:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    del upload_sessions[upload_id]
    
    return {"message": "Upload session deleted successfully"}


@router.get("/sessions")
async def list_upload_sessions():
    """List all upload sessions"""
    sessions = []
    for upload_id, session in upload_sessions.items():
        sessions.append({
            "upload_id": upload_id,
            "filename": session['file_info']['filename'],
            "status": session['status'],
            "rows": session['file_info']['rows'],
            "created_at": session['created_at']
        })
    
    return {"sessions": sessions}
