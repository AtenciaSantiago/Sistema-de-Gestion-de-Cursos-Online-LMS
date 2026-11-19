import { Injectable, Provider } from '@angular/core';
import { MatPaginatorIntl } from '@angular/material/paginator';

/**
 * Entregable 2: textos del paginador de las tablas en español (venían en inglés).
 * Se pone en cada pantalla con tabla (providers: [PAGINADOR_EN_ESPANOL]) y no en la
 * configuración global, para no cargar el paginador en el arranque de la aplicación.
 */
@Injectable()
export class PaginadorEnEspanol extends MatPaginatorIntl {
  override itemsPerPageLabel = 'Filas por página';
  override nextPageLabel = 'Página siguiente';
  override previousPageLabel = 'Página anterior';
  override firstPageLabel = 'Primera página';
  override lastPageLabel = 'Última página';

  override getRangeLabel = (pagina: number, tamano: number, total: number): string => {
    if (total === 0) return '0 de 0';
    const desde = pagina * tamano + 1;
    const hasta = Math.min(desde + tamano - 1, total);
    return `${desde} – ${hasta} de ${total}`;
  };
}

export const PAGINADOR_EN_ESPANOL: Provider = { provide: MatPaginatorIntl, useClass: PaginadorEnEspanol };
