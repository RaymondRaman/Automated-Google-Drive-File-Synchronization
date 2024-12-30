
## Automated Google Drive File Synchronization

This project addresses a common issue faced by users of Google Drive: upload errors that occur when using the web interface. When files fail to upload, it can be challenging to identify which files have not been successfully uploaded. 

Manually comparing local files with those in Google Drive is not only tedious but also time-consuming. This script automates the process of checking local files against those stored in Google Drive, ensuring that all necessary files are uploaded without manual verification.


### Prerequisite
Installed python 3.x, git, pip

### Guideline
#### Step 1: Create a Google Cloud Project with Google Drive API Enabled
```
Go to the Google Cloud Console.
Create a new project. 
Search for "Google Drive API" and enable it for your project
```
#### Step 2: Create Service Account
```
In the same project, go to Enabled APIs & services > Credentials.
Follow the guide to create a service account, add role as Owner and fill in target account in Grant users access section.
```
#### Step 3: Create Create OAuth client ID Credentials with JSON format
```
Click on Create Credentials and select OAuth client ID.
Follow the guide to create OAuth client ID Credentials, choose an application type as Web Application.
Click DOWNLOAD JSON.
```
#### Step 4: Share the Google Drive Folder with Your Service Account
```
Right-click on the folder, select Share, and enter the email address of your service account, like compare-file-loca-and-drive@compare-file-local-and-drive.iam.gserviceaccount.com. 
Set the permissions to Editor.
```
#### Step 5: Clone this repository using Git
```
git clone https://github.com/RaymondRaman/Automated-Google-Drive-File-Synchronization
```
#### Step 6: Navigate into the project directory and install required libraries
```
Open terminal and run follow command
cd Automated-Google-Drive-File-Synchronization
pip install -r requirements.txt
```
#### Step 7: Drag and drop your Credentials file into the project directory.
#### Step 8: Modify config.json
```json
{
    "Google_credentials_paths": "/path/to/your/Credentials.json",
    "Target_folder_Path": "/path/to/local/folder",
    "ignore_files": [
        ".DS_Store",
        ".gitignore",
        "node_modules",
        ".git",
        "lib",
        "__pycache__",
        ".ipynb_checkpoints",
        "bin",
        "pip3.12",
        "python",
        "pip3",
        "nbconfig"
    ],
    "upload_failed": {
        "status": "False",
        "start_process_doc": "extension.js"
    }
}
```
#### Step 9: Run the script using
```
python script.py
```
#### (OPTIONAL) Step 10: Handle Upload Failures
After running the script, monitor the terminal output for any messages indicating which files were successfully uploaded. This will help you identify any files that may have encountered issues during the upload process.
```
Modify ConfigurationUpdate:
-  changing upload_failed status to True
-  chaning upload_failed start_process_doc to the specific file that encountered issues
```
Run Upload Script Again: Execute the script again using:
```
python script.py
```






