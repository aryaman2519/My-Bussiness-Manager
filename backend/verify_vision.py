import sys
import os

# Add app to path
sys.path.append(os.getcwd())

def verify_model():
    print("--- Verifying Vision System ---")
    try:
        from app.services.vision_engine import ProductDetector
        print("Import successful.")
        
        print("Initializing ProductDetector (this may download weights)...")
        detector = ProductDetector()
        
        if detector.model:
            print("Model loaded successfully!")
        else:
            print("Model failed to load.")
            sys.exit(1)
            
        print("Vision verification passed.")
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Ensure 'ultralytics' and 'opencv-python' are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Runtime Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_model()
