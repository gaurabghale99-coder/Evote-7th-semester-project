# E-Vote System

A facial-recognition based electronic voting system.

## Prerequisites
- Python 3.x
- PostgreSQL
- Webcam

## Setup

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Database Setup**
    - Ensure PostgreSQL is running.
    - Update database credentials in `main.py` and `setup_db.py` if necessary.
    - Initialize the database:
      ```bash
      python setup_db.py
      ```

## Running the Application

**The Easiest Way:**

Simply run the helper script from the terminal:
```bash
./run.sh
```
This will automatically:
1.  Verify/Install dependencies.
2.  Start the Backend server.
3.  Start the Frontend server.
4.  Show you the link to open.

---

**Manual Method:**

If you prefer to run manually:

### 1. Start Backend
```bash
# Make sure you are in the root folder
./venv/bin/uvicorn backend:app --reload
```

### 2. Start Frontend
```bash
cd EvoteKABIN
python3 -m http.server 5500
```


## Admin Access
- Click the **Admin** button on the home page.
- Default Password: `admin123`
