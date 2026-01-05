import os

# Define the database files to delete
db_files = ["smartstock.db", "credentials.db"]

print("🧹 Starting database cleanup...")

for db_file in db_files:
    file_path = os.path.join(os.getcwd(), db_file)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"✅ Deleted: {db_file}")
        except Exception as e:
            print(f"❌ Error deleting {db_file}: {e}")
    else:
        print(f"⚠️  File not found (already deleted?): {db_file}")

print("✨ Database cleanup complete. Restart the backend to recreate empty databases.")
