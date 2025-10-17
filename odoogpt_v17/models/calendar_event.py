import logging
from datetime import datetime, timedelta
from odoo import api, models
from dateutil import parser

_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    @api.model
    def create_calendar_event(self, name, start_datetime, end_datetime=None, 
                             description=None, partner_ids=None, location=None,
                             allday=False, duration=1.0):
        """
        Crear un evento de calendario con los parámetros especificados.
        
        Args:
            name (str): Nombre del evento
            start_datetime (str): Fecha y hora de inicio (formato ISO o texto)
            end_datetime (str, optional): Fecha y hora de fin
            description (str, optional): Descripción del evento
            partner_ids (list, optional): Lista de IDs de contactos a invitar
            location (str, optional): Ubicación del evento
            allday (bool, optional): Si es evento de todo el día
            duration (float, optional): Duración en horas (por defecto 1 hora)
        
        Returns:
            dict: Información del evento creado
        """
        try:
            _logger.info(f"Creando evento - Parámetros recibidos: name={name}, start_datetime={start_datetime}, end_datetime={end_datetime}")
            
            # Parsear fecha de inicio
            if isinstance(start_datetime, str):
                start_dt = parser.parse(start_datetime)
            else:
                start_dt = start_datetime
            
            # Compensar desfase de zona horaria (+4 horas)
            start_dt = start_dt + timedelta(hours=4)
            
            # Calcular fecha de fin si no se proporciona
            if end_datetime:
                if isinstance(end_datetime, str):
                    end_dt = parser.parse(end_datetime)
                else:
                    end_dt = end_datetime
                # Compensar desfase de zona horaria (+4 horas)
                end_dt = end_dt + timedelta(hours=4)
            else:
                end_dt = start_dt + timedelta(hours=duration)
            
            _logger.info(f"Fechas parseadas - Start: {start_dt}, End: {end_dt}")
            _logger.info("Fechas ajustadas con +4h para compensar zona horaria")
            
            # Preparar valores del evento
            event_vals = {
                'name': name,
                'start': start_dt,
                'stop': end_dt,
                'allday': allday,
                'user_id': self.env.user.id,
            }
            
            if description:
                event_vals['description'] = description
            
            if location:
                event_vals['location'] = location
            
            if partner_ids:
                event_vals['partner_ids'] = [(6, 0, partner_ids)]
            
            # Crear el evento
            event = self.env['calendar.event'].sudo().create(event_vals)
            
            # Retornar información del evento creado
            try:
                start_formatted = event.start.strftime('%Y-%m-%d %H:%M:%S') if event.start else 'No disponible'
                stop_formatted = event.stop.strftime('%Y-%m-%d %H:%M:%S') if event.stop else 'No disponible'
            except Exception as date_error:
                _logger.error(f"Error formateando fechas: {date_error}")
                start_formatted = str(event.start) if event.start else 'No disponible'
                stop_formatted = str(event.stop) if event.stop else 'No disponible'
            
            result = {
                'id': event.id,
                'name': event.name,
                'start': start_formatted,
                'stop': stop_formatted,
                'description': str(event.description) if event.description else '',
                'location': event.location or '',
                'allday': event.allday,
                'attendees': [{'id': p.id, 'name': p.name} for p in event.partner_ids],
                'status': 'created',
                'message': f'Evento "{name}" creado exitosamente'
            }
            
            _logger.info(f"Evento creado - Start raw: {event.start}, Stop raw: {event.stop}")
            _logger.info(f"Evento creado - Start formatted: {start_formatted}, Stop formatted: {stop_formatted}")
            
            _logger.info(f"Evento de calendario creado: {event.name} (ID: {event.id})")
            return result
            
        except Exception as e:
            _logger.error(f"Error creando evento de calendario: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error al crear el evento: {str(e)}'
            }

    @api.model
    def get_calendar_events(self, start_date=None, end_date=None, partner_id=None, 
                           limit=20, search_term=None):
        """
        Consultar eventos de calendario con filtros opcionales.
        
        Args:
            start_date (str, optional): Fecha de inicio del rango de búsqueda
            end_date (str, optional): Fecha de fin del rango de búsqueda
            partner_id (int, optional): ID del contacto para filtrar eventos
            limit (int, optional): Límite de resultados (por defecto 20)
            search_term (str, optional): Término de búsqueda en nombre o descripción
        
        Returns:
            list: Lista de eventos encontrados
        """
        try:
            domain = []
            
            _logger.info(f"Parámetros de búsqueda - start_date: {start_date}, end_date: {end_date}, partner_id: {partner_id}, search_term: {search_term}")
            
            # Filtro por rango de fechas
            if start_date:
                start_dt = parser.parse(start_date) if isinstance(start_date, str) else start_date
                domain.append(('start', '>=', start_dt))
                _logger.info(f"Filtro fecha inicio: start >= {start_dt}")
            
            if end_date:
                end_dt = parser.parse(end_date) if isinstance(end_date, str) else end_date
                # Para el filtro de fin de día, agregar 23:59:59
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                domain.append(('stop', '<=', end_dt))
                _logger.info(f"Filtro fecha fin: stop <= {end_dt}")
            
            # Filtro por contacto
            if partner_id:
                domain.append(('partner_ids', 'in', [partner_id]))
            
            # Filtro por término de búsqueda
            if search_term:
                domain.append('|')
                domain.append(('name', 'ilike', search_term))
                domain.append(('description', 'ilike', search_term))
            
            _logger.info(f"Dominio de búsqueda: {domain}")
            
            # Buscar eventos
            events = self.env['calendar.event'].sudo().search(domain, limit=limit, order='start desc')
            
            # Para debugging: buscar todos los eventos y mostrar información
            all_events = self.env['calendar.event'].sudo().search([], limit=10, order='start desc')
            _logger.info(f"Todos los eventos recientes ({len(all_events)}):")
            for evt in all_events:
                attendees_names = [p.name for p in evt.partner_ids]
                _logger.info(f"  - ID:{evt.id} '{evt.name}' Start:{evt.start} Attendees:{attendees_names}")
            
            # Formatear resultados
            results = []
            for event in events:
                event_data = {
                    'id': event.id,
                    'name': event.name,
                    'start': event.start.isoformat() if event.start else None,
                    'stop': event.stop.isoformat() if event.stop else None,
                    'description': event.description or '',
                    'location': event.location or '',
                    'allday': event.allday,
                    'user_id': {'id': event.user_id.id, 'name': event.user_id.name} if event.user_id else None,
                    'attendees': [{'id': p.id, 'name': p.name, 'email': p.email} for p in event.partner_ids],
                    'state': event.state if hasattr(event, 'state') else 'confirmed'
                }
                results.append(event_data)
            
            _logger.info(f"Encontrados {len(results)} eventos de calendario")
            return results
            
        except Exception as e:
            _logger.error(f"Error consultando eventos de calendario: {str(e)}")
            return []

    @api.model
    def get_upcoming_events(self, days_ahead=7, limit=10):
        """
        Obtener eventos próximos en los siguientes días.
        
        Args:
            days_ahead (int, optional): Días hacia adelante para buscar (por defecto 7)
            limit (int, optional): Límite de resultados (por defecto 10)
        
        Returns:
            list: Lista de eventos próximos
        """
        try:
            now = datetime.now()
            future_date = now + timedelta(days=days_ahead)
            
            domain = [
                ('start', '>=', now),
                ('start', '<=', future_date)
            ]
            
            events = self.env['calendar.event'].sudo().search(
                domain, limit=limit, order='start asc'
            )
            
            results = []
            for event in events:
                # Calcular tiempo restante
                time_diff = event.start - datetime.now()
                days_left = time_diff.days
                hours_left = time_diff.seconds // 3600
                
                if days_left > 0:
                    time_remaining = f"En {days_left} días"
                elif hours_left > 0:
                    time_remaining = f"En {hours_left} horas"
                else:
                    time_remaining = "Próximamente"
                
                event_data = {
                    'id': event.id,
                    'name': event.name,
                    'start': event.start.isoformat() if event.start else None,
                    'stop': event.stop.isoformat() if event.stop else None,
                    'description': event.description or '',
                    'location': event.location or '',
                    'time_remaining': time_remaining,
                    'attendees_count': len(event.partner_ids),
                    'attendees': [p.name for p in event.partner_ids[:3]]  # Primeros 3 asistentes
                }
                results.append(event_data)
            
            _logger.info(f"Encontrados {len(results)} eventos próximos")
            return results
            
        except Exception as e:
            _logger.error(f"Error obteniendo eventos próximos: {str(e)}")
            return []

    @api.model
    def update_calendar_event(self, event_id, **kwargs):
        """
        Actualizar un evento de calendario existente.
        
        Args:
            event_id (int): ID del evento a actualizar
            **kwargs: Campos a actualizar (name, start, stop, description, location, etc.)
        
        Returns:
            dict: Resultado de la actualización
        """
        try:
            event = self.env['calendar.event'].sudo().browse(event_id)
            if not event.exists():
                return {
                    'status': 'error',
                    'message': f'Evento con ID {event_id} no encontrado'
                }
            
            # Preparar valores de actualización
            update_vals = {}
            
            for field, value in kwargs.items():
                if field in ['start', 'stop'] and isinstance(value, str):
                    update_vals[field] = parser.parse(value)
                elif field in ['name', 'description', 'location', 'allday']:
                    update_vals[field] = value
                elif field == 'partner_ids' and isinstance(value, list):
                    update_vals[field] = [(6, 0, value)]
            
            # Actualizar evento
            event.write(update_vals)
            
            return {
                'status': 'success',
                'message': f'Evento "{event.name}" actualizado exitosamente',
                'event': {
                    'id': event.id,
                    'name': event.name,
                    'start': event.start.isoformat() if event.start else None,
                    'stop': event.stop.isoformat() if event.stop else None,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error actualizando evento {event_id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error al actualizar el evento: {str(e)}'
            }

    @api.model
    def delete_calendar_event(self, event_id):
        """
        Eliminar un evento de calendario.
        
        Args:
            event_id (int): ID del evento a eliminar
        
        Returns:
            dict: Resultado de la eliminación
        """
        try:
            event = self.env['calendar.event'].sudo().browse(event_id)
            if not event.exists():
                return {
                    'status': 'error',
                    'message': f'Evento con ID {event_id} no encontrado'
                }
            
            event_name = event.name
            event.unlink()
            
            return {
                'status': 'success',
                'message': f'Evento "{event_name}" eliminado exitosamente'
            }
            
        except Exception as e:
            _logger.error(f"Error eliminando evento {event_id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error al eliminar el evento: {str(e)}'
            }
