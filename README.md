# django_cms

一， Requirements

django CMS requires Django 1.8, 1.9 or 1.10 and Python 2.7, 3.3 or 3.4.

二， Create and activate a virtual venv

virtualenv env
source env/bin/activate          # mac环境中的启动

三 ， pip is the Python installer. Make sure yours is up-to-date, as earlier versions can be less reliable:
（尽量保证你的pip 版本是最新的， 如果不是就使用下面的命令进行更新）
pip install --upgrade pip

四， Use the django CMS installer
    The django CMS installer is a helpful script that takes care of setting up a new project.

接下来你就有了一个新的django 启动命令： djangocms

五， 创建文件 并切换到文件到文件中
      mkdir my-project
      cd my-project
     
六 ， 运行并 创建django项目 (项目名：my_project )
      djangocms -f -p . my_project
      
      简要说明 －f -p . 
      run the django CMS installer
      install Django Filer too (-f) - required for this tutorial
      use the current directory as the parent of the new project directory (-p .)
      call the new project directory mysite
      
七 ， 值得注意的是： 创建项目完成后，settings 中默认的设置为中文， template , static 默认把项目添加到起始路径中，同时还添加了一些必须的配置
      比如 ：SITE = 1 等，同时还帮我们创建了一个superuser admin  密码 也是 admin 
          The installer creates an admin user for you, with username/password admin/admin.

八， 启动项目   ： 当然 启动项目的命令和Django的是一样的。
          python manage.py runserver




