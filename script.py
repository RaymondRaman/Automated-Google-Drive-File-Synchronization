from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
from collections import defaultdict
from collections import deque
from googleapiclient.http import MediaFileUpload


def google_drive_init(config_file):
    # Define the scope and service account file
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = config_file['Google_credentials_paths']
    # Authenticate using the service account credentials
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    # Build the Google Drive service
    service = build('drive', 'v3', credentials=credentials)
    return service


def get_initial_folder_id(service, folder_name):
    # Get the root folder
    response = service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                    spaces='drive',
                                    fields='files(id, name)').execute()
    folders = response.get('files', [])
    for folder in folders:
        if folder['name'] == folder_name:
            return folder['id']


def compare_files(folder_path, initial_folder_id, local_file_list, ignore_files, service):
    # Using BFS to traverse the Google Drive
    queue = deque([(folder_path, initial_folder_id)])
    while queue:
        folder_path, folder_id = queue.popleft()
        if any(ignore in folder_path for ignore in ignore_files):
            continue
        response = service.files().list(q=f"'{folder_id}' in parents",
                                        spaces='drive',
                                        fields='files(id, name, mimeType)').execute()
        files = response.get('files', [])
        for file in files:
            if file['name'] in ignore_files:
                continue

            if file['mimeType'] != 'application/vnd.google-apps.folder':
                print(f"Checking {file['name']} in {folder_path}")
                if file['name'] in local_file_list and folder_path in local_file_list[file['name']]:
                    del local_file_list[file['name']]
            else:
                queue.append(
                    (os.path.join(folder_path, file["name"]), file['id']))
    return local_file_list


def get_files_need_to_be_in_drive(local_folder_path, ignore_files):
    local_file_list = defaultdict(list)
    prefix = os.path.dirname(local_folder_path)
    for root, dirs, files in os.walk(local_folder_path):
        relative_dir = os.path.relpath(root, prefix)
        if any(ignore in relative_dir for ignore in ignore_files):
            continue
        for file in files:
            if file in ignore_files:
                continue
            local_file_list[file].append(relative_dir)

    return local_file_list


def check_file_ignore(relative_dir, ignore_files):
    if any(ignore in relative_dir for ignore in ignore_files):
        return True


def upload_file(service, file_path, folder_id, ignore_files):
    if check_file_ignore(file_path, ignore_files):
        return

    # Prepare file metadata
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)

    # Upload the file
    print(f"Uploading '{file_name}' to folder with ID: {folder_id}")
    file = service.files().create(body=file_metadata,
                                  media_body=media, fields='id').execute()


def upload_missing_file(local_file_list, initial_folder_id, service, prefix, ignore_files):
    # A hashmap to store the parent folder id of each folder
    parent_id = defaultdict(str)
    parent_id[folder_name] = initial_folder_id
    for file, paths in local_file_list.items():
        for path in paths:
            sub_folder = path.split('/')
            for i in range(len(sub_folder)):
                parent = sub_folder[:i]
                folder_path = '/'.join(sub_folder[:i+1])
                if folder_path not in parent_id:
                    parent = '/'.join(sub_folder[:i])
                    curr_parent_id = parent_id[parent]
                    try:
                        response = service.files().list(q=f"'{curr_parent_id}' in parents and name='{sub_folder[i]}' and mimeType='application/vnd.google-apps.folder'",
                                                        spaces='drive',
                                                        fields='files(id)').execute()
                        folder_id = response.get('files', [])[0]['id']
                        parent_id[folder_path] = folder_id
                    except:
                        # The folder does not exist, create a new folder
                        file_metadata = {
                            'name': sub_folder[i],
                            'mimeType': 'application/vnd.google-apps.folder',
                            'parents': [curr_parent_id]
                        }
                        folder = service.files().create(body=file_metadata,
                                                        fields='id').execute()
                        parent_id[folder_path] = folder['id']

            folder_path = os.path.join(prefix, path)
            folder_id = parent_id[path]
            print(f"Uploading {file} to {folder_path}")
            upload_file(service, os.path.join(
                folder_path, file), folder_id, ignore_files)


if __name__ == '__main__':
    # Open the config file
    config_file_path = os.path.join(os.getcwd(), 'config.json')
    with open(config_file_path) as f:
        config = json.load(f)

    # Target directory path
    local_folder_path = config['Target_folder_Path']
    ignore_files = config['ignore_files']
    folder_name = os.path.basename(local_folder_path)
    local_file_list = get_files_need_to_be_in_drive(
        local_folder_path, ignore_files)

    # Initialize the Google Drive service
    service = google_drive_init(config)
    initial_folder_id = get_initial_folder_id(service, folder_name)
    if initial_folder_id is None:
        print("Please make sure you have shared the folder with the service account email")
        print("Also, please make sure the folder name is the same as the target folder name on google drive")
        exit(1)
    prefix = os.path.dirname(local_folder_path)

    # Handling upload error
    upload_failed = config['upload_failed']['status']
    start_processing = False
    if upload_failed == 'True':
        not_uploaded_file = defaultdict(list)
        start_process_doc = config['upload_failed']['start_process_doc']
        with open('result.txt', 'r') as f:
            for line in f:
                if line.split(' ', 1)[0] == start_process_doc:
                    start_processing = True

                if start_processing:
                    file, path = line.split(' ', 1)
                    not_uploaded_file[file].append(path.strip())

        upload_missing_file(not_uploaded_file,
                            initial_folder_id, service, prefix, ignore_files)
        exit()

    folder_path = f'{folder_name}'
    not_uploaded_file = compare_files(
        folder_path, initial_folder_id, local_file_list, ignore_files, service)

    # When there is upload error, this file is used to restore the upload
    with open('result.txt', 'w') as f:
        for file, paths in not_uploaded_file.items():
            for path in paths:
                f.write(f"{file} {path}\n")

    upload_missing_file(not_uploaded_file, initial_folder_id,
                        service, prefix, ignore_files)
