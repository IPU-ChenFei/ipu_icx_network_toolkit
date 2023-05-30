"""dpgautomation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url
from automation import views

urlpatterns = [
    url(r'^$', views.reports, name='reports'),
    url(r'report/(?P<execution_id>\d+)/$', views.triage_report, name='triage_report'),
    url(r'reports/$', views.reports, name='reports'),
    url(r'testcases/$', views.testcases, name='testcases'),
    url(r'users/add_user$', views.add_user, name='add_user'),
    url(r'sync/',views.sync,name='sync'),
    url(r'login$', views.login, name='login'),
    url(r'logout$', views.logout, name='logout'),
    url(r'users/update_user/$', views.update_user, name='update_user'),
    url(r'reports/create_report/$', views.create_report, name='create_report'),
    url(r'reports/generate_report/$', views.generate_report, name='generate_report'),
    url(r'testcases/(?P<platform>\w+)/(?P<tcid>.+?)/update/$', views.update_testcase, name='update_testcase'),
    url(r'testcases/(?P<platform>\w+)/(?P<tcid>.+?)/$', views.testcase_details, name='testcase_details'),

    url(r'statistics/$', views.statistics, name='statistics'),
    url(r'testplan/(?P<platform>\w+)/(?P<bkc>\w+)/$', views.test_plan, name='test_plan'),
    #_hsdes/(?P<platform>\w+)/$', views.test_plan_hsdes, name='test_plan_hsdes'),
    url(r'teststeps/(?P<platform>\w+)/(?P<tcid>.+?)/$', views.test_steps, name='test_steps'),
    url(r'bkcfilters/(?P<platform>\w+)/$', views.bkc_filters, name='bkc_filters'),
    url(r'filter_query/(?P<platform>\w+)/(?P<bkc>\w+)/(?P<bkc_candidate>.+?)/(?P<automation_category>.+?)/$', views.filter_query, name='filter_query'),
    url(r'automation_dev_tracker/(?P<platform>\w+)/(?P<bkc>\w+)/$', views.automation_dev_tracker, name='automation_dev_tracker'),
    url(r'automation_dev_tracker/(?P<platform>\w+)/(?P<bkc>\w+)/(?P<developer>.+?)/(?P<developed_ww>.+?)/$', views.developer_tracker, name='developer_tracker'),
    url(r'dev_tracker/(?P<platform>\w+)/(?P<bkc>\w+)/(?P<developer>.+?)/(?P<plan_ww>.+?)/(?P<automation_category>\w+)/$',
        views.developer_plan_tracker, name='developer_plan_tracker'),
    url(r'automation_dev_tracker/(?P<platform>\w+)/(?P<bkc>\w+)/(?P<ww>.+?)/$', views.get_automation_plan, name='get_automation_plan'),
    url(r'automation_charts/(?P<platform>\w+)/(?P<bkc>\w+)/$', views.automation_charts, name='automation_charts'),
    url(r'platform_reports/$', views.platform_reports, name='platform_reports'),
    url(r'automation_dev_trackers/$', views.automation_dev_trackers, name='automation_dev_trackers'),
    url(r'platform_reports/(?P<platform>\w+)/(?P<bkc>\w+)$$', views.platform_reports, name='platform_reports'),
    url(r'platform_reports/platform_report/(?P<platform>\w+)/(?P<bkc>\w+)$', views.platform_report, name='platform_report'),
    url(r'statistics/(?P<platform>\w+)/(?P<bkc>\w+)/$', views.platform_statistics, name='platform_statistics')
]
