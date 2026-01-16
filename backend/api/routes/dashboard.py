"""
Dashboard API Routes
"""
from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict

# Import database functions
try:
    from database.db import (
        list_knowledge_bases,
        list_documents,
        list_notebooks,
        list_notebook_items,
        list_guide_sessions,
        is_supabase_configured
    )
    USE_DATABASE = True
except ImportError:
    USE_DATABASE = False
    print("[WARNING] Database functions not available for dashboard")

router = APIRouter()


def get_activity_over_time(days: int = 30) -> List[Dict[str, Any]]:
    """Get activity data over the last N days"""
    if not USE_DATABASE:
        return []
    
    try:
        # Get all notebooks and their items
        notebooks = list_notebooks()
        all_items = []
        for notebook in notebooks:
            items = list_notebook_items(notebook.get("id", ""))
            all_items.extend(items)
        
        # Get guide sessions
        guide_sessions = list_guide_sessions()
        
        # Group by date
        activity_by_date = defaultdict(lambda: {
            "notebook_items": 0,
            "guide_sessions": 0,
            "notebooks": 0
        })
        
        # Process notebook items
        for item in all_items:
            created_at = item.get("created_at")
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
                    activity_by_date[str(date)]["notebook_items"] += 1
                except:
                    pass
        
        # Process guide sessions
        for session in guide_sessions:
            created_at = session.get("created_at")
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
                    activity_by_date[str(date)]["guide_sessions"] += 1
                except:
                    pass
        
        # Process notebooks
        for notebook in notebooks:
            created_at = notebook.get("created_at")
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
                    activity_by_date[str(date)]["notebooks"] += 1
                except:
                    pass
        
        # Generate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Build result with all dates
        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = str(current_date)
            activity = activity_by_date.get(date_str, {
                "notebook_items": 0,
                "guide_sessions": 0,
                "notebooks": 0
            })
            result.append({
                "date": date_str,
                **activity
            })
            current_date += timedelta(days=1)
        
        return result
    except Exception as e:
        print(f"[DASHBOARD] Error getting activity data: {e}")
        return []


@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    if not USE_DATABASE:
        return {
            "knowledge_bases": {"total": 0, "total_documents": 0},
            "notebooks": {"total": 0, "total_items": 0},
            "guide_sessions": {"total": 0, "completed": 0, "active": 0},
            "recent_activities": [],
            "activity_over_time": [],
            "system_status": {
                "llm_connected": False,
                "vector_db_ready": is_supabase_configured() if USE_DATABASE else False
            }
        }
    
    try:
        # Get knowledge bases
        knowledge_bases = list_knowledge_bases()
        total_documents = 0
        for kb in knowledge_bases:
            docs = list_documents(kb.get("id", ""))
            total_documents += len(docs)
        
        # Get notebooks
        notebooks = list_notebooks()
        total_items = 0
        for notebook in notebooks:
            items = list_notebook_items(notebook.get("id", ""))
            total_items += len(items)
        
        # Get guide sessions
        guide_sessions = list_guide_sessions()
        completed_sessions = [s for s in guide_sessions if s.get("status") == "completed"]
        active_sessions = [s for s in guide_sessions if s.get("status") == "active"]
        
        # Get activity over time (last 30 days)
        activity_over_time = get_activity_over_time(30)
        
        return {
            "knowledge_bases": {
                "total": len(knowledge_bases),
                "total_documents": total_documents
            },
            "notebooks": {
                "total": len(notebooks),
                "total_items": total_items
            },
            "guide_sessions": {
                "total": len(guide_sessions),
                "completed": len(completed_sessions),
                "active": len(active_sessions)
            },
            "recent_activities": [],
            "activity_over_time": activity_over_time,
            "system_status": {
                "llm_connected": True,  # Assume connected if we can query DB
                "vector_db_ready": is_supabase_configured()
            }
        }
    except Exception as e:
        print(f"[DASHBOARD] Error getting stats: {e}")
        return {
            "knowledge_bases": {"total": 0, "total_documents": 0},
            "notebooks": {"total": 0, "total_items": 0},
            "guide_sessions": {"total": 0, "completed": 0, "active": 0},
            "recent_activities": [],
            "activity_over_time": [],
            "system_status": {
                "llm_connected": False,
                "vector_db_ready": False
            }
        }


@router.get("/recent")
async def get_recent_activities():
    """Get recent activities"""
    if not USE_DATABASE:
        return {"activities": [], "total": 0}
    
    try:
        activities = []
        
        # Get recent notebooks
        notebooks = list_notebooks()
        for notebook in notebooks[:5]:  # Last 5
            activities.append({
                "type": "notebook_created",
                "title": f"Created notebook: {notebook.get('name', 'Unknown')}",
                "timestamp": notebook.get("created_at", ""),
                "data": notebook
            })
        
        # Get recent guide sessions
        guide_sessions = list_guide_sessions()
        for session in guide_sessions[:5]:  # Last 5
            activities.append({
                "type": "guide_started",
                "title": f"Started learning guide",
                "timestamp": session.get("created_at", ""),
                "data": session
            })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "activities": activities[:10],  # Top 10 most recent
            "total": len(activities)
        }
    except Exception as e:
        print(f"[DASHBOARD] Error getting recent activities: {e}")
        return {"activities": [], "total": 0}








