from django.db import models

# Create your models here.

class Report(models.Model):
    testScriptComponentExecutionResultsId = models.IntegerField()
    name = models.CharField(max_length=250)
    testPackageDisplayedName = models.CharField(max_length=250)
    result = models.CharField(max_length=250)
    startTime = models.CharField(max_length=250)
    stopTime = models.CharField(max_length=250)
    duration = models.CharField(max_length=250)
    logFiles = models.TextField(blank=True)
    testScriptComponentId = models.IntegerField()
    testScriptId = models.IntegerField()
    groupId = models.IntegerField()
    failureReason = models.TextField(blank=True)
    history = models.TextField(blank=True)


class BKCReport(models.Model):
    platform_name_short = models.TextField(blank=False)
    report = models.TextField(blank=False)
    run_ids = models.TextField(blank=True)


class Platform(models.Model):
    platform_name_short = models.TextField(blank=False, unique=True)
    platform_name = models.TextField(blank=True)
    history = models.TextField(blank=True)


class User(models.Model):
    user = models.CharField(blank=False, unique=True, max_length=250)
    full_name = models.CharField(blank=True, max_length=250)
    email = models.CharField(blank=True, max_length=250)
    role = models.CharField(blank=True, max_length=250)


class TestCase(models.Model):
    hsdes_id = models.TextField(blank=False, unique=True)
    platform_name_short = models.TextField(blank=False)
    automation_completion = models.TextField(blank=True)
    automation_eta = models.TextField(blank=True)
    automation_potential = models.TextField(blank=True)
    automation_owner = models.TextField(blank=True)
    egs_blocked = models.TextField(blank=True)
    automation_script = models.TextField(blank=True)
    non_automatable_reason = models.TextField(blank=True)
    automation_comments = models.TextField(blank=True)
    automation_remarks = models.TextField(blank=True)
    automation_applicable = models.TextField(blank=True)
    history = models.TextField(blank=True)

class TestCaseExcel(models.Model):
    temp_test_case_id = models.TextField(blank=True)
    phoenix_id = models.TextField(blank=True)
    test_case_id = models.TextField(blank=False, unique=True)
    platform = models.TextField(blank=False)
    domain = models.TextField(blank=True)
    feature_group = models.TextField(blank=True)
    database_source = models.TextField(blank=True)
    title = models.TextField(blank=True)
    milestone = models.TextField(blank=True)
    bkc_candidate = models.TextField(blank=True)
    automation_current = models.TextField(blank=True)
    automation_potential = models.CharField(blank=True, max_length=250)
    automation_eta = models.TextField(blank=True)
    automation_completion = models.TextField(blank=True)
    automation_deployment_eta = models.TextField(blank=True)
    automation_deployed = models.TextField(blank=True)
    deployed_result = models.TextField(blank=True)
    script_path = models.TextField(blank=True)
    automation_developer = models.TextField(blank=True)
    operating_system = models.TextField(blank=True)
    egs_blocked = models.TextField(blank=True)
    automation_applicable = models.TextField(blank=True)
    automation_category = models.TextField(blank=True)
    automation_block_category = models.TextField(blank=True)
    automation_remarks = models.TextField(blank=True)
    non_automatable_remarks = models.TextField(blank=True)
    developer_comments = models.TextField(blank=True)
    platform_tc_category = models.TextField(blank=True)
    source_patch_link = models.TextField(blank=True)
    hw_config = models.TextField(blank=True)
    common_candidates = models.TextField(blank=True)
    is_new_tc = models.TextField(blank=True)
    is_deprecated = models.TextField(blank=True)
    history = models.TextField(blank=True)

class ExecutionReport(models.Model):
    test_case_id = models.TextField(blank=False)
    platform = models.TextField(blank=False)
    title = models.TextField(blank=True)
    platform_tc_category = models.TextField(blank=True)
    execution_status = models.CharField(blank=True, max_length=250)
    error_message = models.TextField(blank=True)
    ticket_link = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    history = models.TextField(blank=True)


class TestStepsExcel(models.Model):
    test_case_id = models.TextField(blank=False)
    platform = models.TextField(blank=True)
    title = models.TextField(blank=False)
    step_number = models.TextField(blank=True)
    step = models.TextField(blank=True)
    expected_result = models.TextField(blank=True)
    history = models.TextField(blank=True)


