import uvicorn
import sys
import os

# Ensure the root codebase is in the path so env.py can be loaded
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import app

def main():
    uvicorn.run("env:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
