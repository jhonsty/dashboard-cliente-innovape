from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)

def cargar_datos():
    df = pd.read_excel("cliente_progreso.xlsx")
    df.columns = [col.strip() for col in df.columns]

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = df['Fecha'].dt.month_name(locale='es_ES.utf8')
    df['Mes_Num'] = df['Fecha'].dt.month

    df['COMISION'] = df['COMISION'].astype(float)
    df['COMISION_PORCENTAJE'] = (df['COMISION'] * 100).round(2).astype(str) + '%'
    df['Subtotal'] = df['Subtotal'].astype(float).round(2)
    df['IGV'] = df['IGV'].astype(float).round(2)
    df['Total'] = df['Total'].astype(float).round(2)
    df['MONTO DEL SERVICIO'] = df['MONTO DEL SERVICIO'].astype(float).round(2)

    return df

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        codigo = request.form.get("codigo")
        return redirect(url_for("dashboard", codigo=codigo))
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    df = cargar_datos()
    codigo = request.args.get("codigo", "")
    df = df[df['CODIGO'] == codigo]

    if df.empty:
        return f"Código '{codigo}' no válido o sin datos."

    bancos = df['BANCO'].unique()
    banco_seleccionado = request.form.get("banco", bancos[0])
    cliente_seleccionado = request.form.get("cliente", 'Todos')

    df_filtrado = df[df['BANCO'] == banco_seleccionado]
    if cliente_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Cliente'].str.contains(cliente_seleccionado)]

    total_monto = df_filtrado["MONTO DEL SERVICIO"].sum()

    monto_mensual = df_filtrado.groupby("Mes_Num").agg({
        "MONTO DEL SERVICIO": "sum"
    }).sort_index()
    monto_mensual.index = pd.to_datetime(monto_mensual.index, format="%m").month_name(locale='es_ES.utf8')
    monto_mensual = monto_mensual.round(2)

    barras_mes = df[df['Fecha'].dt.month == df_filtrado['Fecha'].dt.month.iloc[0]]
    monto_por_banco = barras_mes.groupby("BANCO")["MONTO DEL SERVICIO"].sum().round(2)

    clientes = df[df['BANCO'] == banco_seleccionado]['Cliente'].unique().tolist()
    columnas = ['Fecha', 'Cliente', 'BANCO', 'COMISION_PORCENTAJE', 'Subtotal', 'IGV', 'Total', 'MONTO DEL SERVICIO']
    datos_tabla = df_filtrado[columnas].to_dict(orient="records")

    return render_template("cliente_dashboard.html",
        bancos=bancos,
        banco_seleccionado=banco_seleccionado,
        clientes=clientes,
        cliente_seleccionado=cliente_seleccionado,
        total_monto=total_monto,
        datos=datos_tabla,
        monto_mensual=monto_mensual,
        monto_por_banco=monto_por_banco
    )

if __name__ == "__main__":
    app.run(debug=True)