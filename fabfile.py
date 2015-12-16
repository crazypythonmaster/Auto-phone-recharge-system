from contextlib import contextmanager
import sys
import os.path
import os
import subprocess

import fabric
from fabric.api import env, prefix
from fabric.colors import green
from fabric.decorators import task
from fabric.utils import abort
from fabric.contrib import console, files
from fabric.colors import red
from fabric.api import local, cd, run, sudo
from fabric.api import put

import fabtools
from fabtools import require


#
# todo test connection and setup and configure for database, redis

do_ip = ['104.236.248.219']
# sm_ip = ['23.250.19.159']

# def data1_root():
#     env.user = 'root'
#     env.key_filename = '~/.ssh/ezoffer'
#     env.hosts = sm_ip

# @task
# def data1():
#     env.user = 'deploy'
#     env.key_filename = '~/.ssh/ezoffer'
#     env.hosts = sm_ip
#
#     # specify path to deploy root dir - you need to create this
#     env.deploy_project_root = '/opt/projects/pparsb/'
#     env.prod_branch = 'production'
#     env.is_production = True
#     env.prod_settings = 'production.py'
#
#     env.conf_prod_uwsgi = 'conf/production/uwsgi/pinim.ini'
#     env.conf_prod_nginx = ['conf/production/nginx/pinim.conf', 'conf/production/nginx/static.pinim.com.conf']
#
#     env.DJANGO_SETTINGS_MODULE = "pinim.settings.production"

@task
def do_root():
    # env.do_r_api_token = '0d5861148b6671f4a940513fb1bee5e1a8906f6dc24eecaaec3da92ccba2ef34'
    env.user = 'root'
    env.key_filename = '~/.ssh/ezoffer'
    env.hosts = do_ip

@task
def do_a():
    # env.do_r_api_token = '0d5861148b6671f4a940513fb1bee5e1a8906f6dc24eecaaec3da92ccba2ef34'
    env.user = 'deploy'
    env.key_filename = '~/.ssh/ezoffer'
    env.hosts = do_ip

    env.prj_name = 'ppars_a'

    # specify path to deploy root dir - you need to create this
    env.deploy_project_root = '/opt/projects/ppars_a/'
    env.prod_branch = 'production'
    env.is_production = True
    env.prod_settings = 'production_a.py'

    env.conf_prod_uwsgi = 'conf/production/uwsgi/ppars_a.ini'
    env.conf_prod_nginx = ['conf/production/nginx/ppars_a.conf', ] #'conf/production/nginx/static.ppars_a.conf']

    env.restart_celery = 'celery_a_restart.sh'

    env.DJANGO_SETTINGS_MODULE = "ppars.settings.production_a"

    # current revision env
    env.curr_revision_env = ''

    # current revision code
    env.curr_revision_code = ''


@task
def do_b():
    # env.do_r_api_token = '0d5861148b6671f4a940513fb1bee5e1a8906f6dc24eecaaec3da92ccba2ef34'
    env.user = 'deploy'
    env.key_filename = '~/.ssh/ezoffer'
    env.hosts = do_ip

    env.prj_name = 'ppars_b'

    # specify path to deploy root dir - you need to create this
    env.deploy_project_root = '/opt/projects/ppars_b/'
    env.prod_branch = 'production'
    env.is_production = True
    env.prod_settings = 'production_b.py'

    env.conf_prod_uwsgi = 'conf/production/uwsgi/ppars_b.ini'
    env.conf_prod_nginx = ['conf/production/nginx/ppars_b.conf', ] #'conf/production/nginx/static.ppars_b.conf']

    env.restart_celery = 'celery_b_restart.sh'

    env.DJANGO_SETTINGS_MODULE = "ppars.settings.production_b"

    # current revision env
    env.curr_revision_env = ''

    # current revision code
    env.curr_revision_code = ''


# def prod():
#     env.host_string = 'prod'
#     env.hosts = ['pin-im.com']
#     env.user = 'deploy'
#     env.key_filename = '~/.ssh/k9-pin-im.pkey'
#
#     # specify path to deploy root dir - you need to create this
#     env.deploy_project_root = '/opt/projects/ppars_b/'
#     env.prod_branch = 'production'
#     env.is_production = True
#     env.prod_settings = 'production.py'
#
#     env.conf_prod_uwsgi = 'conf/production/uwsgi/ppars_b.ini'
#     env.conf_prod_nginx = ['conf/production/nginx/ppars_b.conf', 'conf/production/nginx/static.ppars_b.conf']
#
#     env.DJANGO_SETTINGS_MODULE = "ppars.settings.production"

# @task
# def stag():
#     env.host_string = 'stag'
#     # env.hosts = ['staging.pin-im.com']
#     env.hosts = ['91.200.60.28']
#     env.user = 'deploy'
#     env.key_filename = '~/.ssh/k9-pin-im.pkey'
#
#     # specify path to deploy root dir - you need to create this
#     env.deploy_project_root = '/opt/projects/pinim-staging/'
#     env.prod_branch = 'staging'
#     env.is_production = False
#     env.prod_settings = 'staging.py'
#
#     env.conf_prod_uwsgi = 'conf/staging/uwsgi/pinim-staging.ini'
#     env.conf_prod_nginx = ['conf/staging/nginx/pinim-staging.conf', 'conf/staging/nginx/static.staging.pinim.com.conf']
#
#     env.DJANGO_SETTINGS_MODULE = "pinim.settings.staging"


# def new_server():
#     env.host_string = 'prod-new'
#     env.hosts = sm_ip
#     env.user = 'deploy'
#     env.key_filename = '~/.ssh/k9-pin-im.pkey'
#
#     # specify path to deploy root dir - you need to create this
#     env.deploy_project_root = '/opt/projects/pinim/'
#     env.prod_branch = 'production'
#     env.is_production = True
#     env.prod_settings = 'production.py'
#
#     env.conf_prod_uwsgi = 'conf/production/uwsgi/pinim.ini'
#     env.conf_prod_nginx = ['conf/production/nginx/pinim.conf', 'conf/production/nginx/static.pinim.conf']

