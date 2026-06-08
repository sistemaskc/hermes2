ingresar a la página de metlife https://providaweb.metlife.mx/ 
hacer login (mantener sesión iniciada)
esperar una petición desde la API (ciclo por petición)
    leer los parámetros:
        POLIZA <pestaña> ejemplo:
            - general:       //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[2]/a
            - coberturas:    //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[3]/a
            - beneficiarios: //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[4]/a
            - servicios:     //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[5]/a
            - agentes:       //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[6]/a
            - saldos:        text=SALDOS DE LA PÓLIZA
            - cobranza:      text=COBRANZA (navega a URL distinta, ver sub-navegación abajo)
            - todo
        RFC polizas o RFC poliza
            - AGADU03050733 polizas
    click en ingresar consultador xpath: //*[@id="root"]/div[3]/div/div/div[1]/div/div[2]/a
    click en ingresar xpath: //*[@id="root"]/div[3]/div/div/div/div/div[2]/a
    ingresar número de póliza o RFC: 
        - xpath póliza: //*[@id="root"]/div[3]/div/div/form/div[1]/div/fieldset/label/input
        - xpath RFC: //*[@id="root"]/div[3]/div/div/form/div[2]/div/fieldset/label/input
    click en buscar: //*[@id="root"]/div[3]/div/div/form/div[5]/div[1]/button
    click en botón cofirmar (OK) xpath: /html/body/div[2]/div/div[3]/button[1]
    click en el número de póliza xpath: //*[@id="root"]/div[3]/div/div[2]/div[2]/table/tbody/tr/td[1]/a 
        * Nota: no funciona con inyección de URL ejemplo al completar la URL con el endpoint de la póliza con la URL del portal https://providaweb.metlife.mx/consultadorInformacionGeneral/HMZ317/false
    obtener el screenshot de la primera página de cada pestaña (sin paginación), guardarlos por número de póliza
    orden en el PDF: GENERAL → SALDOS → AGENTES → COBERTURAS → BENEFICIARIOS → SERVICIOS → COBRANZA
    armar un pdf con las imágenes
    regresar a página de consultador https://providaweb.metlife.mx/consultadorBusqueda/false

sub-navegación COBRANZA (capturar_cobranza — 4 screenshots fijos en orden):
    1. Histórico de primas:
        - click tab MOVIMIENTOS xpath: //*[@id="root"]/div[3]/div/div[2]/nav/a[3]
        - click sub-tab Histórico primas xpath: //*[@id="root"]/div[3]/div/div[2]/div/div/div/div/nav/a[4]
        - screenshot
    2. Histórico de Cargos:
        - click sub-tab Histórico cargos xpath: //*[@id="root"]/div[3]/div/div[2]/div/div/div/div/nav/a[5]
        - screenshot
    3. Pagos:
        - click tab PAGOS xpath: //*[@id="root"]/div[3]/div/div[2]/nav/a[4]
        - click OK modal xpath: /html/body/div[2]/div/div[3]/button[1]
        - esperar tabla con datos: #root table tbody tr (tabla existe vacía en DOM desde el inicio)
        - screenshot
    4. Información Adicional:
        - click tab DATOS PÓLIZA xpath: //*[@id="root"]/div[3]/div/div[2]/nav/a[1]
        - click sub-tab Información Adicional xpath: //*[@id="root"]/div[3]/div/div[2]/div/div/div/div[1]/nav/a[5]
        - screenshot
    post-cobranza: go_back() para volver a la póliza
