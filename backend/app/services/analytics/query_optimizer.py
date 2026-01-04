import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, Table, Column, MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Класс для оптимизации SQL-запросов в аналитике"""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация оптимизатора запросов
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
        self.metadata = MetaData()
        self.table_stats: Dict[str, Dict[str, Any]] = {}
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        
    async def analyze_tables(self, table_names: List[str]) -> None:
        """
        Анализирует таблицы для сбора статистики
        
        Args:
            table_names: Список имен таблиц для анализа
        """
        try:
            for table_name in table_names:
                query = text(f"ANALYZE {table_name};")
                await self.session.execute(query)
                
                # Получаем статистику по таблице
                stats_query = text(f"""
                    SELECT reltuples::bigint AS row_count, 
                           pg_total_relation_size('{table_name}') AS total_size
                    FROM pg_class
                    WHERE relname = '{table_name}';
                """)
                result = await self.session.execute(stats_query)
                stats = result.fetchone()
                
                if stats:
                    self.table_stats[table_name] = {
                        "row_count": stats[0],
                        "total_size": stats[1]
                    }
                    
                    logger.info(f"Таблица {table_name} проанализирована: "
                               f"{stats[0]} строк, {stats[1]/1024/1024:.2f} МБ")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при анализе таблиц: {str(e)}")
    
    async def create_index(self, table_name: str, column_names: List[str], 
                          index_name: Optional[str] = None, unique: bool = False,
                          concurrent: bool = True) -> bool:
        """
        Создает индекс на указанных столбцах таблицы
        
        Args:
            table_name: Имя таблицы
            column_names: Список столбцов для индекса
            index_name: Имя индекса (опционально)
            unique: Создать уникальный индекс
            concurrent: Создать индекс параллельно (без блокировки)
            
        Returns:
            bool: Успешно ли создан индекс
        """
        try:
            if not index_name:
                index_name = f"idx_{table_name}_{'_'.join(column_names)}"
                
            unique_str = "UNIQUE " if unique else ""
            concurrent_str = "CONCURRENTLY " if concurrent else ""
            columns_str = ", ".join(column_names)
            
            query = text(f"""
                CREATE {unique_str}INDEX {concurrent_str}{index_name} 
                ON {table_name} ({columns_str});
            """)
            
            await self.session.execute(query)
            await self.session.commit()
            
            logger.info(f"Индекс {index_name} успешно создан на {table_name}({columns_str})")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при создании индекса: {str(e)}")
            await self.session.rollback()
            return False
    
    async def check_index_exists(self, table_name: str, column_names: List[str]) -> bool:
        """
        Проверяет существование индекса на указанных столбцах
        
        Args:
            table_name: Имя таблицы
            column_names: Список столбцов
            
        Returns:
            bool: Существует ли индекс
        """
        try:
            # Преобразуем список столбцов в строку для поиска
            columns_pattern = "%" + "%".join(column_names) + "%"
            
            query = text(f"""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = '{table_name}' 
                AND indexdef LIKE '%({columns_pattern})%';
            """)
            
            result = await self.session.execute(query)
            count = result.scalar()
            
            return count > 0
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при проверке индекса: {str(e)}")
            return False
    
    async def optimize_query(self, query: str) -> str:
        """
        Оптимизирует SQL-запрос на основе статистики
        
        Args:
            query: Исходный SQL-запрос
            
        Returns:
            str: Оптимизированный SQL-запрос
        """
        # Простая оптимизация - добавляем EXPLAIN ANALYZE для отладки
        if "EXPLAIN" not in query.upper():
            optimized_query = query
            
            # Добавляем подсказки для планировщика, если это SELECT
            if query.upper().strip().startswith("SELECT"):
                # Если запрос содержит агрегацию, увеличиваем work_mem
                if any(agg in query.upper() for agg in ["GROUP BY", "ORDER BY", "COUNT(", "SUM(", "AVG("]):
                    optimized_query = f"SET LOCAL work_mem = '32MB'; {optimized_query}"
                
                # Если запрос содержит JOIN, добавляем подсказку для планировщика
                if "JOIN" in query.upper():
                    optimized_query = f"SET LOCAL enable_nestloop = off; {optimized_query}"
            
            return optimized_query
        return query
    
    async def create_materialized_view(self, view_name: str, query: str, 
                                      with_data: bool = True) -> bool:
        """
        Создает материализованное представление
        
        Args:
            view_name: Имя представления
            query: SQL-запрос для представления
            with_data: Заполнить представление данными при создании
            
        Returns:
            bool: Успешно ли создано представление
        """
        try:
            with_data_str = "WITH DATA" if with_data else "WITH NO DATA"
            
            create_query = text(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name}
                AS {query}
                {with_data_str};
            """)
            
            await self.session.execute(create_query)
            await self.session.commit()
            
            logger.info(f"Материализованное представление {view_name} успешно создано")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при создании материализованного представления: {str(e)}")
            await self.session.rollback()
            return False
    
    async def refresh_materialized_view(self, view_name: str, concurrently: bool = True) -> bool:
        """
        Обновляет материализованное представление
        
        Args:
            view_name: Имя представления
            concurrently: Обновить параллельно (требует уникального индекса)
            
        Returns:
            bool: Успешно ли обновлено представление
        """
        try:
            concurrently_str = "CONCURRENTLY" if concurrently else ""
            
            refresh_query = text(f"""
                REFRESH MATERIALIZED VIEW {concurrently_str} {view_name};
            """)
            
            await self.session.execute(refresh_query)
            await self.session.commit()
            
            logger.info(f"Материализованное представление {view_name} успешно обновлено")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении материализованного представления: {str(e)}")
            await self.session.rollback()
            
            # Если ошибка связана с отсутствием уникального индекса при concurrently=True,
            # попробуем без concurrently
            if concurrently and "could not create unique index" in str(e):
                logger.info("Повторная попытка обновления без CONCURRENTLY")
                return await self.refresh_materialized_view(view_name, concurrently=False)
            
            return False
    
    async def check_materialized_view_exists(self, view_name: str) -> bool:
        """
        Проверяет существование материализованного представления
        
        Args:
            view_name: Имя представления
            
        Returns:
            bool: Существует ли представление
        """
        try:
            query = text(f"""
                SELECT COUNT(*) 
                FROM pg_matviews 
                WHERE matviewname = '{view_name}';
            """)
            
            result = await self.session.execute(query)
            count = result.scalar()
            
            return count > 0
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при проверке материализованного представления: {str(e)}")
            return False
    
    async def get_query_plan(self, query: str) -> List[Dict[str, Any]]:
        """
        Получает план выполнения запроса
        
        Args:
            query: SQL-запрос
            
        Returns:
            List[Dict[str, Any]]: План выполнения запроса
        """
        try:
            explain_query = text(f"EXPLAIN (FORMAT JSON) {query}")
            result = await self.session.execute(explain_query)
            plan = result.scalar()
            
            return plan[0]["Plan"] if plan else {}
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении плана запроса: {str(e)}")
            return []
    
    async def analyze_query_performance(self, query: str) -> Tuple[float, Dict[str, Any]]:
        """
        Анализирует производительность запроса
        
        Args:
            query: SQL-запрос
            
        Returns:
            Tuple[float, Dict[str, Any]]: Время выполнения и статистика
        """
        try:
            explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
            result = await self.session.execute(explain_query)
            analysis = result.scalar()
            
            if not analysis:
                return 0.0, {}
            
            plan = analysis[0]
            execution_time = plan.get("Execution Time", 0.0)
            
            stats = {
                "planning_time": plan.get("Planning Time", 0.0),
                "execution_time": execution_time,
                "total_cost": plan["Plan"].get("Total Cost", 0.0),
                "plan_rows": plan["Plan"].get("Plan Rows", 0),
                "actual_rows": plan["Plan"].get("Actual Rows", 0)
            }
            
            # Сохраняем статистику для будущего анализа
            query_hash = hash(query)
            self.query_stats[query_hash] = stats
            
            return execution_time, stats
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при анализе производительности запроса: {str(e)}")
            return 0.0, {} 