# app_dir = '/opt/projects/ppars_b'

# prod_root_dir = '/opt/projects'
# prod_app_dir = os.path.join(prod_root_dir, 'ppars_b')

# current revision env
# env.curr_revision_env = ''

# current revision code
# env.curr_revision_code = ''

# Define sets of servers as roles
# env.roledefs = {
#     'www': ['www1', 'www2', 'www3', 'www4', 'www5'],
#     'databases': ['db1', 'db2']
# }


# remote ssh credentials
# env.hosts = ['10.1.1.25']
# env.user = 'deploy'
# env.password = 'XXXXXXXX' #ssh password for user
# or, specify path to server public key here:
# env.key_filename = ''

# specify path to files being deployed
# env.archive_source = '.'

# archive name, arbitrary, and only for transport
# env.archive_name = 'release'

# specify name of dir that will hold all deployed code
# env.deploy_release_dir = '.releases'

# symlink name. Full path to deployed code is env.deploy_project_root + this
env.deploy_current_dir = 'main'
env.deploy_current_env = '.env'
env.env_requirements = 'requirements.txt'



def get_project_root():
    this_dir = os.path.dirname(__file__)
    this_resolved = os.path.realpath(this_dir)

    return this_resolved


ABSOLUTE_PROJECT_PATH = get_project_root()


def get_app_git_revision():
    git_info = {'branch': 'Unknown', 'revision': 'Unknown', 'updated': 'Unknown'}
    try:
        from git import LocalRepository
        from datetime import datetime

        repo = LocalRepository(ABSOLUTE_PROJECT_PATH)
        branch = repo.getCurrentBranch()
        rev = repo.getHead()
        updated = rev.getDate()
        git_info.update({
            'repo': repo,
            'branch': branch,
            'revision': rev.name,
            'rev': rev.hash[:10],
            'updated': datetime.utcfromtimestamp(updated),
        })
    except Exception, e:
        print e
    return git_info


GIT_DATA = get_app_git_revision()

# print ABSOLUTE_PROJECT_PATH

def upload_archive():
    # create archive from env.archive_source
    print('check current revision ....')
    # print(GIT_DATA)
    hash_name = GIT_DATA['rev']
    arch_name = '%s.tar.gz' % GIT_DATA['rev']
    env.deploy_full_path = os.path.join(env.deploy_project_root, hash_name)
    env.deploy_current_rev = hash_name

    env.curr_revision_code = os.path.join(env.deploy_project_root, hash_name)

    if files.exists(env.deploy_full_path):
        print(green("this revision '%s' is exist on remote server" % hash_name))
        return True

    print('creating archive...')
    local('git archive HEAD | gzip > tmp/%s' % arch_name)
    # local('cd %s && zip -qr %s.zip -x=fabfile.py -x=fabfile.pyc *' % (env.archive_source, env.archive_name))

    # create time named dir in deploy dir
    print('uploading archive...')
    put('tmp/%s' % arch_name, arch_name)

    # with cd(app_dir):
    print('extracting code...')

    run('mkdir -p %s' % env.deploy_full_path)
    run('tar -zxvf %s -C %s' % (arch_name, env.deploy_full_path))

    settings_path = os.path.join(env.deploy_full_path, 'ppars', 'settings')
    print(green('Check settings file: %s' % os.path.join(settings_path, 'settings_local.py')))

    with cd(settings_path):
        if not files.exists('settings_local.py'):
            run('ln -s %s %s' % (env.prod_settings, 'settings_local.py'))

    return True


    # run('rm -f %s' % zip_path)

    # run('cd %s && mkdir %s' % (env.deploy_project_root + env.deploy_release_dir, deploy_timestring))

    # extract code into dir

    # = env.deploy_project_root + env.deploy_release_dir + '/' + hash_name
    # put(env.archive_name+'.zip', env.deploy_full_path)
    # run('cd %s && unzip -q %s.zip -d . && rm %s.zip' % (env.deploy_full_path, env.archive_name, env.archive_name))


def before_symlink():
    # code is uploaded, but not live. Perform final pre-deploy tasks here
    print('before symlink tasks...')


def make_main_symlink():
    # delete existing symlink & replace with symlink to deploy_timestring dir
    print('creating main symlink to uploaded code...')
    main = env.deploy_project_root + env.deploy_current_dir
    run('rm -f %s.prev' % main)
    if files.exists(main):
        run('mv %s %s.prev' % (main, main))
    run('ln -s %s %s' % (env.deploy_full_path, main))


def after_symlink():
    # code is live, perform any post-deploy tasks here
    print('after symlink tasks...')


def cleanup():
    # remove any artifacts of the deploy process
    arch_name = '%s.tar.gz' % GIT_DATA['rev']

    print('cleanup...')
    local('rm -rf tmp/%s' % arch_name)
    run('rm -rf %s' % arch_name)


import hashlib


def md5sum(filename, blocksize=65536):
    h = hashlib.md5()
    with open(filename, "r+b") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            h.update(block)
    return h.hexdigest()


@contextmanager
def virtualenv():
    """
    Run commands within the current virtualenv.
    """

    env_path = os.path.join(env.curr_revision_env, 'bin', 'activate')

    with cd(env.curr_revision_code):
        print(green('on %s, with %s' % (env.curr_revision_code, env.curr_revision_env)))
        with prefix("source %s" % env_path):
            print('env_path:', env_path, )
            print('rev_code', env.curr_revision_code)
            yield


