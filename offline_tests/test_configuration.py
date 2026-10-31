import re
from pathlib import Path

from jinja2 import Environment, StrictUndefined
import pytest
import yaml

from orchestration.platform_config import audit_command, build_command, target_environment


ROOT=Path(__file__).resolve().parents[1]


def render_profile(environment):
    env_var=lambda key,default: environment.get(key,default)
    document=Environment(undefined=StrictUndefined).from_string((ROOT/'profiles.yml.example').read_text(encoding='utf-8')).render(env_var=env_var)
    profile=yaml.safe_load(document)['analytics_engineering_portfolio']
    return profile['target'], profile['outputs'][profile['target']]


@pytest.mark.parametrize('environment', [{}, {'DBT_TARGET':'prod'},
 {'DBT_TARGET':'dev','BQ_PROJECT':'example-project','BQ_DEV_DATASET':'custom_dev'},
 {'DBT_TARGET':'prod','BQ_PROJECT':'example-project','BQ_PROD_DATASET':'custom_prod'}])
def test_deployed_build_and_audit_target_matches_real_profile_template(environment):
    result=target_environment(environment,'/tmp/space and semicolon; directory')
    # Tasks use append_env=True: the worker environment plus explicit task values.
    target_name,target=render_profile({**environment, **result})
    assert result['DBT_TARGET']==target_name
    assert result['BQ_PROJECT']==target['project'] and result['BQ_DATASET']==target['dataset']
    # Values are carried as environment, not interpolated into shell program text.
    assert result['DBT_PROJECT_DIR'] not in build_command(False)
    assert '"$DBT_PROJECT_DIR"' in build_command(False) and '"$DBT_TARGET"' in build_command(False)
    assert '"$DBT_PROJECT_DIR"' in audit_command()


@pytest.mark.parametrize('environment', [{'DBT_TARGET':'unknown'},{'DBT_TARGET':''},{'BQ_PROJECT':''},{'BQ_DEV_DATASET':''},
 {'DBT_TARGET':'prod','BQ_PROD_DATASET':''}])
def test_invalid_deployment_target_fails_before_task_creation(environment):
    with pytest.raises(ValueError):
        target_environment(environment,'/tmp/project')


@pytest.mark.parametrize('inherited', [
    {'BQ_DATASET': 'dbt_dev'},
    {'BQ_DEV_DATASET': 'dbt_dev'},
    {'BQ_DATASET': 'dbt_dev', 'BQ_DEV_DATASET': 'dbt_dev'},
])
def test_dev_dataset_exported_in_the_shell_never_reaches_prod(inherited):
    environment = {**inherited, 'DBT_TARGET': 'prod'}
    result = target_environment(environment, '/tmp/project')
    _, target = render_profile({**environment, **result})
    assert target['dataset'] == 'analytics'
    assert result['BQ_DATASET'] == 'analytics'


def test_profile_outputs_do_not_share_a_dataset_variable():
    template = (ROOT / 'profiles.yml.example').read_text(encoding='utf-8')
    assert "env_var('BQ_DATASET'" not in template
    _, dev = render_profile({'DBT_TARGET': 'dev', 'BQ_DEV_DATASET': 'one', 'BQ_PROD_DATASET': 'two'})
    _, prod = render_profile({'DBT_TARGET': 'prod', 'BQ_DEV_DATASET': 'one', 'BQ_PROD_DATASET': 'two'})
    assert (dev['dataset'], prod['dataset']) == ('one', 'two')


def test_snapshots_use_a_per_target_schema():
    # target_schema is a literal dataset shared by every target; schema is suffixed per target.
    snapshots = sorted((ROOT / 'snapshots').glob('*.sql'))
    assert snapshots
    for path in snapshots:
        text = path.read_text(encoding='utf-8')
        assert 'target_schema' not in text, path.name
        assert re.search(r"\bschema\s*=\s*'snapshots'", text), path.name
    assert 'target_schema' not in (ROOT / 'dbt_project.yml').read_text(encoding='utf-8')
