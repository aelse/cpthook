---
layout: page
title:  "cpthook"
sidebartitle: "About"
permalink: /
---
cpthook is a git hook manager.

## About

If you use a central repository manager such as gitolite or gitosis you
probably have at least a few repositories using custom git hooks.

Managing the hooks in all your repositories by hand, is time consuming
and prone to error. If you need to take advantage of the functionality
provided by more than one hook script you are left to do it yourself.

cpthook allows you to run more than one hook in each repo and manage
them all in one location.

## Configuration Example

This is a basic configuration file which adds a single hook to a single
repository.

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

## Getting Started

Please see the Getting Started page for information on how to install
and use cpthook to manage hooks in your repositories.
