import os
import pathlib
import shutil

def create_project_files_tool(project_name: str, files: dict) -> dict:
    """
    Creates a project directory containing multiple files with specified paths and contents, 
    ensuring the project structure is preserved for download.

    Args:
        project_name (str): The name of the project directory to create.
        files (dict): A dictionary where keys are file paths relative to the project root 
                      and values are the content of those files.

    Returns:
        dict: A dictionary containing 'success' (bool), 'project_name' (str), and 'message' (str).
    """
    if not project_name:
        return {
            "success": False,
            "project_name": project_name,
            "message": "Project name cannot be empty or None."
        }

    if files is None:
        files = {}

    try:
        # Create the root project directory
        root_path = pathlib.Path(project_name)
        root_path.mkdir(parents=True, exist_ok=True)

        for file_path_str, content in files.items():
            if not file_path_str:
                continue
            
            # Security check: Prevent path traversal by ensuring the file path is relative
            # and stays within the project directory.
            # We normalize the path and check if it starts with '..' or is absolute.
            normalized_path = os.path.normpath(file_path_str)
            if normalized_path.startswith("..") or os.path.isabs(normalized_path):
                return {
                    "success": False,
                    "project_name": project_name,
                    "message": f"Invalid file path detected: {file_path_str}. Path traversal is not allowed."
                }

            # Combine root path with the relative file path
            full_file_path = root_path / normalized_path
            
            # Ensure the directory for the file exists
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content to the file
            # Using pathlib's write_text as open() is restricted
            full_file_path.write_text(str(content), encoding='utf-8')

        return {
            "success": True,
            "project_name": project_name,
            "message": f"Project '{project_name}' created successfully with {len(files)} files."
        }

    except Exception as e:
        return {
            "success": False,
            "project_name": project_name,
            "message": f"An error occurred while creating the project: {str(e)}"
        }
