# Search duplicity files v.0.1
The application for searching files which they are in the data storages many times.
It is possible to search only the same files and the results are only informative. 
The application does not delete anything. The user has to find the files alone in his 
storages. 

## Requirements
- Python 3.8 and later
- SQLAlchemy
- pytest (if you want to start the unit test)

## Installation

1. Check of installation version of Python in terminal:

    `$ python3 --version`

2. Create directory for downloading this application
3. Git clone if you have installed git or downloading zip file from GitHub.com:

    `git clone https://github.com/trnecka/search_duplicity_files.git`

4. Install important libraries:

   `pip -r requirements.txt`

5. Run the application:

   `python3 search_duplicity_files.py`

## Action button on main window

### Button: Search duplicity files
It refreshes the list of the founded files after operations carried out by the user. 
For example deleting files from the data storage.

### Button: Root folders
The application has administration so-called root folders. This root folders are 
the folders for searching including sub-folders.

### Button: Changed files
The list of the changed files on the data storage. It is possible the changed files add 
to the database of the application.

### Button: Exit
Exit this application
