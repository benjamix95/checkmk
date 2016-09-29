#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2014             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# tails. You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

import os, pprint, glob
import i18n
from lib import *
import cmk.paths

# FIXME: Make clear whether or not user related values should be part
# of the "config" module. Maybe move to dedicated module (userdb?). Then
# move all user related stuff there. e.g. html.user should also be moved
# there.

#   .--Declarations--------------------------------------------------------.
#   |       ____            _                 _   _                        |
#   |      |  _ \  ___  ___| | __ _ _ __ __ _| |_(_) ___  _ __  ___        |
#   |      | | | |/ _ \/ __| |/ _` | '__/ _` | __| |/ _ \| '_ \/ __|       |
#   |      | |_| |  __/ (__| | (_| | | | (_| | |_| | (_) | | | \__ \       |
#   |      |____/ \___|\___|_|\__,_|_|  \__,_|\__|_|\___/|_| |_|___/       |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  Declarations of global variables and constants                      |
#   '----------------------------------------------------------------------'


user = None
user_id = None
user_confdir = None
builtin_role_ids = [ "user", "admin", "guest" ] # hard coded in various permissions
user_role_ids = []

# Base directory of dynamic configuration
config_dir = cmk.paths.var_dir + "/web"

# Detect modification in configuration
modification_timestamps = []

# Global table of available permissions. Plugins may add their own
# permissions by calling declare_permission()
permissions_by_name              = {}
permissions_by_order             = []
permission_sections              = {}
permission_declaration_functions = []

# Constants for BI
ALL_HOSTS = '(.*)'
HOST_STATE = ('__HOST_STATE__',)
HIDDEN = ('__HIDDEN__',)
class FOREACH_HOST: pass
class FOREACH_CHILD: pass
class FOREACH_CHILD_WITH: pass
class FOREACH_PARENT: pass
class FOREACH_SERVICE: pass
class REMAINING: pass
class DISABLED: pass
class HARD_STATES: pass
class DT_AGGR_WARN: pass

# Has to be declared here once since the functions can be assigned in
# bi.py and also in multisite.mk. "Double" declarations are no problem
# here since this is a dict (List objects have problems with duplicate
# definitions).
aggregation_functions = {}


#.
#   .--Functions-----------------------------------------------------------.
#   |             _____                 _   _                              |
#   |            |  ___|   _ _ __   ___| |_(_) ___  _ __  ___              |
#   |            | |_ | | | | '_ \ / __| __| |/ _ \| '_ \/ __|             |
#   |            |  _|| |_| | | | | (__| |_| | (_) | | | \__ \             |
#   |            |_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/             |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  Helper functions for config parsing, login, etc.                    |
#   '----------------------------------------------------------------------'

# Read in a multisite.d/*.mk file
def include(filename):
    if not filename.startswith("/"):
        filename = cmk.paths.default_config_dir + "/" + filename

    # Config file is obligatory. An empty example is installed
    # during setup.sh. Better signal an error then simply ignore
    # Absence.
    try:
        lm = os.stat(filename).st_mtime
        execfile(filename, globals(), globals())
        modification_timestamps.append(lm)
    except Exception, e:
        global user_id
        user_id = "nobody"
        raise MKConfigError(_("Cannot read configuration file %s: %s:") % (filename, e))

# Load multisite.mk and all files in multisite.d/. This will happen
# for *each* HTTP request.
# FIXME: Optimize this to cache the config etc. until either the config files or plugins
# have changed. We could make this being cached for multiple requests just like the
# plugins of other modules. This may save significant time in case of small requests like
# the graph ajax page or similar.
def load_config():
    global modification_timestamps, sites
    modification_timestamps = []

    # Set default values for all user-changable configuration settings
    load_plugins(True)

    # First load main file
    include("multisite.mk")

    # Load also recursively all files below multisite.d
    conf_dir = cmk.paths.default_config_dir + "/multisite.d"
    filelist = []
    if os.path.isdir(conf_dir):
        for root, dirs, files in os.walk(conf_dir):
            for filename in files:
                if filename.endswith(".mk"):
                    filelist.append(root + "/" + filename)

    filelist.sort()
    for p in filelist:
        include(p)

    # Prevent problem when user has deleted all sites from his configuration
    # and sites is {}. We assume a default single site configuration in
    # that case.
    if not sites:
        sites = default_single_site_configuration()


