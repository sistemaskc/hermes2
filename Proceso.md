ingresar a la página de metlife https://providaweb.metlife.mx/ 
hacer login (mantener sesión iniciada)
esperar una petición desde la API (ciclo por petición)
    leer los parámetros:
        POLIZA <pestaña> ejemplo:
            - general: //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[2]/a
            - coberturas: //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[3]/a
            - beneficiarios: //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[4]/a
            - servicios: //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[5]/a
            - agentes: //*[@id="root"]/div[3]/div[4]/div/table/tbody/tr/td[6]/a
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
    obtener el screenshot de los datos solicitados en los parámetros, guardarlos por número de póliza o RFC en orden
    armar un pdf con las imágenes (aún no sabemos si está en el scope)
    regresar a página de consultador https://providaweb.metlife.mx/consultadorBusqueda/false