def update_virtualenv():
    print('update virtualenv ...')
    h = md5sum(env.env_requirements)
    # print h, h[:10]

    env.env_name = '.env.%s.%s' % (env.prj_name, h[:10])
    env.env_full_path_rev = os.path.join(env.deploy_project_root, env.env_name)

    env.curr_revision_env = os.path.join(env.deploy_project_root, env.env_name)

    if files.exists(env.env_full_path_rev):
        print(green("virtualenv '%s' is exist on remote server" % env.env_name))
        return True

    print(green("install virtualenv '%s' on remote server" % env.env_name))
    with cd(env.deploy_project_root):
        run('virtualenv %s --no-site-packages' % env.env_name)

    # with cd(env.deploy_project_root + env.deploy_current_dir):
    with virtualenv():
        run('pip install -r %s' % env.env_requirements)

    return True


def make_e_symlink():
    print('creating symlink to virtualenv...')
    main = env.deploy_project_root + env.deploy_current_env
    run('rm -f %s.prev' % main)
    if files.exists(main):
        run('mv %s %s.prev' % (main, main))
    run('ln -s %s %s' % (env.curr_revision_env, main))


def git_ensure_clean():
    out = subprocess.check_output(["git", "status", "--porcelain"])
    if len(out) != 0:
        print(red("won't deploy because repo has uncommitted changes:"))
        print(out)
        sys.exit(1)
    print(green("git tree is clean"))


def check_current_branch():
    current_branch = GIT_DATA['branch'].name
    print(green('Current branch: "%s"' % (current_branch)))
    repo = GIT_DATA['repo']

    if not repo.isWorkingDirectoryClean():
        print(green('UntrackedFiles: ') + red(repo.getUntrackedFiles()))
        print(green('ChangedFiles: ') + red(repo.getChangedFiles()))
        print(green('StagedFiles: ') + red(repo.getStagedFiles()))
        ret = fabric.contrib.console.confirm(red('Current branch: %s is not Clean, need: "%s", execute?' % (current_branch, env.prod_branch)))
        if not ret:
            abort(red('"%s" branch is not Clean, STOP' % current_branch))
    else:
        print('Repo is Clean.')

    if not current_branch == env.prod_branch:
        ret = fabric.contrib.console.confirm(red('Current branch: %s is not for deploy, need: "%s", execute?' % (current_branch, env.prod_branch)))
        if not ret:
            abort(red('"%s" branch is not for deploy, STOP' % current_branch))
    return True


def delete_old_deploys(to_keep=5):
    with cd(os.path.join(env.deploy_project_root)):
        out = run('ls -1trA')
        lines = out.split("\n")
        i = 0
        code_to_del = []
        env_to_del = []
        while i < len(lines):
            s = lines[i].strip()
            if len(s) == 10:
                code_to_del.append(s)
            if len(s) == 21:
                env_to_del.append(s)
            i += 1
        if len(code_to_del) > to_keep:
            code_to_del = code_to_del[:-to_keep]
            print("deleting old deploys: %s" % str(code_to_del))
            for d in code_to_del:
                run("rm -rf %s" % d)

        if len(env_to_del) > to_keep:
            env_to_del = env_to_del[:-to_keep]
            print("deleting old env: %s" % str(env_to_del))
            for d in env_to_del:
                run("rm -rf %s" % d)
    return True


def update_conf():
    sudo('cp %s %s' % (os.path.join(env.deploy_project_root, env.deploy_current_dir, env.conf_prod_uwsgi), '/etc/uwsgi/apps-enabled'))
    if env.is_production:
        for conf in env.conf_prod_nginx:
            sudo('cp %s %s' % (os.path.join(env.deploy_project_root, env.deploy_current_dir, conf), '/etc/nginx/sites-enabled'))
    else:
        for conf in env.conf_prod_nginx:
            sudo('cp %s %s' % (os.path.join(env.deploy_project_root, env.deploy_current_dir, conf), '/etc/nginx/conf.d'))

# def copy_newrelic():
#     sudo('cp %s %s' % (os.path.join(env.deploy_project_root, env.deploy_current_dir, 'conf/production/newrelic/newrelic.ini'), env.deploy_project_root))


def restart_uwsgi():
    sudo('/etc/init.d/uwsgi restart')

def restart_nginx():
    sudo('/etc/init.d/nginx restart')


def collectstatic():
    with virtualenv():
        run('python manage.py collectstatic --noinput')

        # DJANGO_SETTINGS_MODULE='pinim.settings'
        # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pinim.settings")
        # from django.core.management import setup_environ
        # import settings
        # setup_environ(settings)


        # sys.path.append(ABSOLUTE_PROJECT_PATH)
        # os.environ["DJANGO_SETTINGS_MODULE"] = env.DJANGO_SETTINGS_MODULE
        # from django.contrib.auth.models import User

        # from django.conf import settings
        # print('COMPRESS_ENABLED', settings.COMPRESS_ENABLED)
        #
        # if settings.COMPRESS_ENABLED:
        #
        #     run('python manage.py compress')

def make_migrate():
    with virtualenv():
        run('python manage.py migrate')

def make_syncdb():
    with virtualenv():
        run('python manage.py syncdb --noinput')


# def update_local_settings():
#     settings_path = os.path.join(env.deploy_project_root, env.deploy_current_rev, 'pinim', 'settings')
#     print(green('Check settings file: %s' % os.path.join(settings_path, 'settings_local.py')))
#     if not files.exists(os.path.join(settings_path, 'settings_local.py')):
#         run('ln -s %s %s' % (os.path.join(settings_path, env.prod_settings), os.path.join(settings_path, 'settings_local.py')))

def first_deploy():

    # todo make install all system packages and configure it
    pass


# def add_user():
#     add(deploy)
#     add_to_sudoers('deploy  ALL=(ALL) NOPASSWD: ALL')


def deploy_conf():
    deploy()
    update_conf()
    sudo('/etc/init.d/uwsgi restart')
    sudo('/etc/init.d/nginx restart')


