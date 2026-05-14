"""
Prueba secuencial: lee lista_prueba.csv y consulta cada identificador.
Uso: uv run python prueba_lista.py
"""
import csv
import time
import httpx

BASE_URL = "http://localhost:8000"
TELEFONO = "5512345678"
TIMEOUT = 300


def main():
    with open("lista_prueba.csv", newline="", encoding="utf-8") as f:
        identificadores = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]

    print(f"Consultando {len(identificadores)} identificadores...\n")

    resultados = []
    for identificador in identificadores:
        print(f"[>] {identificador}", end=" ", flush=True)
        t0 = time.time()
        try:
            r = httpx.post(
                f"{BASE_URL}/consultar",
                json={"identificador": identificador, "numero_telefono": TELEFONO},
                timeout=TIMEOUT,
            )
            elapsed = round(time.time() - t0, 1)
            data = r.json()
            if data["success"]:
                archivos = [d["file_name"] for d in data["data"]]
                print(f"OK ({elapsed}s) -> {archivos}")
                resultados.append({"id": identificador, "ok": True, "archivos": archivos, "tiempo": elapsed})
            else:
                print(f"ERROR ({elapsed}s) -> {data['errorMessage']}")
                resultados.append({"id": identificador, "ok": False, "error": data["errorMessage"], "tiempo": elapsed})
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            print(f"EXCEPCION ({elapsed}s) -> {e}")
            resultados.append({"id": identificador, "ok": False, "error": str(e), "tiempo": elapsed})

    ok = sum(1 for r in resultados if r["ok"])
    fail = len(resultados) - ok
    total_tiempo = round(sum(r["tiempo"] for r in resultados), 1)
    print(f"\n{'='*50}")
    print(f"Exitosos: {ok}/{len(resultados)}  |  Fallidos: {fail}  |  Tiempo total: {total_tiempo}s")

    if fail:
        print("\nFallidos:")
        for r in resultados:
            if not r["ok"]:
                print(f"  {r['id']}: {r['error']}")


if __name__ == "__main__":
    main()
