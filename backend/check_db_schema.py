from sqlalchemy import create_engine, inspect
import sys
import os
import json

# Target the confirmed database file
db_path = "sqlite:///./smartstock.db" 

try:
    engine = create_engine(db_path)
    inspector = inspect(engine)
    
    data = {"sales": [], "sale_items": []}
    
    if inspector.has_table('sales'):
        columns = inspector.get_columns('sales')
        for column in columns:
            col_data = {
                "name": column['name'],
                "type": str(column['type']),
                "nullable": column['nullable']
            }
            data["sales"].append(col_data)

    if inspector.has_table('sale_items'):
        columns = inspector.get_columns('sale_items')
        for column in columns:
            col_data = {
                "name": column['name'],
                "type": str(column['type']),
                "nullable": column['nullable']
            }
            data["sale_items"].append(col_data)
            
    with open("schema.json", "w") as f:
        json.dump(data, f, indent=2)
        
    print("Schema dumped to schema.json")
        
except Exception as e:
    print(f"Error inspecting DB: {e}")
