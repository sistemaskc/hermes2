"""
Inspecciona la estructura DOM de la pagina de poliza para identificar
el elemento que contiene la informacion de cada pestana.
    uv run python scripts/inspect_policy_page.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from dotenv import load_dotenv
import os
import json

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.application.session_manager import SessionManager
from src.domain.value_objects import TipoIdentificador, Pestana


async def main():
    poliza = os.getenv("POLIZA_PRUEBA", "")
    if not poliza:
        print("ERROR: POLIZA_PRUEBA requerida en .env")
        return

    adapter = PlaywrightConsultadorAdapter(
        usuario=os.getenv("METLIFE_USUARIO", ""),
        password=os.getenv("METLIFE_PASSWORD", ""),
        headless=False,
    )
    manager = SessionManager(consultador=adapter, heartbeat_interval=240, max_reintentos=3)

    await manager.startup()

    try:
        await adapter.ir_a_busqueda()
        await adapter.buscar(poliza, TipoIdentificador.POLIZA)
        await adapter.confirmar_dialogo()
        numeros = await adapter.obtener_polizas_resultado()
        print(f"Polizas: {numeros}")

        await adapter.abrir_poliza(numeros[0])

        page = adapter._page

        output_dir = Path("output/inspect")
        output_dir.mkdir(parents=True, exist_ok=True)

        for pestana in [Pestana.GENERAL, Pestana.COBERTURAS, Pestana.BENEFICIARIOS]:
            await adapter.navegar_pestana(pestana)

            # Esperar que el contenido se estabilice: networkidle + sin mutaciones DOM por 500ms
            await page.wait_for_load_state("networkidle")
            await page.evaluate("""() => new Promise(resolve => {
                let timer = setTimeout(resolve, 500);
                const obs = new MutationObserver(() => {
                    clearTimeout(timer);
                    timer = setTimeout(resolve, 500);
                });
                obs.observe(document.body, { childList: true, subtree: true, attributes: true });
                setTimeout(() => { obs.disconnect(); resolve(); }, 5000);
            })""")

            # Screenshot completo para referencia visual
            await page.screenshot(path=str(output_dir / f"{pestana.value}_fullpage.png"), full_page=True)

            # Volcar estructura de elementos candidatos con su bounding box
            info = await page.evaluate("""() => {
                const root = document.getElementById('root');
                const children = Array.from(root.children);

                function bbox(el) {
                    const r = el.getBoundingClientRect();
                    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
                }

                function describe(el, depth=0) {
                    if (depth > 4) return null;
                    const b = bbox(el);
                    if (b.w === 0 && b.h === 0) return null;
                    return {
                        tag: el.tagName,
                        id: el.id || null,
                        cls: el.getAttribute ? (el.getAttribute('class') || '').substring(0, 80) : null,
                        bbox: b,
                        text_preview: el.innerText ? el.innerText.substring(0, 60).split('\\n').join(' ') : null,
                        children: Array.from(el.children).map(c => describe(c, depth+1)).filter(Boolean)
                    };
                }

                return describe(root, 0);
            }""")

            with open(output_dir / f"{pestana.value}_dom.json", "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)

            print(f"  [{pestana.value}] screenshot + DOM guardados en output/inspect/")

            # Intentar capturar elemento de contenido principal
            # Probar: div que sigue a header y precede a tabs
            candidates = [
                '//*[@id="root"]/div[3]/div/div/div[2]',
                '//*[@id="root"]/div[2]',
                '//main',
                '//div[contains(@class,"content")]',
                '//div[contains(@class,"detalle")]',
                '//div[contains(@class,"informacion")]',
            ]
            for xpath in candidates:
                try:
                    el = page.locator(xpath).first
                    box = await el.bounding_box()
                    if box and box['width'] > 100 and box['height'] > 100:
                        await el.screenshot(path=str(output_dir / f"{pestana.value}_element_{xpath.replace('/','').replace('@','').replace('\"','').replace(' ','_')[:30]}.png"))
                        print(f"    -> capturado con: {xpath} ({box})")
                        break
                except Exception:
                    pass

        print("\nRevisa output/inspect/ para identificar el selector correcto.")
        input("Presiona ENTER para cerrar...")

    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