def install_aptitude():
    sudo('apt-get install aptitude -y')


def upgrade():
    """
    Updates the repository definitions and upgrades the server
    """
    sudo('aptitude update -y')
    sudo('aptitude upgrade -y')

def host_type():
    run('uname -s')

@task
def make_swap():
    r = sudo('swapon -s')
    print '-'*20
    print r.stdout

    sudo('df -h')
    if r.stdout == 'Filename				Type		Size	Used	Priority':
        print(green('Create swap File....'))
        # print(green(r.stdout))
        if files.exists('swapfile'):
            sudo('dd if=/dev/zero of=/swapfile bs=100M count=5')
            sudo('chown root:root /swapfile')
            sudo('chmod 0600 /swapfile')

            sudo('mkswap /swapfile')
            sudo('swapon /swapfile')

            fabric.contrib.files.append('/etc/fstab', '/swapfile none swap sw 0 0', use_sudo=True)
            sudo('echo 10 | sudo tee /proc/sys/vm/swappiness')

            sudo('echo vm.swappiness = 10 | sudo tee -a /etc/sysctl.conf')

        else:
            print(red('File "/swapfile" is exists'))

        sudo('swapon -s')


# def create_db():
#     user = 'pinim'
#     db_name = 'pinim_com'
#     db_pass = 'pinimpinim'
#     # run('sudo -u postgres createuser -d -A -P %s' % user)
#     # run('sudo -u postgres createdb -O %s %s' % (user, db_name))
#     # Require a PostgreSQL server
#     require.postgres.server()
#     require.postgres.user(user, db_pass)
#     require.postgres.database(db_name, user)


def create_mysql_db():
    user = 'ppars'
    db_name = 'ppars'
    db_pass = 'ppars123ppars'
    # run('sudo -u postgres createuser -d -A -P %s' % user)
    # run('sudo -u postgres createdb -O %s %s' % (user, db_name))
    # Require a PostgreSQL server
    require.mysql.server()
    require.mysql.user(user, db_pass)
    require.mysql.database(db_name)


def create_work_dir():
    print(green('Check deploy path'))
    if files.exists(env.deploy_project_root):
        print(green("root dir '%s' is exist on remote server" % env.deploy_project_root))
        return True

    print('creating dir...')
    sudo('chmod 777 /opt')
    run('mkdir -p %s' % env.deploy_project_root)


def create_rev_dir():
    print(green('Check deploy path'))
    if files.exists(env.deploy_full_path):
        print(green("this revision '%s' is exist on remote server" % env.deploy_full_path))
        return True

    print('creating dir...')
    sudo('chmod 777 /opt')
    run('mkdir -p %s' % env.deploy_full_path)


# updating the system.
#
# apt-get update
# apt-get upgrade


# munin-node
# pip install PyMunin
# https://github.com/perusio/nginx-munin

def add_user_from_root(new_user='deploy'):

    # env.user = 'root'
    # env.key_filename = ''
    new_user = 'deploy'

    if not fabtools.user.exists(new_user):
        fabtools.user.create(new_user, create_home=True, extra_groups=['sudo', ], shell='/bin/bash')
    fabtools.user.add_ssh_public_key(new_user, '/home/k9/.ssh/k9-pin-im.pub')

    # fabtools.user.add_ssh_public_key('root', '/home/k9/.ssh/k9-key.pub')

    fabric.contrib.files.append('/etc/sudoers', '%s ALL=(ALL) NOPASSWD: ALL' % new_user, use_sudo=False)


# def add_newrelic():
#     require.deb.key('548C16BF', url='https://download.newrelic.com/548C16BF.gpg')
#     require.deb.source('newrelic', 'http://apt.newrelic.com/debian/', 'newrelic', 'non-free')
#     require.deb.packages([
#         'newrelic-sysmond',
#     ])


@task
def init_server():

    # add_user() # need move to end after install

    print fabtools.system.distrib_id()
    print fabtools.system.distrib_release()

    # ubuntu 12.04
    require.deb.ppa('ppa:chris-lea/node.js')

    # ubuntu 14.04
    # need fix ?
    # require.deb.ppa('ppa:chris-lea/node.js')

    require.deb.ppa('ppa:chris-lea/redis-server')

    # if on VM rsyslog use CPU on 100%
    # service rsyslog stop
    # sed -i -e 's/^\$ModLoad imklog/#\$ModLoad imklog/g' /etc/rsyslog.conf
    # service rsyslog start

    fabtools.deb.update_index()
    fabtools.deb.upgrade()

    require.deb.packages([
        'sudo',
        'aptitude',
        'mc',
        'htop',
        'ntp',
        'ntpdate',
        'software-properties-common',
        'python-software-properties',
    ])


    sudo('echo "Etc/GMT" > /etc/timezone')
    sudo('dpkg-reconfigure -f noninteractive tzdata')
    sudo('locale-gen ru_UA')
    sudo('dpkg-reconfigure locales')

    # not need for SM server
    make_swap()

    # fabric.api.reboot()


    # Require some Debian/Ubuntu packages
    require.deb.packages([

        # pkgs
        # 'postgresql',
        'mysql-server',
        'uwsgi',
        'uwsgi-plugin-python',
        'nginx-full',
        'gcc',
        'make',

        # python
        'python-setuptools',
        'python-virtualenv',

        # libs
        'postgresql-server-dev-all',
        'libpq-dev',
        'python-dev',
        'libxml2-dev',
        'libxslt-dev',
        'redis-server',
        'rabbitmq-server',

        # for Pillow
        'libtiff4-dev',
        'libjpeg8-dev',
        'zlib1g-dev',
        'libfreetype6-dev',
        'liblcms2-dev',
        'libwebp-dev',
        'tcl8.5-dev',
        'tk8.5-dev',
        'python-tk',
        'libmysqlclient-dev',

        # for debug toolbar
        'libtidy-dev',

        # compressor
        'yui-compressor',

        # nodejs
        'nodejs',

    ])

    # require.nodejs.package()
    require.nodejs.package('less')
    require.nodejs.package('uglify-js')
    require.nodejs.package('coffee-script')


    # not need for OpenVZ VM
    sudo('echo "ntpdate ntp.ubuntu.com" > /etc/cron.daily/ntpdate')
    sudo('ntpdate -u pool.ntp.org')

    add_user_from_root()

    # sudo('reboot')
    fabric.api.reboot()

