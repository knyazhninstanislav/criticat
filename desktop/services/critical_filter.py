# services/critical_filter.py
from typing import List, Dict, Any

from lis.base import LisResult


class CriticalFilterService:
    """
    Определяет, какие сырые результаты из ЛИС являются критическими.

    Логика:
    - Берёт сырой LisResult
    - Смотрит настройки теста (monitor_type, ref_lower, ref_upper)
    - Решает: критично или нет
    - Если критично — считает процент отклонения
    """

    def filter_critical(
        self,
        raw_results: List[LisResult],
        test_settings: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """
        Отфильтровать критические результаты.

        Args:
            raw_results: сырые результаты из ЛИС
            test_settings: настройки мониторинга тестов из БД

        Returns:
            Список словарей с критическими результатами
            (совместим с тем, что ждёт save_critical_results_batch)
        """
        critical = []

        for result in raw_results:
            settings = test_settings.get(result.test_name, {})
            if not settings.get('monitored'):
                continue

            monitor_type = settings.get('monitor_type', 'both')
            ref_lower = settings.get('ref_lower', result.ref_lower) or 0
            ref_upper = settings.get('ref_upper', result.ref_upper) or 0

            is_critical = False
            deviation = 0.0

            # Только нижний порог
            if monitor_type == 'lower':
                if ref_lower > 0 and result.result_value < ref_lower:
                    is_critical = True
                    deviation = ((ref_lower - result.result_value) / ref_lower) * 100

            # Только верхний порог
            elif monitor_type == 'upper':
                if ref_upper > 0 and result.result_value > ref_upper:
                    is_critical = True
                    deviation = ((result.result_value - ref_upper) / ref_upper) * 100

            # Оба порога
            else:  # both
                if ref_lower > 0 and result.result_value < ref_lower:
                    is_critical = True
                    deviation = ((ref_lower - result.result_value) / ref_lower) * 100
                elif ref_upper > 0 and result.result_value > ref_upper:
                    is_critical = True
                    deviation = ((result.result_value - ref_upper) / ref_upper) * 100

            if is_critical:
                critical.append({
                    'id': result.id,
                    'ids': result.ids,
                    'full_name': result.full_name,
                    'department': result.department,
                    'test_name': result.test_name,
                    'result_value': result.result_value,
                    'ref_lower': ref_lower,
                    'ref_upper': ref_upper,
                    'deviation_percent': round(deviation, 2),
                    'monitor_type': monitor_type,
                })

        return critical