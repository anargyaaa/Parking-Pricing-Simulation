import calculator
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Simulasi Tarif Parkir")


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/api/calculate")
def api_calculate(data: dict):
    try:
        return calculator.calculate(data)
    except calculator.ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Perhitungan gagal: {e}")
