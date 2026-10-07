from pathlib import Path

from jinja2 import Environment, StrictUndefined
import pytest
import yaml

from orchestration.platform_config import audit_command, build_command, target_environment


ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('environment', [{}, {'DBT_TARGET':'prod'},
 {'DBT_TARGET':'dev','BQ_PROJECT':'example-project','BQ_DATASET':'custom_dev'},
 {'DBT_TARGET':'prod','BQ_PROJECT':'example-project','BQ_DATASET':'custom_prod'}])
def test_deployed_build_and_audit_target_matches_real_profile_template(environment):
    result=target_environment(environment,'/tmp/space and semicolon; directory')
    env_var=lambda key,default: environment.get(key,default)
    document=Environment(undefined=StrictUndefined).from_string((ROOT/'profiles.yml.example').read_text(encoding='utf-8')).render(env_var=env_var)
    profile=yaml.safe_load(document)['analytics_engineering_portfolio'];target=profile['outputs'][profile['target']]
    assert result['DBT_TARGET']==profile['target']
    assert result['BQ_PROJECT']==target['project'] and result['BQ_DATASET']==target['dataset']
    # Values are carried as environment, not interpolated into shell program text.
    assert result['DBT_PROJECT_DIR'] not in build_command(False)
    assert '"$DBT_PROJECT_DIR"' in build_command(False) and '"$DBT_TARGET"' in build_command(False)
    assert '"$DBT_PROJECT_DIR"' in audit_command()


@pytest.mark.parametrize('environment', [{'DBT_TARGET':'unknown'},{'DBT_TARGET':''},{'BQ_PROJECT':''},{'BQ_DATASET':''}])
def test_invalid_deployment_target_fails_before_task_creation(environment):
    with pytest.raises(ValueError):target_environment(environment,'/tmp/project')