def reporting_available():
    try:
        # Check the existance of one arbitrary config variable from the
        # reporting module
        reporting_filename
        return True
    except:
        return False


#.
#   .--Permissions---------------------------------------------------------.
#   |        ____                     _         _                          |
#   |       |  _ \ ___ _ __ _ __ ___ (_)___ ___(_) ___  _ __  ___          |
#   |       | |_) / _ \ '__| '_ ` _ \| / __/ __| |/ _ \| '_ \/ __|         |
#   |       |  __/  __/ |  | | | | | | \__ \__ \ | (_) | | | \__ \         |
#   |       |_|   \___|_|  |_| |_| |_|_|___/___/_|\___/|_| |_|___/         |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  Handling of users, permissions and roles                            |
#   '----------------------------------------------------------------------'

def declare_permission(name, title, description, defaults):
    perm = { "name" : name, "title" : title, "description" : description, "defaults" : defaults }

    # Detect if this permission has already been declared before
    # The dict value is replaced automatically but the list value
    # to be replaced -> INPLACE!
    # FIXME: permissions_by_order is bad. Remove this and add a "sort"
    # attribute to the permissions_by_name dict. This would be much cleaner.
    replaced = False
    for index, test_perm in enumerate(permissions_by_order):
        if test_perm['name'] == perm['name']:
            permissions_by_order[index] = perm
            replaced = True

    if not replaced:
        permissions_by_order.append(perm)

    permissions_by_name[name] = perm

def declare_permission_section(name, title, prio = 0, do_sort = False):
    # Prio can be a number which is used for sorting. Higher numbers will
    # be listed first, e.g. in the edit dialogs
    permission_sections[name] = (prio, title, do_sort)

# Some module have a non-fixed list of permissions. For example for
# each user defined view there is also a permission. This list is
# not known at the time of the loading of the module - though. For
# that purpose module can register functions. These functions should
# just call declare_permission(). They are being called in the correct
# situations.
def declare_dynamic_permissions(func):
    permission_declaration_functions.append(func)

# This function needs to be called by all code that needs access
# to possible dynamic permissions
def load_dynamic_permissions():
    for func in permission_declaration_functions:
        func()

# Compute permissions for HTTP user and set in
# global variables. Also store user.
def login(u):
    global user_id
    user_id = u

    # Determine the roles of the user. If the user is listed in
    # users, admin_users or guest_users in multisite.mk then we
    # give him the according roles. If the user has an explicit
    # profile in multisite_users (e.g. due to WATO), we rather
    # use that profile. Remaining (unknown) users get the default_user_role.
    # That can be set to None -> User has no permissions at all.
    global user_role_ids
    user_role_ids = roles_of_user(user_id)

    # Get base roles (admin/user/guest)
    global user_baserole_ids
    user_baserole_ids = base_roles_of(user_role_ids)

    # Get best base roles and use as "the" role of the user
    global user_baserole_id
    if "admin" in user_baserole_ids:
        user_baserole_id = "admin"
    elif "user" in user_baserole_ids:
        user_baserole_id = "user"
    else:
        user_baserole_id = "guest"

    # Prepare user object
    global user, user_alias, user_email
    if u in multisite_users:
        user = multisite_users[u]
        user_alias = user.get("alias", user_id)
        user_email = user.get("email", user_id)
    else:
        user = { "roles" : user_role_ids }
        user_alias = user_id
        user_email = user_id

    # Prepare cache of already computed permissions
    global user_permissions
    user_permissions = {}

    # Make sure, admin can restore permissions in any case!
    if user_id in admin_users:
        user_permissions["general.use"] = True # use Multisite
        user_permissions["wato.use"]    = True # enter WATO
        user_permissions["wato.edit"]   = True # make changes in WATO...
        user_permissions["wato.users"]  = True # ... with access to user management

    # Prepare users' own configuration directory
    set_user_confdir(user_id)

    # load current on/off-switching states of sites
    read_site_config()

