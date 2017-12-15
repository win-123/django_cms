# _*_coding:utf-8_*_
from kingadmin import custom_perm_logic

# 权限样式 app_权限名字
perm_dic = {

    'web_table_index': ['table_index', 'GET', [], {}, ],
    'web_table_list': ['table_list', 'GET', [], {}],
    'web_table_admin_action': ['table_list', 'POST', [], {}],
    'web_table_list_view': ['table_change', 'GET', [], {}],
    'web_table_list_change': ['table_change', 'POST', [], {}],
    'web_table_del': ['table_del', 'POST', [], {}],
    'web_table_del_view': ['table_del', 'GET', [], {}],
    'web_table_add_view': ['table_add', 'GET', [], {}],
    'web_table_add': ['table_add', 'POST', [], {}],
    'web_password_reset_form_view': ['password_reset', 'GET', [], {}],
    'web_password_reset_form': ['password_reset', 'POST', [], {}],
    # 'web_can_access_my_clients': ['table_list', 'GET', [],
    #                               {'perm_check': 33, 'arg2': 'test'},
    #                               custom_perm_logic.only_view_own_customers],
    # 'web_invoke_admin_action':['table_list','POST',[]],
    # 'web_table_change_page':['table_change','GET',[]],
    # 'web_table_change':['table_change','POST',[]],
    #'web_manage_table_list': ['table_list', 'GET', [], {}],
    'web_manage_dashboard': ['dashboard', 'GET', [], {}],
    'web_manage_table_obj_add_view': ['table_obj_add', 'GET', [], {}],
    'web_manage_table_obj_add': ['table_obj_add', 'POST', [], {}],
    'web_manage_table_obj_change_view': ['table_obj_change', 'GET', [], {}],
    'web_manage_table_obj_change': ['table_obj_change', 'POST', [], {}],
    'web_manage_table_obj_del_view': ['table_obj_del', 'GET', [], {}],
    'web_manage_table_obj_del': ['table_obj_del', 'POST', [], {}],

}


django_custom_permissions = (
    # for kingadmin基础权限
    ('web_table_index','可以[查看]kingadmin所有注册的表'),
    ('web_table_list','可以[查看]kingadmin每个注册表的数据列表'),
    ('web_table_admin_action','可以[执行]kingadmin admin action动作'),
    ('web_table_list_view','可以[查看]kingadmin所有表里每条纪录的详细数据'),
    ('web_table_list_change','可以[修改]kingadmin所有注册表的数据'),
    ('web_table_del','可以[删除]kingadmin所有注册表的数据'),
    ('web_table_del_view','可以[查看]kingadmin 数据删除页面'),
    ('web_table_add_view','可以[查看]kingadmin 数据添加页面'),
    ('web_table_add','可以[创建]kingadmin 每个表的数据'),
    ('web_password_reset_form_view','可以[查看]kingadmin 每个account密码修改页'),
    ('web_password_reset_form','可以[修改]kingadmin 每个account的密码'),

    #for 路飞管理后台

    ('web_manage_dashboard','可以[查看]management Dashboard页面'),

    ('web_manage_table_obj_add_view','可以[查看]management数据添加页面'),
    ('web_manage_table_obj_add','可以[创建]management每个表的数据'),
    ('web_manage_table_obj_change_view','可以[查看]management每个表数据修改页面'),
    ('web_manage_table_obj_change','可以[修改]management每个表的数据'),
    ('web_manage_table_obj_del_view','可以[查看]management每个表的数据删除页'),
    ('web_manage_table_obj_del','可以[删除]management每个表的数据'),

)