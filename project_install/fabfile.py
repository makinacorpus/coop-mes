# -*- coding: utf-8 -*-
from fabric.api import env, local, run, sudo, cd, hide, show, settings, prefix, prompt
from fabric.contrib.console import confirm
from fabric.colors import red, green, yellow
from fabric.decorators import task
from fabric.contrib.files import append, contains, exists, sed, upload_template
from fabtools import require
import fabtools

try:
    import config_prod as config
except ImportError:
    import config_dev as config


#Paramétres par défaut
env.domain = config.PROJECT_NAME
env.projet = config.ALIAS_NAME
env.alias = config.DOMAIN_NAME

env.host_string = config.HOST_USER + "@" + config.HOST_NAME
env.pg_user = config.PG_USER
env.pg_pass = config.PG_PASSWORD

env.locale = config.LOCALE


env.base_install = config.PROJECT_HOME

# Paramétres Déploiement
env.websrv = 1



def pretty_apt(pkglist):
    for pkg in (pkglist):
        require.deb.package(pkg)
        print(green(u'Paquet Debian "' + unicode(pkg) + u'" : installé.'))


def pretty_pip(pkglist):
    for pkg in (pkglist):
        fabtools.python.install(pkg)
        print(green(u'Module Python "' + unicode(pkg) + u'" : installé.'))


def local_vm():
    '''First command to use for a Vagrant VM'''
    # change from the default user to 'vagrant'
    env.user = 'vagrant'
    # connect to the port-forwarded ssh
    env.hosts = ['127.0.0.1:2222']
    # use vagrant ssh key
    #with cd(env.vm_path):
    result = local('vagrant ssh_config | grep IdentityFile', capture=True)
    env.key_filename = result.split()[1]

    # si le partage de dossier ne marche pas bien encore ensuite :
    #mise à jour guest additions
    #require.deb.packages(['dkms','linux-headers-2.6.38-8-generic','linux-headers-generic'])
    # sudo('/etc/init.d/vboxadd setup') # puis "vagrant reload"

def remote():
    '''First command to use for a SSH remote host'''
    env.hosts = [prompt('Alias SSH:', default=alias, key='alias')]

    def _annotate_hosts_with_ssh_config_info():
        from os.path import expanduser
        from paramiko.config import SSHConfig

        def hostinfo(host, config):
            hive = config.lookup(host)
            if 'hostname' in hive:
                host = hive['hostname']
            if 'user' in hive:
                host = '%s@%s' % (hive['user'], host)
            if 'port' in hive:
                host = '%s:%s' % (host, hive['port'])
            return host
        try:
            config_file = file(expanduser('~/.ssh/config'))
        except IOError:
            pass
        else:
            config = SSHConfig()
            config.parse(config_file)
            keys = [config.lookup(host).get('identityfile', None)
                for host in env.hosts]
            env.key_filename = [expanduser(key) for key in keys if key is not None]
            env.hosts = [hostinfo(host, config) for host in env.hosts]
    _annotate_hosts_with_ssh_config_info()
    #sudo apt-get install nano
    #update-alternatives  --config editor
    #visudo
    #Dans le fichier, rendez vous à la ligne %admin ALL=(ALL) ALL.
    #Remplacez %admin ALL=(ALL) ALL par %admin ALL=(ALL) NOPASSWD: ALL



#prompt('Config : (1)Apache seul ou (2)Apache+Nginx :',key='websrv',validate=int,default=env.websrv)



def pip_bootstrap():
    with cd("/tmp"):
        run("curl --silent -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py")
        sudo("python get-pip.py")


@task
def server_setup():
    '''Installation serveur pour Ubuntu >= 10.10'''
    with settings(show('user'), hide('warnings', 'running', 'stdout', 'stderr')):

        sudo('apt-get -y install aptitude')  # demande un input
        print(yellow('Mise à jour de l’index APT...'))
        fabtools.deb.update_index()  # apt-get quiet update
        print(yellow('Mise à jour des paquets debian installés...'))
        fabtools.deb.upgrade()
        # paquets communs à tous les serveurs Django+geodjango
        print(yellow('Installation des paquets de base...'))
        pretty_apt(['git-core', 'mercurial', 'gcc', 'curl', 'build-essential',
                    'libfreetype6', 'libfreetype6-dev', 'liblcms1-dev', 'libpng12-dev',
                    'libjpeg8-dev', 'python-imaging', 'supervisor',
                    'python-setuptools', 'nano', 'python-dev', 'swig',
                    'memcached', 'python-memcache'])

        # pip special case
        if not fabtools.python.is_pip_installed():
            fabtools.python.install_pip()
            print(green('pip : installé.'))

        virtualenv_setup()
        #config apache
        apache_setup()

        postgresql()