# Login a user that has all permissions. This is needed for making
# Livestatus queries from unauthentiated page handlers
def login_super_user():
    global user_id
    user_id = None

    global user_role_ids
    user_role_ids = [ "admin" ]

    global user_baserole_ids
    user_baserole_ids = [ "admin" ]

    global user_baserole_id
    user_baserole_id = "admin"

    # Prepare user object
    global user, user_alias, user_email
    user = { "roles" : "admin" }
    user_alias = "Superuser for unauthenticated pages"
    user_email = "admin"

    # Prepare cache of already computed permissions
    global user_permissions
    user_permissions = {}

    # All sites are enabled
    global user_siteconf
    user_siteconf = {}

def set_user_confdir(user_id):
    global user_confdir
    user_confdir = config_dir + "/" + user_id.encode("utf-8")
    make_nagios_directory(user_confdir)

def get_language(default = None):
    if user and "language" in user:
        return user["language"]
    elif default == None:
        return default_language
    else:
        return default

def hide_language(lang):
    return lang in hide_languages

def roles_of_user(user):
    if user in multisite_users:
        return existing_role_ids(multisite_users[user]["roles"])
    elif user in admin_users:
        return [ "admin" ]
    elif user in guest_users:
        return [ "guest" ]
    elif users != None and user in users:
        return [ "user" ]
    elif os.path.exists(config_dir + "/" + user.encode("utf-8") + "/automation.secret"):
        return [ "guest" ] # unknown user with automation account
    elif 'roles' in default_user_profile:
        return existing_role_ids(default_user_profile['roles'])
    elif default_user_role:
        return existing_role_ids([ default_user_role ])
    else:
        return []


def existing_role_ids(role_ids):
    return [
        role_id for role_id in role_ids
        if role_id in roles
    ]


def alias_of_user(user):
    if user in multisite_users:
        return multisite_users[user].get("alias", user)
    else:
        return user


def base_roles_of(some_roles):
    base_roles = set([])
    for r in some_roles:
        if r in builtin_role_ids:
            base_roles.add(r)
        else:
            base_roles.add(roles[r]["basedon"])
    return list(base_roles)


def may_with_roles(some_role_ids, pname):
    # If at least one of the user's roles has this permission, it's fine
    for role_id in some_role_ids:
        role = roles[role_id]

        he_may = role.get("permissions", {}).get(pname)
        # Handle compatibility with permissions without "general." that
        # users might have saved in their own custom roles.
        if he_may == None and pname.startswith("general."):
            he_may = role.get("permissions", {}).get(pname[8:])

        if he_may == None: # not explicitely listed -> take defaults
            if "basedon" in role:
                base_role_id = role["basedon"]
            else:
                base_role_id = role_id
            if pname not in permissions_by_name:
                return False # Permission unknown. Assume False. Functionality might be missing
            perm = permissions_by_name[pname]
            he_may = base_role_id in perm["defaults"]
        if he_may:
            return True
    return False


def may(pname):
    global user_permissions
    if pname in user_permissions:
        return user_permissions[pname]
    he_may = may_with_roles(user_role_ids, pname)
    user_permissions[pname] = he_may
    return he_may

def user_may(user_id, pname):
    return may_with_roles(roles_of_user(user_id), pname)

def need_permission(pname):
    if not may(pname):
        perm = permissions_by_name[pname]
        raise MKAuthException(_("We are sorry, but you lack the permission "
                              "for this operation. If you do not like this "
                              "then please ask you administrator to provide you with "
                              "the following permission: '<b>%s</b>'.") % perm["title"])

def permission_exists(pname):
    return pname in permissions_by_name

def get_role_permissions():
    role_permissions = {}
    # Loop all permissions
    # and for each permission loop all roles
    # and check wether it has the permission or not

    roleids = roles.keys()
    for perm in permissions_by_order:
        for role_id in roleids:
            if not role_id in role_permissions:
                role_permissions[role_id] = []

            if may_with_roles([role_id], perm['name']):
                role_permissions[role_id].append(perm['name'])
    return role_permissions


def load_stars():
    return set(load_user_file("favorites", []))

def save_stars(stars):
    save_user_file("favorites", list(stars))


# Helper functions
def load_user_file(name, deflt, lock = False):
    # In some early error during login phase there are cases where it might
    # happen that a user file is requested byt the user_confdir is not yet
    # set. We have all information to set it, then do it.
    if user_confdir == None:
        if user_id:
            set_user_confdir(user_id)
        else:
            return deflt # No user known at this point of time

    path = user_confdir + "/" + name + ".mk"
    return store.load_data_from_file(path, deflt, lock)