# fab do_root init_server
# fab do init_deploy

@task
def init_deploy():

    create_work_dir()

    create_mysql_db()

    deploy(first=True, restart=True, as_main=True)

# def restart_celery():
#     sudo("/etc/init.d/celeryd_a restart")
#     sudo("/etc/init.d/celerybeat_a restart")
#     sudo("/etc/init.d/celeryevcam_a restart")
#     print(green('Restart Celery Done'))
#
# def restart_celery():
#     sudo("/etc/init.d/celeryd_b restart")
#     sudo("/etc/init.d/celerybeat_b restart")
#     sudo("/etc/init.d/celeryevcam_b restart")
#     print(green('Restart Celery Done'))

def restart_celery():
    run("sh %smain/%s" % (env.deploy_project_root, env.restart_celery))

    print(green('Restart Celery Done'))

# def restart_celery_b():
#     run("sh %smain/celery_b_restart.sh" % env.deploy_project_root)
#
#     print(green('Restart Celery Done'))


# @notify
@task
def deploy(first=False,restart=True, as_main=True):

    check_current_branch()

    ret_c = upload_archive()
    # update_local_settings()
    ret_e = update_virtualenv()

    if first:
        make_syncdb()
    # else:
    make_migrate()

    collectstatic()

    # before_symlink()

    if ret_c and as_main:
        make_main_symlink()
        cleanup()

    if ret_e and as_main:
        make_e_symlink()

        # after_symlink()

    delete_old_deploys()

    if first:
        update_conf()
        # add_newrelic()
        # copy_newrelic()
        restart_nginx()
    if restart:
        restart_uwsgi()

    restart_celery()

    print(green('Current REV: ', env.curr_revision_code))
    print(green('Current ENV: ', env.curr_revision_env))

    # print('deploy complete!')

    # fabric.api.env.hosts = ['localhost',]


    # PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    # INIT_DIR = os.path.join(PROJECT_ROOT, 'init')


    # todo uncomment this for multi server configuration
    # def prod() :
    #     env.host_string = 'prod'
    #     env.hosts = ['pin-im.com']
    #     env.user = 'deploy'
    #     env.key_filename = '~/.ssh/k9-pin-im.pkey'








    # def git_pull():
    #     local("git pull")
    #
    #
    # def git_trunk_sha1():
    #     return subprocess.check_output(["git", "log", "-1", "--pretty=format:%H"])


    # def delete_file(p):
    #     if os.path.exists(p):
    #         os.remove(p)


    # def ensure_remote_dir_exists(p):
    #     if not files.exists(p):
    #         abort(red("dir '%s' doesn't exist on remote server" % p))
    #     print(green("dir '%s' exist on remote server" % p))


    # def ensure_remote_file_exists(p):
    #     if not files.exists(p):
    #         abort("dir '%s' doesn't exist on remote server" % p)


    # def add_dir_files(zip_file, dir):
    #     for (path, dirs, files) in os.walk(dir):
    #         for f in files:
    #             p = os.path.join(path, f)
    #             zip_file.write(p)


    # def zip_files(zip_path):
    #     zf = zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED)
    #     blacklist = ["importsumtrans.go"]
    #     files = [f for f in os.listdir(".") if f.endswith(".go") and not f in blacklist]
    #     for f in files: zf.write(f)
    #     zf.write("config.json")
    #     add_dir_files(zf, "scripts")
    #     add_dir_files(zf, "ext")
    #     add_dir_files(zf, "tmpl")
    #     add_dir_files(zf, "static")
    #     zf.close()


    # def check_config():
    #     if not os.path.exists("config.json"):
    #         abort("config.json doesn't exist locally")

    # def first_deploy():
    #     print(red("Beginning First Deploy:"))
    #
    #     if not files.exists(prod_root_dir):
    #         print(red("dir '%s' doesn't exist on remote server" % prod_root_dir))
    #         print(green("Create dir: %s" % prod_root_dir))
    #         run('mkdir -p %s' % prod_root_dir)
    #
    #     with cd(prod_root_dir):
    #         run('git clone git@bitbucket.org:py3pi/pin-im.com.git pinim')
    #         run('git checkout production')
    #         print(green("git clone: Done"))
    #
    #     print(green("First Deploy: Done"))


    # def deploy():
    #     # git_pull()
    #
    #     # git_ensure_clean()
    #
    #     print(red("Beginning Deploy:"))
    #
    #     ensure_remote_dir_exists(app_dir)
    #     with cd(env[app_dir]):
    #         run('git pull')
    #
    #     print(green("Deploy: Done"))

    # ensure_remote_file_exists('www/data/SumatraPDF/translations.dat')
    # sha1 = git_trunk_sha1()
    # code_path_remote = app_dir + '/' + sha1
    # if files.exists(code_path_remote):
    #     abort('code for revision %s already exists on the server' % sha1)
    # zip_path = sha1 + ".zip"
    # zip_files(zip_path)
    # zip_path_remote = app_dir + '/' + zip_path
    # put(zip_path, zip_path_remote)
    # delete_file(zip_path)
    # with cd(app_dir):
    #     run('unzip -q -x %s -d %s' % (zip_path, sha1))
    #     run('rm -f %s' % zip_path)
    # # make sure it can build
    # with cd(code_path_remote):
    #     run("./scripts/build.sh")
    #
    # curr_dir = app_dir + '/current'
    # if files.exists(curr_dir):
    #     # shut-down currently running instance
    #     sudo("/etc/init.d/apptranslator stop", pty=False)
    #     # rename old current as prev for easy rollback of bad deploy
    #     with cd(app_dir):
    #         run('rm -f prev')
    #         run('mv current prev')
    #
    # # make this version current
    # with cd(app_dir):
    #     run("ln -s %s current" % sha1)
    #
    # if not files.exists("/etc/init.d/apptranslator"):
    #     sudo("ln -s /home/apptranslator/www/app/current/scripts/apptranslator.initd /etc/init.d/apptranslator")
    #     # make sure it runs on startup
    #     sudo("update-rc.d apptranslator defaults")
    #
    # # start it
    # sudo("/etc/init.d/apptranslator start", pty=False)
    # run("ps aux | grep _app | grep -v grep")
    #
    # delete_old_deploys()

    # -----------------------------------------------------------------------------------------------------------

    #
    # def project_path(relative_path):
    #     return os.path.join(PROJECT_ROOT, relative_path)
    #
    #
    # class InitTask(Task):
    #     """
    #     Performs project initialization.
    #     Plan:
    #
    #         1. Setup local settings
    #            * Setup settings_local.py
    #            * Setup Makefile.def
    #         2. Setup database
    #            * Load sql dump
    #            * Run migrations
    #            * Load uploads to proper dir
    #
    #         If everything ok - run tests.
    #
    #     """
    #
    #     class InitTaskException(Exception):
    #         pass
    #
    #     class ValidationError(Exception):
    #         pass
    #
    #     #
    #     # Settings
    #     #
    #     capture_commands_output = False
    #     pip_be_quiet = False
    #     south_be_quiet = False
    #     tar_be_quiet = False
    #
    #     _trac_sql_dump_url = 'https://trac.42cc.co/agiloprojects/rewallse-favim/raw-attachment/wiki/WikiStart/favim2.sql'
    #     _trac_uploads_url  = 'https://trac.42cc.co/agiloprojects/rewallse-favim/raw-attachment/wiki/WikiStart/uploads.tar.gz'
    #     _uploads_target_dir = os.path.join(PROJECT_ROOT, 'favim/static_media/uploads')
    #     _preferred_db_engine = 'django.db.backends.mysql'
    #     _preferred_db_name = 'favim'
    #
    #     _settings_db_required = ['ENGINE', 'NAME']
    #     _settings_db_optional = ['HOST', 'PORT', 'USER', 'PASSWORD']
    #     _settings_db = _settings_db_required + _settings_db_optional
    #
    #     _messages = {
    #         'no_virtualenv_found'   : 'Looks like you are running this script outside '
    #                                   'of virtual environment, so packages will be installed globally.\n'
    #                                   'Do you wish to continue?',
    #         'makefile_def_exists'   : 'File `Makefile.def` already exists. '
    #                                   'Do you wish to overwrite?',
    #         'settings_local_exists' : 'File `settings_local.py` already exists. '
    #                                   'Do you with to overwrite?',
    #         'can_skip_prompts'      : 'You can skip these prompts and setup it manually',
    #         'ask_db_engine'         : 'Choose adapter for your database (default is preferred)',
    #         'ask_db_name'           : 'Choose database name',
    #         'ask_db_username'       : 'Type database user for favim',
    #         'ask_db_password'       : 'Type password for database user',
    #         'ask_db_hostname'       : 'Type database hostname (an empty string means localhost)',
    #         'ask_db_port'           : 'Type database port (an empty string means default port)',
    #         'ask_db_creation'       : 'Database is missing. Create new one?',
    #         'ask_yuicompressor_path': 'Type path to yui-compressor binary',
    #
    #         'no_sql_dump_found'     : 'No MySQL dump found. Download it from %s and put file to %s' \
    #                                    % (_trac_sql_dump_url,  INIT_DIR),
    #         'no_uploads_found'      : 'No uploads archive found. Download it from %s and put file to %s' \
    #                                    % (_trac_uploads_url, INIT_DIR),
    #
    #         'sqlite_cant_load_dump' : 'Using SQLite, skipping loading MySQL dump',
    #         'error_load_sql_dump'   : 'There was an error during sql dump load. '
    #                                   'Proceed anyway? (not recommended)',
    #         'error_migrations'      : 'There was an error during migrations run, can not continue',
    #         'error_uploads_extract' : 'There was an error during uploads archive extraction',
    #         'error_db_is_not_empty' : 'Database is not empty',
    #
    #         'launched_tests'        : 'Launched tests...'
    #
    #     }
    #
    #     #
    #     #  *  Inner functions  *
    #     #
    #
    #     @staticmethod
    #     def empty_string_validator(value):
    #         if value is '':
    #             raise InitTask.ValidationError('Empty string is not allowed')
    #         else:
    #             return value
    #
    #     def __init__(self):
    #         self._user_data = {}
    #
    #     def _is_running_inside_virtualenv(self):
    #         """
    #         Detects that script is running inside virtual environment.
    #
    #         http://stackoverflow.com/questions/1871549/python-determine-if-running-inside-virtualenv
    #         """
    #         return hasattr(sys, 'real_prefix')
    #
    #     def _is_using_sqlite(self):
    #         return 'sqlite' in self._user_data['ENGINE']
    #
    #     def _message_getter(func):
    #         if func.func_defaults:
    #             def wrapped(self, message_key=func.func_defaults[0], format_data=None, **kwargs):
    #                 message = self._messages.get(message_key, message_key)
    #                 message = message if format_data is None else message % format_data
    #                 return func(self, message, **kwargs)
    #         else:
    #             def wrapped(self, message_key, format_data=None, **kwargs):
    #                 message = self._messages.get(message_key, message_key)
    #                 message = message if format_data is None else message % format_data
    #                 return func(self, message, **kwargs)
    #
    #         return wrapped
    #
    #     @_message_getter
    #     def _warn(self, message):
    #         return warn(message)
    #
    #     @_message_getter
    #     def _info(self, message):
    #         return puts(message, show_prefix=True)
    #
    #     @_message_getter
    #     def _success(self, message='OK'):
    #         return puts(green(message), show_prefix=True)
    #
    #     def _local(self, message, capture=None):
    #         capture = self.capture_commands_output if capture is None else capture
    #         return fabric.api.local(message, capture=capture)
    #
    #     def _safe_local(self, command, pre=None, success=None, error=None,
    #                                    capture=False, raise_ex=True):
    #         self._info(pre) if pre is not None else None
    #         with fabric.api.settings(warn_only=True):
    #             result = self._local(command, capture=capture)
    #             if result.failed:
    #                 error_message = '%s: %s' % (error, result.stderr)
    #                 self._warn(error_message)
    #                 if raise_ex:
    #                     raise self.InitTaskException(error_message)
    #                 else:
    #                     return result
    #             else:
    #                 if success is not None:
    #                     self._success(success)
    #                 return result
    #
    #     @_message_getter
    #     def _ask_yes_no(self, question):
    #         return console.confirm(question)
    #
    #     @_message_getter
    #     def _ask_value(self, message, default=None, validate=None):
    #         return prompt(message, default=default, validate=validate)
    #
    #     @_message_getter
    #     def _abort(self, message='Aborted'):
    #         return abort(message)
    #
    #     def _load_settings_local(self):
    #         result = {}
    #         sys.path.append(PROJECT_ROOT)
    #         try:
    #             module = importlib.import_module('favim.settings.settings_local')
    #
    #             if hasattr(module, 'DATABASES') and 'default' in module.DATABASES:
    #                 db_settings = module.DATABASES['default']
    #                 for key in self._settings_db:
    #                     value = db_settings.get(key)
    #                     if value is not None:
    #                         result[key] = value
    #
    #             if hasattr(module, 'COMPRESS_YUI_BINARY'):
    #                 result['yuicompressor_path'] = module.COMPRESS_YUI_BINARY
    #
    #         finally:
    #             sys.path.pop()
    #             return result
    #
    #     def _migrate_cmd(self, *args):
    #         cmd = 'python ./manage.py migrate'
    #         cmd += ' -v 0' if self.south_be_quiet else ''
    #         cmd += ' %s' % ' '.join(args)
    #         return cmd
    #
    #     def _mysql_cmd(self, sql=None, with_database=True):
    #         data = self._user_data
    #         if with_database:
    #             database_arg = ' --database=%(NAME)s'
    #         else:
    #             database_arg = ''
    #         command = (
    #             'mysql ' +
    #             database_arg +
    #             ('' if data.get('HOST') is None else ' --host=%(HOST)s') +
    #             ('' if data.get('PORT') is None else ' --port=%(PORT)s') +
    #             ('' if data.get('USER') is None else ' --user=%(USER)s') +
    #             ('' if data.get('PASSWORD') is None else ' --password=%(PASSWORD)s')
    #         )
    #         return (command + ' --execute="%s"' % sql) if sql else command
    #
    #     #
    #     #  *  Main algorithm  *
    #     #
    #
    #     def run(self):
    #         try:
    #             self.install_requirements()
    #             self.setup_local_settings()
    #             self.init_database()
    #         except InitTask.InitTaskException as e:
    #             message = self._messages.get(e.message, e.message)
    #             self._abort(message)
    #         else:
    #             self._success('Initialized project successfully.')
    #             if self._ask_yes_no('Should i run tests ?'):
    #                 self.run_tests()
    #
    #     def install_requirements(self):
    #         self._info('Installing requirements ...')
    #         if not self._is_running_inside_virtualenv():
    #             confirmed = self._ask_yes_no(self._messages['no_virtualenv_found'])
    #
    #             if confirmed is False:
    #                 self._abort()
    #
    #         self._info('Installing project requirements ...')
    #         self._local('pip install %s -r requirements.txt' %
    #                     ('-q' if self.pip_be_quiet else ''))
    #         self._success()
    #         return True
    #
    #     def setup_local_settings(self):
    #         return all((self._setup_makefile(),
    #                     self._setup_settings_local_py()))
    #
    #     def _setup_makefile(self):
    #         self._info('Initializing Makefile.def ...')
    #         subs = {
    #             'source': project_path('Makefile.def.dev'),
    #             'target': project_path('Makefile.def'),
    #         }
    #         if os.path.exists(subs['target']):
    #             confirmed = self._ask_yes_no(self._messages['makefile_def_exists'])
    #
    #             if confirmed is False:
    #                 return True
    #
    #         self._local('cp %(source)s %(target)s' % subs)
    #         self._info('Rewrited %s' % subs['target'])
    #         self._success()
    #         return True
    #
    #     def _setup_settings_local_py(self):
    #         self._info('Initializing settings_local.py ...')
    #         subs = {
    #             'source': project_path('favim/settings/settings_local.py.def'),
    #             'target': project_path('favim/settings/settings_local.py'),
    #         }
    #         if os.path.exists(subs['target']):
    #             confirmed = self._ask_yes_no(self._messages['settings_local_exists'])
    #             if confirmed is False:
    #                 settings = self._load_settings_local()
    #                 self._user_data.update(settings)
    #                 return True
    #
    #         self._local('cp %(source)s %(target)s' % subs)
    #
    #         with open(subs['target'], 'r+') as f:
    #             self._info('can_skip_prompts')
    #             self._user_data = {
    #                 'ENGINE' : self._ask_value('ask_db_engine',
    #                                             default=self._preferred_db_engine,
    #                                             validate='\S+'),
    #                 'NAME'   : self._ask_value('ask_db_name',
    #                                             default=self._preferred_db_name,
    #                                             validate=self.empty_string_validator),
    #             }
    #
    #             if self._is_using_sqlite():
    #                 # Not used with sqlite
    #                 for key in self._settings_db_optional:
    #                     self._user_data[key] = ''
    #             else:
    #                 self._user_data.update({
    #                     'USER'    : self._ask_value('ask_db_username', default=''),
    #                     'PASSWORD': self._ask_value('ask_db_password', default=''),
    #                     'HOST'    : self._ask_value('ask_db_hostname', default=''),
    #                     'PORT'    : self._ask_value('ask_db_port',     default=''),
    #                 })
    #
    #             self._user_data['yuicompressor_path'] = self._ask_value('ask_yuicompressor_path', default='')
    #             new_settings = f.read() % self._user_data
    #             f.seek(0)
    #             f.write(new_settings)
    #             f.truncate()
    #             self._info('Rewrited %s' % subs['target'])
    #         self._success()
    #         return True
    #
    #     def init_database(self):
    #         return all((self._load_dump(),
    #                     self._run_migrations(),
    #                     self._init_uploads()))
    #
    #     def _load_dump(self):
    #         self._info('Initializing database ...')
    #
    #         if self._is_using_sqlite():
    #             self._warn('sqlite_cant_load_dump')
    #             return False
    #         else:
    #             self._info('Checking database for tables ...')
    #             number_of_tables = self._get_number_of_tables()
    #             if number_of_tables > 0:
    #                 message = ('There are %(tables)s tables in database %(NAME)s. '
    #                            'Drop and create new one?')
    #                 message = message % dict(self._user_data, tables=number_of_tables)
    #                 confirm_drop = self._ask_yes_no(message)
    #                 if confirm_drop:
    #                     self._drop_database()
    #                     self._create_database()
    #                 else:
    #                     raise self.InitTaskException('error_db_is_not_empty')
    #
    #             data = self._user_data
    #             files = {
    #                 'sql_dump': os.path.join(INIT_DIR, 'favim2.sql'),
    #             }
    #             if not os.path.exists(files['sql_dump']):
    #                 self._warn('no_sql_dump_found')
    #                 raise self.InitTaskException('no_sql_dump_found')
    #             else:
    #                 cmd = self._mysql_cmd() + ' < %(sql_dump)s'
    #                 self._safe_local(cmd % dict(self._user_data, **files),
    #                                  pre='Loading sql dump ...', error='error_load_sql_dump')
    #             return True
    #
    #     def _get_number_of_tables(self):
    #         sql = ("SELECT COUNT(*) "
    #                "FROM information_schema.tables "
    #                "WHERE table_schema='%(NAME)s'")
    #         # Get result in HTML (-H) without column names (-N)
    #         cmd = self._mysql_cmd(sql) + ' -N -H'
    #         result = self._safe_local(cmd % dict(self._user_data),
    #                                   pre='Getting number of tables ...', error='MySQL error',
    #                                   capture=True, raise_ex=False)
    #
    #         if 'Unknown database' in result.stderr:
    #             create_confirmed = self._ask_yes_no('ask_db_creation')
    #             if create_confirmed:
    #                 self._create_database()
    #                 return 0
    #         else:
    #             match = re.search(r'<TD>(?P<num>\d+)</TD>', result)
    #             if match:
    #                 return int(match.group('num'))
    #             else:
    #                 raise self.InitTaskException('MySQL returned wrong output: %s' % result)
    #
    #     def _drop_database(self):
    #         sql = "DROP DATABASE %(NAME)s" % self._user_data
    #         cmd = self._mysql_cmd(sql)
    #         result = self._safe_local(cmd % self._user_data,
    #                                   pre='Dropping database %(NAME)s' % self._user_data,
    #                                   error='MySQL error', success='Dropped database',
    #                                   capture=True)
    #         return True
    #
    #     def _create_database(self):
    #         sql = "CREATE SCHEMA %(NAME)s" % self._user_data
    #         cmd = self._mysql_cmd(sql, with_database=False)
    #         result = self._safe_local(cmd % self._user_data,
    #                                   pre='Creating new one',
    #                                   error='MySQL error', success='Created database',
    #                                   capture=True)
    #         return True
    #
    #     def _run_migrations(self):
    #         """
    #         Ignore migration #30 if `images` app, it depends on Redis and is useless
    #         in this case.
    #         """
    #         cmd = self._migrate_cmd('images', '0030', '--fake')
    #         self._safe_local(cmd, pre='Running migrations ...', error='error_migrations')
    #         # Other migrations
    #         cmd = self._migrate_cmd('')
    #         self._safe_local(cmd, error='error_migrations', success='Migrations - OK')
    #         return True
    #
    #     def _init_uploads(self):
    #         """
    #         Extracts uploads archive into proper dir.
    #         """
    #         files = {
    #             'uploads': os.path.join(INIT_DIR, 'uploads.tar.gz')
    #         }
    #         if not os.path.exists(files['uploads']):
    #             self._warn('no_uploads_found')
    #             self._abort()
    #         else:
    #             cmd = 'mkdir -p %s' % self._uploads_target_dir
    #             cmd += ' && tar'
    #             cmd += ' -C %s' % self._uploads_target_dir
    #             cmd += ' -xz%sf %s' % ('' if self.tar_be_quiet else 'v', files['uploads'])
    #             self._safe_local(cmd, pre='Extracting uploads ...', error='error_uploads_extract')
    #             return True
    #
    #     def run_tests(self):
    #         self._info('launched_tests')
    #         self._local('make test')
    #         return True
    #
    #
    # init = InitTask()