def postgresql():
    '''PostgreSQL 9.1 + PostGIS 1.5'''
    with settings(show('user'), hide('warnings', 'running', 'stdout', 'stderr')):
        #if 'pgpass' not in env.keys():
        #    prompt('Passe PostgreSQL :', default=pgpass, key='pgpass')
        print(yellow('Configuration PostgreSQL+PostGIS...'))
        pretty_apt(['postgresql', 'binutils', 'gdal-bin', 'libproj-dev', 'postgresql-9.1-postgis',
                    'postgresql-server-dev-9.1', 'python-psycopg2', 'libgeoip1'])
        # print(yellow('Upgrading all packages...'))
        # fabtools.deb.upgrade()
        # création d'un utilisateur postgresql avec le meme nom d'utilisateur
        if not fabtools.postgres.user_exists(env.user):
            fabtools.postgres.create_user(env.user, env.pg_pass)
            sudo('''psql -c "ALTER ROLE %(user)s CREATEDB;"''' % env, user='postgres')
            sudo('''psql -c "ALTER USER %(user)s with SUPERUSER;"''' % env, user='postgres')
            print(green('Création d’un superuser "%(user)s" PostgreSQL.' % env))
        if not exists('.pgpass'):
            run('echo "*:*:*:%(user)s:%(pg_pass)s" >> .pgpass' % env)
            sudo('chmod 0600 .pgpass')
            print(green('Création du fichier .pgpass.'))
        run('curl https://docs.djangoproject.com/en/dev/_downloads/create_template_postgis-debian.sh -o postgis.sh')
        run('chmod +x postgis.sh')
        run('./postgis.sh')
        #postgresql_net_access()
        require.postgres.server()  # start server



@task
def coop_setup():

    """Creation d'un nouveau projet django-coop"""
    coop_set_project()
    # dependencies() # TODO : parse requirements.txt to test each package
    apache_vhost()
    django_wsgi()
    create_pg_db()

    sudo('apachectl restart')


def coop_set_project():
    '''Créer un projet django dans son virtualenv'''
    with settings(show('user'), hide('warnings', 'running', 'stdout', 'stderr')):
        if not exists('/home/%(user)s/.virtualenvs/%(projet)s' % env):
            # if confirm('Pas de virtualenv "%(projet)s", faut-il le créer ?' % env, default=False):
            run('mkvirtualenv --no-site-packages %(projet)s' % env)
            run('source .bash_profile')

            with cd('%(base_install)s' % env):
                with prefix('workon %(projet)s' % env):
                    run('chmod +x manage.py')
                    run('mkdir media')
                    run('chmod -R g+rw media')

        else:
            #with prefix('workon %(projet)s' % env):
            #run('pip install --timeout=240 -r %(base_install)s/requirements.txt' % env)
            print(yellow('Projet Django-coop nommé "%(projet)s" : déjà installé.' % env))
            # TODO proposer de réinstaller

        with prefix('workon %(projet)s' % env):
            print(yellow('Récupération des dépendances python du projet coop-mes'))
            run('pip install --timeout=1024 --use-mirrors -r %(base_install)s/requirements.txt' % env)
            print(green('Récupération des dépendances python du projet coop-mes'))
             
        # Création du répertoire de logs   
        if not exists('%(base_install)s/logs' % env):
            run('mkdir %(base_install)s/logs' % env)


@task
def initialize_django_env():
    '''Initialisation de l'environnement django'''
    
    # Initialisation PostgreSQL
    if not fabtools.postgres.user_exists(env.pg_user):
        fabtools.postgres.create_user(env.pg_user, env.pg_pass)

    if not fabtools.postgres.database_exists(env.projet):
        fabtools.postgres.create_database(env.projet, env.pg_user)
    
    sudo('''psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d %(projet)s''' % env, user='postgres')
    sudo('''psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d %(projet)s''' % env, user='postgres')
    sudo('''psql -c "ALTER TABLE geometry_columns OWNER TO %(pg_user)s;" -d %(projet)s''' % env, user='postgres')
    sudo('''psql -c "ALTER TABLE spatial_ref_sys OWNER TO %(pg_user)s;" -d %(projet)s''' % env, user='postgres')

    with cd('%(base_install)s' % env):
        
        with prefix('workon %(projet)s' % env):
            
            # Installation Django
            run('python ./manage.py collectstatic --noinput')
            run('python ./manage.py syncdb --all --noinput')
            run('python ./manage.py migrate --fake')
            run('python ./manage.py loaddata coop_local/fixtures/{areatypes,django_site,exchange_methods,linkproperty,location_categories,roles,uriredirect,user,legalstatus,organizationcategory,organizationcategoryiae,agreementiae}.json')


