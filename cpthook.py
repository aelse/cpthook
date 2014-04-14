#!/usr/bin/env python

import inspect
import logging
import os
import os.path
import re
import subprocess


# Supported hooks - see
# https://www.kernel.org/pub/software/scm/git/docs/githooks.html
supported_hooks = [
    'applypatch-msg',
    'pre-applypatch',
    'post-applypatch',
    'pre-commit',
    'prepare-commit-msg',
    'commit-msg',
    'post-commit',
    'pre-rebase',
    'post-checkout',
    'post-merge',
    'pre-receive',
    'update',
    'post-receive',
    'post-update',
    'pre-auto-gc',
    'post-rewrite',
]


class CyclicalDependencyException(Exception):
    """Unresolvable group dependency encountered"""
    pass


class UnknownDependencyException(Exception):
    """Unknown group dependency encountered"""
    pass


class UnknownConfigElementException(Exception):
    """Unexpected configuration element encountered"""
    pass


class NoSuchRepoGroupException(Exception):
    """Repository group does not exist"""
    pass


class NoSuchHookGroupException(Exception):
    """Hook group does not exist"""
    pass


class CptHookConfig(object):
    """An object representing a cpthook configuration"""

    def __init__(self, config_file):
        if not os.path.isfile(config_file):
            raise IOError('No such file {0}'.format(config_file))

        global_config, repo_groups, hook_groups = self._parse_config(config_file)

        self.config_file = config_file
        self.global_config = global_config
        self.repo_groups = repo_groups
        self.hook_groups = hook_groups

        self._normalise_repo_groups('members')
        self._normalise_repo_groups('hooks')
        self._set_missing_globals()

    def _set_missing_globals(self):
        """Set global configuration for all repositories

        Performed in case global settings are not configured in the
        cpthook configuration block in the config file"""

        if 'script-path' not in self.global_config:
            # Default location of hooks.d to config directory
            self.global_config['script-path'] = os.path.join(
                os.path.dirname(self.config_file), 'hooks.d')

        if 'repo-path' not in self.global_config:
            # Default location of hooks.d to config directory
            self.global_config['repo-path'] = [os.path.normpath(
                os.path.join('..', os.path.dirname(self.config_file)))]

    def _normalise_repo_groups(self, option):
        """Resolve inherited memberships"""

        data = self.repo_groups
        tainted = data.keys()
        round_ = 0
        while tainted:
            round_ += 1
            logging.debug('Normalise {0}: round {1}'.format(option, round_))

            did_work = False

            for item in tainted:
                try:
                    members = data[item][option]
                except KeyError:
                    logging.debug('Removed empty item {0}'.format(item))
                    tainted.remove(item)
                    did_work = True
                    continue

                unresolved = [x for x in members if x.startswith('@')]
                if len(unresolved) == 0:
                    logging.debug('Nothing to resolve in {0}'.format(item))
                    tainted.remove(item)
                    did_work = True
                    continue

                resolved = []
                dirty = False
                for member in unresolved:
                    mem = member.lstrip('@')
                    try:
                        new_members = data[mem][option]
                    except KeyError:
                        raise UnknownDependencyException(member)
                    for new_mem in new_members:
                        if new_mem.startswith('@'):
                            # Unresolved membership in upstream group
                            dirty = True
                            break
                    resolved += new_members

                if not dirty:
                    # No dependencies remain - replace resolved groups
                    for member in unresolved:
                        members.remove(member)
                    members += resolved
                    data[item][option] = members
                    did_work = True

            if did_work is False:
                raise CyclicalDependencyException(','.join(tainted))
        self.repo_groups = data

    def _parse_config(self, filename):
        """Parse config file and return global, repo and hook config"""

        import ConfigParser
        parser = ConfigParser.SafeConfigParser()
        parser.read(filename)

        # Record the groups as defined in the config
        conf_repos = {}
        conf_hooks = {}
        conf = {}

        for section in parser.sections():
            logging.debug('Evaluating block {0}'.format(section))
            if section.startswith('repos '):
                repo_group = re.sub('^repos\s+', '', section)
                logging.debug('Found repo {0}'.format(repo_group))
                conf_repos[repo_group] = {}
                for option in ['members', 'hooks']:
                    try:
                        values = parser.get(section, option).split()
                        logging.debug('{0} -> {1} -> {2}'.format(
                            section, option, values))
                        conf_repos[repo_group][option] = values
                    except ConfigParser.NoOptionError:
                        # No members
                        logging.debug('No {0} in {1}'.format(
                            option, section))
            elif section.startswith('hooks '):
                hook_group = re.sub('^hooks\s+', '', section)
                logging.debug('Found hook {0}'.format(hook_group))
                conf_hooks[hook_group] = {}
                for type_ in supported_hooks:
                    try:
                        vals = parser.get(section, type_).split()
                        conf_hooks[hook_group][type_] = vals
                    except ConfigParser.NoOptionError:
                        # No hooks of that type
                        pass
            elif section == 'cpthook':
                try:
                    sp = parser.get(section, 'script-path').split()
                    conf['script-path'] = sp[0]
                except ConfigParser.NoOptionError:
                    # No defined repository search path
                    pass
                try:
                    rp = parser.get(section, 'repo-path').split()
                    conf['repo-path'] = rp
                except ConfigParser.NoOptionError:
                    # No defined repository search path
                    pass
            else:
                raise UnknownConfigElementException(
                    'Unknown config element {0}'.format(section))

        return conf, conf_repos, conf_hooks

    def _aggregate_hooks(self, hook_groups):
        if not hasattr(hook_groups, '__iter__'):
            # Check for __iter__ attribute rather than iter(),
            # which also captures strings.
            raise ValueError('hook_groups must be iterable')

        hooks = {}
        logging.debug('Aggregating hooks for hook groups {0}'.format(
            hook_groups))
        for hook_group in hook_groups:
            logging.debug('Evaluating hook group {0}'.format(hook_group))
            try:
                hg = self.hook_groups[hook_group]
                logging.debug('hg {0} -> {1}'.format(hook_group, hg))
            except KeyError:
                raise NoSuchHookGroupException(hook_group)
            for hook_type, hook_list in hg.items():
                if hook_type not in hooks:
                    hooks[hook_type] = hook_list
                else:
                    for hook in hook_list:
                        if hook not in hooks[hook_type]:
                            hooks[hook_type].append(hook)
        return hooks

    def repo_group_membership(self, repo):
        """Returns list of repo group membership for repo"""

        membership = []
        for repo_group, data in self.repo_groups.items():
            try:
                group_members = data['members']
            except KeyError:
                continue
            if repo in group_members:
                if repo not in membership:
                    membership.append(repo_group)
        logging.debug('{0} is a member of {1}'.format(repo, membership))
        return membership

    def repo_group_hook_groups(self, repo):
        """Returns list of repo group membership for repo"""

        # 1. Get repo group membership for repo
        repo_groups = self.repo_group_membership(repo)

        # 2. Combine lists of hook groups from repo groups
        membership = []
        for repo_group in repo_groups:
            try:
                hook_groups = self.repo_groups[repo_group]['hooks']
            except KeyError:
                logging.debug('No hook groups in {0}'.format(repo_group))
                continue
            for hook_group in hook_groups:
                if hook_group not in membership:
                    membership.append(hook_group)
        if not len(membership):
            logging.debug('No hook groups for {0}'.format(repo))
        return membership

    def hooks_for_repo(self, repo):
        """Returns dict of hooks to be applied to a repository"""

        # 1. Get hook group membership for repo
        hook_groups = self.repo_group_hook_groups(repo)

        # 2. Build dict of hooks from those hook groups
        hooks = self._aggregate_hooks(hook_groups)

        return hooks

    def repos(self):
        """Returns list of known repos"""

        rg = self.repo_groups
        members_by_group = map(lambda x: x['members'], rg.values())
        members = reduce(lambda x, y: set(x + y), members_by_group)
        return list(members)


