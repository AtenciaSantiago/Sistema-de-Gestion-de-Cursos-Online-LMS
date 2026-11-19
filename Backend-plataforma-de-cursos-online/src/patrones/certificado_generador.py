"""
PATRÓN TEMPLATE METHOD (de comportamiento) - HU-13 descarga de certificado

¿Qué problema resuelve?
Un certificado se arma siempre con los mismos siete pasos y en el mismo orden:
iniciar el documento, encabezado de la institución, datos del estudiante,
datos del curso, resultado (promedio y fecha), código de verificación y
entregar el documento terminado. Lo único que cambia es el FORMATO (PDF o texto).
Si cada formato tuviera su función completa, el ORDEN de los pasos quedaría
copiado dos veces y habría que cambiarlo en los dos lados. Con Template Method:
- la clase base define el método plantilla generar(), que fija el orden,
- cada clase concreta solo dice cómo se escribe cada paso en su formato.
Así sacamos el mismo certificado en PDF o en texto sin repetir el orden.

Roles del patrón:
- Clase base (AbstractClass) -> GeneradorCertificado
- Clases concretas           -> GeneradorCertificadoPDF, GeneradorCertificadoTexto
- Método plantilla           -> generar()
- Datos del certificado      -> DatosCertificado

Diferencia con Strategy: Strategy reemplaza TODO el algoritmo por otro objeto;
aquí el orden es el mismo para todos y solo cambia cómo se escribe cada paso.
Diferencia con Builder: Builder pediría un director aparte y una interfaz de
constructor para poder variar el orden de armado; aquí el orden nunca cambia,
así que basta con que la clase base lo fije.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Union, final

from fpdf import FPDF


# Documento terminado: según el generador concreto es un PDF (bytes) o texto plano (str).
DocumentoCertificado = Union[bytes, str]


@dataclass
class DatosCertificado:
    institucion: str
    estudiante: str
    documento: str
    curso: str
    horas: int
    docente: str
    fecha: date
    promedio: float
    codigo: str


class GeneradorCertificado(ABC):
    """CLASE BASE: fija el orden de los pasos en generar(); las clases hijas escriben cada paso."""

    @final
    def generar(self, datos: DatosCertificado) -> DocumentoCertificado:
        """MÉTODO PLANTILLA: no se redefine en las clases hijas porque es el que fija el orden."""
        self.iniciar_documento()
        self.escribir_encabezado(datos.institucion)
        self.escribir_estudiante(datos.estudiante, datos.documento)
        self.escribir_curso(datos.curso, datos.horas, datos.docente)
        self.escribir_resultado(datos.promedio, datos.fecha)
        self.escribir_codigo(datos.codigo)
        return self.entregar_documento()

    @abstractmethod
    def iniciar_documento(self) -> None: ...

    @abstractmethod
    def escribir_encabezado(self, institucion: str) -> None: ...

    @abstractmethod
    def escribir_estudiante(self, nombre: str, documento: str) -> None: ...

    @abstractmethod
    def escribir_curso(self, curso: str, horas: int, docente: str) -> None: ...

    @abstractmethod
    def escribir_resultado(self, promedio: float, fecha: date) -> None: ...

    @abstractmethod
    def escribir_codigo(self, codigo: str) -> None: ...

    @abstractmethod
    def entregar_documento(self) -> DocumentoCertificado:
        """Entrega el documento terminado (bytes del PDF o texto)."""


class GeneradorCertificadoPDF(GeneradorCertificado):
    """Escribe el certificado como archivo PDF (lo que descarga el estudiante)."""

    def iniciar_documento(self) -> None:
        self.pdf = FPDF(orientation="L", format="A4")
        self.pdf.add_page()
        self.pdf.set_draw_color(37, 99, 235)
        self.pdf.set_line_width(1.5)
        self.pdf.rect(10, 10, 277, 190)

    def escribir_encabezado(self, institucion: str) -> None:
        self.pdf.set_font("Helvetica", "B", 14)
        self.pdf.set_text_color(37, 99, 235)
        self.pdf.set_y(25)
        self.pdf.cell(0, 10, institucion.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_font("Helvetica", "B", 30)
        self.pdf.set_text_color(15, 23, 42)
        self.pdf.cell(0, 18, "Certificado de aprobación", align="C", new_x="LMARGIN", new_y="NEXT")

    def escribir_estudiante(self, nombre: str, documento: str) -> None:
        self.pdf.set_font("Helvetica", "", 13)
        self.pdf.cell(0, 10, "Se otorga a", align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_font("Helvetica", "B", 26)
        self.pdf.set_text_color(37, 99, 235)
        self.pdf.cell(0, 14, nombre, align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_font("Helvetica", "", 11)
        self.pdf.set_text_color(71, 85, 105)
        self.pdf.cell(0, 8, f"Documento {documento}", align="C", new_x="LMARGIN", new_y="NEXT")

    def escribir_curso(self, curso: str, horas: int, docente: str) -> None:
        self.pdf.ln(4)
        self.pdf.set_font("Helvetica", "", 13)
        self.pdf.set_text_color(15, 23, 42)
        self.pdf.cell(0, 8, "por haber aprobado el curso", align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_font("Helvetica", "B", 18)
        self.pdf.cell(0, 12, curso, align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_font("Helvetica", "", 11)
        self.pdf.cell(0, 8, f"Intensidad: {horas} horas  ·  Docente: {docente}", align="C", new_x="LMARGIN", new_y="NEXT")

    def escribir_resultado(self, promedio: float, fecha: date) -> None:
        self.pdf.ln(4)
        self.pdf.set_font("Helvetica", "", 11)
        self.pdf.cell(
            0, 8, f"Calificación final: {promedio:.1f} / 5.0  ·  Fecha de emisión: {fecha.strftime('%d/%m/%Y')}",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )

    def escribir_codigo(self, codigo: str) -> None:
        self.pdf.set_y(175)
        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_text_color(37, 99, 235)
        self.pdf.cell(0, 8, f"Código de verificación: {codigo}", align="C")

    def entregar_documento(self) -> bytes:
        return bytes(self.pdf.output())


class GeneradorCertificadoTexto(GeneradorCertificado):
    """Escribe el mismo certificado como texto plano (sirve para vista previa y pruebas)."""

    def iniciar_documento(self) -> None:
        self.lineas = []

    def escribir_encabezado(self, institucion: str) -> None:
        self.lineas += [institucion.upper(), "CERTIFICADO DE APROBACIÓN"]

    def escribir_estudiante(self, nombre: str, documento: str) -> None:
        self.lineas.append(f"Se otorga a {nombre} (documento {documento})")

    def escribir_curso(self, curso: str, horas: int, docente: str) -> None:
        self.lineas.append(f"Curso: {curso} - {horas} horas - Docente: {docente}")

    def escribir_resultado(self, promedio: float, fecha: date) -> None:
        self.lineas.append(f"Calificación final: {promedio:.1f} / 5.0 - Fecha: {fecha.isoformat()}")

    def escribir_codigo(self, codigo: str) -> None:
        self.lineas.append(f"Código de verificación: {codigo}")

    def entregar_documento(self) -> str:
        return "\n".join(self.lineas)
