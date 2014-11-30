---
layout: page
title: "Getting Started"
sidebartitle: "Getting Started"
permalink: /
---
Here is how to get started using cpthook.

## Install cpthook

You can install cpthook either system-wide or into a virtualenv,
using pip or by cloning the repo from github and running the setup script.

### pip

In an activated virtualenv (or system-wide), run:

{% highlight bash %}
$ pip install cpthook
{% endhighlight %}

Usually you should install using pip. However, if you wish to install
the latest source you can use setup.py.

### setup.py

Clone this repo and within it run:

{% highlight bash %}
$ python setup.py install
{% endhighlight %}

## Running cpthook

Check that cpthook is working by running it with the --help flag.

{% highlight bash %}
$ cpthook --help
Usage: cpthook [options]

Options:
  -h, --help            show this help message and exit
  -c FILE, --config=FILE
                        cpthook config file
  -v, --verbose         log verbose status information
  -d, --debug           log debug information
  --dry-run             perform a dry run, making no changes
  --validate            validate a config file, then exit
  --init                install configured hooks and repositories
  --hook=HOOK           the hook to run against the current repository
{% endhighlight %}

Providing it has installed correctly try the basic configuration example
below on a local repository.

## Troubleshooting

If you run into problems there are a few things you can check. Please also
let me know with a GitHub issue so that I can improve cpthook and its
documentation.

If the wrapper script has been
installed but the hooks don't seem to be firing you can attempt to run
cpthook manually by changing directory to the repository and running the
command from the wrapper script. eg:

{% highlight bash %}
$ cd /repos/testrepo
$ cpthook --config=/repos/cpthook-admin/hook.cfg --hook=post-commit
{% endhighlight %}

Also check that the permissions are correct for your scripts under hooks.d.

## Basic Configuration Example

This is a basic configuration file which adds a single hook to a single
repository.

I have created a hook.cfg file under `/repos/cpthook-admin`,
which is a repository used just to store the cpthook config and any of
the hook scripts that we wish to manage.

{% highlight ini %}
[cpthook]
script-path = /repos/cpthook-admin/hooks.d
repo-path = /repos

[repos my_test_repos]
members = testrepo
hooks = test_hooks

[hooks test_hooks]
post-commit = test-post-commit.sh
{% endhighlight %}

In the hooks.d directory I have a post-commit directory with a test
script: `hooks.d/post-commit/test-post-commit.sh`

{% highlight bash %}
#!/bin/bash
# Example hook script
echo -e "\e[0;33mThis is a test hook script saying hi.\e[0m"
exit 0
{% endhighlight %}

To activate the hooks enabled in the configuration file, I run:

{% highlight bash %}
$ cpthook --config=hook.cfg --init
{% endhighlight %}

Now when I commit locally to this repository I should see the message
output by `test-post-commit.sh`.

Once this is working have a look at the full configuration example to
see how you can make use of groups to simplify applying the same hooks
to many repositories.

## Full Configuration Example

This example demonstrates the grouping features you can use in your
cpthook config to chain group memberships together.

A cpthook configuration file uses the python `ConfigParser` syntax.

{% highlight ini %}
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
{% endhighlight %}