class CptHook(object):

    def __init__(self, config_file):
        self.config_file = config_file
        self.config = CptHookConfig(config_file)
        self.dry_run = False


    def _script_name(self):
        file_ = inspect.getfile(inspect.currentframe())
        return os.path.abspath(os.path.realpath(file_))


    def add_hooks_to_repo(self, repo_path, hooks):
        template = (
            "#!/bin/sh\n"
            "#\n"
            "# MAGIC STRING: cpthook-wrapper (do not remove)\n"
            "{0} --config={1} --hook={2}\n"
        )

        config_file = os.path.realpath(self.config_file)
        hook_path = os.path.join(repo_path, 'hooks')
        if not os.path.isdir(hook_path):
            logging.warn('Hook path {0} is not a directory'.format(hook_path))
            return

        cpthook = self._script_name()

        for hook_type in hooks:
            target = os.path.join(repo_path, 'hooks', hook_type)
            if os.path.exists(target):
                if os.path.isfile(target):
                    try:
                        f = open(target, 'r')
                    except:
                        logging.info('Could not read {0}'.format(target))
                        continue
                    header = f.read(100)
                    if header.find('cpthook-wrapper') == -1:
                        logging.warn('{0} hook {1} is not managed by cpthook. '
                                     'Refusing to overwrite'.format(
                                         os.path.basename(repo_path), hook_type))
                        continue
                else:
                    logging.info('{0} exists but is not a file'.format(target))
                    continue

            if self.dry_run:
                logging.info('Dry run. Skipping write to {0}'.format(target))
                continue

            try:
                f = open(target, 'w')
            except:
                logging.warn('Could not write wrapper {0}'.format(target))
                continue

            try:
                wrapper = template.format(cpthook, config_file, hook_type)
                f.write(wrapper)
                f.close()
                os.chmod(target, 0755)
                logging.debug('Wrote {0} hook {1}'.format(
                    os.path.basename(repo_path), hook_type))
            except:
                logging.warn('Failed to create wrapper {0}'.format(target))


    def _locate_repo(self, repo):
        """Find repository location for a given repository name"""

        # Locate by matching 4 common naming cases
        # 1. path/repo
        # 2. path/repo/.git
        # 3. path/repo.git
        # 4. path/repo.git/.git

        search_paths = self.config.global_config['repo-path']
        for path in search_paths:
            path_ = os.path.join(path, repo)
            if os.path.exists(os.path.join(path_, 'hooks')):
                return path_
            path_ = os.path.join(path, repo, '.git')
            if os.path.exists(os.path.join(path_, 'hooks')):
                return path_
            path_ = os.path.join(path, repo + '.git')
            if os.path.exists(os.path.join(path_, 'hooks')):
                return path_
            path_ = os.path.join(path, repo + '.git', '.git')
            if os.path.exists(os.path.join(path_, 'hooks')):
                return path_
        return None


    def install_hooks(self):
        for repo in self.config.repos():
            logging.debug('Examining repo {0}'.format(repo))
            repo_path = self._locate_repo(repo)
            if repo_path is None:
                logging.info('Could not locate repo {0}'.format(repo))
                continue
            hooks = self.config.hooks_for_repo(repo).keys()
            self.add_hooks_to_repo(repo_path, hooks)


    def _abs_script_name(self, hook, script):
        hooksd_path = self.config.global_config['script-path']
        script_file = os.path.join(hooksd_path, hook, script)
        logging.debug('Script path {0}'.format(script_file))
        return script_file


    def run_hook(self, hook, args):
        ret = subprocess.call(['git', 'rev-parse'])
        if ret != 0:
            logging.warn('{0} is not a git repo?'.format(
                os.path.realpath(os.path.curdir)))
            return -1
        # Work out the repository name from the current directory
        repo = os.path.basename(os.path.realpath(os.path.curdir))

        hooks = self.config.hooks_for_repo(repo)
        if hook in hooks:
            logging.info('Found {0} hooks'.format(hook))
            for script in hooks[hook]:
                script_file = self._abs_script_name(hook, script)
                if not os.path.exists(script_file):
                    logging.info('{0} hook {1} does not exist'.format(
                        hook, script))
                if self.dry_run:
                    logging.info('Dry-run: skipping {0} script {1}'.format(
                        repo, script))
                    continue
                logging.info('Running {0} hook {1}'.format(hook, script))
                ret = subprocess.call([script_file] + args)
                if ret != 0:
                    logging.info(
                        'Received non-zero return code from {0}'.format(script))
                    return ret
        return 0
