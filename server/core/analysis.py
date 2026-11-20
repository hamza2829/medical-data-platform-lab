from collections import defaultdict
from .models import FHIRResource

THRESHOLDS = {
    '8867-4': ('Heart rate', 'beats/min', lambda n: n > 100 or n < 50, 'Review heart rate outside the demo reference band.'),
    '59408-5': ('Oxygen saturation', '%', lambda n: n < 92, 'Review oxygen saturation below 92%.'),
    '8310-5': ('Body temperature', '°C', lambda n: n >= 38, 'Review elevated body temperature.'),
}

def analyze_patient(patient_id: str) -> dict:
    records = [r for r in FHIRResource.objects.filter(resource_type='Observation') if r.data.get('subject', {}).get('reference') == f'Patient/{patient_id}']
    grouped = defaultdict(list)
    alerts = []
    for record in records:
        data = record.data
        coding = (data.get('code', {}).get('coding') or [{}])[0]
        code = coding.get('code', '')
        value = data.get('valueQuantity', {}).get('value')
        if not isinstance(value, (int, float)): continue
        grouped[code].append({'value': float(value), 'effectiveDateTime': data.get('effectiveDateTime', '')})
    trends = []
    for code, points in grouped.items():
        ordered = sorted(points, key=lambda point: point['effectiveDateTime'])
        first, last = ordered[0], ordered[-1]
        label, unit, predicate, message = THRESHOLDS.get(code, (code, '', lambda n: False, ''))
        trends.append({'code': code, 'name': label, 'unit': unit, 'count': len(ordered), 'change': round(last['value'] - first['value'], 2), 'direction': 'rising' if last['value'] > first['value'] else 'falling' if last['value'] < first['value'] else 'steady', 'points': ordered[-30:]})
        if predicate(last['value']):
            high = (code == '59408-5' and last['value'] < 90) or (code == '8310-5' and last['value'] >= 39)
            alerts.append({'code': code, 'label': label, 'value': last['value'], 'message': message, 'severity': 'high' if high else 'moderate'})
    return {'patient_id': patient_id, 'trends': trends, 'alerts': alerts, 'observation_count': len(records)}
