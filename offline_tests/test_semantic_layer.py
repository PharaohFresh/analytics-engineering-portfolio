from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def semantic_definitions():
    measures, metrics = {}, {}
    for path in sorted((ROOT / 'models' / 'semantic').glob('*.yml')):
        document = yaml.safe_load(path.read_text(encoding='utf-8'))
        for model in document.get('semantic_models', []):
            for measure in model.get('measures', []):
                measures[measure['name']] = {**measure, 'semantic_model': model['name']}
        for metric in document.get('metrics', []):
            metrics[metric['name']] = metric
    return measures, metrics


def measure_of(metric_name, measures, metrics):
    metric = metrics[metric_name]
    assert metric['type'] == 'simple', metric_name
    return measures[metric['type_params']['measure']]


def test_every_ratio_takes_numerator_and_denominator_from_one_semantic_model():
    # Mixing models would mix time cohorts (item vs order header date) and populations.
    measures, metrics = semantic_definitions()
    ratios = [metric for metric in metrics.values() if metric['type'] == 'ratio']
    assert {metric['name'] for metric in ratios} == {'average_order_value', 'return_rate', 'gross_margin_rate'}
    for metric in ratios:
        numerator = measure_of(metric['type_params']['numerator'], measures, metrics)
        denominator = measure_of(metric['type_params']['denominator'], measures, metrics)
        assert numerator['semantic_model'] == denominator['semantic_model'], metric['name']


def test_aov_divides_item_revenue_by_distinct_orders_with_items():
    measures, metrics = semantic_definitions()
    assert metrics['average_order_value']['type_params'] == {'numerator': 'total_revenue',
                                                             'denominator': 'orders_with_items'}
    denominator = measure_of('orders_with_items', measures, metrics)
    assert (denominator['semantic_model'], denominator['agg'], denominator['expr']) == \
        ('order_items', 'count_distinct', 'order_key')