@task
def initialize_geo_django():
    '''Initialisation de l'environnement django geo'''
 
    FILE_NAME = 'GEOFLA_1-1_SHP_LAMB93_FR-ED111.tar.gz'
    GEO_FILE = 'http://professionnels.ign.fr/sites/default/files/' + FILE_NAME 

    with prefix('workon %(projet)s' % env):
        print(green('Installation de geodjangofla via git'))
        run('pip install git+git://github.com/quinode/geo-django-fla.git')

        with cd('%(base_install)s' % env):
            print(green('Migration de geodjangofla'))
            run('python ./manage.py migrate geodjangofla')

            print(green("Récupération des données IGN à l'adresse"))
            run('wget -P /tmp %s' % GEO_FILE)

            with cd('/tmp'):
                run('tar xfz %s' % FILE_NAME)

            run('python ./manage.py importgeofla /tmp/%s' % FILE_NAME.split('.')[0])
            run('python ./manage.py importfromgeofla 04 05 06 13 83 84')
            run('python ./manage.py create_epci 04 05 06 13 83 84')
            

def apache_vhost():
    
    '''Configuration Vhost apache'''
    if(env.websrv == 1):
        vhost_context = {
            'user': env.user,
            'domain': env.domain,
            'projet': env.projet,
	    'base_install' : env.base_install,
        }
        print 'workon %(projet)s' % env
        run('workon %(projet)s' % env)
        
        #import coop
        #coop_path = coop.__path__[0]
        import os.path
        coop_path = os.path.split(__file__)[0]

        upload_template('%s/fab_templates/vhost.txt' % coop_path,
                        '/etc/apache2/sites-available/%(domain)s' % env,
                        context=vhost_context, use_sudo=True)
        with cd('/etc/apache2/'):
            with settings(hide('warnings', 'running', 'stdout', 'stderr')):
                if exists('sites-enabled/%(domain)s' % env):
                    sudo('rm sites-enabled/%(domain)s' % env)
            sudo('ln -s `pwd`/sites-available/%(domain)s sites-enabled/%(domain)s' % env)
            print(green('VirtualHost Apache pour %(domain)s : OK.' % env))
    elif(env.websrv == 2):
        print(red('Script de déploiement pas encore écrit !!!'))  # TODO
    #sudo('apachectl restart')


def django_wsgi():
    '''paramétrage WSGI/Apache'''
    print 'django_wsgi'

    #if not exists('/home/%(user)s/projects/%(projet)s/coop_local/wsgi.py' % env):
        
    sp_path = '<path-unknown>'
    with prefix('workon %(projet)s' % env):
        sp_path = run('cdsitepackages ; pwd')
        import os.path
        coop_path = os.path.split(__file__)[0]

    wsgi_context = {
        'site-packages': sp_path,
        'user': env.user,
        'projet': env.projet,
        'base_install': env.base_install,
    }

    upload_template('%s/fab_templates/wsgi.txt' % coop_path,
                    '%(base_install)s/coop_local/wsgi.py' % env,
                    context=wsgi_context, use_sudo=True)

    print(green('Script WSGI pour %(projet)s créé.' % env))
    #else:
    #    print(yellow('Script WSGI pour %(projet)s déjà existant.' % env))



def apache_nginx():
    '''Apache + mod_wsgi pour Django avec Nginx en proxy'''
    require.deb.packages(['apache2', 'libapache2-mod-wsgi'])
    with cd('/etc/apache2/'):
        if not contains('ports.conf', '127.0.0.1', use_sudo=True):
            sed('ports.conf', 'NameVirtualHost \\*:80', 'NameVirtualHost 127.0.0.1:80', use_sudo=True)
            sed('ports.conf', 'Listen 80', 'Listen 127.0.0.1:80', use_sudo=True)
            print(green('/etc/apache2/ports.conf updated'))
    with cd('/etc/apache2/'):
        if not contains('apache2.conf', 'ServerName localhost', use_sudo=True):
            sudo("echo 'ServerName localhost'|cat - apache2.conf > /tmp/out && mv /tmp/out apache2.conf")
            sudo("sed -i 's/KeepAlive On/KeepAlive Off/g' apache2.conf")
            print(green('/etc/apache2/apache2.conf updated'))
    #sudo("apache2ctl graceful") #plante de toute façon sans virtualhosts
    pretty_apt(['nginx'])
    with cd('/etc/nginx/'):
        if not contains('nginx.conf', 'worker_processes 2;', use_sudo=True):
            sudo("sed -i 's/worker_processes 4;/worker_processes 2;/g' nginx.conf")
            print(green('/etc/nginx/nginx.conf updated'))
    #to be continued...proxy.conf, vhosts...


