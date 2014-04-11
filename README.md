CptHook
=======

If you use a central repository manager such as gitolite or gitosis you
probably have at least a few repositories using custom git hooks.

CptHook allows you to manage all your hooks from the one location.

Configuration File Example
==========================

A cpthook configuration file uses the python `ConfigParser` syntax.

    [cpthook]
    # Contains global configuration elements.
    
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
