# JiraIssue2MProject
*Generate differents timelines for MSProject from one issue (include transitions, upload files and comments)*

Esta aplicación ayuda a construir un timeline de lo que ha ocurrido en una issue de JIRA. No esta muy depurada, pero traslada los principales hitos a una tabla de tareas.

El gantt que se genera de forma automática es muy malo

Se exportan los datos en tres formatos csv, xml y excel. MSProject procesa los tres pero se recomienda Excel porque se maneja mejor la lista de tareas y, a veces, los formatos de las fechas exportadas no son homogeneos.

Independientemente de su uso en MSProject, se ven bien las fechas de los hitos agrupados en:
* Transiciones: En los estados de la issue desde que se inicia hasta que se resuelve o se cierra.
* Ficheros: En que fecha se anexan ficheros a la issue
* Comentarios: Fecha en la que se suben los comentarios

Mejoras pendientes:
* En español e ingles
* Uniformizar las fechas de salida para que las importe directamente MSProject
* Procesar los comentarios. Tienen muchos caracteres de control y un tamaño que no es asumible como nombre de tarea

Para ejecutar la app (necesitas python instalado):
* Configura issue_key, jira_server, jira_token en JiraIssueGantt
* Instala las dependencias: pip install -r requirements.txt
* Lanza: python JiraIssueGantt.py
