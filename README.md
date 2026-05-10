# Canvas-Bulk-Upload-Skeleton

A Python script to bulk upload local files and attach them to specific Canvas Modules via the Canvas API.

## Setup
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Open `canvas_bulk_uploader.py` and replace `CANVAS_API_TOKEN`, `CANVAS_BASE_URL`, and `COURSE_ID` with your own credentials. **Do not commit your API token!**
4. Place your files in the `documents/` folder.
5. Update the `FILE_MAPPING` dictionary with your module IDs.
6. Run: `python canvas_bulk_uploader.py`
