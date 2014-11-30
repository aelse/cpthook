CptHook
=======

If you use a central repository manager such as gitolite or gitosis you
probably have at least a few repositories using custom git hooks.

CptHook allows you to manage all your hooks from the one location.

Configuration Example
=====================

Here's a basic cpthook config adding a single hook to a single repository.

I have created a hook.cfg file under /repos/cpthook-admin,
which is a repository used just to store the cpthook config and any of
the hook scripts that we wish to manage.

    [cpthook]
    script-path = /repos/cpthook-admin/hooks.d
    repo-path = /repos

    [repos apu_repos]
    members = testrepo
    hooks = test_hooks

    [hooks test_hooks]
    post-commit = test-post-commit.sh

In the hooks.d directory I have a post-commit directory with a test
script: hooks.d/post-commit/test-post-commit.sh

    #!/bin/bash
    # Example hook script

    echo -e "\e[0;33mThis is a test hook script saying hi.\e[0m"
    exit 0

To activate the hooks I've enabled in the configuration file, I run

    $ cpthook --config=hook.cfg --init

If no errors are reported then a wrapper script should have been
installed as the post-commit hook for my testrepo.  The script will
run cpthook instructing it to run the post-commit hooks configured for
this repository.  

The path of the hook will vary depending on whether it is a bare
repository or not. In my case it can be found at:
/repos/testrepo/.git/hooks/post-commit

Now when I commit a change to this repository the hook script I've
configured will run.

    $ date > somefile; git commit -a -m "test"
    This is a test hook script saying hi.
    [master 0d895ef] test
     1 file changed, 1 insertion(+), 1 deletion(-)

Getting Started
===============

You can install cpthook either system-wide or (better) into a
virtualenv. Clone this repo and within it run:

    $ python setup.py install

Providing it has installed correctly try the basic configuration example
given above on a local repository. Check that the permissions are
correct for your scripts under hooks.d. If the wrapper script has been
installed but the hooks don't seem to be firing you can attempt to run
cpthook manually by changing directory to the repository and running the
command from the wrapper script. eg:

    $ cd /repos/testrepo
    $ cpthook --config=/repos/cpthook-admin/hook.cfg --hook=post-commit

Once this is working have a look at the full configuration example to
see how you can make use of groups to simplify applying the same hooks
to many repositories.

Full Configuration Example
==========================

This example demonstrates the grouping features you can use in your
cpthook config to chain group memberships together.

A cpthook configuration file uses the python `ConfigParser` syntax.

    [cpthook]
    # Contains global configuration elements.

    # The hooks.d directory pointed to by script-path contains directories
    # named by hook type  eg. post-commit, update.
    # Hook scripts go into those directories.
    # A single script-path is supported.
    script-path = /path/to/hooks.d

    # One or more paths to locations where git repos may be found
    # eg. if repo-path = /tmp then repository 'foo' may be found
    # in /tmp/foo or perhaps /tmp/foo.git
    # Multiple paths may be specified.
    repo-path = /path/to/git/repos /more/git/repos
    
    # A cpthook config file contains repos and hooks.
    # repos define managed repositories
    # hooks define which hooks are used by repositories
    
    [repos my_repos_1]
    # Each repos group may contain zero or more git repositories
    # matching the directory names on the filesystem.
    # A repository will be matched with or without a .git suffix
    members = some_repo other_repo.git
    
    [repos my_repos_2]
    # A group may inherit members from another repo group with the
    # syntax @<group_name>
    members = another_repo @my_repos_1
    
    [repos repos_with_hooks]
    # And of course repo groups can refer to hook groups
    members = @my_repos_1
    hooks = some_hooks
    
    [repos inherit_hooks]
    # Hooks may also be inherited from repos groups
    members = @my_repos_2
    hooks = @repos_with_hooks
    
    [hooks some_hooks]
    # Lists of hooks may be defined for hook types supported by git
    # Referenced scripts are separated on the filesystem by hook type
    # eg. hooks.d/pre-receive/validate_style.sh
    pre-receive = validate_style.sh
    post-receive = trigger_build.sh

    # There is also a special global repo group. Hooks listed in the
    # global repo group are applied to all known repos.
    [repos *]
    hooks = global_hooks

    [hooks global_hooks]
    post-receive = post-receive-email.sh
