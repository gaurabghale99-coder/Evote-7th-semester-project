import psycopg2
import argparse

# Try to import tabulate for pretty printing, otherwise fallback
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

DB_CONFIG = {
    "dbname": "evote",
    "user": "postgres",
    "password": "gaurab4445",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def list_voters():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, voter_id, full_name, date_of_birth, parliamentary_constituency, voted FROM voters ORDER BY id ASC")
        rows = cur.fetchall()
        
        headers = ["ID", "Voter ID", "Full Name", "DOB", "Constituency", "Voted"]
        
        if HAS_TABULATE:
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            header_str = " | ".join(headers)
            print("\n" + header_str)
            print("-" * len(header_str))
            for row in rows:
                print(" | ".join(str(item) for item in row))
            print("\n(Note: install 'tabulate' for better formatting: pip install tabulate)\n")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error listing voters: {e}")

def update_voter(voter_id, name=None, dob=None, constituency=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if name:
            updates.append("full_name = %s")
            params.append(name)
        if dob:
            updates.append("date_of_birth = %s")
            params.append(dob)
        if constituency:
            updates.append("parliamentary_constituency = %s")
            params.append(constituency)
            
        if not updates:
            print("No fields provided to update. Use --name, --dob, or --constituency.")
            return
            
        params.append(voter_id)
        query = f"UPDATE voters SET {', '.join(updates)} WHERE voter_id = %s"
        
        cur.execute(query, params)
        if cur.rowcount > 0:
            print(f"Successfully updated voter {voter_id}")
        else:
            print(f"Voter ID {voter_id} not found.")
            
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error updating voter: {e}")

def delete_voter(voter_id):
    confirm = input(f"Are you sure you want to delete voter {voter_id}? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM voters WHERE voter_id = %s", (voter_id,))
        if cur.rowcount > 0:
            print(f"Successfully deleted voter {voter_id}")
        else:
            print(f"Voter ID {voter_id} not found.")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error deleting voter: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Voter Management System")
    parser.add_argument("--list", action="store_true", help="List all voters")
    parser.add_argument("--update", metavar="VOTER_ID", help="Update voter details")
    parser.add_argument("--delete", metavar="VOTER_ID", help="Delete a voter")
    parser.add_argument("--name", help="New name for the voter")
    parser.add_argument("--dob", help="New Date of Birth (YYYY-MM-DD)")
    parser.add_argument("--constituency", help="New constituency")

    args = parser.parse_args()

    if args.list:
        list_voters()
    elif args.update:
        update_voter(args.update, args.name, args.dob, args.constituency)
    elif args.delete:
        delete_voter(args.delete)
    else:
        parser.print_help()

