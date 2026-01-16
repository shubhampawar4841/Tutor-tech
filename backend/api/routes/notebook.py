"""
Notebook API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()

# Try to import database functions
try:
    from database.db import (
        create_notebook as db_create_notebook,
        list_notebooks as db_list_notebooks,
        get_notebook as db_get_notebook,
        update_notebook as db_update_notebook,
        delete_notebook as db_delete_notebook,
        create_notebook_item as db_create_notebook_item,
        list_notebook_items as db_list_notebook_items,
        get_notebook_item as db_get_notebook_item,
        delete_notebook_item as db_delete_notebook_item,
        is_supabase_configured
    )
    USE_DATABASE = is_supabase_configured()
except ImportError:
    USE_DATABASE = False
    db_create_notebook = None
    db_list_notebooks = None
    db_get_notebook = None
    db_update_notebook = None
    db_delete_notebook = None
    db_create_notebook_item = None
    db_list_notebook_items = None
    db_get_notebook_item = None
    db_delete_notebook_item = None


class NotebookCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#3b82f6"
    icon: Optional[str] = "📓"


class NotebookItem(BaseModel):
    type: str  # solve, question, research, note
    content: Dict[str, Any]
    title: str


@router.get("/")
async def list_notebooks():
    """List all notebooks"""
    if not USE_DATABASE or not db_list_notebooks:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        notebooks = db_list_notebooks()
        return {
            "notebooks": notebooks,
            "total": len(notebooks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing notebooks: {str(e)}")


@router.post("/")
async def create_notebook(notebook: NotebookCreate):
    """Create a new notebook"""
    if not USE_DATABASE or not db_create_notebook:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        result = db_create_notebook(
            name=notebook.name,
            description=notebook.description or "",
            color=notebook.color or "#3b82f6",
            icon=notebook.icon or "📓"
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create notebook - no data returned")
        return result
    except ValueError as e:
        # Supabase not configured
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"[ERROR] Failed to create notebook: {error_detail}")
        traceback.print_exc()
        # Check if it's a table doesn't exist error
        if "does not exist" in error_detail.lower() or "relation" in error_detail.lower():
            raise HTTPException(
                status_code=500, 
                detail="Notebooks table not found. Please run the database schema: backend/database/schema_notebook.sql"
            )
        raise HTTPException(status_code=500, detail=f"Error creating notebook: {error_detail}")


@router.get("/{notebook_id}")
async def get_notebook(notebook_id: str):
    """Get notebook details and items"""
    if not USE_DATABASE or not db_get_notebook or not db_list_notebook_items:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        notebook = db_get_notebook(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")
        
        # Get items
        items = db_list_notebook_items(notebook_id)
        
        return {
            **notebook,
            "items": items,
            "item_count": len(items)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notebook: {str(e)}")


@router.post("/{notebook_id}/items")
async def add_item(notebook_id: str, item: NotebookItem):
    """Add item to notebook"""
    if not USE_DATABASE or not db_create_notebook_item or not db_get_notebook:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Verify notebook exists
        notebook = db_get_notebook(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")
        
        # Create item
        result = db_create_notebook_item(
            notebook_id=notebook_id,
            item_type=item.type,
            title=item.title,
            content=item.content
        )
        
        return {
            "message": "Item added successfully",
            "item_id": result.get("id"),
            "item": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding item: {str(e)}")


@router.delete("/{notebook_id}/items/{item_id}")
async def delete_item(notebook_id: str, item_id: str):
    """Delete item from notebook"""
    if not USE_DATABASE or not db_delete_notebook_item or not db_get_notebook_item:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Verify item exists and belongs to notebook
        item = db_get_notebook_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if item.get("notebook_id") != notebook_id:
            raise HTTPException(status_code=403, detail="Item does not belong to this notebook")
        
        # Delete item
        success = db_delete_notebook_item(item_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete item")
        
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


@router.delete("/{notebook_id}")
async def delete_notebook(notebook_id: str):
    """Delete a notebook"""
    if not USE_DATABASE or not db_delete_notebook or not db_get_notebook:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        # Verify notebook exists
        notebook = db_get_notebook(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail="Notebook not found")
        
        # Delete notebook (cascade will delete items)
        success = db_delete_notebook(notebook_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete notebook")
        
        return {"message": "Notebook deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting notebook: {str(e)}")







