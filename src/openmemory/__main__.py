import os
import uvicorn
from main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0" if os.getenv("BIND_PUBLIC_HOST", "False") == "True" else "127.0.0.1"
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False
    )
