import os
import mimetypes
import requests
from typing import List, Dict

class CanvasBulkUploader:
    def __init__(self, base_url: str, api_token: str, course_id: int):
        """
        Initializes the Canvas API Uploader.
        
        :param base_url: Your institution's Canvas URL (e.g., 'https://canvas.instructure.com')
        :param api_token: Your Canvas API access token
        :param course_id: The ID of the course you are modifying
        """
        # Ensure the base URL doesn't have a trailing slash and append the API path
        self.base_url = base_url.rstrip('/') + '/api/v1'
        self.headers = {
            "Authorization": f"Bearer {api_token}"
        }
        self.course_id = course_id

    def upload_file_to_course(self, file_path: str) -> int:
        """
        Uploads a single file to the course's root file system.
        
        :param file_path: Local path to the file
        :return: The Canvas file_id of the uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'

        # STEP 1: Tell Canvas we want to upload a file
        print(f"[{file_name}] Initiating upload...")
        init_url = f"{self.base_url}/courses/{self.course_id}/files"
        init_data = {
            "name": file_name,
            "size": file_size,
            "content_type": mime_type,
            "parent_folder_path": "/" # Uploads to root folder, change if needed
        }
        
        init_res = requests.post(init_url, headers=self.headers, data=init_data)
        init_res.raise_for_status()
        upload_data = init_res.json()

        upload_url = upload_data.get("upload_url")
        upload_params = upload_data.get("upload_params", {})

        # STEP 2: Upload the actual file data to the provided URL (usually AWS S3)
        print(f"[{file_name}] Uploading file data...")
        with open(file_path, 'rb') as f:
            files = {'file': f}
            # Note: We don't send the authorization header to the AWS URL
            upload_res = requests.post(upload_url, data=upload_params, files=files)
            upload_res.raise_for_status()

        # Canvas API dictates that the upload response will return the file object 
        # (or redirect to a URL that returns the file object). 
        # Requests handles the 301/302 redirects automatically.
        file_info = upload_res.json()
        
        if 'id' not in file_info:
            raise Exception(f"Failed to retrieve file ID from Canvas after upload. Response: {file_info}")

        print(f"[{file_name}] Successfully uploaded to Canvas (File ID: {file_info['id']})")
        return file_info['id']

    def attach_file_to_module(self, module_id: int, file_id: int, title: str = None) -> dict:
        """
        Attaches an uploaded file to a specific module.
        
        :param module_id: The ID of the module
        :param file_id: The Canvas file_id returned from upload_file_to_course
        :param title: Optional custom title for the module item
        :return: The API response dictionary
        """
        url = f"{self.base_url}/courses/{self.course_id}/modules/{module_id}/items"
        
        payload = {
            "module_item": {
                "type": "File",
                "content_id": file_id
            }
        }
        
        if title:
            payload["module_item"]["title"] = title

        res = requests.post(url, headers=self.headers, json=payload)
        res.raise_for_status()
        return res.json()

    def process_bulk_upload(self, upload_mapping: Dict[int, List[str]]):
        """
        Processes a bulk upload map.
        
        :param upload_mapping: Dictionary mapping module_id (int) to a list of file paths (list of str)
        """
        print(f"Starting bulk upload for Course {self.course_id}...\n" + "-"*40)
        
        for module_id, file_paths in upload_mapping.items():
            print(f"\nProcessing Module ID: {module_id}")
            for file_path in file_paths:
                try:
                    # 1. Upload to course
                    file_id = self.upload_file_to_course(file_path)
                    
                    # 2. Attach to module
                    print(f"[{os.path.basename(file_path)}] Attaching to module {module_id}...")
                    self.attach_file_to_module(module_id, file_id)
                    
                    print(f"✅ Success: {os.path.basename(file_path)}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ API Error processing {file_path}: {e}")
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")

        print("\n" + "-"*40 + "\nBulk upload complete!")

# ==========================================
# CONFIGURATION & EXECUTION
# ==========================================
if __name__ == "__main__":
    # 1. Replace with your actual Canvas details
    CANVAS_BASE_URL = "https://canvas.instructure.com" # e.g., 'https://YOUR_SCHOOL.instructure.com'
    CANVAS_API_TOKEN = "YOUR_CANVAS_API_TOKEN_HERE"
    COURSE_ID = 123456 # Find this in your course URL: .../courses/123456

    # 2. Define what files go into which modules.
    # Format: { Module_ID: ["path/to/file1.pdf", "path/to/file2.docx"] }
    # Find Module IDs by querying the Canvas API or inspecting the Canvas Web UI network tab.
    FILE_MAPPING = {
        987654: [
            "./documents/week_1_syllabus.pdf",
            "./documents/week_1_reading.pdf"
        ],
        987655: [
            "./documents/week_2_assignment.docx"
        ]
    }

    # 3. Initialize and run
    uploader = CanvasBulkUploader(
        base_url=CANVAS_BASE_URL,
        api_token=CANVAS_API_TOKEN,
        course_id=COURSE_ID
    )
    
    uploader.process_bulk_upload(FILE_MAPPING)
