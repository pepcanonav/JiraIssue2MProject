from jira import JIRA
import pandas as pd
import datetime
import plotly.express as px
import xml.etree.ElementTree as ET
import os


issue_key = "PROJECT-XXX"
jira_server = 'https://jira.xxx.es'
jira_token = 'xxxyyyzzz'


def ensure_dir_exists(directory_path: str) -> bool:
    """Versión minimalista que solo crea el directorio si no existe"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except:
        return False


def get_transitions(issue):
    """
    Obtener transiciones
    :param issue: issue
    :return: transitions
    """
    transitions = []
    for history in issue.changelog.histories:
        for item in history.items:
            if item.field == "status":
                ts = datetime.datetime.strptime(history.created, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
                transitions.append({
                    "Tipo": "Transición",
                    "Nombre": f"{item.fromString} → {item.toString}",
                    "Inicio": ts,
                    "Inicio_str": ts.strftime("%d/%m/%Y %H:%M"),
                    "Descripción": f"De: {item.fromString}<br>A: {item.toString}<br>Fecha: {ts.strftime('%d/%m/%Y %H:%M')}"
                })
    return transitions


def get_comments(issue):
    """
    Obtener comentarios
    :param issue: issue
    :return: comments
    """
    comments = []
    for c in issue.fields.comment.comments:
        ts = datetime.datetime.strptime(c.created, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
        cuerpo = c.body.replace("\n", "<br>")
        comments.append({
            "Tipo": "Comentario",
            "Nombre": f"{c.author.displayName}",
            "Inicio": ts,
            "Inicio_str": ts.strftime("%d/%m/%Y %H:%M"),
            "Descripción": f"<b>{c.author.displayName}</b><br>{cuerpo}<br><i>{ts.strftime('%d/%m/%Y %H:%M')}</i>"
        })
    return comments


def get_attachments(issue):
    """
    Obtener archivos adjuntos
    :param issue: issue
    :return: attachments
    """
    attachments = []
    for att in issue.fields.attachment:
        created = datetime.datetime.strptime(att.created, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
        attachments.append({
            "Nombre": att.filename,
            "Inicio": created,
            "Inicio_str": created.strftime("%d/%m/%Y %H:%M"),
            "Autor": att.author.displayName,
            "Descripción": att.content
        })
    return attachments


def build_gantt_html(df_issue, name_issue, output_dir):
    """
    Gantt interactivo (HTML). No funciona muy bien
    :param df_issue: Dataframe
    :param name_issue: name issue
    :param output_dir: output dir
    :return: None
    """
    fig = px.timeline(
        df_issue,
        x_start="Inicio",
        x_end="Fin",
        y="Nombre",
        color="Tipo",
        custom_data=["Tooltip"],
        title=f"Diagrama Gantt interactivo: {name_issue}"
    )
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickformat="%d/%m/%Y")
    fig.write_html(f"{output_dir}//gantt_interactivo.html")


def export_excel(transitions, comments, attachments, output_dir):
    """
    Exportar a Excel. Para usar las entradas como tareas con fechas
    :param transitions: transitions
    :param comments: comments
    :param attachments: attachments
    :param output_dir: output dir
    :return: None
    """
    df_trans = pd.DataFrame(transitions)[["Nombre", "Inicio_str"]]
    df_comm = pd.DataFrame(comments)[["Nombre", "Inicio_str", "Descripción"]]
    df_att = pd.DataFrame(attachments)[["Nombre", "Inicio_str", "Descripción"]]

    df_trans.rename(columns={"Nombre": "Transición", "Inicio_str": "Fecha"}, inplace=True)
    df_comm.rename(columns={"Nombre": "Autor", "Inicio_str": "Fecha", "Descripción": "Comentario"}, inplace=True)
    df_att.rename(columns={"Nombre": "Autor", "Inicio_str": "Fecha", "Descripción": "Comentario"}, inplace=True)

    with pd.ExcelWriter(f"{output_dir}//jira_issue.xlsx", engine="xlsxwriter") as writer:
        df_trans.to_excel(writer, sheet_name="Transiciones", index=False)
        df_comm.to_excel(writer, sheet_name="Comentarios", index=False)
        df_att.to_excel(writer, sheet_name="Adjuntos", index=False)


def export_csv(data_issue, output_dir):
    """
    Exportar CSV (sin hora)
    :param data_issue: transitions + comments + attachments
    :param output_dir:
    :return: None
    """
    csv_rows = []
    for row in data_issue:
        csv_rows.append({
            "Nombre de tarea": row["Nombre"],
            "Inicio": row["Inicio"].strftime("%d/%m/%Y"),  # Solo fecha
            "Duración": "1d"
        })
    pd.DataFrame(csv_rows).to_csv(f"{output_dir}//gantt_project.csv", index=False)


def export_xml(data_issue, output_dir):
    """
    Exportar a XML (Microsoft Project)
    :param data_issue: transitions + comments + attachments
    :param output_dir:
    :return: None
    """
    root = ET.Element("Project")
    tasks = ET.SubElement(root, "Tasks")

    for i, row in enumerate(data_issue, start=1):
        task = ET.SubElement(tasks, "Task")
        ET.SubElement(task, "UID").text = str(i)
        ET.SubElement(task, "ID").text = str(i)
        ET.SubElement(task, "Name").text = row["Nombre"]
        ET.SubElement(task, "Type").text = "1"
        ET.SubElement(task, "IsNull").text = "0"
        ET.SubElement(task, "CreateDate").text = row["Inicio"].strftime("%Y-%m-%dT%H:%M:%S")
        ET.SubElement(task, "Start").text = row["Inicio"].strftime("%Y-%m-%dT%H:%M:%S")
        ET.SubElement(task, "Finish").text = (row["Inicio"] + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        ET.SubElement(task, "Duration").text = "PT8H0M0S"
        ET.SubElement(task, "DurationFormat").text = "7"

    tree = ET.ElementTree(root)
    tree.write(f"{output_dir}//gantt_project.xml", encoding="utf-8", xml_declaration=True)


def process_issue(issue):
    """ Unificar y preparar para Gantt """
    transitions = get_transitions(issue)
    comments = get_comments(issue)
    attachments = get_attachments(issue)

    data = transitions + comments + attachments
    df = pd.DataFrame(data)
    df["Fin"] = df["Inicio"] + pd.Timedelta(hours=1)
    df["Fin_str"] = df["Fin"].dt.strftime("%d/%m/%Y %H:%M")
    df["Tooltip"] = df["Descripción"] + "<br><b>Inicio:</b> " + df["Inicio_str"] + "<br><b>Fin:</b> " + df["Fin_str"]
    return df, transitions, comments, attachments


if __name__ == '__main__':
    # Configuración JIRA
    jira = JIRA(server=jira_server, token_auth=jira_token)
    issue = jira.issue(issue_key, expand='changelog')

    output_dir = f".//{issue_key}"
    ensure_dir_exists(output_dir)

    df, transitions, comments, attachments = process_issue(issue)

    data = transitions + comments + attachments

    build_gantt_html(df, issue_key, output_dir)
    export_excel(transitions, comments, attachments, output_dir)
    export_csv(data, output_dir)
    export_xml(data, output_dir)

    print("✅ Archivos generados: HTML, Excel, CSV, XML.")