def apache_setup():
    '''Config générale Apache + mod_wsgi sans media proxy'''
    print(yellow('Configuration d’Apache...'))
    pretty_apt(['apache2', 'libapache2-mod-wsgi'])
    #virer le site par défaut
    with cd('/etc/apache2/'):
        if not contains('apache2.conf', 'ServerName localhost', use_sudo=True):
            if not contains('apache2.conf', 'ServerName %(domain)s' % env, use_sudo=True):
                sudo("echo 'ServerName %(domain)s'|cat - apache2.conf > /tmp/out && mv /tmp/out apache2.conf" % env)
    with cd('/etc/apache2/sites-enabled/'):
        if exists('000-default'):
            sudo('rm 000-default')
            print(green('Site par défaut d’Apache supprimé'))



def create_pg_db():
    '''Créer une base de données postgres au nom du projet'''
    with settings(show('user')):  # , hide('warnings', 'running', 'stdout', 'stderr')):
        require.postgres.database(env.projet, env.user, template='template_postgis', locale=env.locale)
        print(green('Création base de données PostgreSQL nommée "%(projet)s" : OK.' % env))


def virtualenv_setup():
    '''setup virtualenv'''
    print(yellow('Environnement virtuel et dossier "projects"...'))
    require.python.package('virtualenv', use_sudo=True)
    require.python.package('virtualenvwrapper', use_sudo=True)
    #require.python.package('virtualenvwrapper.django',use_sudo=True)
    print(green('Virtualenv installé.'))
    if not 'www-data' in run('echo | groups %(user)s' % env):
        sudo('usermod -a -G www-data %(user)s' % env)
        print(green('Utilisateur %(user)s ajouté au groupe "www-data".' % env))
    if not exists('projects/'):
        run('mkdir projects .python-eggs .virtualenvs')
        sudo('chown %(user)s:www-data .python-eggs' % env)
        sudo('chgrp -R www-data projects/')
        sudo('chmod -R 2750 projects/')
        print(green('Dossier "projects" créé.'))
    # sur .bashrc et pas .bashrc
    # + fix pour https://bitbucket.org/dhellmann/virtualenvwrapper/issue/62/hooklog-permissions
    run('touch .bash_login')
    if not contains('.bash_login', '. .bashrc'):
        append('.bash_login', 'if [ $USER == %(user)s ]; then' % env)
    if not contains('.bashrc', 'WORKON_HOME'):
        append('.bashrc', 'if [ $USER == %(user)s ]; then' % env)
        append('.bashrc', '    export WORKON_HOME=$HOME/.virtualenvs')
        append('.bashrc', '    export PROJECT_HOME=$HOME/projects')
        append('.bashrc', '    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python')
        append('.bashrc', '    export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv')
        append('.bashrc', '    source /usr/local/bin/virtualenvwrapper.sh')
        append('.bashrc', 'fi')
        append('.bash_profile', 'if [ $USER == %(user)s ]; then' % env)
        append('.bash_profile', '    export WORKON_HOME=$HOME/.virtualenvs')
        append('.bash_profile', '    export PROJECT_HOME=$HOME/projects')
        append('.bash_profile', '    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python')
        append('.bash_profile', '    export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv')
        append('.bash_profile', '    source /usr/local/bin/virtualenvwrapper.sh')
        append('.bash_profile', 'fi')
        run('source .bashrc')
        print(green('Virtualenv et Virtualenvwrapper configurés.'))
    # stop warning from bitbucket https://bitbucket.org/site/master/issue/2780/getting-warning-while-using-https-and-ssh
    if not contains('.hgrc', 'bitbucket.org'):
        append('.hgrc', '[hostfingerprints]')
        append('.hgrc', 'bitbucket.org = 24:9c:45:8b:9c:aa:ba:55:4e:01:6d:58:ff:e4:28:7d:2a:14:ae:3b')


def dependencies():
    '''Vérification des modules nécessaires au projet'''
    with settings(show('user'), hide('warnings', 'running', 'stdout', 'stderr')):
        with cd('%(base_install)s' % env):
            if exists('requirements.txt'):
                print(yellow('Installation des dépendances du projet...'))
                with prefix('workon %(projet)s' % env):
                    with settings(show('running', 'stdout', 'stderr')):
                        run('pip install -r requirements.txt')
            else:
                print(red('Aucun fichier "requirements.txt" trouvé.'))
        with prefix('workon %(projet)s' % env):
            with cd('%(base_install)s' % env):
                run('./manage.py collectstatic --noinput')


def set_locale():
    '''Règlage des locale de l'OS'''
    print "set_locale"
    locale = run("echo $LANG")
    print "run"
    if(locale != env.locale):
        print "different"
        sudo('locale-gen ' + env.locale)
        sudo('/usr/sbin/update-locale LANG=' + env.locale)
        print(green('Locale mise à jour.'))


