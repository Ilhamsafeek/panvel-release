"""
Task Management API Endpoints
File: app/api/v1/endpoints/tasks.py - UPDATED FOR MULTIPLE ASSIGNEES
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
import pymysql
from fastapi import Query

from app.core.config import settings
from app.core.security import get_current_user, require_admin, require_admin_or_employee, get_db_connection, require_admin_or_dept_leader
router = APIRouter()


# ========== PYDANTIC MODELS ==========

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    client_id: int
    assigned_to: Optional[List[int]] = []  # Changed to list for multiple employees
    priority: str = "medium"  # low, medium, high, urgent
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[List[int]] = None  # Changed to list
    priority: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed
    due_date: Optional[date] = None


# ========== TASK CRUD ENDPOINTS ==========

@router.get("/all", summary="Get all tasks with multiple assignees")
async def get_all_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_dept_leader)  # CHANGED THIS LINE
):
    """
    Get all tasks in the system with their assigned employees
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT 
                t.task_id,
                t.task_title as title,
                t.task_description as description,
                t.priority,
                t.status,
                t.due_date,
                t.created_at,
                client.full_name as client_name,
                client.user_id as client_id,
                creator.full_name as created_by_name,
                creator.user_id as created_by_id,
                GROUP_CONCAT(DISTINCT emp.user_id) as assigned_employee_ids,
                GROUP_CONCAT(DISTINCT emp.full_name SEPARATOR ', ') as assigned_employees
            FROM tasks t
            LEFT JOIN users client ON t.client_id = client.user_id
            LEFT JOIN users creator ON t.assigned_by = creator.user_id
            LEFT JOIN task_assignments ta ON t.task_id = ta.task_id
            LEFT JOIN users emp ON ta.employee_id = emp.user_id
            WHERE 1=1
        """
        
        params = []
        
        if status:
            query += " AND t.status = %s"
            params.append(status)
        
        if priority:
            query += " AND t.priority = %s"
            params.append(priority)
        
        query += """ 
            GROUP BY t.task_id, t.task_title, t.task_description, t.priority, 
                     t.status, t.due_date, t.created_at, client.full_name, client.user_id,
                     creator.full_name, creator.user_id
            ORDER BY t.due_date ASC, t.priority DESC, t.created_at DESC
        """
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        # Convert datetime to string and format assigned employees
        for task in tasks:
            if task.get('due_date'):
                task['due_date'] = task['due_date'].isoformat()
            if task.get('created_at'):
                task['created_at'] = task['created_at'].isoformat()
            
            # Convert comma-separated IDs to list
            if task.get('assigned_employee_ids'):
                task['assigned_employee_ids'] = [int(id) for id in task['assigned_employee_ids'].split(',')]
            else:
                task['assigned_employee_ids'] = []
                task['assigned_employees'] = 'Unassigned'
        
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
        
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/my-tasks", summary="Get employee's assigned tasks")
async def get_my_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get tasks assigned to the current employee
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            SELECT 
                t.task_id,
                t.task_title as title,
                t.task_description as description,
                t.priority,
                t.status,
                t.due_date,
                t.created_at,
                u.full_name as client_name,
                u.user_id as client_id
            FROM tasks t
            LEFT JOIN users u ON t.client_id = u.user_id
            INNER JOIN task_assignments ta ON t.task_id = ta.task_id
            WHERE ta.employee_id = %s
        """
        
        params = [current_user['user_id']]
        
        if status:
            query += " AND t.status = %s"
            params.append(status)
        
        query += " ORDER BY t.due_date ASC, t.priority DESC"
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        # Convert datetime to string
        for task in tasks:
            if task.get('due_date'):
                task['due_date'] = task['due_date'].isoformat()
            if task.get('created_at'):
                task['created_at'] = task['created_at'].isoformat()
        
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
        
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/pending", summary="Get pending tasks")
async def get_pending_tasks(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(require_admin_or_employee)
):
    """Get pending tasks for dashboard"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                t.task_id,
                t.task_title,
                t.task_description,
                t.priority,
                t.status,
                t.due_date,
                t.created_at,
                c.full_name as client_name,
                GROUP_CONCAT(DISTINCT emp.full_name SEPARATOR ', ') as assigned_to_name
            FROM tasks t
            LEFT JOIN users c ON t.client_id = c.user_id
            LEFT JOIN task_assignments ta ON t.task_id = ta.task_id
            LEFT JOIN users emp ON ta.employee_id = emp.user_id
            WHERE t.status IN ('pending', 'in_progress')
            GROUP BY t.task_id
            ORDER BY 
                CASE t.priority 
                    WHEN 'urgent' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                END,
                t.due_date ASC
            LIMIT %s
        """, (limit,))
        
        tasks = cursor.fetchall()
        
        # Convert datetime objects
        for task in tasks:
            if task.get('due_date'):
                task['due_date'] = task['due_date'].isoformat()
            if task.get('created_at'):
                task['created_at'] = task['created_at'].isoformat()
        
        return {
            "success": True,
            "tasks": tasks
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending tasks: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/stats", summary="Get task statistics")
async def get_task_stats(
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get task statistics for current user
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        stats = {}
        
        if current_user['role'] == 'admin':
            # Admin sees all tasks
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'completed' AND DATE(updated_at) = CURDATE() THEN 1 ELSE 0 END) as completed_today,
                    SUM(CASE WHEN due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as upcoming_deadlines
                FROM tasks
            """)
        else:
            # Employee sees only their tasks
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN t.status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN t.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN t.status = 'completed' AND DATE(t.updated_at) = CURDATE() THEN 1 ELSE 0 END) as completed_today,
                    SUM(CASE WHEN t.due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as upcoming_deadlines
                FROM tasks t
                INNER JOIN task_assignments ta ON t.task_id = ta.task_id
                WHERE ta.employee_id = %s
            """, (current_user['user_id'],))
        
        stats = cursor.fetchone()
        
        # Get assigned clients count for employees
        if current_user['role'] == 'employee':
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM employee_assignments
                WHERE employee_id = %s
            """, (current_user['user_id'],))
            stats['assigned_clients'] = cursor.fetchone()['count']
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"Error fetching task stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task stats: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@router.post("/create", summary="Create new task with multiple assignees")
async def create_task(
    task: TaskCreate,
    current_user: dict = Depends(require_admin_or_dept_leader)  # CHANGED THIS LINE
):
    """
    Create a new task and assign it to multiple employees
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert task (assigned_to is NULL since we use task_assignments table)
        cursor.execute("""
            INSERT INTO tasks (
                client_id, assigned_to, assigned_by,
                task_title, task_description, priority, due_date, status
            ) VALUES (%s, NULL, %s, %s, %s, %s, %s, 'pending')
        """, (
            task.client_id,
            current_user['user_id'],
            task.title,
            task.description,
            task.priority,
            task.due_date
        ))
        
        task_id = cursor.lastrowid
        
        # Insert multiple employee assignments
        if task.assigned_to and len(task.assigned_to) > 0:
            for employee_id in task.assigned_to:
                cursor.execute("""
                    INSERT INTO task_assignments (task_id, employee_id)
                    VALUES (%s, %s)
                """, (task_id, employee_id))
        
        connection.commit()
        
        return {
            "success": True,
            "message": f"Task created and assigned to {len(task.assigned_to) if task.assigned_to else 0} employee(s)",
            "task_id": task_id,
            "assigned_count": len(task.assigned_to) if task.assigned_to else 0
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.patch("/{task_id}", summary="Update task")
async def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Update task details including reassigning to different employees
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if task exists
        cursor.execute("SELECT task_id FROM tasks WHERE task_id = %s", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Build update query for basic task fields
        update_fields = []
        values = []
        
        if task.title is not None:
            update_fields.append("task_title = %s")
            values.append(task.title)
        
        if task.description is not None:
            update_fields.append("task_description = %s")
            values.append(task.description)
        
        if task.priority is not None:
            update_fields.append("priority = %s")
            values.append(task.priority)
        
        if task.status is not None:
            update_fields.append("status = %s")
            values.append(task.status)
        
        if task.due_date is not None:
            update_fields.append("due_date = %s")
            values.append(task.due_date)
        
        # Update basic task fields if any
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(task_id)
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = %s"
            cursor.execute(query, values)
        
        # Update employee assignments if provided
        if task.assigned_to is not None:
            # Delete existing assignments
            cursor.execute("DELETE FROM task_assignments WHERE task_id = %s", (task_id,))
            
            # Insert new assignments
            if len(task.assigned_to) > 0:
                for employee_id in task.assigned_to:
                    cursor.execute("""
                        INSERT INTO task_assignments (task_id, employee_id)
                        VALUES (%s, %s)
                    """, (task_id, employee_id))
        
        connection.commit()
        
        return {
            "success": True,
            "message": "Task updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.delete("/{task_id}", summary="Delete task")
async def delete_task(
    task_id: int,
    current_user: dict = Depends(require_admin_or_dept_leader)  # CHANGE THIS LINE
):
    """
    Delete a task (assignments will be deleted automatically via CASCADE)
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return {
            "success": True,
            "message": "Task deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error deleting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@router.get("/{task_id}", summary="Get task details with all assigned employees")
async def get_task_details(
    task_id: int,
    current_user: dict = Depends(require_admin_or_employee)
):
    """
    Get detailed information about a specific task including all assigned employees
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get task details
        cursor.execute("""
            SELECT 
                t.task_id,
                t.task_title as title,
                t.task_description as description,
                t.priority,
                t.status,
                t.due_date,
                t.created_at,
                t.updated_at,
                client.full_name as client_name,
                client.user_id as client_id,
                creator.full_name as created_by_name,
                creator.user_id as created_by_id
            FROM tasks t
            LEFT JOIN users client ON t.client_id = client.user_id
            LEFT JOIN users creator ON t.assigned_by = creator.user_id
            WHERE t.task_id = %s
        """, (task_id,))
        
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Get all assigned employees for this task
        cursor.execute("""
            SELECT 
                emp.user_id,
                emp.full_name,
                emp.email,
                ta.assigned_at
            FROM task_assignments ta
            JOIN users emp ON ta.employee_id = emp.user_id
            WHERE ta.task_id = %s
            ORDER BY ta.assigned_at ASC
        """, (task_id,))
        
        assigned_employees = cursor.fetchall()
        
        # Check permission for employees - only if they are assigned to this task
        if current_user['role'] == 'employee':
            employee_ids = [emp['user_id'] for emp in assigned_employees]
            if current_user['user_id'] not in employee_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view tasks assigned to you"
                )
        
        # Convert datetime to string
        if task.get('due_date'):
            task['due_date'] = task['due_date'].isoformat()
        if task.get('created_at'):
            task['created_at'] = task['created_at'].isoformat()
        if task.get('updated_at'):
            task['updated_at'] = task['updated_at'].isoformat()
        
        # Format assigned employees
        for emp in assigned_employees:
            if emp.get('assigned_at'):
                emp['assigned_at'] = emp['assigned_at'].isoformat()
        
        task['assigned_employees'] = assigned_employees
        task['assigned_employee_ids'] = [emp['user_id'] for emp in assigned_employees]
        task['assigned_count'] = len(assigned_employees)
        
        return {
            "success": True,
            "task": task
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching task details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task details: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()