from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlmodel import SQLModel, Field, Session
from sqlmodel import create_engine, select

from contextlib import asynccontextmanager


# =====================================================
# MODELO
# =====================================================
class Factura(SQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)

    codfactura: int
    codproducto: int
    nombreproducto: str
    valor: float
    cantidad: int


# =====================================================
# CONEXIÓN
# =====================================================
postgres_url = "postgresql+psycopg2://postgres:postgres123@localhost/Ventas"

engine = create_engine(postgres_url, echo=True)


# =====================================================
# CREAR TABLAS
# =====================================================
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# =====================================================
# APP
# =====================================================
app = FastAPI(lifespan=lifespan)


# =====================================================
# TEMPLATES Y STATIC
# =====================================================
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# =====================================================
# HOME
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def mostrar_facturas(request: Request):

    with Session(engine) as session:

        facturas = session.exec(
            select(Factura)
        ).all()

    return templates.TemplateResponse(
        "facturas.html",
        {
            "request": request,
            "facturas": facturas
        }
    )


# =====================================================
# CREATE
# =====================================================
@app.post("/factura")
async def crear_factura(
    codfactura: int = Form(...),
    codproducto: int = Form(...),
    nombreproducto: str = Form(...),
    valor: float = Form(...),
    cantidad: int = Form(...)
):
    if valor <= 0 or cantidad <= 0:
        raise HTTPException(
            status_code=400,
            detail="Valor y cantidad deben ser mayores a 0"
    )

    nueva_factura = Factura(
        codfactura=codfactura,
        codproducto=codproducto,
        nombreproducto=nombreproducto,
        valor=valor,
        cantidad=cantidad
    )

    with Session(engine) as session:

        session.add(nueva_factura)
        session.commit()
        session.refresh(nueva_factura)

    return RedirectResponse("/", status_code=303)


# =====================================================
# READ TODAS
# =====================================================
@app.get("/facturas")
async def ver_facturas():

    with Session(engine) as session:

        facturas = session.exec(
            select(Factura)
        ).all()

        return facturas


# =====================================================
# BUSCAR FACTURA
# =====================================================
@app.get("/buscar", response_class=HTMLResponse)
async def buscar_factura(
    request: Request,
    codfactura: int
):

    with Session(engine) as session:

        statement = select(Factura).where(
            Factura.codfactura == codfactura
        )

        facturas = session.exec(statement).all()

    return templates.TemplateResponse(
        "facturas.html",
        {
            "request": request,
            "facturas": facturas
        }
    )


# =====================================================
# TOTAL FACTURA
# =====================================================
@app.get("/total", response_class=HTMLResponse)
async def total_factura(
    request: Request,
    codfactura: int
):

    with Session(engine) as session:

        statement = select(Factura).where(
            Factura.codfactura == codfactura
        )

        productos = session.exec(statement).all()

        total = 0

        for producto in productos:

            total += producto.valor * producto.cantidad

    return templates.TemplateResponse(
        "facturas.html",
        {
            "request": request,
            "facturas": productos,
            "total": total,
            "codfactura": codfactura
        }
    )


# =====================================================
# UPDATE
# =====================================================
@app.post("/actualizar/{id}")
async def actualizar_factura(
    id: int,
    codfactura: int = Form(...),
    codproducto: int = Form(...),
    nombreproducto: str = Form(...),
    valor: float = Form(...),
    cantidad: int = Form(...)
):

    with Session(engine) as session:

        factura = session.get(Factura, id)

        if factura:

            factura.codfactura = codfactura
            factura.codproducto = codproducto
            factura.nombreproducto = nombreproducto
            factura.valor = valor
            factura.cantidad = cantidad

            session.add(factura)
            session.commit()
            session.refresh(factura)

    return RedirectResponse("/", status_code=303)


# =====================================================
# DELETE
# =====================================================
@app.post("/eliminar/{id}")
async def eliminar_factura(id: int):

    with Session(engine) as session:

        factura = session.get(Factura, id)

        if factura:

            session.delete(factura)
            session.commit()

    return RedirectResponse("/", status_code=303)