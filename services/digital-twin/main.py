from fastapi import FastAPI

app = FastAPI(title="digital-twin")


@app.get("/health")
def health():
    return {"status": "up", "service": "digital-twin"}