def save_user_file(name, data, user=None):
    if user == None:
        user = user_id
    dirname = config_dir + "/" + user.encode("utf-8")
    make_nagios_directory(dirname)
    path = dirname + "/" + name + ".mk"
    store.save_data_to_file(path, data)


def user_file_modified(name):
    if user_confdir == None:
        return 0

    try:
        return os.stat(user_confdir + "/" + name + ".mk").st_mtime
    except OSError, e:
        if e.errno == errno.ENOENT:
            return 0
        else:
            raise

#.
#   .--Sites---------------------------------------------------------------.
#   |                        ____  _ _                                     |
#   |                       / ___|(_) |_ ___  ___                          |
#   |                       \___ \| | __/ _ \/ __|                         |
#   |                        ___) | | ||  __/\__ \                         |
#   |                       |____/|_|\__\___||___/                         |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  The config module provides some helper functions for sites.         |
#   '----------------------------------------------------------------------'

def omd_site():
    return os.environ["OMD_SITE"]

def url_prefix():
    return "/%s/" % omd_site()

use_siteicons = False

def default_single_site_configuration():
    return {
        omd_site(): {
            'alias'        : _("Local site %s") % omd_site(),
            'disable_wato' : True,
            'disabled'     : False,
            'insecure'     : False,
            'multisiteurl' : '',
            'persist'      : False,
            'replicate_ec' : False,
            'replication'  : '',
            'timeout'      : 10,
            'user_login'   : True,
    }}

sites = default_single_site_configuration()

def sitenames():
    return sites.keys()

def allsites():
    return dict( [(name, site(name))
                  for name in sitenames()
                  if not site(name).get("disabled", False)
                     and site(name)['socket'] != 'disabled' ] )

def sorted_sites():
    sitenames = []
    for sitename, site in allsites().iteritems():
        sitenames.append((sitename, site['alias']))
    sitenames = sorted(sitenames, key=lambda k: k[1], cmp = lambda a,b: cmp(a.lower(), b.lower()))

    return sitenames


def site(site_id):
    s = dict(sites.get(site_id, {}))
    # Now make sure that all important keys are available.
    # Add missing entries by supplying default values.
    s.setdefault("alias", site_id)
    s.setdefault("socket", "unix:" + cmk.paths.livestatus_unix_socket)
    s.setdefault("url_prefix", "../") # relative URL from /check_mk/
    if type(s["socket"]) == tuple and s["socket"][0] == "proxy":
        s["cache"] = s["socket"][1].get("cache", True)
        s["socket"] = "unix:" + cmk.paths.livestatus_unix_socket + "proxy/" + site_id
    else:
        s["cache"] = False
    s["id"] = site_id
    return s


def site_is_local(site_name):
    s = sites.get(site_name, {})
    sock = s.get("socket")
    return not sock or sock == "unix:" + cmk.paths.livestatus_unix_socket


def default_site():
    for site_name, site in sites.items():
        if site_is_local(site_name):
            return site_name
    return None



def is_multisite():
    # TODO: Remove all calls of this function
    return True

def is_single_local_site():
    if len(sites) > 1:
        return False
    elif len(sites) == 0:
        return True
    else:
        # Also use Multisite mode if the one and only site is not local
        sitename = sites.keys()[0]
        return site_is_local(sitename)

def read_site_config():
    global user_siteconf
    user_siteconf = load_user_file("siteconfig", {})

def save_site_config():
    save_user_file("siteconfig", user_siteconf)

#.
#   .--Plugins-------------------------------------------------------------.
#   |                   ____  _             _                              |
#   |                  |  _ \| |_   _  __ _(_)_ __  ___                    |
#   |                  | |_) | | | | |/ _` | | '_ \/ __|                   |
#   |                  |  __/| | |_| | (_| | | | | \__ \                   |
#   |                  |_|   |_|\__,_|\__, |_|_| |_|___/                   |
#   |                                 |___/                                |
#   +----------------------------------------------------------------------+
#   |  Handling of our own plugins. In plugins other software pieces can   |
#   |  declare defaults for configuration variables.                       |
#   '----------------------------------------------------------------------'

def load_plugins(force):
    load_web_plugins("config", globals())

    # Make sure, builtin roles are present, even if not modified and saved with WATO.
    for br in builtin_role_ids:
        roles.setdefault(br, {})
